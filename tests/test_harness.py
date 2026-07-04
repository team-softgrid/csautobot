"""
CSAutobot 하네스 테스트
LLM/DB Mock 기반으로 CI에서 실행됩니다. 실제 API 키 불필요.
"""
import pytest


class TestHealth:
    def test_root_is_accessible(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json().get("status") == "online"

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"

    def test_docs_accessible(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_schema_valid(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "openapi" in schema
        assert "paths" in schema


class TestAuth:
    def test_login_missing_credentials_fails(self, client):
        resp = client.post("/api/v1/auth/login", data={})
        assert resp.status_code == 422

    def test_login_wrong_credentials_fails(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "notexist@test.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_protected_endpoint_without_token_fails(self, client):
        resp = client.get("/api/v1/users")
        assert resp.status_code in (401, 403)


class TestLeads:
    def test_lead_submission_success(self, client):
        resp = client.post(
            "/api/v1/leads",
            json={
                "company_name": "테스트 충전운영사",
                "contact_name": "홍길동",
                "email": "test@example.com",
                "phone": "010-1234-5678",
                "interest_plans": ["파일럿 (스탠다드)"],
                "message": "데모 요청합니다.",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "NEW"
        assert "id" in data

    def test_lead_invalid_email_rejected(self, client):
        resp = client.post(
            "/api/v1/leads",
            json={
                "company_name": "테스트",
                "contact_name": "홍길동",
                "email": "not-an-email",
            },
        )
        assert resp.status_code == 422


class TestBilling:
    def test_monthly_usage_endpoint(self, client):
        resp = client.get("/api/v1/billing/usage/monthly")
        assert resp.status_code == 200
        data = resp.json()
        assert "plan_code" in data
        assert "usage" in data
        assert "RAG_SEARCH" in data["usage"]

    def test_billing_admin_requires_auth(self, client):
        resp = client.get("/api/v1/billing/admin/summary")
        assert resp.status_code in (401, 403)

    def test_billing_admin_tenants_requires_auth(self, client):
        resp = client.get("/api/v1/billing/admin/tenants")
        assert resp.status_code in (401, 403)

    def test_billing_admin_plans_requires_auth(self, client):
        resp = client.get("/api/v1/billing/admin/plans")
        assert resp.status_code in (401, 403)

    def test_billing_admin_plan_patch_requires_auth(self, client):
        resp = client.patch(
            "/api/v1/billing/admin/tenants/default/plan",
            json={"plan_code": "PRO"},
        )
        assert resp.status_code in (401, 403)

    def test_billing_admin_plan_audit_requires_auth(self, client):
        resp = client.get("/api/v1/billing/admin/plan-audit")
        assert resp.status_code in (401, 403)


class TestLeadsAdmin:
    def test_leads_list_requires_auth(self, client):
        resp = client.get("/api/v1/leads")
        assert resp.status_code in (401, 403)

    def test_notify_failures_requires_auth(self, client):
        resp = client.get("/api/v1/leads/notify-failures")
        assert resp.status_code in (401, 403)

    def test_notify_failure_retry_requires_auth(self, client):
        resp = client.post("/api/v1/leads/notify-failures/1/retry")
        assert resp.status_code in (401, 403)

    def test_notify_channels_requires_auth(self, client):
        resp = client.get("/api/v1/leads/notify-channels")
        assert resp.status_code in (401, 403)


class TestInspectionMetering:
    def test_inspection_draft_records_usage(self, client, mocker):
        mocker.patch("services.billing_metering.check_quota")
        mock_draft = mocker.MagicMock()
        mock_draft.draft_text = "test draft"
        mock_draft.summary_json = {"risk": "low"}
        mocker.patch(
            "app.routes.inspection.svc.generate_inspection_draft",
            return_value=mock_draft,
        )
        resp = client.post(
            "/api/v1/inspection/draft",
            json={
                "target": "충전기",
                "cycle": "월간",
                "checklist": [{"item": "외관", "status": "정상", "note": ""}],
                "memo": "테스트",
            },
        )
        assert resp.status_code == 200
        usage_resp = client.get("/api/v1/billing/usage/monthly")
        assert usage_resp.json()["usage"]["AI_GENERATION"]["used"] >= 1


class TestQuotationMetering:
    def test_quotation_draft_records_usage(self, client, mocker):
        mocker.patch("services.billing_metering.check_quota")
        from services.quotation_service import QuotationDraft

        mocker.patch(
            "app.routes.quotation.generate_quotation_draft",
            return_value=QuotationDraft(
                symptom_summary="증상",
                likely_cause="원인",
                parts=[],
                dispatch_fee=0,
                labor_fee=0,
                supply_value=0,
                vat=0,
                total_amount=0,
            ),
        )
        resp = client.post(
            "/api/v1/quotation/draft",
            json={"query": "충전기 오류", "charger_type": "급속"},
        )
        assert resp.status_code == 200
        usage_resp = client.get("/api/v1/billing/usage/monthly")
        assert usage_resp.json()["usage"]["AI_GENERATION"]["used"] >= 1


class TestSearch:
    def test_search_empty_query_rejected(self, client):
        resp = client.post("/api/v1/search/as-cases", json={"query": ""})
        assert resp.status_code == 422

    def test_search_with_valid_query(self, client, mocker):
        mocker.patch(
            "app.routes.search.resolve_chroma_dir",
            return_value=None,
        )
        resp = client.post(
            "/api/v1/search/as-cases",
            json={"query": "충전기 과열 증상"},
        )
        assert resp.status_code in (200, 500)

    def test_search_query_too_long_rejected(self, client):
        resp = client.post("/api/v1/search/as-cases", json={"query": "a" * 2001})
        assert resp.status_code == 422


class TestInspection:
    def test_inspection_logs_endpoint_exists(self, client):
        resp = client.get("/api/v1/inspection/logs")
        assert resp.status_code == 200

    def test_inspection_preset_endpoint(self, client):
        resp = client.get("/api/v1/inspection/preset")
        assert resp.status_code == 200


class TestInputValidation:
    def test_leads_missing_required_fields(self, client):
        resp = client.post("/api/v1/leads", json={})
        assert resp.status_code == 422

    def test_content_type_json_required_for_leads(self, client):
        resp = client.post(
            "/api/v1/leads",
            data="company_name=test",
            headers={"Content-Type": "text/plain"},
        )
        assert resp.status_code in (400, 415, 422)
