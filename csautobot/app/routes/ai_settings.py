import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

HERE = Path(__file__).resolve().parent.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from auth_service import get_current_user
from services.ai_provider import AIProviderName, _is_rate_limit_error, test_provider_connection
from services.tenant_ai_settings import (
    AiSettingsPublic,
    AiSettingsUpdate,
    get_public_settings,
    load_runtime_config,
    save_settings,
)
from storage.db import get_db

router = APIRouter(tags=["AI Settings"])


class AiSettingsSaveRequest(BaseModel):
    tenant_id: str = "default_tenant"
    provider: str = "hybrid"
    hybrid_providers: list[str] = []
    models: dict[str, str] = {}
    ollama_base_url: str = "http://localhost:11434"
    daily_token_limit: int | None = None
    api_keys: dict[str, str] = {}


class AiSettingsTestRequest(BaseModel):
    tenant_id: str = "default_tenant"
    provider: AIProviderName = "groq"
    api_keys: dict[str, str] = {}


@router.get("/ai-settings", response_model=AiSettingsPublic)
def read_ai_settings(
    tenant_id: str = "default_tenant",
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return get_public_settings(db, tenant_id)


@router.put("/ai-settings", response_model=AiSettingsPublic)
def update_ai_settings(
    req: AiSettingsSaveRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    try:
        payload = AiSettingsUpdate(
            tenant_id=req.tenant_id,
            provider=req.provider,  # type: ignore[arg-type]
            hybrid_providers=req.hybrid_providers,  # type: ignore[arg-type]
            models=req.models,
            ollama_base_url=req.ollama_base_url,
            daily_token_limit=req.daily_token_limit,
            api_keys=req.api_keys,
        )
        return save_settings(db, payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 설정 저장 실패: {exc}") from exc


@router.post("/ai-settings/test")
def test_ai_settings_connection(
    req: AiSettingsTestRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    try:
        runtime = load_runtime_config(db, req.tenant_id)
        runtime.provider = req.provider  # type: ignore[assignment]
        for provider, value in (req.api_keys or {}).items():
            cleaned = (value or "").strip()
            if cleaned:
                runtime.api_keys[provider] = cleaned
        return test_provider_connection(req.provider, ai_config=runtime)
    except Exception as exc:
        if _is_rate_limit_error(exc):
            raise HTTPException(
                status_code=429,
                detail=(
                    "API 키는 인식되었으나 Gemini/OpenAI 등 사용 한도(quota)가 초과되었습니다. "
                    "Hybrid 1순위 Groq 키를 저장·테스트하거나, 유료 플랜/새 API 키를 사용하세요."
                ),
            ) from exc
        raise HTTPException(status_code=400, detail=f"연결 테스트 실패: {exc}") from exc
