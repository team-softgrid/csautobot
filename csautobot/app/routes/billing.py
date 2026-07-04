from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth_service import get_current_admin_user
from services.billing_metering import (
    DEFAULT_TENANT_ID,
    get_monthly_summary,
    list_plans,
    list_tenants,
    update_tenant_plan,
)

router = APIRouter(tags=["Billing"])


class TenantItem(BaseModel):
    tenant_id: str
    tenant_name: str
    plan_code: str


class PlanUpdateRequest(BaseModel):
    plan_code: Literal["FREE", "PRO", "ENTERPRISE"]


class PlanItem(BaseModel):
    plan_code: str
    limits: dict[str, int | None]


@router.get("/billing/usage/monthly")
def monthly_usage(tenant_id: Optional[str] = Query(default=DEFAULT_TENANT_ID)) -> dict[str, Any]:
    tid = tenant_id or DEFAULT_TENANT_ID
    return get_monthly_summary(tid)


@router.get("/billing/admin/plans", response_model=list[PlanItem])
def billing_admin_plans(
    _admin: dict = Depends(get_current_admin_user),
) -> list[PlanItem]:
    return [PlanItem(**row) for row in list_plans()]


@router.get("/billing/admin/tenants", response_model=list[TenantItem])
def billing_admin_tenants(
    _admin: dict = Depends(get_current_admin_user),
) -> list[TenantItem]:
    return [TenantItem(**row) for row in list_tenants()]


@router.patch("/billing/admin/tenants/{tenant_id}/plan", response_model=TenantItem)
def patch_tenant_plan(
    tenant_id: str,
    body: PlanUpdateRequest,
    _admin: dict = Depends(get_current_admin_user),
) -> TenantItem:
    try:
        row = update_tenant_plan(tenant_id, body.plan_code)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TenantItem(**row)


@router.get("/billing/admin/summary")
def billing_admin_summary(
    tenant_id: Optional[str] = Query(default=DEFAULT_TENANT_ID),
    _admin: dict = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Admin-only billing summary (same payload, auth-gated)."""
    tid = tenant_id or DEFAULT_TENANT_ID
    return get_monthly_summary(tid)
