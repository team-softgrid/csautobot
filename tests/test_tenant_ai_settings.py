"""Tests for tenant AI settings and credential encryption."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from services.ai_credentials import decrypt_credentials, encrypt_credentials, mask_api_key
from services.tenant_ai_settings import AiSettingsUpdate, get_public_settings, load_runtime_config, save_settings
from storage.repositories import TenantAiSettings


class TestAiCredentials:
    def test_encrypt_decrypt_roundtrip(self):
        original = {"openai": "sk-test-key-1234567890", "gemini": "AIzaSyTestKey1234567890"}
        token = encrypt_credentials(original)
        restored = decrypt_credentials(token)
        assert restored == original

    def test_mask_api_key(self):
        assert mask_api_key("sk-abcdefghijklmnop") == "sk-a…mnop"


class TestTenantAiSettings:
    def test_save_and_load_public_settings(self, db_session: Session):
        payload = AiSettingsUpdate(
            tenant_id="tenant_ai_test",
            provider="hybrid",
            hybrid_providers=["groq", "gemini", "openai", "claude", "ollama"],
            api_keys={
                "openai": "sk-test-openai-key-1234567890",
                "gemini": "AIzaSyGeminiTestKey1234567890",
            },
        )
        saved = save_settings(db_session, payload)
        assert "openai" in saved.configured_providers
        assert "gemini" in saved.configured_providers
        assert saved.credential_hints.get("openai", "").startswith("sk-")

        public = get_public_settings(db_session, "tenant_ai_test")
        assert "openai" in public.configured_providers
        assert "claude" not in public.configured_providers

    def test_runtime_config_has_decrypted_keys(self, db_session: Session):
        save_settings(
            db_session,
            AiSettingsUpdate(
                tenant_id="tenant_runtime_test",
                api_keys={"claude": "sk-ant-test-key-12345678901234567890"},
            ),
        )
        runtime = load_runtime_config(db_session, "tenant_runtime_test")
        assert runtime.api_keys["claude"].startswith("sk-ant")

    def test_update_key_merge_preserves_other_providers(self, db_session: Session):
        tid = "tenant_merge_test"
        save_settings(
            db_session,
            AiSettingsUpdate(
                tenant_id=tid,
                api_keys={"openai": "sk-openai-111111111111111111111111"},
            ),
        )
        save_settings(
            db_session,
            AiSettingsUpdate(
                tenant_id=tid,
                api_keys={"gemini": "AIzaSyGemini222222222222222222"},
            ),
        )
        runtime = load_runtime_config(db_session, tid)
        assert "openai" in runtime.api_keys
        assert "gemini" in runtime.api_keys
