"""
Authentication utilities.

This module provides utilities for verifying LINE tokens:
- Access Token verification via LINE APIs
- ID Token verification with signature (RS256/ES256) and audience checks using JWKS

Notes:
- JWKS are cached in-memory with TTL to reduce network calls and support key rotation.
- In production, signature verification must be enabled and `LINE_CHANNEL_ID` must be set.
"""

import base64
import json
import logging
import threading
import time
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

logger = logging.getLogger(__name__)

# Constants for JWKS handling
JWKS_URL = "https://api.line.me/oauth2/v2.1/certs"
JWKS_TTL_SECONDS = 24 * 60 * 60  # 24 hours
HTTP_TIMEOUT_SECONDS = 5.0
SUPPORTED_ALGS = ["RS256", "ES256"]

# In-memory cache: (jwks_dict, fetched_at)
_JWKS_CACHE: tuple[dict[str, dict], float] | None = None
_JWKS_LOCK = threading.Lock()


def _base64url_decode_nopad(data: str) -> bytes:
    """
    Decode base64url string without padding.

    Args:
        data: Base64url encoded string without padding

    Returns:
        Decoded bytes
    """
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _load_jwks_from_network() -> dict[str, dict]:
    """
    Fetch JWKS from LINE and return a dict keyed by kid.

    Returns:
        Mapping of `kid` to JWK dict

    Raises:
        httpx.RequestError: On network errors
        ValueError: If JWKS payload is invalid
    """
    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = client.get(JWKS_URL)
        resp.raise_for_status()
        data = resp.json()
    keys = data.get("keys")
    if not isinstance(keys, list):
        raise TypeError("Invalid JWKS format: 'keys' not found")
    by_kid: dict[str, dict] = {}
    for jwk in keys:
        kid = jwk.get("kid")
        if isinstance(kid, str):
            by_kid[kid] = jwk
    return by_kid


def _get_cached_jwks(
    force_refresh: bool = False,
    allow_stale_on_error: bool = True,
) -> dict[str, dict]:
    """
    Get JWKS with caching and optional stale-if-error behavior.

    Args:
        force_refresh: If True, fetch from network regardless of TTL
        allow_stale_on_error: If True, return cached data when network fails

    Returns:
        Mapping of `kid` to JWK dict

    Raises:
        HTTPException: 503 when network fails and no cache is available
    """
    global _JWKS_CACHE

    now = time.time()
    # Decide whether to refresh
    need_refresh = force_refresh
    if _JWKS_CACHE is None:
        need_refresh = True
    else:
        _, fetched_at = _JWKS_CACHE
        if (now - fetched_at) > JWKS_TTL_SECONDS:
            need_refresh = True

    if need_refresh:
        try:
            by_kid = _load_jwks_from_network()
            # Update cache under lock to avoid race conditions in multi-thread contexts
            with _JWKS_LOCK:
                _JWKS_CACHE = (by_kid, now)
        except httpx.RequestError as e:
            # Network problem: fallback to stale cache if allowed
            if _JWKS_CACHE and allow_stale_on_error:
                logger.warning("JWKS fetch failed, using stale cache: %s", e)
                return _JWKS_CACHE[0]
            logger.exception("Unable to fetch JWKS and no cache available")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch JWKS from LINE",
            ) from e
        except Exception as e:  # noqa: BLE001
            logger.exception("Invalid JWKS response")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Invalid JWKS from LINE",
            ) from e
        else:
            return by_kid

    # No refresh needed, return cache
    # Type guard for static analyzers
    if _JWKS_CACHE is None:
        # Should not happen: when not refreshing and cache is None; safeguard
        try:
            by_kid = _load_jwks_from_network()
        except httpx.RequestError as e:  # pragma: no cover - defensive branch
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch JWKS from LINE",
            ) from e
        else:
            with _JWKS_LOCK:
                _JWKS_CACHE = (by_kid, now)
    return _JWKS_CACHE[0]


