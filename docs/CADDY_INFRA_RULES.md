# Caddy / HTTPS 공유 인프라 규칙

> **cs.evflow.co.kr (포트 5000)은 Caddy가 HTTPS로 프록시합니다.**
> Caddy 설정은 이 repo가 아닌 **aiCsms**에서 중앙 관리합니다.

## 절대 금지

- repo 또는 `deploy.yml` / `deploy-remote.ps1`에 **`Caddyfile` 추가·SCP·배포**
- `C:\caddy\` 경로 수정
- `pm2 kill`, `pm2 delete all`, `Stop-Process -Name node` (csautobot-backend/frontend만 제어)

## 장애 시 (502 / SSL 오류)

1. GitHub → **team-softgrid/aiCsms** → Actions → **Caddy Guardian** → Run workflow
2. 백엔드 확인: `pm2 status` → `csautobot-backend`, `csautobot-frontend` online 여부
3. 로컬 포트: `http://localhost:5000` (frontend), `http://localhost:8000` (backend)

## 정본 문서

https://github.com/team-softgrid/aiCsms/blob/develop/docs/CADDY_INFRA_RULES.md
