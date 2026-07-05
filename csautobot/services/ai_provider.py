"""Pluggable AI provider routing (ocppautomation-compatible)."""

from __future__ import annotations

import os
from typing import Any, Literal, Type, TypeVar

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

AIProviderName = Literal["claude", "openai", "gemini", "ollama"]
AISelectionMode = Literal["claude", "openai", "gemini", "ollama", "hybrid"]

DEFAULT_HYBRID_ORDER: list[AIProviderName] = ["ollama", "claude", "openai", "gemini"]

DEFAULT_MODELS: dict[AIProviderName, str] = {
    "claude": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "ollama": "qwen3:8b",
}

T = TypeVar("T", bound=BaseModel)


class AiProviderConfigPayload(BaseModel):
    provider: AISelectionMode = "hybrid"
    hybrid_providers: list[AIProviderName] = Field(default_factory=lambda: list(DEFAULT_HYBRID_ORDER))
    api_keys: dict[str, str] = Field(default_factory=dict)
    models: dict[str, str] = Field(default_factory=dict)
    ollama_base_url: str = "http://localhost:11434"


def _is_usable_key(value: str | None) -> bool:
    if not value or not value.strip():
        return False
    lowered = value.strip().lower()
    return not lowered.startswith("mock-")


def _resolve_api_key(provider: AIProviderName, client_key: str | None) -> str | None:
    if provider == "ollama":
        return None
    if _is_usable_key(client_key):
        return client_key.strip()
    env_candidates: dict[AIProviderName, list[str]] = {
        "openai": ["OPENAI_API_KEY"],
        "claude": ["ANTHROPIC_API_KEY"],
        "gemini": ["GOOGLE_API_KEY"],
    }
    for env_name in env_candidates.get(provider, []):
        env_value = os.environ.get(env_name)
        if _is_usable_key(env_value):
            return env_value.strip()
    return None


def _resolve_model(provider: AIProviderName, models: dict[str, str]) -> str:
    configured = (models.get(provider) or "").strip()
    return configured or DEFAULT_MODELS[provider]


def _provider_chain(config: AiProviderConfigPayload | None) -> list[AIProviderName]:
    cfg = config or AiProviderConfigPayload()
    if cfg.provider == "hybrid":
        order = cfg.hybrid_providers or list(DEFAULT_HYBRID_ORDER)
        return [p for p in order if p in DEFAULT_MODELS]
    if cfg.provider in DEFAULT_MODELS:
        return [cfg.provider]  # type: ignore[list-item]
    return list(DEFAULT_HYBRID_ORDER)


def _build_llm(provider: AIProviderName, model: str, api_key: str | None, base_url: str | None):
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        kwargs: dict[str, Any] = {"model": model, "temperature": 0}
        if api_key:
            kwargs["api_key"] = api_key
        return ChatOpenAI(**kwargs)

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        kwargs = {"model": model, "temperature": 0}
        if api_key:
            kwargs["google_api_key"] = api_key
        return ChatGoogleGenerativeAI(**kwargs)

    if provider == "claude":
        from langchain_anthropic import ChatAnthropic

        kwargs = {"model": model, "temperature": 0}
        if api_key:
            kwargs["api_key"] = api_key
        return ChatAnthropic(**kwargs)

    from langchain_community.chat_models import ChatOllama

    return ChatOllama(
        model=model,
        base_url=(base_url or "http://localhost:11434").rstrip("/"),
        temperature=0,
    )


def invoke_structured_output(
    output_model: Type[T],
    *,
    system_prompt: str,
    human_template: str,
    inputs: dict[str, Any],
    ai_config: AiProviderConfigPayload | None = None,
) -> tuple[T, str]:
    """Try configured provider chain; return (parsed model, model label)."""
    cfg = ai_config or AiProviderConfigPayload()
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_template)]
    )
    last_error: Exception | None = None

    for provider in _provider_chain(cfg):
        model = _resolve_model(provider, cfg.models)
        api_key = _resolve_api_key(provider, cfg.api_keys.get(provider))
        if provider != "ollama" and not api_key:
            continue
        try:
            llm = _build_llm(
                provider,
                model,
                api_key,
                cfg.ollama_base_url if provider == "ollama" else None,
            )
            chain = prompt | llm.with_structured_output(output_model)
            result: T = chain.invoke(inputs)
            label = f"{provider}:{model}"
            return result, label
        except Exception as exc:
            last_error = exc
            print(f"[ai_provider] {provider} failed: {exc}")

    if last_error:
        raise last_error
    raise RuntimeError("No AI provider available. Configure API keys or select Hybrid mode.")
