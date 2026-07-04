# CSAutobot Sprint — Harness + GTM + Billing

> AGENTS.md §4-5 자율 루프 상태 저장소. 세션 재개 시 이 파일부터 읽습니다.

## 현재 스프린트 (2026-07-04) — Sprint 9

| ID | 태스크 | 상태 |
|----|--------|:----:|
| K1 | billing 임계치 Slack/이메일 발송 + dedupe | done |
| K2 | POST /billing/admin/usage-alerts/notify | done |
| K3 | leads 채널별 성공/실패 통계 API + UI | done |

## 이전 스프린트 (완료)

| ID | 태스크 | 상태 |
|----|--------|:----:|
| J1~J3 | dry-run test + usage threshold UI | done |
| I1~I3 | channel status + audit pagination | done |

## Done 기준 (AGENTS.md §2)

- [ ] `pytest tests/` pass + `--cov-fail-under=60`
- [ ] `cd frontend && npm run build` pass
- [ ] CI Harness Gate pass (PR push 후)
- [ ] 프로덕션 배포

## 환경 변수 (알림)

| 변수 | 용도 |
|------|------|
| `BILLING_ALERT_SLACK_WEBHOOK_URL` | Billing 임계치 Slack (미설정 시 `LEADS_SLACK_WEBHOOK_URL`) |
| `BILLING_ALERT_EMAIL` | Billing 임계치 이메일 (미설정 시 `LEADS_NOTIFY_EMAIL`) |
| `LEADS_*` / `SMTP_*` | leads 알림 (기존) |

## 다음 스프린트 (대기)

1. billing 임계치 자동 발송 (record_usage hook)
2. leads 통계 기간 선택 UI
3. `ERROR.md` 없음 유지

## Blocked

_(없음)_
