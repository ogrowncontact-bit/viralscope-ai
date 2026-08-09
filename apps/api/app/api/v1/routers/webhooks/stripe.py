import logging
from typing import Annotated

import stripe as stripe_sdk
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import SettingsDep, get_billing_service
from app.services.billing_service import BillingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", status_code=status.HTTP_204_NO_CONTENT)
async def handle_stripe_webhook(
    request: Request,
    settings: SettingsDep,
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> None:
    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STRIPE_WEBHOOK_SECRET não configurado",
        )

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe_sdk.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except (ValueError, stripe_sdk.SignatureVerificationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura inválida"
        ) from exc

    await billing_service.handle_webhook_event(event.to_dict())
