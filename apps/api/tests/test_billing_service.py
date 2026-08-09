import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.integrations.interfaces.payment_client import (
    CheckoutSession,
    PaymentError,
    PortalSession,
    PriceInfo,
)
from app.models.enums import SubscriptionPlan, SubscriptionStatus
from app.models.subscription import Subscription
from app.services.billing_service import BillingService

PRICE_ID_BY_PLAN = {
    SubscriptionPlan.PRO: "price_pro",
    SubscriptionPlan.BUSINESS: "price_business",
}


def _make_service(subscription_repository=None, payment_client=None, price_id_by_plan=None):
    return BillingService(
        subscription_repository=subscription_repository or AsyncMock(),
        payment_client=payment_client or AsyncMock(),
        price_id_by_plan=price_id_by_plan if price_id_by_plan is not None else PRICE_ID_BY_PLAN,
        frontend_url="https://app.viralscope.ai/",
    )


def _make_subscription(**overrides) -> Subscription:
    defaults = dict(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        stripe_customer_id="cus_1",
        stripe_subscription_id="sub_1",
        plan=SubscriptionPlan.PRO,
        status=SubscriptionStatus.ACTIVE,
        current_period_end=datetime(2026, 9, 1, tzinfo=UTC),
    )
    defaults.update(overrides)
    return Subscription(**defaults)


async def test_get_subscription_returns_free_when_no_row_exists() -> None:
    subscription_repository = AsyncMock()
    subscription_repository.get_by_user_id.return_value = None
    service = _make_service(subscription_repository=subscription_repository)

    result = await service.get_subscription(uuid.uuid4())

    assert result.plan == SubscriptionPlan.FREE
    assert result.status == SubscriptionStatus.ACTIVE
    assert result.current_period_end is None


async def test_get_subscription_returns_existing_row() -> None:
    subscription_repository = AsyncMock()
    subscription_repository.get_by_user_id.return_value = _make_subscription()
    service = _make_service(subscription_repository=subscription_repository)

    result = await service.get_subscription(uuid.uuid4())

    assert result.plan == SubscriptionPlan.PRO
    assert result.status == SubscriptionStatus.ACTIVE


async def test_list_plans_includes_free_and_live_stripe_prices() -> None:
    prices_by_id = {
        "price_pro": PriceInfo(unit_amount=999, currency="brl", interval="month"),
        "price_business": PriceInfo(unit_amount=1899, currency="brl", interval="month"),
    }
    payment_client = AsyncMock()
    payment_client.get_price.side_effect = lambda price_id: prices_by_id[price_id]
    service = _make_service(payment_client=payment_client)

    plans = await service.list_plans()

    assert [p.id for p in plans] == [
        SubscriptionPlan.FREE,
        SubscriptionPlan.PRO,
        SubscriptionPlan.BUSINESS,
    ]
    assert plans[0].price_cents == 0
    assert plans[1].price_cents == 999
    assert plans[2].price_cents == 1899


async def test_list_plans_marks_price_unavailable_without_price_id_configured() -> None:
    service = _make_service(price_id_by_plan={SubscriptionPlan.PRO: ""})

    plans = await service.list_plans()

    pro_plan = next(p for p in plans if p.id == SubscriptionPlan.PRO)
    assert pro_plan.price_cents is None


async def test_list_plans_marks_price_unavailable_when_stripe_call_fails() -> None:
    payment_client = AsyncMock()
    payment_client.get_price.side_effect = PaymentError("boom")
    service = _make_service(payment_client=payment_client)

    plans = await service.list_plans()

    assert all(p.price_cents is None for p in plans if p.id != SubscriptionPlan.FREE)


async def test_create_checkout_session_raises_for_free_plan() -> None:
    service = _make_service()

    with pytest.raises(ValueError):
        await service.create_checkout_session(
            uuid.uuid4(), "user@example.com", SubscriptionPlan.FREE
        )


