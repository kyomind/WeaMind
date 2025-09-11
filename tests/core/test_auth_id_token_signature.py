"""Tests for ID Token signature and audience verification logic."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
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


def test_id_token_invalid_signature() -> None:
    """Token signed with a different key than JWKS public key -> invalid signature (401)."""
    _reset_jwks_cache()
    _set_sig_verify(True)
    _set_channel_id("chan-1")

    from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore[import-not-found]

    # Key A is installed to JWKS; token is signed by Key B
    priv_key_a = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_key_a = priv_key_a.public_key()
    kid = "kid-x"
    jwk_dict = json.loads(jwt_algorithms.RSAAlgorithm.to_jwk(pub_key_a))
    jwk_dict["kid"] = kid
    _install_jwks({kid: jwk_dict})

    priv_key_b = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    token = jwt.encode(
        {
            "iss": "https://access.line.me",
            "sub": "U" + "s" * 32,
            "exp": int(time.time()) + 3600,
            "aud": "chan-1",
        },
        key=priv_key_b,
        algorithm="RS256",
        headers={"kid": kid},
    )

    with pytest.raises(HTTPException) as exc:
        auth_module.verify_line_id_token(token)
    assert exc.value.status_code == 401


def test_id_token_expired_signature() -> None:
    """Signed token with past exp should raise 401 (ExpiredSignatureError path)."""
    _reset_jwks_cache()
    _set_sig_verify(True)
    _set_channel_id("chan-exp")

    from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore[import-not-found]

    priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_key = priv_key.public_key()
    kid = "kid-exp"
    jwk_dict = json.loads(jwt_algorithms.RSAAlgorithm.to_jwk(pub_key))
    jwk_dict["kid"] = kid
    _install_jwks({kid: jwk_dict})

    token = jwt.encode(
        {
            "iss": "https://access.line.me",
            "sub": "U" + "e" * 32,
            "exp": int(time.time()) - 3600,  # expired well beyond 5m leeway
            "aud": "chan-exp",
        },
        key=priv_key,
        algorithm="RS256",
        headers={"kid": kid},
    )

    with pytest.raises(HTTPException) as exc:
        auth_module.verify_line_id_token(token)
    assert exc.value.status_code == 401


def test_id_token_invalid_issuer_signature() -> None:
    """Signed token with invalid issuer hits InvalidIssuerError path (401)."""
    _reset_jwks_cache()
    _set_sig_verify(True)
    _set_channel_id("chan-iss")

    from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore[import-not-found]

    priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_key = priv_key.public_key()
    kid = "kid-iss"
    jwk_dict = json.loads(jwt_algorithms.RSAAlgorithm.to_jwk(pub_key))
    jwk_dict["kid"] = kid
    _install_jwks({kid: jwk_dict})

    token = jwt.encode(
        {
            "iss": "https://invalid.issuer.example",  # wrong iss
            "sub": "U" + "i" * 32,
            "exp": int(time.time()) + 3600,
            "aud": "chan-iss",
        },
        key=priv_key,
        algorithm="RS256",
        headers={"kid": kid},
    )

    with pytest.raises(HTTPException) as exc:
        auth_module.verify_line_id_token(token)
    assert exc.value.status_code == 401


def test_unknown_kid_refresh_still_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """kid not in cache and still not after refresh -> 401."""
    _reset_jwks_cache()
    _set_sig_verify(True)
    _set_channel_id("chan-2")

    from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore[import-not-found]

    # Install JWKS with kid-a
    priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_key = priv_key.public_key()
    jwk_a = json.loads(jwt_algorithms.RSAAlgorithm.to_jwk(pub_key))
    jwk_a["kid"] = "kid-a"
    _install_jwks({"kid-a": jwk_a})

    # Token uses kid-b which isn't present
    token = jwt.encode(
        {
            "iss": "https://access.line.me",
            "sub": "U" + "t" * 32,
            "exp": int(time.time()) + 3600,
            "aud": "chan-2",
        },
        key=priv_key,
        algorithm="RS256",
        headers={"kid": "kid-b"},
    )

    # Refresh returns same JWKS (still no kid-b)
    def _fake_load() -> dict[str, dict[str, Any]]:
        return {"kid-a": jwk_a}

    monkeypatch.setattr(auth_module, "_load_jwks_from_network", _fake_load)

    with pytest.raises(HTTPException) as exc:
        auth_module.verify_line_id_token(token)
    assert exc.value.status_code == 401


def test_refresh_network_error_uses_stale_then_unknown_kid(monkeypatch: pytest.MonkeyPatch) -> None:
    """On refresh network error, stale cache is used but unknown kid still yields 401."""
    _reset_jwks_cache()
    _set_sig_verify(True)
    _set_channel_id("chan-3")

    from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore[import-not-found]

    priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_key = priv_key.public_key()
    jwk_a = json.loads(jwt_algorithms.RSAAlgorithm.to_jwk(pub_key))
    jwk_a["kid"] = "kid-a"
    _install_jwks({"kid-a": jwk_a})

    token = jwt.encode(
        {
            "iss": "https://access.line.me",
            "sub": "U" + "u" * 32,
            "exp": int(time.time()) + 3600,
            "aud": "chan-3",
        },
        key=priv_key,
        algorithm="RS256",
        headers={"kid": "kid-b"},
    )

    def _raise_request_error() -> dict[str, dict[str, Any]]:  # type: ignore[return-type]
        raise httpx.RequestError("boom")

    monkeypatch.setattr(auth_module, "_load_jwks_from_network", _raise_request_error)

    with pytest.raises(HTTPException) as exc:
        auth_module.verify_line_id_token(token)
    assert exc.value.status_code == 401


def test_invalid_jwks_raises_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid JWKS response (non-network error) should yield 503."""
    _reset_jwks_cache()
    _set_sig_verify(True)
    _set_channel_id("chan-4")

    from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore[import-not-found]

    priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_key = priv_key.public_key()
    jwk_a = json.loads(jwt_algorithms.RSAAlgorithm.to_jwk(pub_key))
    jwk_a["kid"] = "kid-a"
    _install_jwks({"kid-a": jwk_a})

    token = jwt.encode(
        {
            "iss": "https://access.line.me",
            "sub": "U" + "v" * 32,
            "exp": int(time.time()) + 3600,
            "aud": "chan-4",
        },
        key=priv_key,
        algorithm="RS256",
        headers={"kid": "kid-b"},
    )

    def _raise_value_error() -> dict[str, dict[str, Any]]:  # type: ignore[return-type]
        raise ValueError("invalid jwks payload")

    monkeypatch.setattr(auth_module, "_load_jwks_from_network", _raise_value_error)

    with pytest.raises(HTTPException) as exc:
        auth_module.verify_line_id_token(token)
    assert exc.value.status_code == 503
