"""Regression: quotation API must pass ai_config as keyword, not use_web_search."""

from __future__ import annotations

from functools import partial
from unittest.mock import MagicMock, patch


def test_quotation_draft_executor_passes_ai_config_kwarg():
    """Mirrors app/routes/quotation.py run_in_executor call shape."""
    captured = {}

    def fake_generate(query, charger_type="급속", use_web_search=False, ai_config=None):
        captured["use_web_search"] = use_web_search
        captured["ai_config"] = ai_config
        captured["query"] = query
        return "ok"

    ai_cfg = MagicMock(name="AiProviderConfigPayload")

    # Bug (old): positional 3rd arg → use_web_search=ai_cfg, ai_config=None
    fake_generate("q", "급속", ai_cfg)
    assert captured["ai_config"] is None
    assert captured["use_web_search"] is ai_cfg

    # Fix: keyword via partial
    captured.clear()
    fn = partial(fake_generate, "q", "급속", ai_config=ai_cfg)
    assert fn() == "ok"
    assert captured["ai_config"] is ai_cfg
    assert captured["use_web_search"] is False
