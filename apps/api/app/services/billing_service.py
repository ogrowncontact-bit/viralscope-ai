import asyncio
import logging
import uuid
from datetime import UTC, datetime

from app.integrations.interfaces.payment_client import PaymentClientProtocol, PaymentError
from app.models.enums import SubscriptionPlan, SubscriptionStatus
from app.repositories.interfaces.subscription_repository import SubscriptionRepositoryProtocol
from app.schemas.subscription import PlanOut, SubscriptionOut

logger = logging.getLogger(__name__)

_PLAN_NAMES: dict[SubscriptionPlan, str] = {
    SubscriptionPlan.FREE: "Free",
    SubscriptionPlan.PRO: "Pro",
    SubscriptionPlan.BUSINESS: "Business",
}

_STRIPE_STATUS_MAP: dict[str, SubscriptionStatus] = {
    "active": SubscriptionStatus.ACTIVE,
    "trialing": SubscriptionStatus.TRIALING,
    "past_due": SubscriptionStatus.PAST_DUE,
    "canceled": SubscriptionStatus.CANCELED,
    "incomplete": SubscriptionStatus.INCOMPLETE,
    "incomplete_expired": SubscriptionStatus.CANCELED,
    "unpaid": SubscriptionStatus.PAST_DUE,
}

# Status que indicam uma assinatura paga "em vigor" (mesmo com problema de pagamento) — usados
# para bloquear um segundo checkout paralelo enquanto uma assinatura já existe.
_ACTIVE_PAID_STATUSES = (
    SubscriptionStatus.ACTIVE,
    SubscriptionStatus.TRIALING,
    SubscriptionStatus.PAST_DUE,
)


