from typing import Any, Optional

from fastapi import APIRouter, Query

from services.billing_metering import DEFAULT_TENANT_ID, get_monthly_summary

router = APIRouter(tags=["Billing"])


@router.get("/billing/usage/monthly")
def monthly_usage(tenant_id: Optional[str] = Query(default=DEFAULT_TENANT_ID)) -> dict[str, Any]:
    tid = tenant_id or DEFAULT_TENANT_ID
    return get_monthly_summary(tid)
