# csautobot — AI 에이전트 지시사항 초안 (CLAUDE.draft.md)

> 이 파일은 csautobot 저장소의 AI 에이전트용 운영 및 자동화 지침 초안입니다.

---

## 1. 프로젝트 개요

- **목적:** 충전기 AS 유사사례 검색, 점검일지 AI, 운영 대시보드, 피드백 데이터 관리
- **실행:** `poetry run streamlit run csautobot/streamlit_app.py`
- **데이터 파이프라인:** `csData/` 엑셀 → `ingest.py` → `as_records.jsonl` → `build_index.py` → Chroma + BM25

## 2. 기술 스택

| 구분 | 기술 |
|------|------|
| Runtime | Python 3.11, Poetry |
| UI | Streamlit |
| LLM | OpenAI API (`text-embedding-3-small`, ChatOpenAI) |
| 검색 | Chroma + BM25 하이브리드 |
| DB | SQLite |

> 변경 시에는 반드시 `pyproject.toml` 의존성 일관성을 유지하고 운영 영향도를 문서화합니다.

## 3. 자동화 및 검증

- 현재 `.github/workflows`가 없으므로, 첫 단계는 수동 `poetry run pytest` / `poetry run streamlit run` 검증입니다.
- 자동화 도입 시 `workflow_dispatch` 기반 수동 트리거를 우선 추가합니다.
- 로컬 self-hosted runner는 `self-hosted` 라벨이 있는 안정 환경에서만 사용합니다.
- 라벨 정책:
  - `auto-build`: 워크플로우 실행 허용
  - `needs-review`: 사람 검수가 필요함
  - `blocker`: 병합 금지

## 4. 실행 및 테스트

```bash
cd csautobot
poetry install
poetry run python csautobot/ingest.py
poetry run python csautobot/build_index.py
poetry run streamlit run csautobot/streamlit_app.py
```

- `ingest.py`와 `build_index.py`는 데이터 준비 단계이며, `csData/` 원본 엑셀이 없으면 실행 불가
- Streamlit 앱은 데이터 인덱스와 메모리 사용량을 확인하며 실행

## 5. 환경변수 및 민감 정보

| 변수 | 용도 |
|------|------|
| `OPENAI_API_KEY` | AI 임베딩/챗 사용 |
| `INGEST_ONLY_SUBSTR` | 특정 xlsx만 인제스트 |
| `INGEST_USE_LEGACY_FILE_SKIP` | 레거시 파일 제외 |

- `.env`는 Git 커밋 금지
- `.env_sample`을 참조하여 환경변수를 설정

## 6. 코드 변경 주의사항

- `csData/`, `chroma_db_*`, `as_records.jsonl`는 Git에 커밋 금지
- `tutorials/` 파일 변경은 제품 PR과 분리
- `paths.repo_root()` 기반 경로 해석 유지
- 필수 데이터 파이프라인 요소(`sparse_index.pkl`, `active_chroma_dir.txt`) 생략 금지
- RAG 응답은 `search.py` 시스템 프롬프트 기준으로 참고 사례만 사용

## 7. PR/병합 기준

- 기능 추가 시 검색 파이프라인 테스트 또는 인덱스 재생성 검증 결과를 포함
- `tutorials/` 수정은 별도 문서 또는 노트로 분리
- 자동화/CI 변경은 `README.md` 또는 `docs/`에 함께 문서화

## 8. 문서 참조

- `PROJECT_STRUCTURE_PROPOSAL.md`
- `docs/local-llm-rag-models.md`
- `docs/rag-improvement-design.md`
- `docs/README.md`

## 9. 특별 주의

- Streamlit UI는 운영 환경에서 사용자가 데이터 업로드/검색 시 민감 정보 유출을 방지해야 함
- `csData/` 원본은 반드시 `.gitignore` 대상이며, Git에 커밋해서는 안 됩니다
- OpenAI API 키는 개발/운영 환경 모두에서 안전하게 관리합니다.