async def test_create_checkout_session_raises_when_price_id_not_configured() -> None:
    service = _make_service(price_id_by_plan={SubscriptionPlan.PRO: ""})

    with pytest.raises(PaymentError):
        await service.create_checkout_session(
            uuid.uuid4(), "user@example.com", SubscriptionPlan.PRO
        )


async def test_create_checkout_session_returns_url_for_new_customer() -> None:
    subscription_repository = AsyncMock()
    subscription_repository.get_by_user_id.return_value = None
    payment_client = AsyncMock()
    payment_client.create_checkout_session.return_value = CheckoutSession(
        url="https://checkout.stripe.com/pay/cs_1"
    )
    service = _make_service(
        subscription_repository=subscription_repository, payment_client=payment_client
    )
    user_id = uuid.uuid4()

    url = await service.create_checkout_session(user_id, "user@example.com", SubscriptionPlan.PRO)

    assert url == "https://checkout.stripe.com/pay/cs_1"
    payment_client.create_checkout_session.assert_awaited_once_with(
        price_id="price_pro",
        client_reference_id=str(user_id),
        success_url="https://app.viralscope.ai/dashboard/billing?checkout=success",
        cancel_url="https://app.viralscope.ai/dashboard/billing?checkout=cancel",
        customer_id=None,
        customer_email="user@example.com",
    )


async def test_create_checkout_session_reuses_existing_stripe_customer_id() -> None:
    subscription_repository = AsyncMock()
    subscription_repository.get_by_user_id.return_value = _make_subscription(
        plan=SubscriptionPlan.FREE,
        status=SubscriptionStatus.CANCELED,
        stripe_customer_id="cus_existing",
    )
    payment_client = AsyncMock()
    payment_client.create_checkout_session.return_value = CheckoutSession(
        url="https://checkout.stripe.com/pay/cs_1"
    )
    service = _make_service(
        subscription_repository=subscription_repository, payment_client=payment_client
    )
    user_id = uuid.uuid4()

    await service.create_checkout_session(user_id, "user@example.com", SubscriptionPlan.PRO)

    payment_client.create_checkout_session.assert_awaited_once_with(
        price_id="price_pro",
        client_reference_id=str(user_id),
        success_url="https://app.viralscope.ai/dashboard/billing?checkout=success",
        cancel_url="https://app.viralscope.ai/dashboard/billing?checkout=cancel",
        customer_id="cus_existing",
        customer_email="user@example.com",
    )


async def test_create_checkout_session_blocks_when_active_paid_subscription_exists() -> None:
    subscription_repository = AsyncMock()
    subscription_repository.get_by_user_id.return_value = _make_subscription(
        plan=SubscriptionPlan.PRO, status=SubscriptionStatus.ACTIVE
    )
    payment_client = AsyncMock()
    service = _make_service(
        subscription_repository=subscription_repository, payment_client=payment_client
    )

    with pytest.raises(PaymentError):
        await service.create_checkout_session(
            uuid.uuid4(), "user@example.com", SubscriptionPlan.BUSINESS
        )

    payment_client.create_checkout_session.assert_not_awaited()


async def test_create_checkout_session_allows_when_existing_subscription_is_canceled() -> None:
    subscription_repository = AsyncMock()
    subscription_repository.get_by_user_id.return_value = _make_subscription(
        plan=SubscriptionPlan.PRO, status=SubscriptionStatus.CANCELED
    )
    payment_client = AsyncMock()
    payment_client.create_checkout_session.return_value = CheckoutSession(
        url="https://checkout.stripe.com/pay/cs_1"
    )
    service = _make_service(
        subscription_repository=subscription_repository, payment_client=payment_client
    )

    url = await service.create_checkout_session(
        uuid.uuid4(), "user@example.com", SubscriptionPlan.BUSINESS
    )

    assert url == "https://checkout.stripe.com/pay/cs_1"


