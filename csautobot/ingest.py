"""
csData 폴더의 민원/AS 엑셀을 읽어 증상·조치 중심 텍스트 청크로 변환합니다.
시트마다 헤더 행 위치가 달라 키워드 점수로 헤더 행을 추정합니다.

환경변수:
  INGEST_ONLY_SUBSTR — 경로에 이 문자열이 들어간 xlsx만 처리 (예: 품질회의).
  INGEST_USE_LEGACY_FILE_SKIP=1 — 과거 파일명 제외 규칙(_SKIP_PATH_SUBSTR) 활성화.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd

from normalizer import error_code_norm_field, normalize_symptom_text
from paths import repo_root

ROOT = repo_root()
CS_DIR = ROOT / "csData"
OUT_JSONL = Path(__file__).resolve().parent / "as_records.jsonl"

# 헤더 후보 행에 많이 등장하는 토큰
_HEADER_TOKENS = (
    "순번",
    "순 번",
    "NO",
    "접수",
    "조치",
    "민원",
    "고장",
    "상세조치",
    "수리",
    "유형",
    "무상",
    "발주처",
    "파트",
    # 품질회의·불량 이력 등 (월간 품질회의 현장 품질 불량건.xlsx)
    "발생일자",
    "운영사",
    "고객사",
    "장비",
    "제조사",
    "모델",
    "품질",
    "불량",
    "개선",
)

# 의미 없는 짧은 행
_MIN_TEXT = 12


def _index_row(i: Any) -> int | str:
    try:
        return int(i)
    except (TypeError, ValueError):
        return str(i)


# 파일 단위 제외(집계·비용·생산량 등, 증상-조치 서술이 거의 없음)
_SKIP_PATH_SUBSTR = (
    "생산 수량",
    "보증시간",
    "자재비",
    "SK일렉링크_시그넷",
    "모던텍_2022_2023간_장애접수집계",
)


def _cell_str(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).replace("\n", " ").strip()
    return re.sub(r"\s+", " ", s)


def _header_score(row: list[Any]) -> int:
    text = " ".join(_cell_str(x) for x in row)
    return sum(1 for t in _HEADER_TOKENS if t in text)


def _find_header_row(raw: pd.DataFrame, max_scan: int = 30) -> int | None:
    best_i: int | None = None
    best_s = 0
    for i in range(min(max_scan, len(raw))):
        row = raw.iloc[i].tolist()
        s = _header_score(row)
        if s >= 5 and s >= best_s:
            best_s = s
            best_i = i
    return best_i


def _norm_col(c: str) -> str:
    return re.sub(r"\s+", " ", str(c).replace("\n", " ")).strip()


def _pick_col(cols: list[str], *must_include: str) -> str | None:
    for c in cols:
        cn = _norm_col(c)
        if all(m in cn for m in must_include):
            return c
    for c in cols:
        cn = _norm_col(c)
        if must_include[0] in cn:
            return c
    return None


def _row_skip(symptom: str, action: str, seq: str) -> bool:
    t = f"{symptom} {action}".strip()
    if len(t) < _MIN_TEXT:
        return True
    if re.fullmatch(r"(PB|DP)", _cell_str(seq)):
        return True
    if "민원 관리대장" in t and len(t) < 50:
        return True
    return False


def sheet_to_records(path: Path, sheet: str) -> list[dict[str, Any]]:
    raw = pd.read_excel(path, sheet_name=sheet, header=None, dtype=object, engine="openpyxl")
    hi = _find_header_row(raw)
    if hi is None:
        return []

    header_cells = raw.iloc[hi].tolist()
    df = raw.iloc[hi + 1 :].copy()
    df.columns = [_norm_col(c) for c in header_cells]
    df.reset_index(drop=True, inplace=True)

    cols = list(df.columns)
    col_symptom = (
        _pick_col(cols, "접수내용")
        or _pick_col(cols, "민원내용")
        or _pick_col(cols, "고장", "내역")
        or _pick_col(cols, "민원")
        or _pick_col(cols, "품명", "품질")
        or _pick_col(cols, "품질", "내역")
    )
    col_action = (
        _pick_col(cols, "상세조치")
        or _pick_col(cols, "수리", "내역")
        or _pick_col(cols, "불량", "개선")
        or _pick_col(cols, "불량", "내역")
    )
    col_parts = _pick_col(cols, "교체", "부품") or _pick_col(cols, "교체부품")
    col_type = _pick_col(cols, "유형")
    col_customer = (
        _pick_col(cols, "구분")
        or _pick_col(cols, "상호명")
        or _pick_col(cols, "여객사")
        or _pick_col(cols, "발주처")
    )
    col_equip = _pick_col(cols, "접수장비") or _pick_col(cols, "충전기")

    if not col_action and not col_symptom:
        return []

    records: list[dict[str, Any]] = []
    rel = path.relative_to(ROOT).as_posix()

    for i, row in df.iterrows():
        def get(c: str | None) -> str:
            if not c or c not in df.columns:
                return ""
            return _cell_str(row.get(c))

        symptom = get(col_symptom)
        action = get(col_action)
        parts = get(col_parts)
        hw = get(col_type)
        customer = get(col_customer)
        equip = get(col_equip)

        if not symptom and not action:
            continue
        seq0 = get(cols[0]) if cols else ""
        if _row_skip(symptom, action, seq0):
            continue

        page = (
            f"[전기차 충전기 AS 사례]\n"
            f"출처: {rel} | 시트: {sheet} | 데이터행: {i}\n"
            f"고객/현장: {customer}\n"
            f"장비: {equip}\n"
            f"증상/접수: {symptom}\n"
            f"조치/수리: {action}\n"
            f"교체 부품: {parts}\n"
            f"유형: {hw}\n"
        )
        codes_src = f"{symptom}\n{action}\n{parts}\n{equip}"
        records.append(
            {
                "page_content": page.strip(),
                "metadata": {
                    "source": rel,
                    "sheet": sheet,
                    "row": _index_row(i),
                    "symptom_norm": normalize_symptom_text(symptom),
                    "error_code_norm": error_code_norm_field(codes_src),
                },
                "symptom_raw": symptom,
                "action_detail": action,
                "parts": parts,
                "customer": customer,
                "equip": equip,
                "hw": hw
            }
        )
    return records


def iter_all_records() -> list[dict[str, Any]]:
    # 기본값은 전수 반영(True). 필요 시 환경변수로 기존 제외 정책을 켤 수 있음.
    use_legacy_skip = os.environ.get("INGEST_USE_LEGACY_FILE_SKIP", "").strip().lower() in {
        "1",
        "true",
        "y",
        "yes",
    }
    # 경로에 이 문자열이 포함된 xlsx만 처리 (예: 특정 파일만 재인제스트)
    only_substr = os.environ.get("INGEST_ONLY_SUBSTR", "").strip()
    all_recs: list[dict[str, Any]] = []
    for path in sorted(CS_DIR.rglob("*.xlsx")):
        if only_substr and only_substr not in path.as_posix():
            continue
        if use_legacy_skip and any(s in path.name for s in _SKIP_PATH_SUBSTR):
            continue
        try:
            xl = pd.ExcelFile(path, engine="openpyxl")
        except Exception:
            continue
        other_sheets = [s for s in xl.sheet_names if s != "Sheet1"]
        for sheet in xl.sheet_names:
            if "#자재" in sheet or "자재 번호" in sheet:
                continue
            if sheet == "Sheet1" and len(other_sheets) > 0:
                continue
            try:
                recs = sheet_to_records(path, sheet)
            except Exception:
                continue
            all_recs.extend(recs)
    return all_recs


def ingest_to_db(records: list[dict[str, Any]]) -> None:
    import hashlib
    from storage.db import init_db, get_db_context
    from storage.repositories import (
        TenantRepository,
        SiteRepository,
        ChargerRepository,
        IncidentRepository,
        ActionRepository,
        Action,
        PartUsage
    )

    print("Initializing DB...")
    init_db()

    def make_id(prefix: str, *args: str) -> str:
        s = "_".join(str(a) for a in args)
        return f"{prefix}-{hashlib.md5(s.encode('utf-8')).hexdigest()[:16]}"

    print(f"Ingesting {len(records)} records to DB...")
    tenant_id = "default_tenant"

    with get_db_context() as db:
        tenant_repo = TenantRepository(db)
        if not tenant_repo.get_by_id(tenant_id):
            tenant_repo.create(tenant_id, "Default Tenant", "PRO")

        site_repo = SiteRepository(db)
        charger_repo = ChargerRepository(db)
        incident_repo = IncidentRepository(db)
        action_repo = ActionRepository(db)

        known_sites = {}
        known_chargers = {}

        for r in records:
            customer_name = r.get("customer") or "Unknown Site"
            equip_name = r.get("equip") or ""
            symptom = r.get("symptom_raw") or ""
            action = r.get("action_detail") or ""
            parts = r.get("parts") or ""
            hw = r.get("hw") or ""
            
            metadata = r.get("metadata") or {}
            source_file = metadata.get("source") or ""
            sheet = metadata.get("sheet") or ""
            row_idx = metadata.get("row") or 0
            
            symptom_norm = metadata.get("symptom_norm") or ""
            error_code_norm = metadata.get("error_code_norm") or ""

            # Site
            site_key = (tenant_id, customer_name)
            if site_key not in known_sites:
                site = site_repo.get_by_name(tenant_id, customer_name)
                if not site:
                    site_id = make_id("site", tenant_id, customer_name)
                    site = site_repo.create(site_id, tenant_id, customer_name)
                known_sites[site_key] = site.site_id
            site_id = known_sites[site_key]

            # Charger
            charger_id = None
            if equip_name:
                charger_key = (tenant_id, site_id, equip_name)
                if charger_key not in known_chargers:
                    charger_id_candidate = make_id("charger", tenant_id, site_id, equip_name)
                    charger = charger_repo.get_by_id(charger_id_candidate)
                    if not charger:
                        charger = charger_repo.create(charger_id_candidate, tenant_id, site_id, model_name=equip_name)
                    known_chargers[charger_key] = charger.charger_id
                charger_id = known_chargers[charger_key]

            # Incident
            incident_id = make_id("inc", source_file, sheet, str(row_idx))
            incident = incident_repo.get_by_id(incident_id)
            if not incident:
                incident = incident_repo.create(
                    incident_id=incident_id,
                    tenant_id=tenant_id,
                    site_id=site_id,
                    charger_id=charger_id,
                    occurred_at=None,
                    reported_at=None,
                    symptom_raw=symptom,
                    symptom_norm=symptom_norm,
                    error_code_raw=None,
                    error_code_norm=error_code_norm,
                    severity=hw,
                    source_file=source_file,
                    source_sheet=sheet,
                    source_row=int(row_idx) if isinstance(row_idx, int) else None
                )

            # Action
            if action:
                action_id = make_id("act", source_file, sheet, str(row_idx))
                existing_action = db.query(Action).filter(Action.action_id == action_id).first()
                if not existing_action:
                    action_obj = action_repo.create(
                        action_id=action_id,
                        incident_id=incident_id,
                        action_type="REPAIR",
                        action_detail=action
                    )
                    # If parts are present, create a PartUsage entry
                    if parts:
                        part_usage = PartUsage(
                            part_usage_id=make_id("part", source_file, sheet, str(row_idx), parts),
                            action_id=action_id,
                            part_name=parts,
                            qty=1
                        )
                        db.add(part_usage)


def export_jsonl(path: Path = OUT_JSONL) -> int:
    recs = iter_all_records()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in recs:
            # Remove raw values when writing to jsonl to keep backward compatibility
            jsonl_record = {
                "page_content": r["page_content"],
                "metadata": r["metadata"]
            }
            f.write(json.dumps(jsonl_record, ensure_ascii=False) + "\n")
            
    # Also write to Database
    ingest_to_db(recs)
    return len(recs)


if __name__ == "__main__":
    n = export_jsonl()
    print(f"Exported {n} records -> {OUT_JSONL} and ingested to database.")

