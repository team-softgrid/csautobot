# AS AI 문서 목차

> **문서 버전**: v2.2  
> **최종 수정일**: 2026-06-26  

> ⚠️ **보안 안내**: 이 폴더에는 사업계획서, 견적표, 내부 전략 등 **대외비 문서**가 포함되어 있습니다.  
> 공개 저장소에 포함하지 마시고, 별도의 Private 레포 또는 독립 프로젝트로 분리를 권장합니다.

---

## 핵심 문서
- `as-ai-business-plan.md`: **사업계획서** *(투자자·경영진 대상, 가격 티어·TAM/SAM/SOM·유닛이코노믹스·3년 재무추정 포함 — v1.1)*
- `as-ai-master-plan.md`: 전체 전략/로드맵 통합본 *(시장규모, 경쟁분석, 자금계획 포함)*
- `as-ai-proposal.md`: 고객 제출용 제안서 *(경쟁비교, 가격, ROI 시뮬레이션 포함)*

## 실행/운영 문서
- `as-ai-starting-member-summary.md`: 스타팅 멤버 실행 요약 *(팀 프로필, 채용 로드맵, 자금현황 포함)*
- `as-ai-internal-version.md`: 내부 실행안 *(예산계획, 데이터 정책, 리스크관리, Plan B 포함)*
- `as-ai-customer-version.md`: 고객용 요약 버전 *(ROI 예시, 가격 티어, 경쟁비교 포함)*

## 발표/영업 자료
- `as-ai-ppt-and-quotation-templates.md`: PPT 12장 구성안 + 견적표 템플릿 *(가격 범위, 파일럿 견적 포함)*
- `as-ai-5min-speech.md`: 대표 발표용 5분 스크립트 *(시장규모, 경쟁포지셔닝, 자금계획 포함)*

## RAG 기술 문서
- `rag-implementation-current.md`: 현재 RAG 구현 구조/동작/한계 *(PoC↔프로덕션 Gap 분석 포함)*
- `rag-improvement-design.md`: 정확도 개선 5개 축 설계 + 하이브리드/로컬 LLM 전환안
- `web-migration-local-llm-plan.md`: 웹 서비스 전환 상세 계획 *(인프라 비용 시뮬레이션 포함)*

## 권장 활용 순서

### 투자 피칭 준비 시
1. `as-ai-business-plan.md`로 사업 전체 구조 파악 (시장→솔루션→경쟁→재무)
2. `as-ai-5min-speech.md`로 발표 연습
3. `as-ai-starting-member-summary.md`로 팀/실행력 보완

### 고객 미팅 준비 시
1. `as-ai-master-plan.md`로 전체 방향 정렬
2. `as-ai-customer-version.md` + PPT 구성안으로 발표 자료 제작
3. 계약 협의: 견적표 템플릿 기반으로 상업 조건 구체화

### 내부 실행 시
1. `as-ai-starting-member-summary.md`로 팀 실행 기준 맞춤
2. `as-ai-internal-version.md`로 예산/리스크/게이트 운영
3. 기술 개발: RAG 기술 문서 3개 순서대로 참조

---

## 변경 이력
| 버전 | 날짜 | 주요 변경 |
|:----:|------|----------|
| v1.0 | 2026-04 (초판) | 전체 문서 초안 작성 |
| v2.0 | 2026-04-14 | 투자자 리뷰 반영: 시장규모, 경쟁분석, 유닛이코노믹스, 팀구성, 데이터전략, 자금계획, 인프라비용, 문서버전관리 추가 |
| v2.1 | 2026-06-26 | `as-ai-business-plan.md` v1.0 추가 (코드베이스 기반 사업계획 초안) |
| v2.2 | 2026-06-26 | `as-ai-business-plan.md` v1.1 — 가격·재무 추정 보강 |
