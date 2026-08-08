import httpx
import pytest
import respx
from httpx import Response

from app.integrations.interfaces.payment_client import PaymentError
from app.integrations.stripe_payment_client import StripePaymentClient

STRIPE_CHECKOUT_URL = "https://api.stripe.com/v1/checkout/sessions"
STRIPE_PORTAL_URL = "https://api.stripe.com/v1/billing_portal/sessions"
STRIPE_PRICE_URL = "https://api.stripe.com/v1/prices/price_123"
STRIPE_SUBSCRIPTION_URL = "https://api.stripe.com/v1/subscriptions/sub_123"


async def test_create_checkout_session_raises_without_api_key() -> None:
    client = StripePaymentClient(api_key="")

    with pytest.raises(PaymentError):
        await client.create_checkout_session(
            price_id="price_123",
            client_reference_id="user-1",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            customer_id=None,
            customer_email=None,
        )


@respx.mock
async def test_create_checkout_session_returns_url() -> None:
    route = respx.post(STRIPE_CHECKOUT_URL).mock(
        return_value=Response(
            200,
            json={
                "id": "cs_test_1",
                "object": "checkout.session",
                "url": "https://checkout.stripe.com/pay/cs_test_1",
            },
        )
    )

    client = StripePaymentClient(api_key="sk_test_fake")
    result = await client.create_checkout_session(
        price_id="price_123",
        client_reference_id="user-1",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        customer_id=None,
        customer_email="user@example.com",
    )

    assert result.url == "https://checkout.stripe.com/pay/cs_test_1"
    sent_body = route.calls.last.request.content.decode()
    assert "client_reference_id=user-1" in sent_body
    assert "customer_email=user%40example.com" in sent_body
    assert "mode=subscription" in sent_body


@respx.mock
async def test_create_checkout_session_uses_customer_id_over_email_when_both_given() -> None:
    route = respx.post(STRIPE_CHECKOUT_URL).mock(
        return_value=Response(
            200,
            json={
                "id": "cs_test_1",
                "object": "checkout.session",
                "url": "https://checkout.stripe.com/pay/cs_test_1",
            },
        )
    )

    client = StripePaymentClient(api_key="sk_test_fake")
    await client.create_checkout_session(
        price_id="price_123",
        client_reference_id="user-1",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        customer_id="cus_existing",
        customer_email="user@example.com",
    )

    sent_body = route.calls.last.request.content.decode()
    assert "customer=cus_existing" in sent_body
    assert "customer_email" not in sent_body


@respx.mock
async def test_create_checkout_session_omits_customer_email_when_absent() -> None:
    route = respx.post(STRIPE_CHECKOUT_URL).mock(
        return_value=Response(
            200,
            json={
                "id": "cs_test_1",
                "object": "checkout.session",
                "url": "https://checkout.stripe.com/pay/cs_test_1",
            },
        )
    )

    client = StripePaymentClient(api_key="sk_test_fake")
    await client.create_checkout_session(
        price_id="price_123",
        client_reference_id="user-1",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        customer_id=None,
        customer_email=None,
    )

    sent_body = route.calls.last.request.content.decode()
    assert "customer_email" not in sent_body
    assert "customer=" not in sent_body


@respx.mock
async def test_create_checkout_session_raises_on_stripe_error() -> None:
    respx.post(STRIPE_CHECKOUT_URL).mock(
        return_value=Response(
            400, json={"error": {"message": "No such price", "type": "invalid_request_error"}}
        )
    )

    client = StripePaymentClient(api_key="sk_test_fake")

    with pytest.raises(PaymentError):
        await client.create_checkout_session(
            price_id="price_invalid",
            client_reference_id="user-1",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            customer_id=None,
            customer_email=None,
        )


async def test_create_portal_session_raises_without_api_key() -> None:
    client = StripePaymentClient(api_key="")

    with pytest.raises(PaymentError):
        await client.create_portal_session(customer_id="cus_1", return_url="https://example.com")


@respx.mock
async def test_create_portal_session_returns_url() -> None:
    respx.post(STRIPE_PORTAL_URL).mock(
        return_value=Response(
            200,
            json={
                "id": "bps_1",
                "object": "billing_portal.session",
                "url": "https://billing.stripe.com/p/session/bps_1",
            },
        )
    )

    client = StripePaymentClient(api_key="sk_test_fake")
    result = await client.create_portal_session(
        customer_id="cus_1", return_url="https://example.com/dashboard/billing"
    )

    assert result.url == "https://billing.stripe.com/p/session/bps_1"


async def test_get_price_raises_without_api_key() -> None:
    client = StripePaymentClient(api_key="")

    with pytest.raises(PaymentError):
        await client.get_price("price_123")


@respx.mock
async def test_get_price_returns_price_info() -> None:
    respx.get(STRIPE_PRICE_URL).mock(
        return_value=Response(
            200,
            json={
                "id": "price_123",
                "object": "price",
                "unit_amount": 999,
                "currency": "brl",
                "recurring": {"interval": "month"},
            },
        )
    )

    client = StripePaymentClient(api_key="sk_test_fake")
    price = await client.get_price("price_123")

    assert price.unit_amount == 999
    assert price.currency == "brl"
    assert price.interval == "month"


@respx.mock
async def test_get_price_raises_when_unit_amount_missing() -> None:
    respx.get(STRIPE_PRICE_URL).mock(
        return_value=Response(
            200,
            json={
                "id": "price_123",
                "object": "price",
                "unit_amount": None,
                "currency": "brl",
                "recurring": None,
            },
        )
    )

    client = StripePaymentClient(api_key="sk_test_fake")

    with pytest.raises(PaymentError):
        await client.get_price("price_123")


@respx.mock
async def test_get_price_raises_on_connection_error() -> None:
    respx.get(STRIPE_PRICE_URL).mock(side_effect=httpx.ConnectError("boom"))

    client = StripePaymentClient(api_key="sk_test_fake")

    with pytest.raises(PaymentError):
        await client.get_price("price_123")


async def test_get_subscription_raises_without_api_key() -> None:
    client = StripePaymentClient(api_key="")

    with pytest.raises(PaymentError):
        await client.get_subscription("sub_123")


@respx.mock
async def test_get_subscription_returns_plain_dict() -> None:
    respx.get(STRIPE_SUBSCRIPTION_URL).mock(
        return_value=Response(
            200,
            json={
                "id": "sub_123",
                "object": "subscription",
                "customer": "cus_1",
                "status": "active",
                "items": {
                    "object": "list",
                    "data": [
                        {
                            "id": "si_1",
                            "object": "subscription_item",
                            "price": {"id": "price_pro", "object": "price"},
                            "current_period_end": 1_800_000_000,
                        }
                    ],
                },
            },
        )
    )

    client = StripePaymentClient(api_key="sk_test_fake")
    subscription = await client.get_subscription("sub_123")

    assert isinstance(subscription, dict)
    assert subscription["status"] == "active"
    assert subscription["items"]["data"][0]["price"]["id"] == "price_pro"
    assert subscription["items"]["data"][0]["current_period_end"] == 1_800_000_000


@respx.mock
async def test_get_subscription_raises_on_stripe_error() -> None:
    respx.get(STRIPE_SUBSCRIPTION_URL).mock(
        return_value=Response(
            404,
            json={"error": {"message": "No such subscription", "type": "invalid_request_error"}},
        )
    )

    client = StripePaymentClient(api_key="sk_test_fake")

    with pytest.raises(PaymentError):
        await client.get_subscription("sub_123")
