# CSAutobot Sprint — Harness + GTM + Billing

> AGENTS.md §4-5 자율 루프 상태 저장소. 세션 재개 시 이 파일부터 읽습니다.

## 현재 스프린트 (2026-07-04)

| ID | 태스크 | 상태 |
|----|--------|:----:|
| D1 | 점검·견적 AI draft → usage_meter 기록 | done |
| D2 | `GET/PATCH /api/v1/leads` Admin API | done |
| D3 | `GET /api/v1/billing/admin/summary` | done |
| D4 | Admin UI: leads / billing 페이지 | done |
| D5 | `frontend/src/lib/backend.ts` 프록시 유틸 | done |

## 이전 스프린트 (완료)

| ID | 태스크 | 상태 |
|----|--------|:----:|
| A1 | `GET /health` 엔드포인트 | done |
| A2 | `test_harness.py` ↔ 실제 API 동기화 | done |
| B1 | `POST /api/v1/leads` 도입 상담 API | done |
| B2 | 랜딩 Contact 폼 → API 연동 | done |
| C1 | `billing_metering.py` + usage 집계 API | done |
| C2 | 검색 API 쿼터 체크·기록 | done |

## Done 기준 (AGENTS.md §2)

- [x] `GET /health` → 200
- [x] `pytest tests/` pass + `--cov-fail-under=60`
- [x] `cd frontend && npm run build` pass
- [x] CI Harness Gate pass (main)
- [x] 프로덕션 배포 완료
- [ ] Admin leads/billing 배포 후 검증

## 다음 스프린트 (대기)

1. 점검·견적 프론트에 tenant_id 전달
2. leads 이메일 알림 / CRM 연동
3. `ERROR.md` 없음 유지

## Blocked

_(없음)_
