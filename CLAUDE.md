# csautobot — AI 에이전트 지시사항 (CLAUDE.md)

> Claude Code, Cursor, Gemini 등 AI 코딩 에이전트가 이 저장소에서 작업할 때 반드시 준수해야 하는 규칙입니다.

---

## 배포 격리 규칙 (CRITICAL — 반드시 준수)

이 서버(211.237.13.172)에는 **csautobot, aiCallCenter, aiCsms** 3개 프로젝트가 동일 서버에서 PM2/Windows Service로 동시 운영됩니다.

### 포트 할당 (변경 금지)

| 프로젝트 | 백엔드 | 프론트엔드 | 프로세스 관리 |
|----------|--------|-----------|-------------|
| **csautobot** | **8000** (uvicorn) | **5000** (Next.js) | PM2 |
| aiCallCenter | 8090 (uvicorn) | 3000 (Next.js) | PM2 |
| aiCsms | Spring Boot (JAR) | Thymeleaf SSR | Windows Service |

### 배포 스크립트 수정 시 절대 금지 사항

1. **`pm2 kill`, `pm2 delete all`, `pm2 stop all` 사용 금지** — 다른 프로젝트 서비스가 전부 죽음
2. **`Stop-Process -Name python` / `Stop-Process -Name node` 사용 금지** — 프로세스명 기반 kill은 다른 프로젝트까지 종료시킴
3. **반드시 PM2 앱 이름을 명시하여 자기 앱만 제어**: `pm2 stop csautobot-backend csautobot-frontend` / `pm2 delete csautobot-backend csautobot-frontend`
4. **ecosystem.config.js의 앱 이름(`csautobot-backend`, `csautobot-frontend`)을 임의로 변경 금지**
5. **다른 프로젝트(aiCallCenter, aiCsms)의 PM2 앱을 stop/delete/restart 하는 코드 추가 금지**

### 위반 사례 (과거 장애 원인)

```powershell
# ❌ 절대 금지 — 서버 전체 서비스 다운
pm2 kill
pm2 delete all
Stop-Process -Name python
Stop-Process -Name node

# ✅ 올바른 방법 — 자기 앱만 제어
pm2 delete csautobot-backend -s
pm2 delete csautobot-frontend -s
```

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3.11+, FastAPI, uvicorn |
| Frontend | Next.js, React, Tailwind |
| LLM | LangChain (OpenAI, Anthropic, Google) |
| Vector DB | ChromaDB |
| 프로세스 관리 | PM2 (ecosystem.config.js) |
| 배포 | GitHub Actions → SSH/SCP → PM2 |

---

## 절대 금지

- `.env`, `*.db`, API 키를 Git에 커밋
- `deploy.yml`, `deploy-remote.ps1`을 사용자 확인 없이 수정
- 범위 밖 대규모 리팩토링
