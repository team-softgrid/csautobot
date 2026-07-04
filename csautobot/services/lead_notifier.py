"""Best-effort notifications when a new sales lead is created."""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Any

import httpx

logger = logging.getLogger(__name__)


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
    try:
        _send_webhook(lead)
    except Exception as exc:
        logger.warning("Lead webhook failed: %s", exc)
    try:
        _send_slack(lead)
    except Exception as exc:
        logger.warning("Lead Slack notification failed: %s", exc)
    try:
        _send_smtp(lead)
    except Exception as exc:
        logger.warning("Lead email notification failed: %s", exc)
