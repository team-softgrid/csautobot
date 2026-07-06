# AGENTS.md — csautobot
# team-softgrid AI Harness v1.1.0
# 이 파일은 ai-harness 레포에서 자동 동기화됩니다.
## 7. PROJECT OVERRIDE (프로젝트 전용 커스텀)

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
