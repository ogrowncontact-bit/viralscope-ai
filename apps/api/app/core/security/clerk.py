from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from app.core.config import Settings, get_settings


class ClerkAuthError(Exception):
    """Erro de verificação do token de sessão do Clerk (assinatura, claims ou formato)."""


def decode_clerk_token(
    token: str,
    signing_key: str,
    issuer: str,
    allowed_parties: list[str] | None = None,
) -> dict[str, Any]:
    """Decodifica e valida um JWT de sessão do Clerk contra uma chave já resolvida via JWKS.

    Função pura (sem I/O) para poder ser testada com um par de chaves RSA gerado no teste,
    sem depender de credenciais reais do Clerk.
    """
    try:
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=issuer or None,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise ClerkAuthError(f"Token inválido: {exc}") from exc

    azp = claims.get("azp")
    if allowed_parties and azp is not None and azp not in allowed_parties:
        raise ClerkAuthError(f"Authorized party '{azp}' não permitida")

    return claims


@lru_cache
def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True)


def get_signing_key(token: str, jwks_url: str) -> str:
    try:
        client = _get_jwk_client(jwks_url)
        return client.get_signing_key_from_jwt(token).key
    except jwt.PyJWKClientError as exc:
        raise ClerkAuthError(f"Não foi possível resolver a chave de assinatura: {exc}") from exc


def verify_clerk_token(token: str, settings: Settings) -> dict[str, Any]:
    if not settings.clerk_jwks_url:
        raise ClerkAuthError("CLERK_JWKS_URL não configurado")

    signing_key = get_signing_key(token, settings.clerk_jwks_url)
    return decode_clerk_token(
        token,
        signing_key,
        issuer=settings.clerk_issuer,
        allowed_parties=settings.cors_origins,
    )


def get_current_user_id(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Dependency do FastAPI: extrai e valida o Bearer token do Clerk, retorna o `sub` (user id)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabeçalho Authorization ausente ou inválido",
        )

    token = authorization.split(" ", 1)[1]

    try:
        claims = verify_clerk_token(token, settings)
    except ClerkAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return claims["sub"]
