"""Pluggable AI provider routing (ocppautomation-compatible)."""

from __future__ import annotations

import os
from typing import Any, Literal, Type, TypeVar

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

AIProviderName = Literal["claude", "openai", "gemini", "ollama", "groq"]
AISelectionMode = Literal["claude", "openai", "gemini", "ollama", "groq", "hybrid"]

TaskType = Literal[
    "intent_detect",
    "inspection_basic",
    "inspection_detail",
    "quotation_simple",
    "quotation_complex",
    "batch_classify",
    "general",
]

DEFAULT_HYBRID_ORDER: list[AIProviderName] = ["groq", "gemini", "openai", "claude", "ollama"]

DEFAULT_MODELS: dict[AIProviderName, str] = {
    "claude": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "ollama": "qwen2.5:3b",
    "groq": "llama-3.1-8b-instant",
}

GROQ_70B_MODEL = "llama-3.3-70b-versatile"

# task_type → (provider order, per-provider model overrides)
TASK_ROUTING: dict[TaskType, tuple[list[AIProviderName], dict[str, str]]] = {
    "intent_detect": (["groq", "gemini"], {"groq": "llama-3.1-8b-instant"}),
    "inspection_basic": (["groq", "gemini"], {"groq": "llama-3.1-8b-instant"}),
    "inspection_detail": (["groq", "gemini"], {"groq": GROQ_70B_MODEL}),
    "quotation_simple": (["groq", "gemini"], {"groq": "llama-3.1-8b-instant"}),
    "quotation_complex": (["groq", "gemini"], {"groq": GROQ_70B_MODEL}),
    "batch_classify": (["groq", "gemini"], {"groq": GROQ_70B_MODEL}),
    "general": (["groq", "gemini"], {"groq": "llama-3.1-8b-instant"}),
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
        "gemini": ["GOOGLE_API_KEY_CSAUTOBOT", "GOOGLE_API_KEY"],
        "groq": ["GROQ_API_KEY_CSAUTOBOT", "GROQ_API_KEY"],
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
        order = [
            p for p in (cfg.hybrid_providers or DEFAULT_HYBRID_ORDER)
            if p in DEFAULT_MODELS  # type: ignore[comparison-overlap]
        ]
        if not order:
            order = list(DEFAULT_HYBRID_ORDER)
        if "groq" in order:
            return ["groq", *[p for p in order if p != "groq"]]
        return ["groq", *order]
    if cfg.provider in DEFAULT_MODELS:
        return [cfg.provider]  # type: ignore[list-item]
    return list(DEFAULT_HYBRID_ORDER)


def ensure_groq_first_hybrid_order(
    providers: list[AIProviderName] | list[str] | None,
) -> list[AIProviderName]:
    """Normalize hybrid fallback order so Groq is always tried first."""
    order: list[AIProviderName] = [
        p for p in (providers or DEFAULT_HYBRID_ORDER) if p in DEFAULT_MODELS  # type: ignore[comparison-overlap]
    ]
    if "groq" not in order:
        order.insert(0, "groq")
    else:
        order = ["groq", *[p for p in order if p != "groq"]]
    for provider in DEFAULT_HYBRID_ORDER:
        if provider not in order:
            order.append(provider)
    return order


def route_by_task(
    task_type: TaskType,
    base_config: AiProviderConfigPayload | None = None,
) -> AiProviderConfigPayload:
    """Return hybrid config tuned for the given task (Korean quality vs speed)."""
    task_providers, model_overrides = TASK_ROUTING.get(task_type, TASK_ROUTING["general"])
    cfg = base_config or AiProviderConfigPayload()
    
    if cfg.provider != "hybrid":
        return AiProviderConfigPayload(
            provider=cfg.provider,
            hybrid_providers=cfg.hybrid_providers,
            api_keys=dict(cfg.api_keys),
            models={**cfg.models, **model_overrides},
            ollama_base_url=cfg.ollama_base_url,
        )

    merged_providers = list(task_providers)
    for p in cfg.hybrid_providers:
        if p not in merged_providers:
            merged_providers.append(p)

    return AiProviderConfigPayload(
        provider="hybrid",
        hybrid_providers=merged_providers,
        api_keys=dict(cfg.api_keys),
        models={**cfg.models, **model_overrides},
        ollama_base_url=cfg.ollama_base_url,
    )


def _is_rate_limit_error(exc: Exception) -> bool:
    err = str(exc).lower()
    markers = ("429", "rate limit", "rate_limit", "resource_exhausted", "quota", "too many requests")
    return any(m in err for m in markers)


def _is_json_schema_unsupported(exc: Exception) -> bool:
    err = str(exc).lower()
    return "json_schema" in err or "response format" in err or "response_format" in err


GROQ_NATIVE_JSON_SCHEMA_PREFIXES = (
    "openai/gpt-oss",
    "meta-llama/llama-4-scout",
    "llama-4-scout",
)


def _groq_prefers_json_mode(model: str) -> bool:
    """Groq llama-3.x models need json_object mode, not json_schema."""
    lowered = model.lower()
    return not any(prefix in lowered for prefix in GROQ_NATIVE_JSON_SCHEMA_PREFIXES)


def _structured_output_chain(
    prompt: ChatPromptTemplate,
    llm: Any,
    output_model: Type[T],
    *,
    use_json_mode: bool,
):
    if use_json_mode:
        return prompt | llm.with_structured_output(output_model, method="json_mode")
    return prompt | llm.with_structured_output(output_model)


def _invoke_structured_on_provider(
    prompt: ChatPromptTemplate,
    *,
    provider: AIProviderName,
    model: str,
    api_key: str | None,
    base_url: str | None,
    output_model: Type[T],
    inputs: dict[str, Any],
) -> T:
    llm = _build_llm(provider, model, api_key, base_url)
    use_json_mode = provider == "groq" and _groq_prefers_json_mode(model)
    chain = _structured_output_chain(prompt, llm, output_model, use_json_mode=use_json_mode)
    try:
        return chain.invoke(inputs)
    except Exception as exc:
        if provider == "groq" and not use_json_mode and _is_json_schema_unsupported(exc):
            fallback_chain = _structured_output_chain(
                prompt, llm, output_model, use_json_mode=True
            )
            return fallback_chain.invoke(inputs)
        raise


def _build_llm(provider: AIProviderName, model: str, api_key: str | None, base_url: str | None):
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        kwargs: dict[str, Any] = {"model": model, "temperature": 0}
        if api_key:
            kwargs["api_key"] = api_key
        return ChatOpenAI(**kwargs)

    if provider == "groq":
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model,
            "temperature": 0,
            "base_url": "https://api.groq.com/openai/v1",
            "max_retries": 0,
        }
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

    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        from langchain_community.chat_models import ChatOllama

    return ChatOllama(
        model=model,
        base_url=(base_url or "http://localhost:11434").rstrip("/"),
        temperature=0,
    )


