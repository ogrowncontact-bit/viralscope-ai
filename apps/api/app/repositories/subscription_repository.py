import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SubscriptionPlan, SubscriptionStatus
from app.models.subscription import Subscription


class SqlAlchemySubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> Subscription | None:
        result = await self._session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_by_stripe_customer_id(self, stripe_customer_id: str) -> Subscription | None:
        result = await self._session.execute(
            select(Subscription).where(Subscription.stripe_customer_id == stripe_customer_id)
        )
        return result.scalar_one_or_none()

    async def upsert_by_user(
        self,
        user_id: uuid.UUID,
        *,
        stripe_customer_id: str,
        stripe_subscription_id: str | None,
        plan: SubscriptionPlan,
        status: SubscriptionStatus,
        current_period_end: datetime | None,
    ) -> Subscription:
        values = {
            "user_id": user_id,
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "plan": plan,
            "status": status,
            "current_period_end": current_period_end,
        }
        stmt = (
            insert(Subscription)
            .values(**values)
            .on_conflict_do_update(index_elements=[Subscription.user_id], set_=values)
            .returning(Subscription)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalar_one()

    async def update_from_stripe(
        self,
        stripe_customer_id: str,
        *,
        stripe_subscription_id: str | None,
        plan: SubscriptionPlan,
        status: SubscriptionStatus,
        current_period_end: datetime | None,
    ) -> Subscription | None:
        await self._session.execute(
            update(Subscription)
            .where(Subscription.stripe_customer_id == stripe_customer_id)
            .values(
                stripe_subscription_id=stripe_subscription_id,
                plan=plan,
                status=status,
                current_period_end=current_period_end,
            )
        )
        await self._session.commit()
        return await self._get_by_stripe_customer_id(stripe_customer_id)

    async def update_status(
        self, stripe_customer_id: str, status: SubscriptionStatus
    ) -> Subscription | None:
        await self._session.execute(
            update(Subscription)
            .where(Subscription.stripe_customer_id == stripe_customer_id)
            .values(status=status)
        )
        await self._session.commit()
        return await self._get_by_stripe_customer_id(stripe_customer_id)
