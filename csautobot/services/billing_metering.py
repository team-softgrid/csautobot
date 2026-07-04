"""Plan quotas and usage metering for tenant billing."""

from __future__ import annotations

import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func

from storage.db import get_db_context
from storage.repositories import Tenant, UsageMeter

# feature_code values align with usage_meter.feature_code in schema.sql
FEATURE_RAG_SEARCH = "RAG_SEARCH"
FEATURE_AI_GENERATION = "AI_GENERATION"

PLAN_LIMITS: dict[str, dict[str, int | None]] = {
    "FREE": {FEATURE_RAG_SEARCH: 100, FEATURE_AI_GENERATION: 10},
    "PRO": {FEATURE_RAG_SEARCH: 5000, FEATURE_AI_GENERATION: 500},
    "ENTERPRISE": {FEATURE_RAG_SEARCH: None, FEATURE_AI_GENERATION: None},
}

DEFAULT_TENANT_ID = "default_tenant"


def _month_start() -> datetime.datetime:
    now = datetime.datetime.utcnow()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_plan_code(tenant_id: str = DEFAULT_TENANT_ID) -> str:
    with get_db_context() as db:
        tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if not tenant:
            return "FREE"
        return (tenant.plan_code or "FREE").upper()


def get_limit(plan_code: str, feature_code: str) -> int | None:
    limits = PLAN_LIMITS.get(plan_code.upper(), PLAN_LIMITS["FREE"])
    return limits.get(feature_code)


def get_monthly_count(tenant_id: str, feature_code: str) -> int:
    start = _month_start()
    with get_db_context() as db:
        total = (
            db.query(func.coalesce(func.sum(UsageMeter.request_count), 0))
            .filter(
                UsageMeter.tenant_id == tenant_id,
                UsageMeter.feature_code == feature_code,
                UsageMeter.measured_at >= start,
            )
            .scalar()
        )
        return int(total or 0)


def check_quota(tenant_id: str, feature_code: str) -> None:
    plan = get_plan_code(tenant_id)
    limit = get_limit(plan, feature_code)
    if limit is None:
        return
    used = get_monthly_count(tenant_id, feature_code)
    if used >= limit:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "월 사용량 한도를 초과했습니다.",
                "plan_code": plan,
                "feature_code": feature_code,
                "used": used,
                "limit": limit,
            },
        )


def record_usage(
    tenant_id: str,
    feature_code: str,
    *,
    user_id: str | None = None,
    model_name: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    request_count: int = 1,
) -> None:
    with get_db_context() as db:
        db.add(
            UsageMeter(
                tenant_id=tenant_id,
                user_id=user_id,
                feature_code=feature_code,
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_count=request_count,
            )
        )


def get_monthly_summary(tenant_id: str = DEFAULT_TENANT_ID) -> dict[str, Any]:
    plan = get_plan_code(tenant_id)
    features = [FEATURE_RAG_SEARCH, FEATURE_AI_GENERATION]
    usage: dict[str, Any] = {}
    for code in features:
        used = get_monthly_count(tenant_id, code)
        limit = get_limit(plan, code)
        usage[code] = {
            "used": used,
            "limit": limit,
            "remaining": None if limit is None else max(0, limit - used),
        }
    return {
        "tenant_id": tenant_id,
        "plan_code": plan,
        "period_start": _month_start().isoformat() + "Z",
        "usage": usage,
    }
