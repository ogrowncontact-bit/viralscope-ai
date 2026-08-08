from dataclasses import dataclass
from typing import Protocol


class PaymentError(Exception):
    """Falha ao chamar a API da Stripe (checkout, portal, consulta de preço)."""


@dataclass(frozen=True)
class CheckoutSession:
    url: str


@dataclass(frozen=True)
class PortalSession:
    url: str


@dataclass(frozen=True)
class PriceInfo:
    unit_amount: int
    """Valor em centavos (menor unidade da moeda), como a Stripe representa preços."""

    currency: str
    interval: str | None


class PaymentClientProtocol(Protocol):
    async def create_checkout_session(
        self,
        *,
        price_id: str,
        client_reference_id: str,
        success_url: str,
        cancel_url: str,
        customer_id: str | None,
        customer_email: str | None,
    ) -> CheckoutSession: ...

    async def create_portal_session(
        self, *, customer_id: str, return_url: str
    ) -> PortalSession: ...

    async def get_price(self, price_id: str) -> PriceInfo: ...

    async def get_subscription(self, subscription_id: str) -> dict: ...
