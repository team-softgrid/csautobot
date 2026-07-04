"""Unit tests for billing metering (no LLM/Chroma required)."""
import pytest
from fastapi import HTTPException

from services.billing_metering import (
    FEATURE_RAG_SEARCH,
    PLAN_LIMITS,
    VALID_PLAN_CODES,
    check_quota,
    get_limit,
    get_monthly_summary,
    list_plan_change_audits,
    list_plans,
    record_usage,
    update_tenant_plan,
)


class TestBillingMetering:
    def test_plan_limits_defined(self):
        assert "FREE" in PLAN_LIMITS
        assert PLAN_LIMITS["FREE"][FEATURE_RAG_SEARCH] == 100

    def test_get_limit_free(self):
        assert get_limit("FREE", FEATURE_RAG_SEARCH) == 100

    def test_get_limit_enterprise_unlimited(self):
        assert get_limit("ENTERPRISE", FEATURE_RAG_SEARCH) is None

    def test_record_and_summary(self):
        tenant_id = "test_billing_tenant"
        record_usage(tenant_id, FEATURE_RAG_SEARCH, request_count=1)
        summary = get_monthly_summary(tenant_id)
        assert summary["tenant_id"] == tenant_id
        assert summary["usage"][FEATURE_RAG_SEARCH]["used"] >= 1

    def test_quota_exceeded_raises_429(self, mocker):
        tenant_id = "quota_test_tenant"
        mocker.patch(
            "services.billing_metering.get_plan_code",
            return_value="FREE",
        )
        mocker.patch(
            "services.billing_metering.get_monthly_count",
            return_value=100,
        )
        with pytest.raises(HTTPException) as exc:
            check_quota(tenant_id, FEATURE_RAG_SEARCH)
        assert exc.value.status_code == 429

    def test_list_plans_returns_all_codes(self):
        plans = list_plans()
        codes = {row["plan_code"] for row in plans}
        assert codes == set(VALID_PLAN_CODES)
        for row in plans:
            assert row["limits"] == PLAN_LIMITS[row["plan_code"]]

    def test_update_tenant_plan(self):
        row = update_tenant_plan("pytest_plan_tenant", "PRO")
        assert row["tenant_id"] == "pytest_plan_tenant"
        assert row["plan_code"] == "PRO"
        summary = get_monthly_summary("pytest_plan_tenant")
        assert summary["plan_code"] == "PRO"

    def test_update_tenant_plan_invalid_raises(self):
        with pytest.raises(ValueError):
            update_tenant_plan("pytest_plan_tenant", "INVALID")

    def test_update_tenant_plan_records_audit(self):
        update_tenant_plan("pytest_audit_tenant", "PRO", changed_by="admin@test.com")
        audits = list_plan_change_audits(tenant_id="pytest_audit_tenant", limit=10)
        assert len(audits) >= 1
        assert audits[0]["old_plan"] == "FREE"
        assert audits[0]["new_plan"] == "PRO"
        assert audits[0]["changed_by"] == "admin@test.com"
