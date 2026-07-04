"""Send billing usage threshold alerts via Slack / email with monthly dedupe."""

from __future__ import annotations

import logging
import os
import smtplib
import sqlite3
import time
from email.message import EmailMessage
from typing import Any

import httpx

from services.billing_metering import DEFAULT_TENANT_ID, get_monthly_summary

logger = logging.getLogger(__name__)

BILLING_ALERT_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "billing_alerts.db",
)

FEATURE_LABELS = {
    "RAG_SEARCH": "AS 유사 사례 검색",
    "AI_GENERATION": "AI 생성 (점검·견적)",
}


def init_billing_alert_db() -> None:
    conn = sqlite3.connect(BILLING_ALERT_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_alert_sent (
            tenant_id TEXT NOT NULL,
            feature_code TEXT NOT NULL,
            threshold_percent INTEGER NOT NULL,
            period_start TEXT NOT NULL,
            sent_at REAL NOT NULL,
            PRIMARY KEY (tenant_id, feature_code, threshold_percent, period_start)
        )
        """
    )
    conn.commit()
    conn.close()


def _slack_webhook_url() -> str:
    return (
        os.environ.get("BILLING_ALERT_SLACK_WEBHOOK_URL", "").strip()
        or os.environ.get("LEADS_SLACK_WEBHOOK_URL", "").strip()
    )


def _alert_email_to() -> str:
    return (
        os.environ.get("BILLING_ALERT_EMAIL", "").strip()
        or os.environ.get("LEADS_NOTIFY_EMAIL", "").strip()
    )


def _smtp_configured() -> bool:
    return bool(_alert_email_to() and os.environ.get("SMTP_HOST", "").strip())


def _was_alert_sent(
    tenant_id: str,
    feature_code: str,
    threshold_percent: int,
    period_start: str,
) -> bool:
    conn = sqlite3.connect(BILLING_ALERT_DB_PATH)
    try:
        row = conn.execute(
            """
            SELECT 1 FROM usage_alert_sent
            WHERE tenant_id = ? AND feature_code = ? AND threshold_percent = ? AND period_start = ?
            """,
            (tenant_id, feature_code, threshold_percent, period_start),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _mark_alert_sent(
    tenant_id: str,
    feature_code: str,
    threshold_percent: int,
    period_start: str,
) -> None:
    conn = sqlite3.connect(BILLING_ALERT_DB_PATH)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO usage_alert_sent
                (tenant_id, feature_code, threshold_percent, period_start, sent_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tenant_id, feature_code, threshold_percent, period_start, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def _alert_message(tenant_id: str, summary: dict[str, Any], alert: dict[str, Any]) -> str:
    feature = FEATURE_LABELS.get(alert["feature_code"], alert["feature_code"])
    level = "위험" if alert["level"] == "critical" else "주의"
    return (
        f"테넌트: {tenant_id} ({summary['plan_code']})\n"
        f"기능: {feature}\n"
        f"사용량: {alert['used']}/{alert['limit']} ({alert['percent_used']}%)\n"
        f"임계치: {alert['threshold_percent']}% ({level})\n"
        f"집계 시작: {summary['period_start']}"
    )


def _send_slack_alert(tenant_id: str, summary: dict[str, Any], alert: dict[str, Any]) -> None:
    url = _slack_webhook_url()
    if not url:
        return
    feature = FEATURE_LABELS.get(alert["feature_code"], alert["feature_code"])
    payload = {
        "text": f"[CSAutobot] 사용량 {alert['threshold_percent']}% 임계치 — {tenant_id}",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "⚠️ Billing 사용량 임계치"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": _alert_message(tenant_id, summary, alert).replace("\n", "\n"),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*기능*\n{feature}"},
                    {"type": "mrkdwn", "text": f"*사용률*\n{alert['percent_used']}%"},
                ],
            },
        ],
    }
    with httpx.Client(timeout=10.0) as client:
        client.post(url, json=payload)


def _send_email_alert(tenant_id: str, summary: dict[str, Any], alert: dict[str, Any]) -> None:
    if not _smtp_configured():
        return
    to_addr = _alert_email_to()
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("SMTP_FROM", smtp_user or to_addr).strip()
    feature = FEATURE_LABELS.get(alert["feature_code"], alert["feature_code"])

    subject = f"[CSAutobot] 사용량 {alert['threshold_percent']}% — {tenant_id} / {feature}"
    body = "Billing 사용량이 임계치에 도달했습니다.\n\n" + _alert_message(tenant_id, summary, alert)

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


def send_usage_alert_notifications(
    tenant_id: str = DEFAULT_TENANT_ID,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Dispatch Slack/email for active usage alerts. Dedupes per month unless force=True."""
    init_billing_alert_db()
    tid = (tenant_id or DEFAULT_TENANT_ID).strip()
    summary = get_monthly_summary(tid)
    period_start = summary["period_start"]
    alerts = summary["usage_alerts"]

    if not _slack_webhook_url() and not _smtp_configured():
        return {
            "tenant_id": tid,
            "sent_count": 0,
            "skipped_count": len(alerts),
            "channels_available": [],
            "message": "Slack/이메일 알림 채널이 설정되지 않았습니다.",
            "results": [],
        }

    channels_available: list[str] = []
    if _slack_webhook_url():
        channels_available.append("slack")
    if _smtp_configured():
        channels_available.append("smtp")

    results: list[dict[str, Any]] = []
    sent_count = 0
    skipped_count = 0

    for alert in alerts:
        feature_code = alert["feature_code"]
        threshold = int(alert["threshold_percent"])
        if not force and _was_alert_sent(tid, feature_code, threshold, period_start):
            skipped_count += 1
            results.append(
                {
                    "feature_code": feature_code,
                    "threshold_percent": threshold,
                    "status": "skipped",
                    "message": "이번 달 이미 발송됨",
                }
            )
            continue
        try:
            _send_slack_alert(tid, summary, alert)
            _send_email_alert(tid, summary, alert)
            _mark_alert_sent(tid, feature_code, threshold, period_start)
            sent_count += 1
            results.append(
                {
                    "feature_code": feature_code,
                    "threshold_percent": threshold,
                    "status": "sent",
                    "channels": channels_available,
                }
            )
        except Exception as exc:
            logger.exception("Usage alert dispatch failed")
            results.append(
                {
                    "feature_code": feature_code,
                    "threshold_percent": threshold,
                    "status": "error",
                    "message": str(exc),
                }
            )

    message = f"{sent_count}건 발송, {skipped_count}건 건너뜀"
    return {
        "tenant_id": tid,
        "sent_count": sent_count,
        "skipped_count": skipped_count,
        "channels_available": channels_available,
        "message": message,
        "results": results,
    }
