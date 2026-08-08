import stripe

from app.integrations.interfaces.payment_client import (
    CheckoutSession,
    PaymentError,
    PortalSession,
    PriceInfo,
)


class StripePaymentClient:
    """Usa o SDK oficial `stripe` (mesma razão do `ClaudeAnalysisClient` para a Anthropic: chamada
    à própria API do provedor). Métodos `*_async` do SDK usam `httpx` internamente quando `httpx` +
    `anyio` estão instalados (já são, via FastAPI/anthropic) — sem precisar de `asyncio.to_thread`.
    `api_key` é passado explicitamente em cada chamada em vez de mutar `stripe.api_key` global."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def create_checkout_session(
        self,
        *,
        price_id: str,
        client_reference_id: str,
        success_url: str,
        cancel_url: str,
        customer_id: str | None,
        customer_email: str | None,
    ) -> CheckoutSession:
        if not self._api_key:
            raise PaymentError("STRIPE_SECRET_KEY não configurado")

        params = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "client_reference_id": client_reference_id,
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        # Stripe aceita `customer` OU `customer_email`, nunca os dois — reaproveitar o customer
        # existente evita criar um Customer duplicado na Stripe para quem já assinou antes.
        if customer_id:
            params["customer"] = customer_id
        elif customer_email:
            params["customer_email"] = customer_email

        try:
            session = await stripe.checkout.Session.create_async(api_key=self._api_key, **params)
        except stripe.StripeError as exc:
            raise PaymentError(str(exc)) from exc

        if not session.url:
            raise PaymentError("Stripe não retornou uma URL de checkout")
        return CheckoutSession(url=session.url)

    async def create_portal_session(self, *, customer_id: str, return_url: str) -> PortalSession:
        if not self._api_key:
            raise PaymentError("STRIPE_SECRET_KEY não configurado")

        try:
            session = await stripe.billing_portal.Session.create_async(
                api_key=self._api_key, customer=customer_id, return_url=return_url
            )
        except stripe.StripeError as exc:
            raise PaymentError(str(exc)) from exc

        return PortalSession(url=session.url)

    async def get_price(self, price_id: str) -> PriceInfo:
        if not self._api_key:
            raise PaymentError("STRIPE_SECRET_KEY não configurado")

        try:
            price = await stripe.Price.retrieve_async(price_id, api_key=self._api_key)
        except stripe.StripeError as exc:
            raise PaymentError(str(exc)) from exc

        if price.unit_amount is None:
            raise PaymentError(f"Price {price_id} não tem unit_amount (preço não fixo?)")

        interval = price.recurring.interval if price.recurring else None
        return PriceInfo(unit_amount=price.unit_amount, currency=price.currency, interval=interval)

    async def get_subscription(self, subscription_id: str) -> dict:
        if not self._api_key:
            raise PaymentError("STRIPE_SECRET_KEY não configurado")

        try:
            subscription = await stripe.Subscription.retrieve_async(
                subscription_id, api_key=self._api_key
            )
        except stripe.StripeError as exc:
            raise PaymentError(str(exc)) from exc

        return subscription.to_dict()