def _public_key_from_jwk(jwk: dict) -> Any:  # noqa: ANN401 - PyJWT returns crypto key object
    """
    Convert a single JWK dict to a public key object usable by PyJWT.

    Args:
        jwk: JSON Web Key dictionary

    Returns:
        A cryptography public key object
    """
    # PyJWT provides algorithm helpers to parse JWK
    kty = jwk.get("kty")
    if kty == "RSA":
        # Import locally to avoid hard dependency at module import time
        from jwt import algorithms as jwt_algorithms

        return jwt_algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
    if kty == "EC":
        from jwt import algorithms as jwt_algorithms

        return jwt_algorithms.ECAlgorithm.from_jwk(json.dumps(jwk))
    raise ValueError("Unsupported key type")


def _get_signing_key_for_kid(kid: str) -> Any:  # noqa: ANN401 - crypto key
    """
    Get signing public key for the given `kid` with one refresh attempt.

    Args:
        kid: Key ID from JWT header

    Returns:
        Public key object

    Raises:
        HTTPException: 401 if kid not found; 503 if JWKS unavailable
    """
    jwks = _get_cached_jwks(force_refresh=False)
    jwk = jwks.get(kid)
    if jwk is None:
        # Try one refresh for rotation
        jwks = _get_cached_jwks(force_refresh=True)
        jwk = jwks.get(kid)
        if jwk is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown key id")
    try:
        return _public_key_from_jwk(jwk)
    except Exception as e:  # noqa: BLE001
        logger.exception("Failed to parse JWK for kid=%s", kid)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to use JWKS key",
        ) from e


