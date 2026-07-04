from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from auth_service import get_current_admin_user
from services.billing_metering import (
    DEFAULT_TENANT_ID,
    get_monthly_summary,
    list_tenants,
)

router = APIRouter(tags=["Billing"])


class TenantItem(BaseModel):
    tenant_id: str
    tenant_name: str
    plan_code: str


@router.get("/billing/usage/monthly")
def monthly_usage(tenant_id: Optional[str] = Query(default=DEFAULT_TENANT_ID)) -> dict[str, Any]:
    tid = tenant_id or DEFAULT_TENANT_ID
    return get_monthly_summary(tid)


@router.get("/billing/admin/tenants", response_model=list[TenantItem])
def billing_admin_tenants(
    _admin: dict = Depends(get_current_admin_user),
) -> list[TenantItem]:
    return [TenantItem(**row) for row in list_tenants()]


@router.get("/billing/admin/summary")
def billing_admin_summary(
    tenant_id: Optional[str] = Query(default=DEFAULT_TENANT_ID),
    _admin: dict = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Admin-only billing summary (same payload, auth-gated)."""
    tid = tenant_id or DEFAULT_TENANT_ID
    return get_monthly_summary(tid)
