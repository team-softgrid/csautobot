"""Pluggable AI provider routing (ocppautomation-compatible)."""

from __future__ import annotations

import os
import time
from typing import Any, Literal, Type, TypeVar

from langchain_core.callbacks import BaseCallbackHandler
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


class AiUsageInfo(BaseModel):
    """Per-invocation model/token/latency metrics for UI and metering."""

    model_label: str = ""
    provider: str | None = None
    model_name: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    fallback_provider: str | None = None
    generation_path: str = "llm"  # llm | faq-shortcut | offline-rules
    fallback_reason: str | None = Field(
        default=None,
        description="generation_path=offline-rules일 때, 시도한 provider들이 왜 실패/스킵됐는지 요약",
    )

    def with_label(self, label: str, *, fallback_provider: str | None = None) -> "AiUsageInfo":
        provider: str | None = None
        model_name: str | None = None
        bare = label.split("->", 1)[-1] if "->" in label else label
        if ":" in bare:
            provider, model_name = bare.split(":", 1)
        total = self.input_tokens + self.output_tokens
        return self.model_copy(
            update={
                "model_label": label,
                "provider": provider,
                "model_name": model_name,
                "total_tokens": total if total else self.total_tokens,
                "fallback_provider": fallback_provider,
                "generation_path": "llm",
            }
        )


def usage_for_non_llm(path: str, *, latency_ms: int = 0, fallback_reason: str | None = None) -> AiUsageInfo:
    """Build usage meta for FAQ shortcut / offline-rules paths (no LLM tokens)."""
    return AiUsageInfo(
        model_label=path,
        generation_path=path,
        latency_ms=latency_ms,
        fallback_reason=fallback_reason,
    )


def describe_provider_attempts(attempts: list["ProviderAttempt"]) -> str:
    """Human-readable summary of a fallback chain's attempts, in try order.

    Used to surface *which* provider/model actually hit its quota (or was never
    tried due to a missing key) instead of the previous behavior of discarding
    every attempt but the last one.
    """
    if not attempts:
        return "시도된 provider 없음"
    lines = []
    for a in attempts:
        if a.skipped:
            lines.append(f"{a.provider}:{a.model} — 스킵({a.error})")
        elif a.rate_limited:
            lines.append(f"{a.provider}:{a.model} — 한도 초과/rate-limit: {a.error}")
        else:
            lines.append(f"{a.provider}:{a.model} — 오류: {a.error}")
    return " → ".join(lines)


class _TokenCaptureCallback(BaseCallbackHandler):
    """Capture prompt/completion tokens from provider callback metadata."""

    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        in_tok, out_tok = _tokens_from_llm_result(response)
        if in_tok or out_tok:
            self.input_tokens += in_tok
            self.output_tokens += out_tok


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _tokens_from_mapping(data: dict[str, Any] | None) -> tuple[int, int]:
    if not data:
        return 0, 0
    in_tok = _as_int(
        data.get("input_tokens")
        or data.get("prompt_tokens")
        or data.get("prompt_token_count")
    )
    out_tok = _as_int(
        data.get("output_tokens")
        or data.get("completion_tokens")
        or data.get("candidates_token_count")
    )
    if not in_tok and not out_tok:
        total = _as_int(data.get("total_tokens") or data.get("total_token_count"))
        if total:
            return total, 0
    return in_tok, out_tok


def _tokens_from_llm_result(response: Any) -> tuple[int, int]:
    in_tok = out_tok = 0
    llm_output = getattr(response, "llm_output", None) or {}
    if isinstance(llm_output, dict):
        usage = llm_output.get("token_usage") or llm_output.get("usage") or {}
        a, b = _tokens_from_mapping(usage if isinstance(usage, dict) else {})
        in_tok += a
        out_tok += b

    generations = getattr(response, "generations", None) or []
    for gen_list in generations:
        for gen in gen_list or []:
            message = getattr(gen, "message", None)
            usage_meta = getattr(message, "usage_metadata", None) if message is not None else None
            if isinstance(usage_meta, dict):
                a, b = _tokens_from_mapping(usage_meta)
                in_tok += a
                out_tok += b
            elif usage_meta is not None:
                a, b = _tokens_from_mapping(
                    {
                        "input_tokens": getattr(usage_meta, "input_tokens", None),
                        "output_tokens": getattr(usage_meta, "output_tokens", None),
                        "total_tokens": getattr(usage_meta, "total_tokens", None),
                    }
                )
                in_tok += a
                out_tok += b
            resp_meta = getattr(message, "response_metadata", None) if message is not None else None
            if isinstance(resp_meta, dict):
                nested = resp_meta.get("token_usage") or resp_meta.get("usage") or resp_meta
                if isinstance(nested, dict):
                    a, b = _tokens_from_mapping(nested)
                    in_tok += a
                    out_tok += b
    return in_tok, out_tok

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


