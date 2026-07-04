"""Best-effort notifications when a new sales lead is created."""

from __future__ import annotations

import logging
import os
import smtplib
import time
from collections.abc import Callable
from email.message import EmailMessage
from typing import Any

import httpx

from leads_db import record_notify_event, record_notify_failure

logger = logging.getLogger(__name__)
MAX_NOTIFY_RETRIES = 3

TEST_LEAD: dict[str, Any] = {
    "id": 0,
    "company_name": "[테스트] CSAutobot",
    "contact_name": "관리자",
    "email": "test@csautobot.local",
    "phone": "010-0000-0000",
    "interest_plans": "테스트 발송",
    "message": "알림 채널 테스트 메시지입니다.",
    "status": "NEW",
    "created_at": 0.0,
}


def _is_channel_configured(channel: str) -> bool:
    for row in get_notify_channel_status():
        if row["channel"] == channel:
            return bool(row["configured"])
    return False


def _channel_sender(channel: str) -> Callable[[dict[str, Any]], None] | None:
    senders: dict[str, Callable[[dict[str, Any]], None]] = {
        "webhook": _send_webhook,
        "slack": _send_slack,
        "smtp": _send_smtp,
    }
    return senders.get(channel)


def _lead_summary(lead: dict[str, Any]) -> str:
    plans = lead.get("interest_plans") or "-"
    phone = lead.get("phone") or "-"
    message = lead.get("message") or "-"
    return (
        f"회사: {lead.get('company_name', '-')}\n"
        f"담당자: {lead.get('contact_name', '-')}\n"
        f"이메일: {lead.get('email', '-')}\n"
        f"전화: {phone}\n"
        f"관심 플랜: {plans}\n"
        f"메시지: {message}\n"
        f"Lead ID: {lead.get('id', '-')}\n"
    )


def _attempt_channel(
    channel: str,
    lead: dict[str, Any],
    send_fn: Callable[[dict[str, Any]], None],
    *,
    source: str = "lead_created",
) -> None:
    lead_id = int(lead.get("id") or 0)
    last_exc: Exception | None = None
    for attempt in range(MAX_NOTIFY_RETRIES):
        try:
            send_fn(lead)
            record_notify_event(lead_id, channel, success=True, source=source)
            return
        except Exception as exc:
            last_exc = exc
            logger.warning("Lead %s attempt %s failed: %s", channel, attempt + 1, exc)
            if attempt < MAX_NOTIFY_RETRIES - 1:
                time.sleep(0.2 * (attempt + 1))
    if last_exc is not None:
        record_notify_failure(lead_id, channel, str(last_exc))
        logger.error("Lead %s dead-letter lead_id=%s: %s", channel, lead_id, last_exc)


def _send_webhook(lead: dict[str, Any]) -> None:
    url = os.environ.get("LEADS_WEBHOOK_URL", "").strip()
    if not url:
        return
    payload = {
        "event": "lead.created",
        "lead": {
            "id": lead.get("id"),
            "company_name": lead.get("company_name"),
            "contact_name": lead.get("contact_name"),
            "email": lead.get("email"),
            "phone": lead.get("phone"),
            "interest_plans": lead.get("interest_plans"),
            "message": lead.get("message"),
            "status": lead.get("status", "NEW"),
            "created_at": lead.get("created_at"),
        },
    }
    with httpx.Client(timeout=10.0) as client:
        client.post(url, json=payload)


def _send_slack(lead: dict[str, Any]) -> None:
    url = os.environ.get("LEADS_SLACK_WEBHOOK_URL", "").strip()
    if not url:
        return
    company = lead.get("company_name", "신규")
    contact = lead.get("contact_name", "-")
    email = lead.get("email", "-")
    plans = lead.get("interest_plans") or "-"
    payload = {
        "text": f"[CSAutobot] 새 도입 상담 — {company}",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📋 새 도입 상담 접수"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*회사*\n{company}"},
                    {"type": "mrkdwn", "text": f"*담당자*\n{contact}"},
                    {"type": "mrkdwn", "text": f"*이메일*\n{email}"},
                    {"type": "mrkdwn", "text": f"*관심 플랜*\n{plans}"},
                ],
            },
        ],
    }
    message = lead.get("message")
    if message:
        payload["blocks"].append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*메시지*\n{message}"},
            }
        )
    with httpx.Client(timeout=10.0) as client:
        client.post(url, json=payload)


