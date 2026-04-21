"""
AS 텍스트용 에러코드 정규화 및 BM25용 토큰화.

설계: docs/rag-improvement-design.md §3.1
"""
from __future__ import annotations

import re
from typing import Iterable

# (pattern, repl) — 증상 텍스트 정규화용 동의어/표기 통합
_SYNONYM_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"비상\s*정지", re.I), "긴급정지"),
    (re.compile(r"긴급\s*정지", re.I), "긴급정지"),
    (re.compile(r"emergency\s*stop", re.I), "긴급정지"),
)

# 에러코드 후보 추출 → 정규 키 (대문자, 구분자 통일)
_EC_NUM = re.compile(r"\bEC\s*[-_]?\s*(\d+)\b", re.I)
_EC_PLAIN = re.compile(r"\bEC(\d{1,4})\b", re.I)
_ERR_KO = re.compile(r"에러\s*코드?\s*[:：]?\s*(\d{1,4})", re.I)
_ERR_KO2 = re.compile(r"에러\s*(\d{1,4})\b", re.I)
_PC_EC = re.compile(r"\bPC\s*(\d{1,3})\s*[-_/]?\s*EC\s*(\d{1,4})\b", re.I)
_PC_EC_COMPACT = re.compile(r"\bPC(\d{1,3})EC(\d{1,4})\b", re.I)


def normalize_symptom_text(text: str) -> str:
    """공백 축소 + 동의어 통합."""
    t = (text or "").strip()
    for pat, rep in _SYNONYM_PATTERNS:
        t = pat.sub(rep, t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_error_code_keys(text: str) -> list[str]:
    """
    문서/질의에서 에러코드 표기를 뽑아 정규 키 리스트로 반환.
    예: EC23, EC 23 → EC23 | pc7 ec75 → PC7_EC75
    """
    if not text:
        return []
    keys: set[str] = set()
    for m in _EC_NUM.finditer(text):
        keys.add(f"EC{m.group(1)}")
    for m in _EC_PLAIN.finditer(text):
        keys.add(f"EC{m.group(1)}")
    for m in _ERR_KO.finditer(text):
        keys.add(f"EC{m.group(1)}")
    for m in _ERR_KO2.finditer(text):
        keys.add(f"EC{m.group(1)}")
    for m in _PC_EC.finditer(text):
        keys.add(f"PC{m.group(1)}_EC{m.group(2)}".upper())
    for m in _PC_EC_COMPACT.finditer(text):
        keys.add(f"PC{m.group(1)}_EC{m.group(2)}".upper())
    return sorted(keys)


def error_code_norm_field(text: str) -> str:
    """메타데이터 저장용 단일 문자열 (| 구분)."""
    keys = extract_error_code_keys(text)
    return "|".join(keys)


def tokenize_for_bm25(text: str) -> list[str]:
    """영숫자 토큰 + 한글 연속 구간."""
    if not text:
        return []
    lowered = text.lower()
    parts = re.findall(r"[a-z0-9_]{2,}|[가-힣]{2,}", lowered)
    return parts if parts else lowered.split()
