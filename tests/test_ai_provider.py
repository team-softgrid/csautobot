"""Tests for AI provider routing."""

from __future__ import annotations

import os

import pytest

from services.ai_provider import (
    AiProviderConfigPayload,
    _provider_chain,
    _resolve_api_key,
    _resolve_model,
)


class TestAiProviderHelpers:
    def test_provider_chain_hybrid_default_order(self):
        cfg = AiProviderConfigPayload(provider="hybrid")
        assert _provider_chain(cfg) == ["groq", "gemini", "openai", "claude", "ollama"]

    def test_provider_chain_single_provider(self):
        cfg = AiProviderConfigPayload(provider="gemini")
        assert _provider_chain(cfg) == ["gemini"]

    def test_resolve_api_key_prefers_client_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        key = _resolve_api_key("openai", "sk-client-key-12345678901234567890")
        assert key == "sk-client-key-12345678901234567890"

    def test_resolve_api_key_falls_back_to_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")
        key = _resolve_api_key("claude", None)
        assert key == "sk-ant-env-key"

    def test_resolve_api_key_ignores_mock_keys(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "mock-test-key")
        assert _resolve_api_key("gemini", None) is None

    def test_resolve_model_uses_configured_value(self):
        cfg = AiProviderConfigPayload(models={"openai": "gpt-4o"})
        assert _resolve_model("openai", cfg.models) == "gpt-4o"

    def test_resolve_model_default(self):
        assert _resolve_model("claude", {}) == "claude-sonnet-4-6"

    def test_resolve_model_groq_default(self):
        assert _resolve_model("groq", {}) == "llama-3.1-8b-instant"


class TestAiUsageInfo:
    def test_usage_for_non_llm(self):
        from services.ai_provider import usage_for_non_llm

        u = usage_for_non_llm("faq-shortcut")
        assert u.model_label == "faq-shortcut"
        assert u.generation_path == "faq-shortcut"
        assert u.total_tokens == 0

    def test_with_label_parses_provider_model(self):
        from services.ai_provider import AiUsageInfo

        u = AiUsageInfo(input_tokens=10, output_tokens=5, latency_ms=120)
        labeled = u.with_label("groq:llama-3.1-8b-instant")
        assert labeled.provider == "groq"
        assert labeled.model_name == "llama-3.1-8b-instant"
        assert labeled.total_tokens == 15

    def test_tokens_from_mapping(self):
        from services.ai_provider import _tokens_from_mapping

        assert _tokens_from_mapping({"prompt_tokens": 3, "completion_tokens": 7}) == (3, 7)
        assert _tokens_from_mapping({"input_tokens": 1, "output_tokens": 2}) == (1, 2)


class TestJsonModeSchemaHint:
    def test_lists_all_field_names_verbatim(self):
        from services.ai_provider import _json_mode_schema_hint
        from services.inspection_service import InspectionDraft

        hint = _json_mode_schema_hint(InspectionDraft)
        for field_name in InspectionDraft.model_fields:
            assert f'"{field_name}"' in hint

    def test_marks_required_vs_optional(self):
        from services.ai_provider import _json_mode_schema_hint
        from services.inspection_service import InspectionDraft

        hint = _json_mode_schema_hint(InspectionDraft)
        assert '"overall_risk" (필수)' in hint
        assert '"key_findings" (선택)' in hint


class TestInvokeStructuredOutput:
    def test_raises_when_no_provider_available(self, monkeypatch):
        from services.ai_provider import invoke_structured_output
        from services.inspection_service import InspectionDraft

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        cfg = AiProviderConfigPayload(
            provider="openai",
            api_keys={"openai": ""},
        )

        with pytest.raises(RuntimeError, match="No AI provider available"):
            invoke_structured_output(
                InspectionDraft,
                system_prompt="test",
                human_template="{charger_block}",
                inputs={"charger_block": "x"},
                ai_config=cfg,
            )
