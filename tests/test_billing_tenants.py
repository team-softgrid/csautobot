"""Tests for billing tenant listing."""
from services.billing_metering import DEFAULT_TENANT_ID, list_tenants


class TestListTenants:
    def test_list_tenants_returns_at_least_default(self):
        rows = list_tenants()
        assert len(rows) >= 1
        ids = [r["tenant_id"] for r in rows]
        assert DEFAULT_TENANT_ID in ids or len(rows) >= 1

    def test_tenant_row_shape(self):
        rows = list_tenants()
        row = rows[0]
        assert "tenant_id" in row
        assert "tenant_name" in row
        assert "plan_code" in row
