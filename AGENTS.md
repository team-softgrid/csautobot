# AGENTS.md — csautobot
# team-softgrid AI Harness v1.0
# 병합: CLAUDE.md + .cursorrules + .continuerules → 단일 마스터 룰
# CS 자동화 봇 — LangChain 기반 고객지원 자동 응대 시스템

---

## 1. 프로젝트 식별
- **레포**: team-softgrid/csautobot
- **스택**: Python 3.11 + FastAPI + Next.js + ChromaDB + LangChain + SQLite
- **서버**: 211.237.13.172:20022 (SSH 포트)
- **배포 경로**: `C:\deploy\csautobot`
- **Python 경로**: `C:\deploy\csautobot\.venv\Scripts\python.exe`
- **포트**: Backend 8000 (uvicorn) / Frontend 5000 (Next.js)
- **프로세스**: PM2 (`ecosystem.config.js` — 앱명: `csautobot-backend`, `csautobot-frontend`)
- **배포**: GitHub Actions → SCP → PM2

---

## 2. 완료 기준 (Done = 이 조건 전부 충족)
- [ ] `pytest tests/ --cov=csautobot --cov-fail-under=60` → pass *(CI Harness Gate 기준)*
- [ ] `cd frontend && npm run build` → exit code 0
- [ ] `curl -f http://localhost:8000/health` → 200 응답
- [ ] `curl -f http://localhost:5000` → 200 응답
- [ ] `.env`, `*.db`, `chroma_db*/` Git 미포함 확인
- [ ] `gh run watch` CI pass 확인
- [ ] `TASK.md` 현재 스프린트 완료 / `ERROR.md` 내용 없음

---

## 3. 아키텍처

```
csautobot/
├── csautobot/           # Python 앱 루트
│   ├── main.py          # FastAPI 앱 (+ GET /health)
│   ├── app/routes/      # API 라우터 (search, inspection, billing, leads …)
│   ├── services/        # 비즈니스 로직 (billing_metering, quotation …)
│   ├── storage/         # SQLAlchemy DB (tenant, usage_meter …)
│   ├── auth_db.py       # 인증 SQLite
│   └── leads_db.py      # 도입 상담 SQLite
├── frontend/            # Next.js (port 5000)
├── tests/               # pytest harness
├── TASK.md              # 스프린트 상태
├── csData/              # 학습 데이터
├── csautobot.db         # SQLite (Git 제외)
├── ecosystem.config.js
└── pyproject.toml
```

---

## 4. 에이전트 핵심 행동 규칙

### 4-1. 절대 금지 (CRITICAL — 서버 장애 방지)
- 사용자에게 질문하지 않는다 — 최선의 판단으로 진행
- `.env`, `*.db`, `chroma_db*/` Git 커밋 금지
- `deploy.yml`, `deploy-remote.ps1` 사용자 확인 없이 수정 금지
- Port 8000 / 5000 변경 금지


### 4-2b. 작업 전 현황 보고 (필수)

**모든 구현·수정·리팩토링 작업 전 아래 형식으로 보고 후 승인 대기:**

`
현재 상태: 어떤 방식으로 동작하는가 (파일명:라인 포함)
현재 문제: 문제점 또는 한계
개선 방향: 무엇을 어떻게 바꾸는가
변경 범위: 수정 파일 목록, 기존 동작 영향 여부
진행할까요?
`
보고 없이 코드 작성 금지 — 사용자 승인 후에만 구현 시작.
### 4-2. 배포 격리 규칙 (서버 공유 — 절대 준수)
이 서버(211.237.13.172)에는 **csautobot, aiCallCenter, aiCsms** 3개 프로젝트가 동시 운영됩니다.

```powershell
# ❌ 절대 금지 — 전체 서비스 다운 (과거 장애 원인)
pm2 kill
pm2 delete all
pm2 stop all
Stop-Process -Name python    # 다른 프로젝트 python 프로세스까지 종료
Stop-Process -Name node      # 다른 프로젝트 node 프로세스까지 종료

# ✅ 올바른 방법 — 앱명 명시하여 자기 앱만 제어
pm2 stop csautobot-backend csautobot-frontend
pm2 restart csautobot-backend csautobot-frontend
pm2 delete csautobot-backend -s
pm2 delete csautobot-frontend -s
```

**포트 할당 (변경 금지)**
| 프로젝트 | 백엔드 | 프론트 | 프로세스 |
|---------|--------|--------|---------|
| **csautobot** | **8000** | **5000** | PM2 |
| aiCallCenter | 8090 | 3000 | PM2 |
| aiCsms | 8080 | SSR | Windows Service |

### 4-3. Windows 서버 배포 특수 규칙 (과거 실패에서 학습)
- PM2 daemon: SSH 세션 종료 시 죽는 문제 → `sc.exe` + wrapper batch file로 Windows Service 등록
- 절대 사용 금지: WMI, wmic, pm2-windows-startup, pm2 `--home` flag, NSSM
- PowerShell 버전: 서버는 **PS 5.x** → `?.` null-conditional, `??=` 등 PS 7+ 문법 사용 금지
- PM2_HOME 반드시 명시: `PM2_HOME=C:\Users\Administrator\.pm2`
- `pm2 startOrReload` 후 반드시 `pm2 save` (SSH disconnect 전)

### 4-4. 필수 배포 루틴
1. `git commit` + `git push`
2. `gh run watch` — CI 완료까지 모니터링 (port health check만으로 완료 판단 금지)
3. 배포 성공 확인: `curl http://211.237.13.172:8000/health` + `curl http://211.237.13.172:5000`
4. `completed: success` 확인 후에만 완료 보고

### 4-5. 자율 실행 루프
```
태스크 선택 → 코드 작성 → 즉시 실행 → 결과 확인
  └─ 실패 → 에러 로그 통째로 컨텍스트 유지 → 자가 수정 (최대 3회)
       └─ 3회 실패 → ERROR.md 기록 → [blocked] → 다음 태스크
```

### 4-6. Git 워크플로우
```bash
git checkout -b agent/{task-name}
# pytest pass 후
git add -p
git commit -m "feat(csautobot): {task-name} 완료"
gh pr create --base main
```

---

## 5. 기술 스택 패턴

### FastAPI
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

router = APIRouter(prefix="/api/v1", tags=["cs"])

class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None

@router.post("/query")
async def query_cs(body: QueryRequest):
    try:
        result = await cs_service.answer(body.question, body.session_id)
        return {"answer": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### LangChain + ChromaDB
```python
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ["OPENAI_API_KEY"]  # 하드코딩 절대 금지
)
```

### PM2 ecosystem.config.js
```javascript
// 앱명 변경 금지 (배포 스크립트가 이 이름으로 제어)
module.exports = {
  apps: [
    { name: 'csautobot-backend', script: '...' },
    { name: 'csautobot-frontend', script: '...' }
  ]
}
```

---

## 6. 테스트
```bash
# 전체 (커버리지 포함)
pytest --cov=csautobot --cov-report=term-missing --cov-fail-under=80

# 빠른 실행
pytest tests/ -v --tb=short

# LLM Mock 활용 (실제 API 키 불필요)
# conftest.py의 mock_llm fixture 사용
```

---

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
