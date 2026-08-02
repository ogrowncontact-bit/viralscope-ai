from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.dependencies import SettingsDep, get_user_service
from app.services.user_service import UserService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _extract_profile(data: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    email_addresses = data.get("email_addresses") or []
    primary_email_id = data.get("primary_email_address_id")
    email = next(
        (e["email_address"] for e in email_addresses if e.get("id") == primary_email_id),
        email_addresses[0]["email_address"] if email_addresses else None,
    )
    full_name = " ".join(filter(None, [data.get("first_name"), data.get("last_name")])) or None
    avatar_url = data.get("image_url")
    return email, full_name, avatar_url


@router.post("/clerk", status_code=status.HTTP_204_NO_CONTENT)
async def handle_clerk_webhook(
    request: Request,
    settings: SettingsDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    if not settings.clerk_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CLERK_WEBHOOK_SECRET não configurado",
        )

    payload = await request.body()

    try:
        event = Webhook(settings.clerk_webhook_secret).verify(payload, dict(request.headers))
    except WebhookVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura inválida"
        ) from exc

    event_type = event.get("type")
    data = event.get("data", {})
    clerk_user_id = data.get("id")

    if event_type in {"user.created", "user.updated"} and clerk_user_id:
        email, full_name, avatar_url = _extract_profile(data)
        await user_service.sync_from_clerk(clerk_user_id, email, full_name, avatar_url)
    elif event_type == "user.deleted" and clerk_user_id:
        await user_service.delete_from_clerk(clerk_user_id)
