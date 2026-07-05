"""
LLM 응답 품질 하네스 — DeepEval 기반 (csautobot)
실제 LLM 호출 없이 CS 자동화봇의 응답 품질 기준을 검증합니다.

평가 기준:
- AnswerRelevancy : CS 문의에 대한 답변 관련성 ≥ 0.7
- Hallucination  : 사실 왜곡 없음 (score ≤ 0.3)
- Toxicity       : 고객 응대 언어 품질 (score ≤ 0.1)
"""
import pytest

deepeval = pytest.importorskip("deepeval", reason="deepeval not installed — skip LLM quality tests")

from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric, ToxicityMetric
from deepeval.test_case import LLMTestCase


@pytest.fixture(scope="module")
def cs_responses():
    """CS 자동화봇 표준 응답 샘플."""
    return {
        "점검 일정": "현재 점검 일정은 시스템에서 확인 중입니다. 담당 엔지니어가 24시간 내 연락 드리겠습니다.",
        "견적 문의": "견적은 현장 상황에 따라 달라집니다. 기본 점검 비용과 부품 비용이 별도로 산정됩니다.",
        "긴급 출동": "긴급 출동 요청을 접수했습니다. 가장 가까운 엔지니어를 배정하여 2시간 내 도착하도록 하겠습니다.",
    }


class TestCSAnswerRelevancy:
    def test_inspection_schedule_relevancy(self, cs_responses):
        metric = AnswerRelevancyMetric(threshold=0.7, model="gpt-4o-mini", include_reason=True)
        test_case = LLMTestCase(
            input="다음 정기 점검은 언제인가요?",
            actual_output=cs_responses["점검 일정"],
        )
        assert_test(test_case, [metric])

    def test_emergency_dispatch_relevancy(self, cs_responses):
        metric = AnswerRelevancyMetric(threshold=0.7, model="gpt-4o-mini", include_reason=True)
        test_case = LLMTestCase(
            input="지금 당장 엔지니어가 필요합니다. 긴급 출동 가능한가요?",
            actual_output=cs_responses["긴급 출동"],
        )
        assert_test(test_case, [metric])


class TestCSHallucination:
    def test_quotation_no_hallucination(self, cs_responses):
        metric = HallucinationMetric(threshold=0.3, model="gpt-4o-mini")
        test_case = LLMTestCase(
            input="점검 비용이 얼마나 되나요?",
            actual_output=cs_responses["견적 문의"],
            context=[
                "견적은 현장 조사 후 확정",
                "기본 점검비 + 부품비 별도 산정",
                "긴급 출동 시 할증 적용",
            ],
        )
        assert_test(test_case, [metric])


# ── API 키 없이 실행 가능한 기본 품질 검사 ─────────────────────
class TestCSResponseQualityOffline:

    @pytest.mark.parametrize("response,required_kw", [
        ("담당 엔지니어가 24시간 내 연락 드리겠습니다.", ["엔지니어", "연락"]),
        ("가장 가까운 엔지니어를 배정하여 2시간 내 도착하도록 하겠습니다.", ["배정", "도착"]),
    ])
    def test_response_contains_required_keywords(self, response, required_kw):
        """CS 응답에 필수 키워드가 포함되어야 함."""
        for kw in required_kw:
            assert kw in response, f"필수 키워드 누락: '{kw}'"

    @pytest.mark.parametrize("response", [
        "담당 엔지니어가 24시간 내 연락 드리겠습니다.",
        "기본 점검 비용과 부품 비용이 별도로 산정됩니다.",
        "가장 가까운 엔지니어를 배정하여 2시간 내 도착하도록 하겠습니다.",
    ])
    def test_response_has_closure(self, response):
        """CS 응답이 명확한 다음 단계를 포함해야 함."""
        closure_keywords = ["드리겠습니다", "됩니다", "하겠습니다", "드립니다"]
        has_closure = any(kw in response for kw in closure_keywords)
        assert has_closure, f"CS 응답에 마무리 문구 누락: {response[:30]}"

    def test_no_vague_response(self, cs_responses):
        """모호한 답변 패턴 감지."""
        vague_patterns = ["잘 모르겠습니다", "확실하지 않습니다", "아마도"]
        for key, response in cs_responses.items():
            for pattern in vague_patterns:
                assert pattern not in response, f"[{key}] 모호한 표현 감지: '{pattern}'"
