from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUserDep, get_billing_service
from app.integrations.interfaces.payment_client import PaymentError
from app.schemas.subscription import (
    CheckoutSessionIn,
    CheckoutSessionOut,
    PlanOut,
    PortalSessionOut,
    SubscriptionOut,
)
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])

BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]


@router.get("/subscription", response_model=SubscriptionOut)
async def get_subscription(
    current_user: CurrentUserDep, service: BillingServiceDep
) -> SubscriptionOut:
    return await service.get_subscription(current_user.id)


@router.get("/plans", response_model=list[PlanOut])
async def list_plans(service: BillingServiceDep) -> list[PlanOut]:
    return await service.list_plans()


@router.post("/checkout", response_model=CheckoutSessionOut)
async def create_checkout_session(
    body: CheckoutSessionIn,
    current_user: CurrentUserDep,
    service: BillingServiceDep,
) -> CheckoutSessionOut:
    try:
        url = await service.create_checkout_session(current_user.id, current_user.email, body.plan)
    except (ValueError, PaymentError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CheckoutSessionOut(url=url)


@router.post("/portal", response_model=PortalSessionOut)
async def create_portal_session(
    current_user: CurrentUserDep, service: BillingServiceDep
) -> PortalSessionOut:
    try:
        url = await service.create_portal_session(current_user.id)
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return PortalSessionOut(url=url)
