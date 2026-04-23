-- csautobot MVP 스키마 (점검일지 + 피드백)
-- docs/TECHNICAL_DESIGN_V1.md 의 inspection_log / audit_log 를 MVP 수준으로 축약.

CREATE TABLE IF NOT EXISTS inspection_log (
    inspection_id     TEXT PRIMARY KEY,
    site_name         TEXT,
    charger_id        TEXT,
    manufacturer      TEXT,
    model_name        TEXT,
    inspection_type   TEXT NOT NULL,           -- 정기점검/고장AS/긴급출동/설치후점검
    inspection_cycle  TEXT,                    -- 월/분기/반기/년/수시
    engineer_name     TEXT,
    checklist_json    TEXT NOT NULL,           -- JSON array: [{item,status,note}]
    memo_text         TEXT,
    photo_paths_json  TEXT,                    -- JSON array of local paths
    ai_summary_json   TEXT,                    -- AI 초안 JSON 직렬화
    ai_model          TEXT,
    status            TEXT NOT NULL DEFAULT 'draft',  -- draft / confirmed
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_inspection_log_created_at
    ON inspection_log(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_inspection_log_charger
    ON inspection_log(charger_id);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id    TEXT PRIMARY KEY,
    target_type    TEXT NOT NULL,              -- 'inspection' | 'search' | 'general'
    target_id      TEXT,                       -- inspection_id 등
    role           TEXT NOT NULL,              -- 팀원 / 고객 / 엔지니어 / 기타
    reviewer_name  TEXT,
    rating         INTEGER,                    -- 1~5 (전반 만족도)
    usefulness     INTEGER,                    -- 1~5 (업무 도움도)
    comment        TEXT,
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_created_at
    ON feedback(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_feedback_target
    ON feedback(target_type, target_id);
