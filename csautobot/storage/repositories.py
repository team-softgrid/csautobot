"""점검일지 / 피드백 CRUD 리포지토리."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .db import get_conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ---------- inspection_log ----------


def create_inspection_log(
    *,
    site_name: str | None,
    charger_id: str | None,
    manufacturer: str | None,
    model_name: str | None,
    inspection_type: str,
    inspection_cycle: str | None,
    engineer_name: str | None,
    checklist: list[dict[str, Any]],
    memo_text: str | None,
    photo_paths: list[str] | None,
    ai_summary: dict[str, Any] | None = None,
    ai_model: str | None = None,
    status: str = "draft",
    inspection_id: str | None = None,
) -> str:
    iid = inspection_id or new_id("ins")
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO inspection_log (
                inspection_id, site_name, charger_id, manufacturer, model_name,
                inspection_type, inspection_cycle, engineer_name,
                checklist_json, memo_text, photo_paths_json,
                ai_summary_json, ai_model, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                iid,
                site_name,
                charger_id,
                manufacturer,
                model_name,
                inspection_type,
                inspection_cycle,
                engineer_name,
                json.dumps(checklist, ensure_ascii=False),
                memo_text,
                json.dumps(photo_paths or [], ensure_ascii=False),
                json.dumps(ai_summary, ensure_ascii=False) if ai_summary else None,
                ai_model,
                status,
                now,
                now,
            ),
        )
    return iid


def update_inspection_ai_summary(
    inspection_id: str,
    ai_summary: dict[str, Any],
    ai_model: str | None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE inspection_log
               SET ai_summary_json = ?, ai_model = ?, updated_at = ?
             WHERE inspection_id = ?
            """,
            (
                json.dumps(ai_summary, ensure_ascii=False),
                ai_model,
                _now_iso(),
                inspection_id,
            ),
        )


def confirm_inspection_log(inspection_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE inspection_log
               SET status = 'confirmed', updated_at = ?
             WHERE inspection_id = ?
            """,
            (_now_iso(), inspection_id),
        )


def list_inspection_logs(limit: int = 100) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT *
              FROM inspection_log
             ORDER BY created_at DESC
             LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_inspection_row_to_dict(r) for r in rows]


def get_inspection_log(inspection_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM inspection_log WHERE inspection_id = ?",
            (inspection_id,),
        ).fetchone()
    return _inspection_row_to_dict(row) if row else None


def _inspection_row_to_dict(row: Any) -> dict[str, Any]:
    d = dict(row)
    for key in ("checklist_json", "photo_paths_json", "ai_summary_json"):
        if d.get(key):
            try:
                d[key.replace("_json", "")] = json.loads(d[key])
            except json.JSONDecodeError:
                d[key.replace("_json", "")] = None
        else:
            d[key.replace("_json", "")] = None
    return d


# ---------- feedback ----------


def create_feedback(
    *,
    target_type: str,
    target_id: str | None,
    role: str,
    reviewer_name: str | None,
    rating: int | None,
    usefulness: int | None,
    comment: str | None,
) -> str:
    fid = new_id("fb")
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO feedback (
                feedback_id, target_type, target_id, role,
                reviewer_name, rating, usefulness, comment, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (fid, target_type, target_id, role, reviewer_name, rating, usefulness, comment, now),
        )
    return fid


def list_feedback(
    target_type: str | None = None,
    target_id: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM feedback"
    params: list[Any] = []
    clauses: list[str] = []
    if target_type:
        clauses.append("target_type = ?")
        params.append(target_type)
    if target_id:
        clauses.append("target_id = ?")
        params.append(target_id)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]
