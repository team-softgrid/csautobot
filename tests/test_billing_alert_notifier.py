"""Tests for billing usage alert notifications."""
from services.billing_alert_notifier import send_usage_alert_notifications


class TestBillingAlertNotifier:
    def test_no_channels_configured(self, mocker):
        mocker.patch("services.billing_alert_notifier._slack_webhook_url", return_value="")
        mocker.patch("services.billing_alert_notifier._smtp_configured", return_value=False)
        mocker.patch(
            "services.billing_alert_notifier.get_monthly_summary",
            return_value={
                "period_start": "2026-07-01T00:00:00Z",
                "usage_alerts": [
                    {
                        "feature_code": "RAG_SEARCH",
                        "used": 90,
                        "limit": 100,
                        "percent_used": 90,
                        "threshold_percent": 90,
                        "level": "critical",
                    }
                ],
            },
        )
        result = send_usage_alert_notifications("test_tenant")
        assert result["sent_count"] == 0
        assert "설정되지 않았습니다" in result["message"]

    def test_sends_and_dedupes(self, mocker):
        mocker.patch("services.billing_alert_notifier._slack_webhook_url", return_value="https://hooks.example")
        mocker.patch("services.billing_alert_notifier._smtp_configured", return_value=False)
        mocker.patch("services.billing_alert_notifier._send_slack_alert")
        mocker.patch("services.billing_alert_notifier._was_alert_sent", return_value=False)
        mark_mock = mocker.patch("services.billing_alert_notifier._mark_alert_sent")
        mocker.patch(
            "services.billing_alert_notifier.get_monthly_summary",
            return_value={
                "plan_code": "FREE",
                "period_start": "2026-07-01T00:00:00Z",
                "usage_alerts": [
                    {
                        "feature_code": "RAG_SEARCH",
                        "used": 85,
                        "limit": 100,
                        "percent_used": 85,
                        "threshold_percent": 80,
                        "level": "warning",
                    }
                ],
            },
        )
        result = send_usage_alert_notifications("dedupe_tenant")
        assert result["sent_count"] == 1
        mark_mock.assert_called_once()
