# AGENTS.md — csautobot
# team-softgrid AI Harness v1.0
# CS 자동화 봇 — LangChain 기반 고객지원 자동 응대 시스템

---

## 1. 프로젝트 식별
- **레포**: team-softgrid/csautobot
- **스택**: Python 3.11 + FastAPI + Next.js + ChromaDB + LangChain + SQLite
- **서버**: 211.237.13.172
- **포트**: Backend 8000 (uvicorn) / Frontend 5000 (Next.js)
- **프로세스**: PM2 (`ecosystem.config.js` — 앱명: `csautobot-backend`, `csautobot-frontend`)

---

## 2. 완료 기준 (Done = 이 조건 전부 충족)
- [ ] `pytest --cov=csautobot --cov-fail-under=80` → pass
- [ ] `cd frontend && npm run build` → exit code 0
- [ ] `curl -f http://localhost:8000/health` → 200 응답
- [ ] `curl -f http://localhost:5000` → 200 응답
- [ ] `.env`, `*.db`, `chroma_db*/` Git 미포함 확인
- [ ] ERROR.md 내용 없음

---

## 3. 아키텍처

```
csautobot/
├── csautobot/           # Python 패키지 루트
│   ├── main.py          # FastAPI 앱
│   ├── routers/         # API 라우터
│   ├── services/        # 비즈니스 로직 + LangChain 체인
│   ├── models/          # DB 모델 (SQLite)
│   └── tests/           # pytest
├── frontend/            # Next.js
│   └── src/app/         # App Router
├── csData/              # 학습 데이터
├── csautobot.db         # SQLite (Git 제외)
├── ecosystem.config.js
├── requirements.txt
└── pyproject.toml
```

---

## 4. 에이전트 핵심 행동 규칙

### 4-1. 절대 금지 (서버 장애 방지 — CRITICAL)
- 사용자에게 질문하지 않는다 — 최선의 판단으로 진행
- **`pm2 kill` / `pm2 delete all` / `pm2 stop all` 절대 금지**
  → 동일 서버의 aiCallCenter, aiCsms까지 전부 다운됨
- **`Stop-Process -Name python` / `Stop-Process -Name node` 절대 금지**
  → 프로세스명 기반 kill은 다른 프로젝트까지 종료
- `.env`, `*.db`, `chroma_db*/` Git 커밋 금지
- `deploy.yml`, `deploy-remote.ps1` 사용자 확인 없이 수정 금지
- Port 8000 / 5000 변경 금지

### 4-2. PM2 제어 (자기 앱만)
```powershell
# ✅ 올바른 방법 — 앱명 명시
pm2 stop csautobot-backend csautobot-frontend
pm2 restart csautobot-backend csautobot-frontend
pm2 delete csautobot-backend csautobot-frontend -s

# ❌ 절대 금지
pm2 kill
pm2 delete all
Stop-Process -Name python
Stop-Process -Name node
```

### 4-3. 자율 실행 루프
```
태스크 선택 → 코드 작성 → 즉시 실행 → 결과 확인
  └─ 실패 → 에러 로그 통째로 컨텍스트 유지 → 자가 수정 (최대 3회)
       └─ 3회 실패 → ERROR.md 기록 → [blocked] → 다음 태스크
```

### 4-4. Git 워크플로우
```bash
git checkout -b agent/{task-name}
# pytest pass 후
git add -p
git commit -m "feat(csautobot): {task-name} 완료"
gh pr create --base main
```

---

## 5. 기술 스택 패턴

### FastAPI 라우터
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

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

### LangChain 체인 패턴
```python
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
import os

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ["OPENAI_API_KEY"]
)
vectorstore = Chroma(persist_directory="./chroma_db")
chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())
```

### 환경변수
```python
import os
# .env에서 로드 (python-dotenv), 절대 하드코딩 금지
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
```

---

## 6. 테스트
```bash
# 전체 (커버리지 포함)
pytest --cov=csautobot --cov-report=term-missing --cov-fail-under=80

# 빠른 실행 (커버리지 제외)
pytest tests/ -v --tb=short

# LLM Mock 필수
# conftest.py의 mock_llm fixture 활용 (실제 API 키 불필요)
```

---

## 7. 배포 (Level 1 — 사용자 승인 필요)
```powershell
# 스테이징 확인 후 수동 실행
.\scripts\deploy-remote.ps1

# 배포 후 헬스체크
curl http://211.237.13.172:8000/health
curl http://211.237.13.172:5000
```

---

## 8. PROJECT OVERRIDE (프로젝트 전용 커스텀)

### 특화 완료 기준
- [ ] CS 질문 응답 API (`POST /api/v1/query` 200 + 답변 반환)
- [ ] ChromaDB 학습 데이터 인덱싱 완료
- [ ] 대화 세션 관리 (`session_id` 기반 히스토리 유지)
- [ ] 관리자 대시보드 CS 이력 조회 정상

### 특화 금지 사항
- LangChain 버전 임의 업그레이드 금지 (`pyproject.toml` 버전 고정)
- ChromaDB 컬렉션명 변경 금지
- SQLite DB 파일(`csautobot.db`) 스키마 임의 변경 금지

### 포트 / 엔드포인트
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5000`
- Health: `http://localhost:8000/health`
- CS 질문: `POST http://localhost:8000/api/v1/query`