def normalize_provider_order(
    providers: list[AIProviderName] | list[str] | None,
) -> list[AIProviderName]:
    """Normalize hybrid fallback order, filling in any missing providers at the end.

    "groq"는 항상 맨 앞으로 보낸다 — 함수명(그리고 옛 이름 ensure_groq_first_hybrid_order)이
    약속하는 동작인데, 입력 리스트에 groq가 없을 때 끝에 그냥 append만 되고 실제로는
    맨 앞으로 옮겨지지 않던 기존 버그(2026-07-14, CI에서 발견).
    """
    order: list[AIProviderName] = [
        p for p in (providers or DEFAULT_HYBRID_ORDER) if p in DEFAULT_MODELS  # type: ignore[comparison-overlap]
    ]
    if not order:
        order = list(DEFAULT_HYBRID_ORDER)
    for provider in DEFAULT_HYBRID_ORDER:
        if provider not in order:
            order.append(provider)
    if "groq" in order:
        order = ["groq", *[p for p in order if p != "groq"]]  # type: ignore[list-item]
    else:
        order = ["groq", *order]  # type: ignore[list-item]
    return order


def ensure_groq_first_hybrid_order(
    providers: list[AIProviderName] | list[str] | None,
) -> list[AIProviderName]:
    """Deprecated: use normalize_provider_order. Kept for compatibility."""
    return normalize_provider_order(providers)


def route_by_task(
    task_type: TaskType,
    base_config: AiProviderConfigPayload | None = None,
) -> AiProviderConfigPayload:
    """Return hybrid config tuned for the given task (Korean quality vs speed).

    base_config를 안 넘기면(bare default) 태스크 전용 짧은 체인(예: quotation_simple의
    groq+gemini)만 써야 하는데, `AiProviderConfigPayload()`의 hybrid_providers가
    기본값으로 이미 전체 5-provider 리스트라서, 아래에서 무조건 병합해버리면 항상
    5개 전부가 붙어 "짧은 체인" 의도가 무력화되던 기존 버그(2026-07-14, CI에서 발견).
    base_config가 실제로 넘어온 경우(호출자가 명시적으로 provider를 지정한 경우)에만
    그 목록을 태스크 목록과 병합한다.
    """
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

    if base_config is None:
        merged_providers = list(task_providers)
    else:
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


_RATE_LIMIT_MARKERS = ("429", "rate limit", "rate_limit", "resource_exhausted", "quota", "too many requests")


def _is_rate_limit_error_str(err: str) -> bool:
    err = err.lower()
    return any(m in err for m in _RATE_LIMIT_MARKERS)


def _is_rate_limit_error(exc: Exception) -> bool:
    return _is_rate_limit_error_str(str(exc))


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


def _json_mode_schema_hint(output_model: Type[T]) -> str:
    """json_mode는 (json_schema/tool-calling과 달리) 모델에 실제 필드명을 강제하지
    않고 프롬프트 지시만 따른다. 각 프롬프트 yaml이 "지정된 스키마의 영문 키"라고만
    말하고 정작 그 키 목록을 보여주지 않아, 모델이 임의의(예: 한글) 키로 응답해
    Pydantic 검증이 실패하는 사례가 있었다(OUTPUT_PARSING_FAILURE). Pydantic 모델
    자체에서 키 목록을 뽑아 프롬프트에 명시적으로 박아 넣는다(단일 소스, 수기 동기화 불필요).
    """
    schema = output_model.model_json_schema()
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    lines = ["다음 JSON 키를 정확히 그대로(한글로 바꾸지 말고) 사용해서 응답하세요:"]
    for name, spec in properties.items():
        desc = spec.get("description", "")
        marker = "(필수)" if name in required else "(선택)"
        lines.append(f'- "{name}" {marker}: {desc}' if desc else f'- "{name}" {marker}')
    return "\n".join(lines)


def _structured_output_chain(
    prompt: ChatPromptTemplate,
    llm: Any,
    output_model: Type[T],
    *,
    use_json_mode: bool,
):
    if use_json_mode:
        # human 메시지 뒤에 system 메시지가 오면 일부 프로바이더가 거부하거나 지시를 무시할 수 있어
        # (gemini-code-assist 리뷰) 마지막(human) 메시지 앞에 삽입해 system들이 항상 먼저 오게 한다.
        messages = list(prompt.messages)
        messages.insert(len(messages) - 1, ("system", _json_mode_schema_hint(output_model)))
        prompt = ChatPromptTemplate.from_messages(messages)
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
) -> tuple[T, AiUsageInfo]:
    llm = _build_llm(provider, model, api_key, base_url)
    use_json_mode = provider == "groq" and _groq_prefers_json_mode(model)
    chain = _structured_output_chain(prompt, llm, output_model, use_json_mode=use_json_mode)
    token_cb = _TokenCaptureCallback()
    invoke_cfg = {"callbacks": [token_cb]}
    started = time.perf_counter()
    try:
        try:
            result = chain.invoke(inputs, config=invoke_cfg)
        except Exception as exc:
            if provider == "groq" and not use_json_mode and _is_json_schema_unsupported(exc):
                fallback_chain = _structured_output_chain(
                    prompt, llm, output_model, use_json_mode=True
                )
                result = fallback_chain.invoke(inputs, config=invoke_cfg)
            else:
                raise
    finally:
        latency_ms = max(0, int((time.perf_counter() - started) * 1000))

    usage = AiUsageInfo(
        model_label=f"{provider}:{model}",
        provider=provider,
        model_name=model,
        input_tokens=token_cb.input_tokens,
        output_tokens=token_cb.output_tokens,
        total_tokens=token_cb.input_tokens + token_cb.output_tokens,
        latency_ms=latency_ms,
        generation_path="llm",
    )
    return result, usage


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


