# csautobot — GitHub Copilot Instructions

## 배포 격리 규칙 (CRITICAL)

이 서버(211.237.13.172)에는 csautobot, aiCallCenter, aiCsms 3개 프로젝트가 동일 서버에서 PM2/Windows Service로 동시 운영됩니다.

### 절대 금지

1. `pm2 kill`, `pm2 delete all`, `pm2 stop all` — 다른 프로젝트 서비스가 전부 죽음
2. `Stop-Process -Name python` / `Stop-Process -Name node` — 다른 프로젝트 프로세스까지 종료
3. 반드시 PM2 앱 이름 명시: `pm2 stop csautobot-backend csautobot-frontend`
4. 포트 변경 금지: 백엔드 8000, 프론트엔드 5000
5. ecosystem.config.js 앱 이름 변경 금지

```powershell
# ❌ 금지
pm2 kill
pm2 delete all
Stop-Process -Name python

# ✅ 올바름
pm2 delete csautobot-backend -s
pm2 delete csautobot-frontend -s
```

## 기타 규칙

상세 규칙은 `CLAUDE.md` 참조.