def _send_smtp(lead: dict[str, Any]) -> None:
    to_addr = os.environ.get("LEADS_NOTIFY_EMAIL", "").strip()
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    if not to_addr or not smtp_host:
        return

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("SMTP_FROM", smtp_user or to_addr).strip()

    subject = f"[CSAutobot] 도입 상담 접수 — {lead.get('company_name', '신규')}"
    body = "새 도입 상담 요청이 접수되었습니다.\n\n" + _lead_summary(lead)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        if smtp_user and smtp_password:
            server.starttls()
            server.login(smtp_user, smtp_password)
        server.send_message(msg)


def notify_new_lead(lead: dict[str, Any]) -> None:
    """Notify ops/CRM about a new lead. Failures are logged, never raised."""
    logger.info("New lead #%s: %s", lead.get("id"), lead.get("company_name"))
    _attempt_channel("webhook", lead, _send_webhook)
    _attempt_channel("slack", lead, _send_slack)
    _attempt_channel("smtp", lead, _send_smtp)


def retry_lead_channel(lead: dict[str, Any], channel: str) -> bool:
    """Manually retry a single notification channel. Returns True on success."""
    send_fn = _channel_sender(channel)
    if send_fn is None:
        return False
    lead_id = int(lead.get("id") or 0)
    last_exc: Exception | None = None
    for attempt in range(MAX_NOTIFY_RETRIES):
        try:
            send_fn(lead)
            record_notify_event(lead_id, channel, success=True, source="manual_retry")
            return True
        except Exception as exc:
            last_exc = exc
            logger.warning("Lead %s manual retry %s failed: %s", channel, attempt + 1, exc)
            if attempt < MAX_NOTIFY_RETRIES - 1:
                time.sleep(0.2 * (attempt + 1))
    if last_exc is not None:
        record_notify_failure(lead_id, channel, str(last_exc))
    return False


def get_notify_channel_status() -> list[dict[str, Any]]:
    """Return whether each notification channel is configured (no secrets exposed)."""
    return [
        {
            "channel": "webhook",
            "label": "CRM Webhook",
            "configured": bool(os.environ.get("LEADS_WEBHOOK_URL", "").strip()),
            "env_var": "LEADS_WEBHOOK_URL",
        },
        {
            "channel": "slack",
            "label": "Slack",
            "configured": bool(os.environ.get("LEADS_SLACK_WEBHOOK_URL", "").strip()),
            "env_var": "LEADS_SLACK_WEBHOOK_URL",
        },
        {
            "channel": "smtp",
            "label": "이메일 (SMTP)",
            "configured": bool(
                os.environ.get("LEADS_NOTIFY_EMAIL", "").strip()
                and os.environ.get("SMTP_HOST", "").strip()
            ),
            "env_var": "LEADS_NOTIFY_EMAIL, SMTP_HOST",
        },
    ]


def send_test_notification(channel: str, *, dry_run: bool = True) -> dict[str, Any]:
    """Send or validate a test lead notification for admin diagnostics."""
    send_fn = _channel_sender(channel)
    if send_fn is None:
        return {
            "channel": channel,
            "configured": False,
            "dry_run": dry_run,
            "success": False,
            "message": f"알 수 없는 채널: {channel}",
        }
    configured = _is_channel_configured(channel)
    if dry_run:
        return {
            "channel": channel,
            "configured": configured,
            "dry_run": True,
            "success": configured,
            "message": "설정 확인됨 — 실제 발송 없음" if configured else "채널이 설정되지 않았습니다.",
        }
    if not configured:
        return {
            "channel": channel,
            "configured": False,
            "dry_run": False,
            "success": False,
            "message": "채널이 설정되지 않았습니다.",
        }
    try:
        send_fn(TEST_LEAD)
        record_notify_event(0, channel, success=True, source="test")
        return {
            "channel": channel,
            "configured": True,
            "dry_run": False,
            "success": True,
            "message": "테스트 알림 발송 완료",
        }
    except Exception as exc:
        return {
            "channel": channel,
            "configured": True,
            "dry_run": False,
            "success": False,
            "message": str(exc),
        }
