"""Encrypt/decrypt tenant AI API credentials at rest."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

AIProviderName = ("claude", "openai", "gemini")


def _fernet() -> Fernet:
    secret = (
        os.environ.get("AI_CREDENTIALS_SECRET")
        or os.environ.get("JWT_SECRET_KEY")
        or "csautobot-dev-insecure-credentials-key"
    )
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_credentials(credentials: dict[str, str]) -> str:
    payload = json.dumps(credentials, ensure_ascii=False).encode("utf-8")
    return _fernet().encrypt(payload).decode("ascii")


def decrypt_credentials(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    try:
        raw = _fernet().decrypt(token.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            return {}
        return {str(k): str(v) for k, v in data.items() if v}
    except (InvalidToken, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def mask_api_key(value: str) -> str:
    key = value.strip()
    if len(key) <= 8:
        return "••••"
    return f"{key[:4]}…{key[-4:]}"


def build_credential_hints(credentials: dict[str, str]) -> dict[str, str]:
    return {provider: mask_api_key(key) for provider, key in credentials.items() if key.strip()}


def configured_providers(credentials: dict[str, str]) -> list[str]:
    return sorted([p for p, v in credentials.items() if v and v.strip()])
