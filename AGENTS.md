# AGENTS.md — csautobot
# team-softgrid AI Harness v1.1.0
# 이 파일은 ai-harness 레포에서 자동 동기화됩니다.
## 7. PROJECT OVERRIDE (프로젝트 전용 커스텀)

### ⚠️ 정상 동작 코드 무단 수정 금지 (2026-07-14 사고 재발 방지 — 전 에이전트 공통, 최우선 준수)

> **배경 (aiCsms 사고)**: PR #54에서 부품검색 드롭다운 클리핑을 고치면서, 같은 파일의 다른
> 정상 동작 중이던 이메일 입력 위젯에도 **검증 없이 동일한 수정을 같이 적용**했다가 완전히
> 고장냈다. 이후 원인 파악 없이 캐시 버전만 올리는 헛수정까지 하면서 사용자가 같은 문제를
> 두 번 재검증해야 했다. 이 원칙은 Claude Code뿐 아니라 이 레포를 다루는 **모든 AI 에이전트**
> (Cursor, Antigravity 등)에 적용되므로 CLAUDE.md가 아닌 AGENTS.md(공통 규칙)에 둔다.

**절대 규칙 — 위반 시 즉시 중단하고 사용자에게 보고:**

1. **"비슷해 보인다"는 이유만으로 같이 고치지 않는다.** 같은 파일·같은 패턴(예: 동일 함수/설정을
   여러 곳에서 호출)이 있어도, 지금 고치려는 **그 증상을 실제로 겪고 있는 위치인지 각각 개별
   확인**한 뒤에만 수정 범위에 포함시킨다.
2. **정상 동작 중인 코드를 수정 범위에 포함시킬 때는, 그 변경이 "왜 이 위치에도 필요한지" 한 문장으로
   설명 가능해야 한다.** 설명하지 못하면 그 부분은 건드리지 않는다.
3. **회귀 가능성이 있는 수정(공용 함수/설정, 여러 소비자가 공유하는 모듈 등)은 `git diff <이전 커밋>
   -- <파일>`로 원래 동작하던 버전과 실제로 diff해서, 의도한 부분만 바뀌었는지 확인 후 커밋한다.**
4. **PR·커밋·배포를 언급할 때 실제 링크/번호를 지어내지 않는다.** `gh pr create` 또는 해당 MCP
   도구를 **실제로 호출한 결과값**만 사용자에게 보고한다.

### 특화 완료 기준
- [ ] CS 질문 응답 (`POST /api/v1/search/as-cases` 200 + 답변 반환)
- [ ] 도입 상담 접수 (`POST /api/v1/leads` 201)
- [ ] 월 사용량 조회 (`GET /api/v1/billing/usage/monthly` 200)
- [ ] ChromaDB 인덱싱 완료
- [ ] PM2 `pm2 save` 완료 (SSH disconnect 후에도 서비스 유지)

### 특화 금지 사항
- LangChain 버전 임의 업그레이드 금지 (`pyproject.toml` 버전 고정)
- `csautobot.db` SQLite 스키마 임의 변경 금지
- ecosystem.config.js 앱명 변경 금지

### 포트 / 엔드포인트
- Backend: `http://localhost:8000` / Health: `/health`
- Frontend: `http://localhost:5000`
- AS 검색: `POST /api/v1/search/as-cases`
- 도입 상담: `POST /api/v1/leads`
- 과금 사용량: `GET /api/v1/billing/usage/monthly`
