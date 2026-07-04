import os
import sqlite3
import time
from typing import Any

LEADS_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def init_leads_db() -> None:
    conn = sqlite3.connect(LEADS_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            contact_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            interest_plans TEXT NOT NULL DEFAULT '',
            message TEXT,
            status TEXT NOT NULL DEFAULT 'NEW',
            created_at REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def get_leads_db():
    conn = sqlite3.connect(LEADS_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_lead(
    *,
    company_name: str,
    contact_name: str,
    email: str,
    phone: str | None,
    interest_plans: list[str],
    message: str | None,
) -> dict[str, Any]:
    now = time.time()
    plans_text = ", ".join(interest_plans)
    conn = sqlite3.connect(LEADS_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO leads
                (company_name, contact_name, email, phone, interest_plans, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (company_name, contact_name, email, phone, plans_text, message, now),
        )
        conn.commit()
        lead_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row) if row else {"id": lead_id}
    finally:
        conn.close()


def list_leads(*, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    conn = sqlite3.connect(LEADS_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT * FROM leads
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_lead_status(lead_id: int, status: str) -> dict[str, Any] | None:
    conn = sqlite3.connect(LEADS_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE leads SET status = ? WHERE id = ?",
            (status, lead_id),
        )
        if cursor.rowcount == 0:
            return None
        conn.commit()
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
