"""Authentication utilities."""

import base64
import json
import logging
import time
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)


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

            logger.info(f"Access token verified successfully for user: {line_user_id}")
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

    Args:
        token: LINE ID Token from LIFF

    Returns:
        LINE user ID

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Basic JWT format validation
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        # Decode header to check algorithm
        header = parts[0]
        header += "=" * (4 - len(header) % 4)
        header_decoded = base64.urlsafe_b64decode(header)
        header_data = json.loads(header_decoded)

        # Verify it's using the expected algorithm
        if header_data.get("alg") not in ["RS256", "ES256"]:
            raise ValueError("Unsupported algorithm")

        # Decode payload (base64 URL decode)
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        payload_decoded = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(payload_decoded)

        # Verify token claims
        current_time = int(time.time())

        # Check expiration with some tolerance (5 minutes buffer)
        exp = payload_data.get("exp")
        if not exp:
            raise ValueError("No expiration time in token")

        # Add 5 minutes buffer to handle clock skew
        time_buffer = 5 * 60  # 5 minutes
        if current_time > (exp + time_buffer):
            # Log for debugging
            logger.warning(
                f"Token expired: current_time={current_time}, exp={exp}, diff={current_time - exp}"
            )
            raise ValueError("Token expired")

        # Check issuer (should be LINE)
        iss = payload_data.get("iss")
        if iss != "https://access.line.me":
            raise ValueError("Invalid issuer")

        # Extract LINE user ID
        line_user_id = payload_data.get("sub")
        if not line_user_id:
            raise ValueError("No user ID in token")

        # Log successful verification for debugging
        logger.info(f"Token verified successfully for user: {line_user_id}")

        # TODO: 完整的生產環境實作應該：
        # 1. 從 LINE 的 JWK endpoint 取得公鑰
        # 2. 驗證 token 的數位簽名
        # 3. 驗證 audience (aud) 是否為正確的 LIFF app ID
        # 參考: https://developers.line.biz/en/docs/liff/using-user-profile/

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid LINE ID Token: {str(e)}"
        ) from e
    else:
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
