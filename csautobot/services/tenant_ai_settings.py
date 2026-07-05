"""Tenant-scoped AI provider settings and encrypted API credentials."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.ai_credentials import (
    build_credential_hints,
    configured_providers,
    decrypt_credentials,
    encrypt_credentials,
)
from services.ai_provider import (
    AIProviderName,
    AISelectionMode,
    AiProviderConfigPayload,
    DEFAULT_HYBRID_ORDER,
    DEFAULT_MODELS,
)
from services.billing_metering import DEFAULT_TENANT_ID, get_daily_token_total
from storage.repositories import Tenant, TenantAiSettings


class AiSettingsPublic(BaseModel):
    tenant_id: str
    provider: AISelectionMode = "hybrid"
    hybrid_providers: list[AIProviderName] = Field(default_factory=lambda: list(DEFAULT_HYBRID_ORDER))
    models: dict[str, str] = Field(default_factory=dict)
    ollama_base_url: str = "http://localhost:11434"
    daily_token_limit: int | None = None
    configured_providers: list[str] = Field(default_factory=list)
    credential_hints: dict[str, str] = Field(default_factory=dict)


class AiSettingsUpdate(BaseModel):
    tenant_id: str = DEFAULT_TENANT_ID
    provider: AISelectionMode = "hybrid"
    hybrid_providers: list[AIProviderName] = Field(default_factory=lambda: list(DEFAULT_HYBRID_ORDER))
    models: dict[str, str] = Field(default_factory=dict)
    ollama_base_url: str = "http://localhost:11434"
    daily_token_limit: int | None = None
    api_keys: dict[str, str] = Field(default_factory=dict)


def _ensure_tenant(db: Session, tenant_id: str) -> None:
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if tenant is None:
        db.add(Tenant(tenant_id=tenant_id, tenant_name=tenant_id, plan_code="FREE"))
        db.flush()


def _default_models() -> dict[str, str]:
    return dict(DEFAULT_MODELS)


def get_public_settings(db: Session, tenant_id: str) -> AiSettingsPublic:
    tid = (tenant_id or DEFAULT_TENANT_ID).strip()
    row = db.query(TenantAiSettings).filter(TenantAiSettings.tenant_id == tid).first()
    if row is None:
        return AiSettingsPublic(tenant_id=tid, models=_default_models())

    credentials = decrypt_credentials(row.credentials_encrypted)
    return AiSettingsPublic(
        tenant_id=tid,
        provider=row.provider,  # type: ignore[arg-type]
        hybrid_providers=row.hybrid_providers or list(DEFAULT_HYBRID_ORDER),
        models={**_default_models(), **(row.models or {})},
        ollama_base_url=row.ollama_base_url or "http://localhost:11434",
        daily_token_limit=row.daily_token_limit,
        configured_providers=configured_providers(credentials),
        credential_hints=row.credential_hints or build_credential_hints(credentials),
    )


def save_settings(db: Session, payload: AiSettingsUpdate) -> AiSettingsPublic:
    tid = (payload.tenant_id or DEFAULT_TENANT_ID).strip()
    _ensure_tenant(db, tid)

    row = db.query(TenantAiSettings).filter(TenantAiSettings.tenant_id == tid).first()
    existing = decrypt_credentials(row.credentials_encrypted if row else None)

    merged = dict(existing)
    for provider, value in (payload.api_keys or {}).items():
        cleaned = (value or "").strip()
        if cleaned:
            merged[provider] = cleaned
        elif provider in merged:
            del merged[provider]

    encrypted = encrypt_credentials(merged) if merged else None
    hints = build_credential_hints(merged)

    hybrid = payload.hybrid_providers or list(DEFAULT_HYBRID_ORDER)
    models = {**_default_models(), **(payload.models or {})}

    if row is None:
        row = TenantAiSettings(
            tenant_id=tid,
            provider=payload.provider,
            hybrid_providers=hybrid,
            models=models,
            ollama_base_url=payload.ollama_base_url or "http://localhost:11434",
            daily_token_limit=payload.daily_token_limit,
            credentials_encrypted=encrypted,
            credential_hints=hints,
        )
        db.add(row)
    else:
        row.provider = payload.provider
        row.hybrid_providers = hybrid
        row.models = models
        row.ollama_base_url = payload.ollama_base_url or "http://localhost:11434"
        row.daily_token_limit = payload.daily_token_limit
        row.credentials_encrypted = encrypted
        row.credential_hints = hints

    db.commit()
    db.refresh(row)
    return get_public_settings(db, tid)


def load_runtime_config(db: Session, tenant_id: str) -> AiProviderConfigPayload:
    """Build server-side AI config including decrypted tenant credentials."""
    public = get_public_settings(db, tenant_id)
    row = db.query(TenantAiSettings).filter(TenantAiSettings.tenant_id == public.tenant_id).first()
    credentials = decrypt_credentials(row.credentials_encrypted if row else None)

    hybrid_providers = public.hybrid_providers
    models = dict(public.models)

    limit = public.daily_token_limit
    if limit is not None and limit > 0:
        used = get_daily_token_total(public.tenant_id)
        if used >= limit:
            hybrid_providers = ["groq", "ollama"]
            models["groq"] = "llama-3.1-8b-instant"

    return AiProviderConfigPayload(
        provider=public.provider,
        hybrid_providers=hybrid_providers,
        api_keys=credentials,
        models=models,
        ollama_base_url=public.ollama_base_url,
    )


def resolve_ai_config_for_request(
    db: Session,
    tenant_id: str,
    client_config: AiProviderConfigPayload | None = None,
) -> AiProviderConfigPayload:
    """Tenant-stored credentials take precedence; client api_keys are ignored."""
    runtime = load_runtime_config(db, tenant_id)
    if client_config is None:
        return runtime

    return AiProviderConfigPayload(
        provider=client_config.provider or runtime.provider,
        hybrid_providers=client_config.hybrid_providers or runtime.hybrid_providers,
        api_keys=runtime.api_keys,
        models={**runtime.models, **(client_config.models or {})},
        ollama_base_url=client_config.ollama_base_url or runtime.ollama_base_url,
    )