class BillingService:
    """Preços de Pro/Business nunca são hardcoded: `list_plans` busca o valor ao vivo na Stripe
    via `PaymentClientProtocol.get_price`, usando os Price IDs configurados em `price_id_by_plan`
    (`STRIPE_PRICE_ID_PRO`/`STRIPE_PRICE_ID_BUSINESS`) — trocar o preço no Dashboard da Stripe não
    exige deploy. `Subscription` sem linha no banco (usuário nunca assinou) é tratada como Free.

    Nota sobre a API da Stripe: a partir da versão usada por este SDK, `current_period_end` não
    existe mais no nível raiz do objeto `Subscription` — só em cada `items.data[].price` (uma
    assinatura pode ter múltiplos itens). `_resolve_plan_and_period_end` lê os dois do mesmo
    primeiro item, assumindo (como o resto deste módulo) uma assinatura com um único item/preço.
    """

    def __init__(
        self,
        subscription_repository: SubscriptionRepositoryProtocol,
        payment_client: PaymentClientProtocol,
        price_id_by_plan: dict[SubscriptionPlan, str],
        frontend_url: str,
    ) -> None:
        self._subscription_repository = subscription_repository
        self._payment_client = payment_client
        self._price_id_by_plan = price_id_by_plan
        self._plan_by_price_id = {
            price_id: plan for plan, price_id in price_id_by_plan.items() if price_id
        }
        self._frontend_url = frontend_url.rstrip("/")

    async def get_subscription(self, user_id: uuid.UUID) -> SubscriptionOut:
        subscription = await self._subscription_repository.get_by_user_id(user_id)
        if subscription is None:
            return SubscriptionOut(
                plan=SubscriptionPlan.FREE,
                status=SubscriptionStatus.ACTIVE,
                current_period_end=None,
            )
        return SubscriptionOut.model_validate(subscription)

    async def list_plans(self) -> list[PlanOut]:
        free = PlanOut(
            id=SubscriptionPlan.FREE, name="Free", price_cents=0, currency=None, interval=None
        )
        pro, business = await asyncio.gather(
            self._describe_plan(SubscriptionPlan.PRO),
            self._describe_plan(SubscriptionPlan.BUSINESS),
        )
        return [free, pro, business]

    async def _describe_plan(self, plan: SubscriptionPlan) -> PlanOut:
        price_id = self._price_id_by_plan.get(plan)
        if not price_id:
            return PlanOut(
                id=plan, name=_PLAN_NAMES[plan], price_cents=None, currency=None, interval=None
            )
        try:
            price = await self._payment_client.get_price(price_id)
        except PaymentError:
            logger.exception("list_plans: falha ao buscar preço do plano %s na Stripe.", plan)
            return PlanOut(
                id=plan, name=_PLAN_NAMES[plan], price_cents=None, currency=None, interval=None
            )
        return PlanOut(
            id=plan,
            name=_PLAN_NAMES[plan],
            price_cents=price.unit_amount,
            currency=price.currency,
            interval=price.interval,
        )

    async def create_checkout_session(
        self, user_id: uuid.UUID, email: str | None, plan: SubscriptionPlan
    ) -> str:
        if plan == SubscriptionPlan.FREE:
            raise ValueError("Não é possível iniciar checkout para o plano Free")

        price_id = self._price_id_by_plan.get(plan)
        if not price_id:
            raise PaymentError(f"Nenhum Price ID configurado para o plano {plan.value}")

        existing = await self._subscription_repository.get_by_user_id(user_id)
        if (
            existing is not None
            and existing.plan != SubscriptionPlan.FREE
            and existing.status in _ACTIVE_PAID_STATUSES
        ):
            raise PaymentError(
                "Você já tem uma assinatura paga em vigor — use 'Gerenciar assinatura' para "
                "trocar de plano em vez de assinar um novo."
            )

        session = await self._payment_client.create_checkout_session(
            price_id=price_id,
            client_reference_id=str(user_id),
            success_url=f"{self._frontend_url}/dashboard/billing?checkout=success",
            cancel_url=f"{self._frontend_url}/dashboard/billing?checkout=cancel",
            customer_id=existing.stripe_customer_id if existing else None,
            customer_email=email,
        )
        return session.url

    async def create_portal_session(self, user_id: uuid.UUID) -> str:
        subscription = await self._subscription_repository.get_by_user_id(user_id)
        if subscription is None or not subscription.stripe_customer_id:
            raise PaymentError("Usuário ainda não possui uma assinatura Stripe ativa")

        session = await self._payment_client.create_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=f"{self._frontend_url}/dashboard/billing",
        )
        return session.url

    async def handle_webhook_event(self, event: dict) -> None:
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            await self._handle_checkout_completed(data)
        elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
            await self._handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(data)
        elif event_type == "invoice.payment_failed":
            await self._handle_payment_failed(data)
        else:
            logger.info("handle_webhook_event: evento %s ignorado.", event_type)

    async def _handle_checkout_completed(self, data: dict) -> None:
        raw_user_id = data.get("client_reference_id")
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        if not raw_user_id or not customer_id or not subscription_id:
            logger.warning(
                "checkout.session.completed sem client_reference_id/customer/subscription, "
                "ignorando."
            )
            return

        try:
            user_id = uuid.UUID(raw_user_id)
        except ValueError:
            logger.warning(
                "checkout.session.completed: client_reference_id %r não é um UUID válido, "
                "ignorando.",
                raw_user_id,
            )
            return

        # Busca o estado real da assinatura na hora, em vez de gravar um placeholder e esperar
        # customer.subscription.created/updated: a Stripe não garante ordem de entrega de
        # webhooks, então depender do próximo evento para popular plano/status corretos deixaria
        # a linha presa em Free/Incomplete se ele chegasse antes (ou nunca, num evento perdido).
        try:
            subscription_data = await self._payment_client.get_subscription(subscription_id)
        except PaymentError:
            logger.exception(
                "checkout.session.completed: falha ao buscar assinatura %s na Stripe.",
                subscription_id,
            )
            return

        plan, period_end = self._resolve_plan_and_period_end(subscription_data)
        status = _STRIPE_STATUS_MAP.get(
            subscription_data.get("status", ""), SubscriptionStatus.INCOMPLETE
        )

        await self._subscription_repository.upsert_by_user(
            user_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan=plan,
            status=status,
            current_period_end=period_end,
        )

    async def _handle_subscription_updated(self, data: dict) -> None:
        customer_id = data.get("customer")
        if not customer_id:
            return

        plan, period_end = self._resolve_plan_and_period_end(data)
        updated = await self._subscription_repository.update_from_stripe(
            customer_id,
            stripe_subscription_id=data.get("id"),
            plan=plan,
            status=_STRIPE_STATUS_MAP.get(data.get("status", ""), SubscriptionStatus.INCOMPLETE),
            current_period_end=period_end,
        )
        if updated is None:
            logger.warning(
                "customer.subscription.%s: nenhuma assinatura vinculada ao customer %s.",
                "created/updated",
                customer_id,
            )

    async def _handle_subscription_deleted(self, data: dict) -> None:
        customer_id = data.get("customer")
        if not customer_id:
            return

        await self._subscription_repository.update_from_stripe(
            customer_id,
            stripe_subscription_id=data.get("id"),
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.CANCELED,
            current_period_end=None,
        )

    async def _handle_payment_failed(self, data: dict) -> None:
        customer_id = data.get("customer")
        if not customer_id:
            return

        await self._subscription_repository.update_status(customer_id, SubscriptionStatus.PAST_DUE)

    def _resolve_plan_and_period_end(self, data: dict) -> tuple[SubscriptionPlan, datetime | None]:
        items = data.get("items", {}).get("data", [])
        if not items:
            return SubscriptionPlan.FREE, None

        item = items[0]
        price_id = item.get("price", {}).get("id")
        plan = self._plan_by_price_id.get(price_id, SubscriptionPlan.FREE)

        timestamp = item.get("current_period_end")
        period_end = datetime.fromtimestamp(timestamp, tz=UTC) if timestamp is not None else None
        return plan, period_end
