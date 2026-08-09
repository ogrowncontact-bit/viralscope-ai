from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import SubscriptionPlan, SubscriptionStatus


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan: SubscriptionPlan
    status: SubscriptionStatus
    current_period_end: datetime | None


class PlanOut(BaseModel):
    id: SubscriptionPlan
    name: str
    price_cents: int | None
    currency: str | None
    interval: str | None


class CheckoutSessionIn(BaseModel):
    plan: SubscriptionPlan


class CheckoutSessionOut(BaseModel):
    url: str


class PortalSessionOut(BaseModel):
    url: str
