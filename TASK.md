# CSAutobot Sprint — Harness + GTM + Billing

> AGENTS.md §4-5 자율 루프 상태 저장소. 세션 재개 시 이 파일부터 읽습니다.

## 현재 스프린트 (2026-07-04) — Sprint 8

| ID | 태스크 | 상태 |
|----|--------|:----:|
| J1 | leads 알림 테스트 발송 (dry-run) API + UI | done |
| J2 | billing 사용량 임계치 알림 (80%/90%) | done |
| J3 | Admin billing 임계치 경고 UI | done |

## 이전 스프린트 (완료)

| ID | 태스크 | 상태 |
|----|--------|:----:|
| I1~I3 | channel status + audit pagination | done |
| H1~H3 | notify retry + plan audit log | done |

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

1. billing 임계치 Slack/이메일 알림 발송
2. leads 채널별 최근 성공/실패 통계
3. `ERROR.md` 없음 유지

## Blocked

_(없음)_
