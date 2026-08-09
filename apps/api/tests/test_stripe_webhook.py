import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.core.config import Settings, get_settings
from app.core.dependencies import get_billing_service
from app.main import app

WEBHOOK_SECRET = "whsec_test_secret"


def _sign(payload: bytes, secret: str = WEBHOOK_SECRET) -> str:
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload.decode()}"
    signature = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def _settings_with_secret() -> Settings:
    return Settings(stripe_webhook_secret=WEBHOOK_SECRET)


async def test_returns_503_when_webhook_secret_not_configured(client: AsyncClient) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(stripe_webhook_secret="")

    response = await client.post("/api/v1/webhooks/stripe", content=b"{}")

    assert response.status_code == 503

    app.dependency_overrides.clear()


async def test_returns_401_on_invalid_signature(client: AsyncClient) -> None:
    app.dependency_overrides[get_settings] = _settings_with_secret

    response = await client.post(
        "/api/v1/webhooks/stripe",
        content=b"{}",
        headers={"stripe-signature": "t=1,v1=invalid"},
    )

    assert response.status_code == 401

    app.dependency_overrides.clear()


async def test_returns_401_when_signature_header_missing(client: AsyncClient) -> None:
    app.dependency_overrides[get_settings] = _settings_with_secret

    response = await client.post("/api/v1/webhooks/stripe", content=b"{}")

    assert response.status_code == 401

    app.dependency_overrides.clear()


async def test_returns_204_and_dispatches_event_on_valid_signature(client: AsyncClient) -> None:
    fake_service = AsyncMock()
    payload = json.dumps(
        {
            "id": "evt_1",
            "object": "event",
            "type": "invoice.payment_failed",
            "data": {"object": {"customer": "cus_1"}},
        }
    ).encode()

    app.dependency_overrides[get_settings] = _settings_with_secret
    app.dependency_overrides[get_billing_service] = lambda: fake_service

    response = await client.post(
        "/api/v1/webhooks/stripe",
        content=payload,
        headers={
            "stripe-signature": _sign(payload),
            "content-type": "application/json",
        },
    )

    assert response.status_code == 204
    fake_service.handle_webhook_event.assert_awaited_once()
    dispatched_event = fake_service.handle_webhook_event.await_args.args[0]
    assert dispatched_event["type"] == "invoice.payment_failed"
    assert dispatched_event["data"]["object"]["customer"] == "cus_1"

    app.dependency_overrides.clear()
