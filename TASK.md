# CSAutobot Sprint — Harness + GTM + Billing

> AGENTS.md §4-5 자율 루프 상태 저장소. 세션 재개 시 이 파일부터 읽습니다.

## 현재 스프린트 (2026-07-04) — Sprint 6

| ID | 태스크 | 상태 |
|----|--------|:----:|
| H1 | leads 알림 수동 재전송 API + Admin UI | done |
| H2 | billing 플랜 변경 감사 로그 (audit_log) | done |
| H3 | Admin billing 감사 로그 UI | done |

## 이전 스프린트 (완료)

| ID | 태스크 | 상태 |
|----|--------|:----:|
| G1~G3 | 플랜 변경 + notify retry/dead-letter | done |
| F1~F3 | billing tenant 선택 + Slack 알림 | done |

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

1. leads 알림 채널별 설정 상태 표시
2. billing 감사 로그 필터/페이지네이션
3. `ERROR.md` 없음 유지

## Blocked

_(없음)_
