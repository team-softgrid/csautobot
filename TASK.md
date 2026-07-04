# CSAutobot Sprint — Harness + GTM + Billing

> AGENTS.md §4-5 자율 루프 상태 저장소. 세션 재개 시 이 파일부터 읽습니다.

## 현재 스프린트 (2026-07-04)

| ID | 태스크 | 상태 |
|----|--------|:----:|
| E1 | 프론트 search/inspection/quotation → `tenant_id` 전달 | done |
| E2 | `readApiError` 429 한도 메시지 | done |
| E3 | `lead_notifier` — SMTP + CRM webhook | done |

## 이전 스프린트 (완료)

| ID | 태스크 | 상태 |
|----|--------|:----:|
| D1~D5 | usage metering + Admin leads/billing | done |
| A1~C2 | Harness + leads + billing v1 | done |

## Done 기준 (AGENTS.md §2)

- [x] `pytest tests/` pass + `--cov-fail-under=60`
- [x] `cd frontend && npm run build` pass
- [ ] CI Harness Gate pass (PR push 후)
- [ ] 프로덕션 배포

## 환경 변수 (leads 알림, 선택)

| 변수 | 용도 |
|------|------|
| `LEADS_NOTIFY_EMAIL` | 알림 수신 이메일 |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | SMTP 발송 |
| `LEADS_WEBHOOK_URL` | CRM webhook (JSON POST) |
| `NEXT_PUBLIC_TENANT_ID` | 프론트 기본 tenant (미설정 시 `default_tenant`) |

## 다음 스프린트 (대기)

1. Admin billing — tenant 선택 UI
2. leads Slack 알림
3. `ERROR.md` 없음 유지

## Blocked

_(없음)_
