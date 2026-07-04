from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from auth_service import get_current_admin_user
from services.billing_metering import DEFAULT_TENANT_ID, get_monthly_summary

router = APIRouter(tags=["Billing"])


@router.get("/billing/usage/monthly")
def monthly_usage(tenant_id: Optional[str] = Query(default=DEFAULT_TENANT_ID)) -> dict[str, Any]:
    tid = tenant_id or DEFAULT_TENANT_ID
    return get_monthly_summary(tid)


@router.get("/billing/admin/summary")
def billing_admin_summary(
    tenant_id: Optional[str] = Query(default=DEFAULT_TENANT_ID),
    _admin: dict = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Admin-only billing summary (same payload, auth-gated)."""
    tid = tenant_id or DEFAULT_TENANT_ID
    return get_monthly_summary(tid)