class ProviderAttempt(BaseModel):
    """Fallback chain 상의 provider 1개 시도 결과 (성공 시엔 기록되지 않음)."""

    provider: str
    model: str
    skipped: bool = Field(default=False, description="API 키 미설정으로 호출 자체를 시도하지 않음")
    rate_limited: bool = Field(default=False, description="429/quota/rate-limit 계열 오류 여부")
    error: str = ""


class AllProvidersFailedError(RuntimeError):
    """Fallback chain의 모든 provider가 실패(또는 키 미설정으로 스킵)했을 때 발생.

    개별 provider 오류를 서버 print() 로그에만 남기고 마지막 예외만 밖으로 던지면
    "어떤 모델이 왜 실패했는지"가 API 응답/화면 어디에도 남지 않는다 — attempts에
    시도 순서 전체를 담아 라우터가 사용자에게 구체적인 사유를 보여줄 수 있게 한다.

    RuntimeError를 상속 — 예전엔 이 상황에서 그냥 RuntimeError("No AI provider
    available...")를 던졌어서, 그걸 잡던 기존 코드/테스트가 계속 동작하도록 유지.
    """

    def __init__(self, attempts: list[ProviderAttempt]):
        self.attempts = attempts
        tried = [a for a in attempts if not a.skipped]
        summary = "; ".join(f"{a.provider}:{a.model} - {a.error}" for a in tried) or "no provider attempted"
        super().__init__(f"All AI providers failed: {summary}")


def invoke_with_fallback(
    output_model: Type[T],
    *,
    system_prompt: str,
    human_template: str,
    inputs: dict[str, Any],
    ai_config: AiProviderConfigPayload | None = None,
    rate_limit_fallback_order: list[AIProviderName] | None = None,
) -> tuple[T, AiUsageInfo]:
    """
    Try provider chain; on failure from primary, retry with next provider.
    Returns (parsed model, usage info including model label / tokens / latency).
    Raises AllProvidersFailedError (with per-provider attempt detail) if every
    provider in the chain fails or is skipped for missing API keys.
    """
    cfg = ai_config or AiProviderConfigPayload()
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_template)]
    )
    chain_providers = _provider_chain(cfg)
    attempts: list[ProviderAttempt] = []
    fallback_provider: str | None = None
    total_latency_ms = 0

    for provider in chain_providers:
        model = _resolve_model(provider, cfg.models)
        api_key = _resolve_api_key(provider, cfg.api_keys.get(provider))
        if provider != "ollama" and not api_key:
            attempts.append(ProviderAttempt(provider=provider, model=model, skipped=True, error="API 키 미설정"))
            continue
        try:
            result, usage = _invoke_structured_on_provider(
                prompt,
                provider=provider,
                model=model,
                api_key=api_key,
                base_url=cfg.ollama_base_url if provider == "ollama" else None,
                output_model=output_model,
                inputs=inputs,
            )
            total_latency_ms += usage.latency_ms
            label = f"{provider}:{model}"
            if fallback_provider:
                label = f"{fallback_provider}->{provider}:{model}"
            usage = usage.with_label(label, fallback_provider=fallback_provider)
            usage.latency_ms = total_latency_ms
            return result, usage
        except Exception as exc:
            err_str = str(exc)
            if len(err_str) > 200:
                err_str = err_str[:200] + "..."
            attempts.append(ProviderAttempt(
                provider=provider,
                model=model,
                rate_limited=_is_rate_limit_error(exc),
                error=err_str,
            ))
            # Approximate failed-attempt latency is not tracked separately;
            # mark next provider as fallback of the one that failed.
            fallback_provider = provider
            print(f"[ai_provider] {provider} failed: {exc}")

    raise AllProvidersFailedError(attempts)


def invoke_structured_output(
    output_model: Type[T],
    *,
    system_prompt: str,
    human_template: str,
    inputs: dict[str, Any],
    ai_config: AiProviderConfigPayload | None = None,
    task_type: TaskType | None = None,
) -> tuple[T, AiUsageInfo]:
    """Try configured provider chain; return (parsed model, usage metrics)."""
    cfg = route_by_task(task_type, ai_config) if task_type else (ai_config or AiProviderConfigPayload())
    return invoke_with_fallback(
        output_model,
        system_prompt=system_prompt,
        human_template=human_template,
        inputs=inputs,
        ai_config=cfg,
    )
