"""Tests for ID Token signature and audience verification logic."""

from __future__ import annotations

import json
import time
from typing import Any

import jwt
import pytest
from fastapi import HTTPException
from jwt import algorithms as jwt_algorithms

from app.core import auth as auth_module

# Skip module if cryptography is not available at runtime
try:  # pragma: no cover - environment dependent
    import importlib.util

    if importlib.util.find_spec("cryptography") is None:  # type: ignore[truthy-bool]
        raise ImportError
except Exception:  # noqa: BLE001
    pytest.skip("cryptography not installed", allow_module_level=True)


def _reset_jwks_cache() -> None:
    # Reset private cache in module
    auth_module._JWKS_CACHE = None  # type: ignore[attr-defined]


def _set_sig_verify(enabled: bool) -> None:
    # Modify settings for test
    auth_module.settings.ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION = enabled  # type: ignore[attr-defined]


def _set_channel_id(channel_id: str | None) -> None:
    auth_module.settings.LINE_CHANNEL_ID = channel_id  # type: ignore[attr-defined]


def _install_jwks(jwks_by_kid: dict[str, dict[str, Any]]) -> None:
    # Install in cache with fresh timestamp
    auth_module._JWKS_CACHE = (jwks_by_kid, time.time())  # type: ignore[attr-defined]


def _make_jwt(header: dict[str, Any], payload: dict[str, Any], key: Any) -> str:  # noqa: ANN401
    return jwt.encode(payload, key=key, algorithm=header["alg"], headers=header)


@pytest.mark.parametrize("alg", ["RS256", "ES256"])
def test_id_token_signature_success(alg: str) -> None:
    """Valid token passes with signature and audience check."""
    _reset_jwks_cache()
    _set_sig_verify(True)
    _set_channel_id("1234567890")

    now = int(time.time())
    kid = "kid-1"
    if alg == "RS256":
        from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore[import-not-found]

        priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pub_key = priv_key.public_key()
        jwk_dict = json.loads(jwt_algorithms.RSAAlgorithm.to_jwk(pub_key))
        jwk_dict.update({"kid": kid})
        _install_jwks({kid: jwk_dict})
        signing_key = priv_key
    else:
        from cryptography.hazmat.primitives.asymmetric import ec  # type: ignore[import-not-found]

        priv_key = ec.generate_private_key(ec.SECP256R1())
        pub_key = priv_key.public_key()
        jwk_dict = json.loads(jwt_algorithms.ECAlgorithm.to_jwk(pub_key))
        jwk_dict.update({"kid": kid})
        _install_jwks({kid: jwk_dict})
        signing_key = priv_key

    header = {"alg": alg, "typ": "JWT", "kid": kid}
    payload = {
        "iss": "https://access.line.me",
        "sub": "U" + "x" * 32,  # length 33
        "exp": now + 3600,
        "aud": "1234567890",
        "iat": now,
    }
    token = _make_jwt(header, payload, signing_key)

    user_id = auth_module.verify_line_id_token(token)
    assert user_id == payload["sub"]


def test_id_token_audience_mismatch() -> None:
    """Audience mismatch yields 401."""
    _reset_jwks_cache()
    _set_sig_verify(True)
    _set_channel_id("expected-aud")

    from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore[import-not-found]

    priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_key = priv_key.public_key()
    kid = "kid-aud"
    jwk_dict = json.loads(jwt_algorithms.RSAAlgorithm.to_jwk(pub_key))
    jwk_dict["kid"] = kid
    _install_jwks({kid: jwk_dict})

    token = jwt.encode(
        {
            "iss": "https://access.line.me",
            "sub": "U" + "y" * 32,
            "exp": int(time.time()) + 3600,
            "aud": "other-aud",
        },
        key=priv_key,
        algorithm="RS256",
        headers={"kid": kid},
    )
    with pytest.raises(HTTPException) as exc:
        auth_module.verify_line_id_token(token)
    assert exc.value.status_code == 401


def test_id_token_missing_kid() -> None:
    """Missing kid is rejected."""
    _reset_jwks_cache()
    _set_sig_verify(True)
    _set_channel_id("123")
    from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore[import-not-found]

    priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(
        {
            "iss": "https://access.line.me",
            "sub": "U" + "z" * 32,
            "exp": int(time.time()) + 3600,
            "aud": "123",
        },
        key=priv_key,
        algorithm="RS256",
        headers={},
    )
    with pytest.raises(HTTPException) as exc:
        auth_module.verify_line_id_token(token)
    assert exc.value.status_code == 401
