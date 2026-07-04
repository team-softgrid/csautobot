# CSAutobot Sprint — Harness + GTM + Billing

> AGENTS.md §4-5 자율 루프 상태 저장소. 세션 재개 시 이 파일부터 읽습니다.

## 현재 스프린트 (2026-07-04) — Sprint 5

| ID | 태스크 | 상태 |
|----|--------|:----:|
| G1 | Admin billing 플랜 변경 UI + PATCH API | done |
| G2 | leads 알림 재시도 (3회) | done |
| G3 | dead-letter 로그 + Admin UI | done |

## 이전 스프린트 (완료)

| ID | 태스크 | 상태 |
|----|--------|:----:|
| F1~F3 | billing tenant 선택 + Slack 알림 | done |
| E1~E3 | tenant_id + lead_notifier | done |
| D1~D5 | usage metering + Admin UI | done |

## Done 기준 (AGENTS.md §2)

- [ ] `pytest tests/` pass + `--cov-fail-under=60`
- [ ] `cd frontend && npm run build` pass
- [ ] CI Harness Gate pass (PR push 후)
- [ ] 프로덕션 배포

## 환경 변수 (leads 알림, 선택)

| 변수 | 용도 |
|------|------|
| `LEADS_NOTIFY_EMAIL` | 알림 수신 이메일 |
| `SMTP_*` | SMTP 발송 |
| `LEADS_WEBHOOK_URL` | CRM webhook (JSON POST) |
| `LEADS_SLACK_WEBHOOK_URL` | Slack Incoming Webhook |
| `NEXT_PUBLIC_TENANT_ID` | 프론트 기본 tenant |

## 다음 스프린트 (대기)

1. leads 알림 수동 재전송 UI
2. billing 플랜 변경 감사 로그
3. `ERROR.md` 없음 유지

## Blocked

_(없음)_