async def verify_line_access_token(access_token: str) -> str:
    """
    Verify LINE Access Token using LINE Platform API and extract LINE user ID.

    Args:
        access_token: LINE Access Token from LIFF

    Returns:
        LINE user ID

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Verify access token using LINE Platform API
        async with httpx.AsyncClient() as client:
            verify_response = await client.get(
                "https://api.line.me/oauth2/v2.1/verify",
                params={"access_token": access_token},
                timeout=10.0,
            )

            if verify_response.status_code != 200:
                logger.warning(f"Token verification failed: {verify_response.status_code}")
                raise ValueError("Access token verification failed")

            verify_data = verify_response.json()

            # Check if the token is valid and matches our LIFF app
            if not verify_data.get("client_id"):
                raise ValueError("Invalid token response")

            expires_in = verify_data.get("expires_in", 0)
            if expires_in <= 0:
                raise ValueError("Token expired")

            logger.info(f"Access token verified successfully, expires in: {expires_in} seconds")

        # Get user profile using the access token
        async with httpx.AsyncClient() as client:
            profile_response = await client.get(
                "https://api.line.me/v2/profile",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )

            if profile_response.status_code != 200:
                logger.warning(f"Profile retrieval failed: {profile_response.status_code}")
                raise ValueError("Failed to retrieve user profile")

            profile_data = profile_response.json()
            line_user_id = profile_data.get("userId")

            if not line_user_id:
                raise ValueError("No user ID in profile")

            logger.info("Access token verified successfully")
            return line_user_id

    except httpx.RequestError as e:
        logger.exception("Network error during token verification")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify token due to network error",
        ) from e
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid LINE Access Token: {str(e)}",
        ) from e


def verify_line_id_token(token: str) -> str:
    """
    Verify LINE ID Token and extract LINE user ID.

    This performs:
    - Format and algorithm checks
    - Signature verification using LINE JWKS (RS256/ES256)
    - Issuer check (`iss=https://access.line.me`)
    - Audience check when `settings.LINE_CHANNEL_ID` is set

    When `settings.ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION` is False, the function falls back
    to lightweight checks (exp/iss[/aud]) without verifying the signature. This is only
    acceptable in development/testing.

    Args:
        token: LINE ID Token from LIFF

    Returns:
        LINE user ID (the `sub` claim)

    Raises:
        HTTPException: If token is invalid or verification fails
    """
    # Quick format check
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID Token: Invalid token format",
        )

    # Parse header
    try:
        header_data = json.loads(_base64url_decode_nopad(parts[0]))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID Token: Invalid header",
        ) from e

    alg = header_data.get("alg")
    if alg not in SUPPORTED_ALGS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID Token: Unsupported algorithm",
        )

    # Production safeguards
    if settings.is_production:
        if not settings.ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION:
            logger.error("Signature verification disabled in production")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ID Token signature verification must be enabled in production",
            )
        if not settings.LINE_CHANNEL_ID:
            logger.error("LINE_CHANNEL_ID is not configured in production")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LINE_CHANNEL_ID must be configured in production",
            )

    # Optional audience to check
    audience: str | None = settings.LINE_CHANNEL_ID

    # If signature verification is disabled: fallback to lightweight checks
    if not settings.ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION:
        try:
            payload_data = json.loads(_base64url_decode_nopad(parts[1]))
        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid LINE ID Token: Invalid payload",
            ) from e

        current_time = int(time.time())
        exp = payload_data.get("exp")
        if not isinstance(exp, int):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid LINE ID Token: No expiration time in token",
            )
        if current_time > (exp + 300):  # 5 minutes skew
            logger.warning(
                "Token expired: current_time=%s exp=%s diff=%s",
                current_time,
                exp,
                current_time - exp,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid LINE ID Token: Token expired",
            )

        iss = payload_data.get("iss")
        if iss != "https://access.line.me":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid LINE ID Token: Invalid issuer",
            )

        if audience is not None:
            aud = payload_data.get("aud")
            if isinstance(aud, str):
                aud_ok = aud == audience
            elif isinstance(aud, list):
                aud_ok = audience in aud
            else:
                aud_ok = False
            if not aud_ok:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid LINE ID Token: Audience mismatch",
                )

        line_user_id = payload_data.get("sub")
        if not line_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid LINE ID Token: No user id in token",
            )
        if len(line_user_id) != 33:
            logger.warning("Suspicious LINE user id length: %s", len(line_user_id))
        logger.info("ID Token verified (lightweight, signature disabled)")
        return line_user_id

    # Signature verification path
    kid = header_data.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID Token: Missing kid",
        )

    key = _get_signing_key_for_kid(kid)

    try:
        decoded = jwt.decode(
            token,
            key=key,
            algorithms=SUPPORTED_ALGS,
            issuer="https://access.line.me",
            audience=audience if audience else None,
            leeway=300,  # 5 minutes clock skew
            options={
                # When audience isn't provided, disable aud check
                "verify_aud": bool(audience),
            },
        )
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID Token: Token expired",
        ) from e
    except jwt.InvalidIssuerError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID Token: Invalid issuer",
        ) from e
    except jwt.InvalidAudienceError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID Token: Audience mismatch",
        ) from e
    except jwt.InvalidSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID Token: Invalid signature",
        ) from e
    except Exception as e:  # noqa: BLE001
        logger.warning("ID Token verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid LINE ID Token: {e}"
        ) from e

    line_user_id = decoded.get("sub")
    if not line_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE ID Token: No user id in token",
        )
    if len(line_user_id) != 33:
        logger.warning("Suspicious LINE user id length: %s", len(line_user_id))
    logger.info("ID Token verified successfully")
    return line_user_id


security = HTTPBearer()


async def get_current_line_user_id_from_access_token(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """
    Dependency to get current LINE user ID from Bearer Access token.

    Args:
        token: HTTP Bearer token (LINE Access Token)

    Returns:
        LINE user ID
    """
    return await verify_line_access_token(token.credentials)


def get_current_line_user_id(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """
    Dependency to get current LINE user ID from Bearer token (Legacy ID Token).

    Args:
        token: HTTP Bearer token (LINE ID Token)

    Returns:
        LINE user ID
    """
    return verify_line_id_token(token.credentials)
