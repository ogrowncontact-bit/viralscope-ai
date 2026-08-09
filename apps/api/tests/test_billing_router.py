import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.core.dependencies import get_billing_service, get_current_user
from app.integrations.interfaces.payment_client import PaymentError
from app.main import app
from app.models.enums import SubscriptionPlan, SubscriptionStatus
from app.models.user import User
from app.schemas.subscription import PlanOut, SubscriptionOut

FAKE_USER = User(id=uuid.uuid4(), clerk_user_id="user_test", email="test@example.com")


async def _override_current_user() -> User:
    return FAKE_USER


async def test_get_subscription_returns_current_plan(client: AsyncClient) -> None:
    fake_service = AsyncMock()
    fake_service.get_subscription.return_value = SubscriptionOut(
        plan=SubscriptionPlan.PRO,
        status=SubscriptionStatus.ACTIVE,
        current_period_end=datetime(2026, 9, 1, tzinfo=UTC),
    )
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_billing_service] = lambda: fake_service

    response = await client.get("/api/v1/billing/subscription")

    assert response.status_code == 200
    assert response.json()["plan"] == "pro"
    fake_service.get_subscription.assert_awaited_once_with(FAKE_USER.id)

    app.dependency_overrides.clear()


async def test_list_plans_returns_all_plans(client: AsyncClient) -> None:
    fake_service = AsyncMock()
    fake_service.list_plans.return_value = [
        PlanOut(id=SubscriptionPlan.FREE, name="Free", price_cents=0, currency=None, interval=None),
        PlanOut(
            id=SubscriptionPlan.PRO, name="Pro", price_cents=999, currency="brl", interval="month"
        ),
    ]
    app.dependency_overrides[get_billing_service] = lambda: fake_service

    response = await client.get("/api/v1/billing/plans")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["price_cents"] == 999

    app.dependency_overrides.clear()


async def test_create_checkout_session_returns_url(client: AsyncClient) -> None:
    fake_service = AsyncMock()
    fake_service.create_checkout_session.return_value = "https://checkout.stripe.com/pay/cs_1"
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_billing_service] = lambda: fake_service

    response = await client.post("/api/v1/billing/checkout", json={"plan": "pro"})

    assert response.status_code == 200
    assert response.json()["url"] == "https://checkout.stripe.com/pay/cs_1"
    fake_service.create_checkout_session.assert_awaited_once_with(
        FAKE_USER.id, FAKE_USER.email, SubscriptionPlan.PRO
    )

    app.dependency_overrides.clear()


async def test_create_checkout_session_returns_400_on_payment_error(client: AsyncClient) -> None:
    fake_service = AsyncMock()
    fake_service.create_checkout_session.side_effect = PaymentError("Price ID não configurado")
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_billing_service] = lambda: fake_service

    response = await client.post("/api/v1/billing/checkout", json={"plan": "business"})

    assert response.status_code == 400

    app.dependency_overrides.clear()


async def test_create_portal_session_returns_url(client: AsyncClient) -> None:
    fake_service = AsyncMock()
    fake_service.create_portal_session.return_value = "https://billing.stripe.com/p/session/bps_1"
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_billing_service] = lambda: fake_service

    response = await client.post("/api/v1/billing/portal")

    assert response.status_code == 200
    assert response.json()["url"] == "https://billing.stripe.com/p/session/bps_1"

    app.dependency_overrides.clear()


async def test_create_portal_session_returns_400_when_no_subscription(
    client: AsyncClient,
) -> None:
    fake_service = AsyncMock()
    fake_service.create_portal_session.side_effect = PaymentError("sem assinatura")
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_billing_service] = lambda: fake_service

    response = await client.post("/api/v1/billing/portal")

    assert response.status_code == 400

    app.dependency_overrides.clear()
