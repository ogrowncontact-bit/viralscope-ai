import uuid
from datetime import datetime
from typing import Protocol

from app.models.enums import SubscriptionPlan, SubscriptionStatus
from app.models.subscription import Subscription


class SubscriptionRepositoryProtocol(Protocol):
    async def get_by_user_id(self, user_id: uuid.UUID) -> Subscription | None: ...

    async def upsert_by_user(
        self,
        user_id: uuid.UUID,
        *,
        stripe_customer_id: str,
        stripe_subscription_id: str | None,
        plan: SubscriptionPlan,
        status: SubscriptionStatus,
        current_period_end: datetime | None,
    ) -> Subscription: ...

    async def update_from_stripe(
        self,
        stripe_customer_id: str,
        *,
        stripe_subscription_id: str | None,
        plan: SubscriptionPlan,
        status: SubscriptionStatus,
        current_period_end: datetime | None,
    ) -> Subscription | None: ...

    async def update_status(
        self, stripe_customer_id: str, status: SubscriptionStatus
    ) -> Subscription | None: ...
