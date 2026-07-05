"""FAQ exact-match shortcuts — skip LLM when input matches a known pattern."""

from __future__ import annotations

import re

KEYWORD_RULES: dict[str, str] = {
    "충전기 안됨": (
        "1) 메인 차단기·누전차단기 상태 확인\n"
        "2) 충전기 전면 표시등/에러코드 확인\n"
        "3) RFID·QR 결제 단말 재부팅\n"
        "4) 통신(LTE/이더넷) 연결 상태 점검\n"
        "5) 지속 시 제조사 A/S 또는 현장 엔지니어 출동"
    ),
    "충전 안됨": (
        "1) 메인 차단기·누전차단기 상태 확인\n"
        "2) 충전기 전면 표시등/에러코드 확인\n"
        "3) RFID·QR 결제 단말 재부팅\n"
        "4) 통신(LTE/이더넷) 연결 상태 점검\n"
        "5) 지속 시 제조사 A/S 또는 현장 엔지니어 출동"
    ),
    "카드 인식 안됨": (
        "1) RFID 리더기 표면 청소\n"
        "2) 다른 카드/앱으로 결제 시도\n"
        "3) 충전기 재부팅(전원 OFF 30초 후 ON)\n"
        "4) 결제 단말 펌웨어·통신 상태 확인\n"
        "5) 리더기 교체 검토"
    ),
    "rfid 인식 안됨": (
        "1) RFID 리더기 표면 청소\n"
        "2) 다른 카드/앱으로 결제 시도\n"
        "3) 충전기 재부팅(전원 OFF 30초 후 ON)\n"
        "4) 결제 단말 펌웨어·통신 상태 확인\n"
        "5) 리더기 교체 검토"
    ),
    "에러코드 e001": (
        "E001: 통신 단절 오류\n"
        "1) LTE/이더넷 케이블·안테나 확인\n"
        "2) CSMS 서버 연결 상태 확인\n"
        "3) 통신 모듈(PLC/LTE) 재부팅\n"
        "4) 지속 시 통신 모듈 교체 검토"
    ),
    "출장비 얼마": (
        "기본 출장 교통비: 100,000원\n"
        "기본 작업 공임비: 70,000원\n"
        "완속 단순 보드 교체 등 일부 작업은 출장비 면제 가능\n"
        "부품비·VAT(10%)는 별도 산정"
    ),
    "견적 문의": (
        "증상·충전기 구분(완속/급속)을 알려주시면 AI 견적 초안을 생성합니다.\n"
        "기본 출장비 100,000원 + 공임 70,000원 + 부품비 + VAT(10%)"
    ),
}


def normalize_input(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip().lower())
    return cleaned


def try_shortcut(user_input: str) -> str | None:
    """Return canned FAQ answer on exact normalized match, else None."""
    key = normalize_input(user_input)
    if not key:
        return None
    return KEYWORD_RULES.get(key)
