# INFRA_FACTS.md — 공유 서버 인프라 사실 (Single Source of Truth)
# 이 파일은 ai-harness 레포에서 자동 동기화됩니다. 직접 수정하지 마세요.
# 정정이 필요하면 team-softgrid/ai-harness의 templates/INFRA_FACTS.md.template을 고치세요.
# (csautobot 레포 기준 동기화됨 — 하네스 v1.3.0)

---

## 1. 공유 서버
- **IP**: 211.237.13.172 (단일 서버, 4개 프로젝트가 함께 운영됨)
- **동시 운영 프로젝트**: aiCsms, aiCallCenter, csautobot, ocppautomation

## 2. 서비스별 실제 포트 (검증됨 — 2026-07-06 직접 확인)
| 프로젝트 | 외부 접속 URL | 내부 포트 | 프로세스 관리 |
|---|---|---|---|
| **aiCsms** | `https://csms.evflow.co.kr` 또는 `http://211.237.13.172:28080` | **28080** (내부·외부 동일, `server.port=28080`. **8080 아님 — 8080은 존재하지 않음**) | Windows Service (`aiCsmsService`) |
| **aiCallCenter** | `https://help.evflow.co.kr` | 3000 (frontend), 8090 (backend) | PM2 (`aicallcenter-backend`, `aicallcenter-frontend`) |
| **csautobot** | `https://cs.evflow.co.kr` | 5000 (frontend), 8000 (backend) | PM2 (`csautobot-backend`, `csautobot-frontend`) |
| **ocppautomation** | `https://ocpp.evflow.co.kr` | 3100 | PM2 (`ocppautomation-frontend`) |

> ⚠️ aiCallCenter/csautobot/ocppautomation은 **외부 방화벽 포트가 없음** — IP:3000, IP:5000, IP:3100 등 직접 접속은 타임아웃됨. 반드시 HTTPS 도메인으로 접속.

### 기타 (같은 서버, 4개 프로젝트 외)
| 서비스 | 포트 | 비고 |
|---|---|---|
| `ocppRestService` | 10005 | OCPP REST API (Java, 별도 레포) |
| `ocppWsService` | 9091 | OCPP WebSocket (Java, 별도 레포) |
| Caddy (리버스 프록시, 443) | — | PM2 프로세스명 `aicallcenter-caddy` (aiCallCenter 소유로 등록되어 있으나 4개 서비스 공유 인프라) |

## 3. Caddy 리버스 프록시 (공유 인프라 — 단일 정본)
- **Git 정본**: `aiCsms` 레포의 `infra/caddy/Caddyfile`
- **서버 정본**: `C:\caddy\Caddyfile` (각 프로젝트 deploy 경로 밖 — 절대 각 레포 deploy에 포함 금지)
- **자동 복구**: `aiCsms`의 `.github/workflows/caddy-guardian.yml` (2시간마다 + `infra/caddy/**` push 시 + 수동)
- 502/SSL 오류 시: aiCsms 레포 → Actions → **Caddy Guardian** → Run workflow

## 4. 절대 금지 명령 (전체 서비스 다운 유발)
```powershell
pm2 kill
pm2 delete all
Stop-Process -Name python
Stop-Process -Name node
taskkill /F /IM java.exe   # ocppRestService/ocppWsService/aiCsms 전부 죽음 — 실행했다면 셋 다 재시작 필요
```
각 프로젝트는 **자기 프로세스만** 재시작할 것 (예: aiCsms는 `Restart-Service aiCsmsService`만 사용, PM2 전체 재시작 금지).

## 5. 배포 워크플로 필수 규칙
**모든 `deploy.yml`은 반드시 `concurrency` 락을 포함해야 함**:
```yaml
concurrency:
  group: deploy-csautobot
  cancel-in-progress: true
```
- **Why**: 2026-07-05~06, aiCsms와 aiCallCenter가 동시 에이전트 세션에서 각자 짧은 간격으로 연속 push → concurrency 락 부재로 배포가 겹쳐 실행 → JAR/프로세스 파일 핸들 경합 + SSH 세션 누적(zombie sshd, CPU 과점유)으로 서버 전체 불안정 발생. 두 레포가 독립적으로 같은 사고를 겪고 각자 수정함 (근본 원인이 레포마다 따로 관리되어 전파 안 됨).
- 락이 없는 배포 워크플로를 새로 만들거나 발견하면 즉시 추가할 것.

## 6. 이 문서의 목적
개별 레포에서 에이전트가 작업할 때 "다른 프로젝트/공유 서버의 실제 상태"를 몰라서 반복적으로 잘못된 가정(예: 포트 번호, 프로세스 이름)을 하는 것을 막기 위함. 사실이 바뀌면 **이 템플릿(ai-harness)에서만 수정** — 각 레포 사본은 매주 월요일 자동 동기화됨.
