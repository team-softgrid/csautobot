"""Tests for lead notification service."""
from unittest.mock import MagicMock, patch

from services.lead_notifier import notify_new_lead

SAMPLE_LEAD = {
    "id": 1,
    "company_name": "테스트 충전",
    "contact_name": "홍길동",
    "email": "test@example.com",
    "phone": "010-1234-5678",
    "interest_plans": "Pro 구독",
    "message": "데모 요청",
    "status": "NEW",
    "created_at": 1710000000.0,
}


class TestLeadNotifier:
    def test_notify_without_config_does_not_raise(self):
        with patch.dict("os.environ", {}, clear=True):
            notify_new_lead(SAMPLE_LEAD)

    def test_webhook_called_when_url_set(self, mocker):
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mocker.patch("services.lead_notifier.httpx.Client", return_value=mock_client)
        mocker.patch.dict(
            "os.environ",
            {"LEADS_WEBHOOK_URL": "https://crm.example/hooks/leads"},
            clear=False,
        )
        notify_new_lead(SAMPLE_LEAD)
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == "https://crm.example/hooks/leads"
        assert kwargs["json"]["event"] == "lead.created"
        assert kwargs["json"]["lead"]["email"] == "test@example.com"

    def test_smtp_skipped_without_host(self, mocker):
        smtp_mock = mocker.patch("services.lead_notifier.smtplib.SMTP")
        mocker.patch.dict(
            "os.environ",
            {"LEADS_NOTIFY_EMAIL": "ops@example.com"},
            clear=False,
        )
        notify_new_lead(SAMPLE_LEAD)
        smtp_mock.assert_not_called()

    def test_slack_called_when_url_set(self, mocker):
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mocker.patch("services.lead_notifier.httpx.Client", return_value=mock_client)
        mocker.patch.dict(
            "os.environ",
            {"LEADS_SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/TEST"},
            clear=False,
        )
        notify_new_lead(SAMPLE_LEAD)
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert "hooks.slack.com" in args[0]
        assert kwargs["json"]["text"].startswith("[CSAutobot]")

    def test_webhook_retries_then_dead_letter(self, mocker):
        mocker.patch("services.lead_notifier.time.sleep")
        mocker.patch(
            "services.lead_notifier._send_webhook",
            side_effect=RuntimeError("webhook down"),
        )
        record_mock = mocker.patch("services.lead_notifier.record_notify_failure")
        notify_new_lead(SAMPLE_LEAD)
        record_mock.assert_called_once_with(1, "webhook", "webhook down")