async def test_create_portal_session_raises_when_no_subscription() -> None:
    subscription_repository = AsyncMock()
    subscription_repository.get_by_user_id.return_value = None
    service = _make_service(subscription_repository=subscription_repository)

    with pytest.raises(PaymentError):
        await service.create_portal_session(uuid.uuid4())


async def test_create_portal_session_raises_when_no_stripe_customer_id() -> None:
    subscription_repository = AsyncMock()
    subscription_repository.get_by_user_id.return_value = _make_subscription(
        stripe_customer_id=None
    )
    service = _make_service(subscription_repository=subscription_repository)

    with pytest.raises(PaymentError):
        await service.create_portal_session(uuid.uuid4())


async def test_create_portal_session_returns_url() -> None:
    subscription_repository = AsyncMock()
    subscription_repository.get_by_user_id.return_value = _make_subscription(
        stripe_customer_id="cus_1"
    )
    payment_client = AsyncMock()
    payment_client.create_portal_session.return_value = PortalSession(
        url="https://billing.stripe.com/p/session/bps_1"
    )
    service = _make_service(
        subscription_repository=subscription_repository, payment_client=payment_client
    )

    url = await service.create_portal_session(uuid.uuid4())

    assert url == "https://billing.stripe.com/p/session/bps_1"
    payment_client.create_portal_session.assert_awaited_once_with(
        customer_id="cus_1", return_url="https://app.viralscope.ai/dashboard/billing"
    )


async def test_handle_checkout_completed_fetches_subscription_and_upserts() -> None:
    subscription_repository = AsyncMock()
    payment_client = AsyncMock()
    payment_client.get_subscription.return_value = {
        "id": "sub_1",
        "status": "active",
        "items": {
            "data": [{"price": {"id": "price_business"}, "current_period_end": 1_800_000_000}]
        },
    }
    service = _make_service(
        subscription_repository=subscription_repository, payment_client=payment_client
    )
    user_id = uuid.uuid4()

    await service.handle_webhook_event(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": str(user_id),
                    "customer": "cus_1",
                    "subscription": "sub_1",
                }
            },
        }
    )

    payment_client.get_subscription.assert_awaited_once_with("sub_1")
    subscription_repository.upsert_by_user.assert_awaited_once_with(
        user_id,
        stripe_customer_id="cus_1",
        stripe_subscription_id="sub_1",
        plan=SubscriptionPlan.BUSINESS,
        status=SubscriptionStatus.ACTIVE,
        current_period_end=datetime.fromtimestamp(1_800_000_000, tz=UTC),
    )


async def test_handle_checkout_completed_ignores_incomplete_payload() -> None:
    subscription_repository = AsyncMock()
    payment_client = AsyncMock()
    service = _make_service(
        subscription_repository=subscription_repository, payment_client=payment_client
    )

    await service.handle_webhook_event(
        {"type": "checkout.session.completed", "data": {"object": {"customer": "cus_1"}}}
    )

    payment_client.get_subscription.assert_not_awaited()
    subscription_repository.upsert_by_user.assert_not_awaited()


async def test_handle_checkout_completed_ignores_malformed_client_reference_id() -> None:
    subscription_repository = AsyncMock()
    payment_client = AsyncMock()
    service = _make_service(
        subscription_repository=subscription_repository, payment_client=payment_client
    )

    await service.handle_webhook_event(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": "not-a-uuid",
                    "customer": "cus_1",
                    "subscription": "sub_1",
                }
            },
        }
    )

    payment_client.get_subscription.assert_not_awaited()
    subscription_repository.upsert_by_user.assert_not_awaited()


async def test_handle_checkout_completed_skips_upsert_when_stripe_fetch_fails() -> None:
    subscription_repository = AsyncMock()
    payment_client = AsyncMock()
    payment_client.get_subscription.side_effect = PaymentError("boom")
    service = _make_service(
        subscription_repository=subscription_repository, payment_client=payment_client
    )

    await service.handle_webhook_event(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": str(uuid.uuid4()),
                    "customer": "cus_1",
                    "subscription": "sub_1",
                }
            },
        }
    )

    subscription_repository.upsert_by_user.assert_not_awaited()


