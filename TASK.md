# CSAutobot Sprint — Harness + GTM + Billing

> AGENTS.md §4-5 자율 루프 상태 저장소. 세션 재개 시 이 파일부터 읽습니다.

## 현재 스프린트 (2026-07-04)

| ID | 태스크 | 상태 |
|----|--------|:----:|
| A1 | `GET /health` 엔드포인트 | done |
| A2 | `test_harness.py` ↔ 실제 API 동기화 | done |
| A3 | `AGENTS.md` 문서 정합 | done |
| B1 | `POST /api/v1/leads` 도입 상담 API | done |
| B2 | 랜딩 Contact 폼 → API 연동 | done |
| C1 | `billing_metering.py` + usage 집계 API | done |
| C2 | 검색 API 쿼터 체크·기록 | done |

## Done 기준 (AGENTS.md §2)

- [x] `GET /health` → 200
- [x] `pytest tests/` 22 passed (로컬)
- [x] `cd frontend && npm run build` pass
- [ ] `pytest --cov-fail-under=60` CI 확인
- [ ] `.env`, `*.db` Git 미포함 (배포 전 확인)
- [ ] `gh run watch` CI pass (push 후)

## 다음 스프린트 (대기)

1. 검색·점검·견적 전 API에 usage_meter 기록 확대
2. Admin UI: leads 목록 / billing usage 조회
3. `ERROR.md` 없음 유지

## Blocked

_(없음)_