def test_provider_connection(
    provider: AIProviderName,
    *,
    ai_config: AiProviderConfigPayload | None = None,
) -> dict[str, str]:
    """Lightweight connectivity check for settings UI."""
    cfg = ai_config or AiProviderConfigPayload(provider=provider)
    model = _resolve_model(provider, cfg.models)
    api_key = _resolve_api_key(provider, cfg.api_keys.get(provider))
    if provider != "ollama" and not api_key:
        raise RuntimeError(f"{provider} API 키가 설정되지 않았습니다.")
    llm = _build_llm(
        provider,
        model,
        api_key,
        cfg.ollama_base_url if provider == "ollama" else None,
    )
    response = llm.invoke("ping")
    content = getattr(response, "content", str(response))
    preview = str(content)[:80]
    return {"provider": provider, "model": model, "status": "ok", "preview": preview}


def invoke_with_fallback(
    output_model: Type[T],
    *,
    system_prompt: str,
    human_template: str,
    inputs: dict[str, Any],
    ai_config: AiProviderConfigPayload | None = None,
    rate_limit_fallback_order: list[AIProviderName] | None = None,
) -> tuple[T, str, str | None]:
    """
    Try provider chain; on 429/rate-limit from primary, retry with fallback order.
    Returns (parsed model, model label, fallback_provider or None).
    """
    cfg = ai_config or AiProviderConfigPayload()
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_template)]
    )
    chain_providers = _provider_chain(cfg)
    last_error: Exception | None = None
    fallback_provider: str | None = None

    for provider in chain_providers:
        model = _resolve_model(provider, cfg.models)
        api_key = _resolve_api_key(provider, cfg.api_keys.get(provider))
        if provider != "ollama" and not api_key:
            continue
        try:
            result = _invoke_structured_on_provider(
                prompt,
                provider=provider,
                model=model,
                api_key=api_key,
                base_url=cfg.ollama_base_url if provider == "ollama" else None,
                output_model=output_model,
                inputs=inputs,
            )
            label = f"{provider}:{model}"
            if fallback_provider:
                label = f"{fallback_provider}->{provider}:{model}"
            return result, label, fallback_provider
        except Exception as exc:
            last_error = exc
            print(f"[ai_provider] {provider} failed: {exc}")

    if last_error:
        raise last_error
    raise RuntimeError("No AI provider available. Configure API keys or select Hybrid mode.")


def invoke_structured_output(
    output_model: Type[T],
    *,
    system_prompt: str,
    human_template: str,
    inputs: dict[str, Any],
    ai_config: AiProviderConfigPayload | None = None,
    task_type: TaskType | None = None,
) -> tuple[T, str]:
    """Try configured provider chain; return (parsed model, model label)."""
    cfg = route_by_task(task_type, ai_config) if task_type else (ai_config or AiProviderConfigPayload())
    result, label, _ = invoke_with_fallback(
        output_model,
        system_prompt=system_prompt,
        human_template=human_template,
        inputs=inputs,
        ai_config=cfg,
    )
    return result, label