async def test_handle_subscription_updated_resolves_plan_and_period_end_from_item() -> None:
    subscription_repository = AsyncMock()
    service = _make_service(subscription_repository=subscription_repository)

    await service.handle_webhook_event(
        {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_1",
                    "customer": "cus_1",
                    "status": "active",
                    "items": {
                        "data": [
                            {
                                "price": {"id": "price_business"},
                                "current_period_end": 1_800_000_000,
                            }
                        ]
                    },
                }
            },
        }
    )

    subscription_repository.update_from_stripe.assert_awaited_once_with(
        "cus_1",
        stripe_subscription_id="sub_1",
        plan=SubscriptionPlan.BUSINESS,
        status=SubscriptionStatus.ACTIVE,
        current_period_end=datetime.fromtimestamp(1_800_000_000, tz=UTC),
    )


async def test_handle_subscription_created_dispatches_same_as_updated() -> None:
    subscription_repository = AsyncMock()
    service = _make_service(subscription_repository=subscription_repository)

    await service.handle_webhook_event(
        {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_1",
                    "customer": "cus_1",
                    "status": "trialing",
                    "items": {
                        "data": [
                            {"price": {"id": "price_pro"}, "current_period_end": 1_800_000_000}
                        ]
                    },
                }
            },
        }
    )

    subscription_repository.update_from_stripe.assert_awaited_once_with(
        "cus_1",
        stripe_subscription_id="sub_1",
        plan=SubscriptionPlan.PRO,
        status=SubscriptionStatus.TRIALING,
        current_period_end=datetime.fromtimestamp(1_800_000_000, tz=UTC),
    )


async def test_handle_subscription_updated_defaults_to_free_for_unknown_price() -> None:
    subscription_repository = AsyncMock()
    service = _make_service(subscription_repository=subscription_repository)

    await service.handle_webhook_event(
        {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_1",
                    "customer": "cus_1",
                    "status": "active",
                    "items": {"data": [{"price": {"id": "price_unknown"}}]},
                }
            },
        }
    )

    call = subscription_repository.update_from_stripe.await_args
    assert call.kwargs["plan"] == SubscriptionPlan.FREE
    assert call.kwargs["current_period_end"] is None


async def test_handle_subscription_deleted_resets_to_free_canceled() -> None:
    subscription_repository = AsyncMock()
    service = _make_service(subscription_repository=subscription_repository)

    await service.handle_webhook_event(
        {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_1", "customer": "cus_1"}},
        }
    )

    subscription_repository.update_from_stripe.assert_awaited_once_with(
        "cus_1",
        stripe_subscription_id="sub_1",
        plan=SubscriptionPlan.FREE,
        status=SubscriptionStatus.CANCELED,
        current_period_end=None,
    )


async def test_handle_payment_failed_marks_past_due() -> None:
    subscription_repository = AsyncMock()
    service = _make_service(subscription_repository=subscription_repository)

    await service.handle_webhook_event(
        {"type": "invoice.payment_failed", "data": {"object": {"customer": "cus_1"}}}
    )

    subscription_repository.update_status.assert_awaited_once_with(
        "cus_1", SubscriptionStatus.PAST_DUE
    )


async def test_handle_webhook_event_ignores_unknown_event_types() -> None:
    subscription_repository = AsyncMock()
    service = _make_service(subscription_repository=subscription_repository)

    await service.handle_webhook_event({"type": "customer.created", "data": {"object": {}}})

    subscription_repository.upsert_by_user.assert_not_awaited()
    subscription_repository.update_from_stripe.assert_not_awaited()
    subscription_repository.update_status.assert_not_awaited()
