"""Tests for FAQ shortcut and LLM gateway enhancements."""

from __future__ import annotations

import pytest

from services.ai_provider import (
    DEFAULT_HYBRID_ORDER,
    _groq_prefers_json_mode,
    _is_rate_limit_error,
    _resolve_api_key,
    route_by_task,
)
from services.faq_shortcut import try_shortcut
from services.inspection_service import _draft_from_faq_shortcut, generate_inspection_draft


class TestFaqShortcut:
    def test_exact_match_returns_answer(self):
        answer = try_shortcut("충전기 안됨")
        assert answer is not None
        assert "차단기" in answer

    def test_unknown_input_returns_none(self):
        assert try_shortcut("완전히 새로운 증상 설명") is None

    def test_partial_match_rfid_card(self):
        answer = try_shortcut("rfid 카드 인식 안됨")
        assert answer is not None
        assert "RFID 리더기" in answer

    def test_inspection_draft_from_shortcut(self):
        answer = try_shortcut("출장비 얼마")
        assert answer
        draft = _draft_from_faq_shortcut(answer)
        assert draft.overall_risk == "low"
        assert draft.recommended_actions


class TestTaskRouting:
    def test_default_hybrid_order_starts_with_groq(self):
        assert DEFAULT_HYBRID_ORDER[0] == "groq"

    def test_inspection_detail_prefers_groq(self):
        cfg = route_by_task("inspection_detail")
        assert cfg.hybrid_providers[0] == "groq"

    def test_inspection_basic_prefers_groq(self):
        cfg = route_by_task("inspection_basic")
        assert cfg.hybrid_providers[0] == "groq"

    def test_quotation_task_chain_includes_ollama(self):
        from services.ai_provider import _provider_chain

        cfg = route_by_task("quotation_simple")
        chain = _provider_chain(cfg)
        # groq-first 정책 유지 + ollama 폴백(키 없음·gemini 429 대비)
        assert chain == ["groq", "ollama", "gemini"]
        assert "ollama" in chain

    def test_user_hybrid_order_respected_for_inspection_detail(self):
        """UI Hybrid 순서(groq→ollama→gemini…)가 task 기본(groq→gemini)에 덮이지 않아야 함."""
        from services.ai_provider import AiProviderConfigPayload, _provider_chain

        user_cfg = AiProviderConfigPayload(
            provider="hybrid",
            hybrid_providers=["groq", "ollama", "gemini", "openai", "claude"],
        )
        cfg = route_by_task("inspection_detail", user_cfg)
        chain = _provider_chain(cfg)
        assert chain == ["groq", "ollama", "gemini", "openai", "claude"]
        # 태스크 모델 오버라이드(70B)는 유지
        assert cfg.models.get("groq") == "llama-3.3-70b-versatile"

    def test_ensure_groq_first_from_legacy_order(self):
        from services.ai_provider import ensure_groq_first_hybrid_order

        order = ensure_groq_first_hybrid_order(["gemini", "openai", "claude", "ollama"])
        assert order[0] == "groq"
        assert "gemini" in order

    def test_groq_env_key_csautobot(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY_CSAUTOBOT", "gsk-test-key-1234567890")
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        assert _resolve_api_key("groq", None) == "gsk-test-key-1234567890"


class TestRateLimitDetection:
    def test_detects_429(self):
        assert _is_rate_limit_error(Exception("Error 429 Too Many Requests"))

    def test_detects_resource_exhausted(self):
        assert _is_rate_limit_error(Exception("RESOURCE_EXHAUSTED quota"))


class TestGroqStructuredOutput:
    def test_llama_31_uses_json_mode(self):
        assert _groq_prefers_json_mode("llama-3.1-8b-instant") is True

    def test_gpt_oss_supports_native_schema(self):
        assert _groq_prefers_json_mode("openai/gpt-oss-120b") is False


class TestInspectionFaqIntegration:
    def test_generate_draft_uses_faq_shortcut_without_llm(self, monkeypatch):
        def fail_llm(*args, **kwargs):
            raise AssertionError("LLM should not be called")

        monkeypatch.setattr("services.ai_provider.invoke_structured_output", fail_llm)
        draft, model, _, _ = generate_inspection_draft(
            site_name="테스트",
            charger_id=None,
            manufacturer=None,
            model_name=None,
            checklist=[{"item": "외관", "status": "정상", "note": ""}],
            memo_text="충전기 안됨",
        )
        assert model == "faq-shortcut"
        assert draft.recommended_actions
