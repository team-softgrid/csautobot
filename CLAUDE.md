# CLAUDE.md — csautobot
# 모든 공통 규칙은 AGENTS.md에 있습니다. 반드시 먼저 읽으세요.
@AGENTS.md

---
## Claude Code 전용 추가 규칙

### 응답 언어
- **모든 응답은 한국어로 작성** (코드/커밋 메시지 등은 기존 관례 유지, 대화 응답만 해당)

### ⚠️ 정상 동작 코드 무단 수정 금지 — AGENTS.md §7로 이동 (2026-07-14)
- 이 규칙은 Claude Code뿐 아니라 이 레포를 다루는 모든 AI 에이전트에 적용되므로, 에이전트 무관
  공통 규칙 파일인 `AGENTS.md`의 PROJECT OVERRIDE 섹션(§7)에 있습니다. **반드시 거기를 읽으세요.**

### 세션 관리
- 작업 재개: `claude --continue`
- 컨텍스트 초과 시 TASK.md를 상태 저장소로 활용

### 자율 실행 시작
```bash
claude "AGENTS.md를 읽고 TASK.md의 현재 태스크부터 끝까지 진행해. 질문 없이."
claude --continue "ERROR.md를 읽고 blocked 태스크를 재시도해."
```

### 절대 금지 명령
```
pm2 kill / pm2 delete all (→ AGENTS.md § 4-2 참조)
Stop-Process -Name python / Stop-Process -Name node
```

### Windows 서버 배포 체크리스트
- [ ] `PM2_HOME=C:\Users\Administrator\.pm2` 환경변수 설정 확인
- [ ] `pm2 startOrReload` 후 `pm2 save` 실행 (SSH disconnect 전)
- [ ] PowerShell 5.x 문법만 사용 (`?.`, `??=` 등 PS 7+ 금지)
- [ ] `gh run watch` CI 완료 확인
