"""
점검일지 AI 초안 생성 서비스.

- 체크리스트(정상/주의/이상/N-A) + 엔지니어 메모를 입력으로 받음
- LLM(gpt-4o-mini)에 구조화 출력을 요청해 JSON 스키마로 반환
- 프롬프트는 csautobot/prompts/inspection_summary.yaml
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML 은 streamlit 의존성으로 들어옴
    yaml = None  # type: ignore[assignment]


HERE = Path(__file__).resolve().parent
PROMPT_PATH = HERE.parent / "prompts" / "inspection_summary.yaml"

DEFAULT_MODEL = "gpt-4o-mini"


class InspectionDraft(BaseModel):
    """AI 초안 구조화 스키마."""

    overall_risk: str = Field(description="전반 위험도: low / mid / high")
    key_findings: list[str] = Field(
        default_factory=list, description="체크리스트·메모에서 도출한 핵심 관찰 사항 (최대 5개)"
    )
    recommended_actions: list[str] = Field(
        default_factory=list, description="권장 조치 순서 (최대 5개)"
    )
    parts_to_check: list[str] = Field(
        default_factory=list, description="점검·교체 필요 가능 부품 (최대 5개)"
    )
    follow_up_items: list[str] = Field(
        default_factory=list, description="후속 점검/모니터링 항목 (최대 5개)"
    )
    inspector_note: str = Field(description="엔지니어 확인용 한두 줄 요약 메모")
    safety_notice: str = Field(
        description="안전·책임 고지. 최종 판단은 담당 엔지니어에게 있음을 명시"
    )


def _load_system_prompt() -> str:
    """YAML 에서 system 프롬프트 로드. PyYAML 없으면 기본 문자열."""
    if yaml and PROMPT_PATH.is_file():
        try:
            data = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("system"):
                return str(data["system"])
        except yaml.YAMLError:
            pass
    return (
        "당신은 전기차 충전소 현장 점검 AI 어시스턴트입니다. "
        "체크리스트와 메모의 '이상/주의' 항목을 근거로만 위험도와 권장 조치를 제시하세요. "
        "응답은 지정된 JSON 스키마를 따르며 모든 필드는 한국어입니다."
    )


def _format_checklist(checklist: list[dict[str, Any]]) -> str:
    """LLM 입력용으로 체크리스트를 사람이 읽기 쉬운 불릿으로 변환."""
    if not checklist:
        return "(체크리스트 입력 없음)"
    lines: list[str] = []
    for i, item in enumerate(checklist, 1):
        name = item.get("item") or "(항목 미상)"
        status = item.get("status") or "미표기"
        note = (item.get("note") or "").strip()
        base = f"{i}. [{status}] {name}"
        if note:
            base += f" — 메모: {note}"
        lines.append(base)
    return "\n".join(lines)


def _format_similar_cases(similar_cases: list[dict[str, Any]] | None) -> str:
    if not similar_cases:
        return "(유사 AS 사례 없음)"
    lines = []
    for i, c in enumerate(similar_cases[:3], 1):
        title = c.get("title") or c.get("symptom") or "(제목 미상)"
        action = c.get("action") or ""
        lines.append(f"- #{i} {title}" + (f" · 조치요약: {action}" if action else ""))
    return "\n".join(lines)


def generate_inspection_draft(
    *,
    site_name: str | None,
    charger_id: str | None,
    manufacturer: str | None,
    model_name: str | None,
    inspection_type: str,
    inspection_cycle: str | None,
    checklist: list[dict[str, Any]],
    memo_text: str | None,
    photo_count: int = 0,
    similar_cases: list[dict[str, Any]] | None = None,
    model_name_llm: str = DEFAULT_MODEL,
) -> tuple[InspectionDraft, str]:
    """
    LLM 호출 없이도 임포트 가능하도록 OpenAIEmbeddings 등은 지연 로딩.

    반환: (초안 객체, 사용한 LLM 모델명)
    """
    system_prompt = _load_system_prompt()

    charger_block = (
        f"- 충전소: {site_name or '(미입력)'}\n"
        f"- 충전기ID: {charger_id or '(미입력)'}\n"
        f"- 제조사/모델: {manufacturer or '-'} / {model_name or '-'}\n"
        f"- 점검 유형: {inspection_type}\n"
        f"- 점검 주기: {inspection_cycle or '-'}\n"
        f"- 첨부 사진 수: {photo_count}"
    )
    checklist_block = _format_checklist(checklist)
    memo_block = (memo_text or "").strip() or "(엔지니어 메모 없음)"
    similar_block = _format_similar_cases(similar_cases)

    human_template = (
        "[설비 정보]\n{charger_block}\n\n"
        "[체크리스트 결과]\n{checklist_block}\n\n"
        "[엔지니어 메모]\n{memo_block}\n\n"
        "[참고: 과거 유사 AS 사례 (선택)]\n{similar_block}\n\n"
        "---\n"
        "위 정보를 바탕으로 점검일지 AI 초안을 JSON 스키마로 작성하세요. "
        "근거 없는 추측은 금지하며, 체크리스트에 표시된 '주의/이상' 항목을 최우선으로 반영하세요."
    )

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_template)]
    )
    llm = ChatOpenAI(model=model_name_llm, temperature=0).with_structured_output(InspectionDraft)
    chain = prompt | llm
    draft: InspectionDraft = chain.invoke(
        {
            "charger_block": charger_block,
            "checklist_block": checklist_block,
            "memo_block": memo_block,
            "similar_block": similar_block,
        }
    )
    return draft, model_name_llm


# ---------- 점검 주기별 체크리스트 프리셋 ----------
#
# 주기가 길수록 점검 항목이 누적·심화됩니다 (일간 ⊂ 주간 ⊂ 월간 ⊂ 분기 ⊂ 반기 ⊂ 연간 형태).
# 실제 운영에선 제조사 매뉴얼/사업자 표준을 팀·고객과 합의해 확정해야 하며,
# 현재 값은 환경부/무공해차 통합누리집·제조사 매뉴얼 일반 관행에 기반한 **초안**입니다.

CHECKLIST_CYCLES: list[str] = ["일간", "주간", "월간", "분기", "반기", "연간", "수시"]

CHECKLIST_STATUS_OPTIONS: list[str] = ["정상", "주의", "이상", "N/A"]


CHECKLIST_PRESETS: dict[str, list[str]] = {
    "일간": [
        "외관 파손/낙서/이물질 여부",
        "케이블·커넥터 외관(피복 손상, 변색)",
        "디스플레이/터치 정상 동작",
        "결제 단말(RFID/QR/카드) 반응 확인",
        "현장 청결 상태(바닥 청소, 쓰레기)",
        "경고등/표시등 이상 여부",
    ],
    "주간": [
        "외관 파손/낙서/이물질 여부",
        "케이블·커넥터 외관(피복 손상, 변색)",
        "디스플레이/터치 정상 동작",
        "결제 단말(RFID/QR/카드) 반응 확인",
        "비상정지 스위치 외관·작동 확인",
        "도어 잠금장치 정상 동작",
        "시험 충전(저용량) 정상 완료 여부",
        "에러 코드 이력(최근 7일) 확인",
        "주변 환경(조도, 배수, 침수 흔적)",
    ],
    "월간": [
        "외함/외관 상태 (파손, 이물질, 낙서)",
        "충전 커넥터/건 (피복, 고정, LED)",
        "디스플레이/터치 정상 동작",
        "RFID/QR 결제 인증 정상",
        "접지/절연 상태 (가능 시 계측값)",
        "통신 상태 (LTE/이더넷 신호)",
        "최근 에러 코드 이력 확인",
        "내부 청결/팬/필터 상태",
        "경고 문구·라벨·QR 스티커 상태",
        "설치 환경 (침수 흔적, 조도, 접근성)",
    ],
    "분기": [
        "외함/외관 상태 및 고정 볼트 토크 확인",
        "충전 커넥터·건 체결부 마모도 측정",
        "케이블 권취/꼬임/피복 상태",
        "접지저항 계측값 기록 (기준치 이내)",
        "절연저항 계측값 기록",
        "통신 신호 품질(RSSI, 패킷 드롭) 로깅",
        "누적 에러 코드 Top-5 분석",
        "팬·필터 청소 및 방열 상태",
        "DC 출력 파형/전압 스팟 측정",
        "펌웨어 버전 및 최신화 필요 여부",
        "주변 CCTV/조명/표지 상태",
    ],
    "반기": [
        "외함/외관 상태 및 실링(방수) 점검",
        "충전 커넥터·건 완전 분해 청소 및 도유",
        "케이블 전 구간 피복·굴곡·고정 점검",
        "접지저항 정식 계측(교정된 계측기)",
        "절연저항 정식 계측 및 누설전류 확인",
        "주요 회로 보드(PCB) 육안·열화상 점검",
        "콘덴서/전해 부품 외관(부풀음) 확인",
        "SMPS/파워모듈 출력 전압 계측",
        "통신 모듈 로그 추출 및 분석",
        "펌웨어 업데이트 및 설정 백업",
        "비상정지·누설차단기 동작 시험",
        "사고/고장 이력 누적 리뷰 및 예방조치안",
    ],
    "연간": [
        "종합 외관·구조 점검 및 사진 대장 갱신",
        "전 계통 절연·접지 정식 계측 (성적서 발행)",
        "충전 커넥터·건 전면 교체 검토",
        "케이블 전수 육안 + 샘플 저항 측정",
        "주요 PCB 클리닝 및 고정부 재체결",
        "배터리/UPS(있는 경우) 용량 시험",
        "SMPS/파워모듈 풀 점검 및 교정",
        "통신 보안(TLS, 인증서 만료) 점검",
        "펌웨어/OS 연간 패치 현황 정리",
        "법정 안전점검 준수 및 보고서 작성",
        "연간 고장/재방문 통계 분석 및 개선안",
        "소방/누전/경보 시스템 연계 시험",
        "운영자 교육 및 매뉴얼 최신화 확인",
    ],
    "수시": [
        "신고/민원 접수 항목 현장 재현 확인",
        "관련 에러 코드/로그 추출",
        "직전 정기점검 이후 변경 이력 확인",
        "안전 차단(전원/통신) 후 조치",
        "임시 복구 vs 부품 교체 판단 근거 기록",
    ],
}


# 과거 이름 유지 (월간 프리셋을 기본으로 간주)
DEFAULT_CHECKLIST_ITEMS: list[str] = CHECKLIST_PRESETS["월간"]


def preset_checklist(cycle: str) -> list[dict[str, Any]]:
    """주기명 → 프리셋 체크리스트(list of dict)."""
    items = CHECKLIST_PRESETS.get(cycle) or CHECKLIST_PRESETS["월간"]
    return [{"item": name, "status": "정상", "note": ""} for name in items]


def default_checklist() -> list[dict[str, Any]]:
    """UI 첫 렌더용 기본 체크리스트 (월간)."""
    return preset_checklist("월간")
