# RAG 구현 문서 (현재 구현 기준)

> **문서 버전**: v2.0  
> **최종 수정일**: 2026-04-14  
> **상태**: PoC/프로토타입 (프로덕션 전환 필요 — [web-migration-local-llm-plan.md](web-migration-local-llm-plan.md) 참조)

## 1. 개요
이 문서는 현재 프로젝트에 구현된 전기차 충전기 AS RAG 프로토타입의 구조와 동작 방식을 정리합니다.  
범위는 `scripts/csdata_as_bot` 기준입니다.

## 2. 사용 기술 스택
- Python 3.11
- Streamlit (UI)
- LangChain (RAG 오케스트레이션)
- Chroma (로컬 벡터 DB)
- OpenAI Embedding: `text-embedding-3-small`
- OpenAI Chat Model: `gpt-4o-mini`
- pandas/openpyxl (엑셀 데이터 전처리)
- 로컬 전환 시 모델·VRAM 대안: [local-llm-rag-models.md](local-llm-rag-models.md)

## 3. 디렉터리 및 주요 파일
- `scripts/csdata_as_bot/ingest.py`
  - 엑셀 AS 이력 파싱/정규화
  - 검색 가능한 텍스트 레코드(JSONL) 생성
- `scripts/csdata_as_bot/build_index.py`
  - JSONL을 임베딩 후 Chroma 인덱스 생성
  - 배치 단위 진행률 로그 출력
- `scripts/csdata_as_bot/streamlit_app.py`
  - 질의 입력, 유사사례 검색, 답변 생성 UI
- `scripts/csdata_as_bot/as_records.jsonl`
  - 인덱싱 입력 데이터(행 단위 사례 문서)
- `scripts/csdata_as_bot/chroma_db_*`
  - 생성된 로컬 벡터 인덱스

## 4. 데이터 파이프라인
### 4.1 Ingest 단계
1. `csData` 하위 엑셀 파일 순회
2. 시트별 헤더 행 자동 탐지(키워드 점수 방식)
3. 컬럼 매핑:
   - 증상/접수
   - 조치/수리
   - 교체부품
   - 유형(H/W, S/W 등)
   - 고객/장비 정보
4. 행 단위 문서 생성(`page_content`, `metadata`)
5. `as_records.jsonl`로 저장

### 4.2 Index Build 단계
1. JSONL 로드
2. 임베딩 생성(`text-embedding-3-small`)
3. Chroma 컬렉션(`csdata_as`)에 배치 업서트
4. 인덱싱 진행률 출력
5. 타임스탬프 기반 인덱스 폴더 생성

### 4.3 Query/Answer 단계
1. 사용자 질의 입력(에러코드/증상)
2. 벡터 검색 Top-K 수행
3. 검색 결과를 컨텍스트로 결합
4. LLM 응답 생성(`gpt-4o-mini`)
5. 답변 + 근거 청크 표시

## 5. 현재 프롬프트 원칙
- 제공된 참고 사례 내 근거만 사용
- 추측/일반론 금지
- 유사 사례 요약 + 실제 조치 + 추가 확인사항 중심 답변
- 최종 안전 판단은 엔지니어 수행

## 6. 운영 시 주의사항
- `OPENAI_API_KEY` 필요 (클라우드 호출)
- Streamlit 실행 시 온보딩 프롬프트 방지를 위해 사용 권장:
  - `--browser.gatherUsageStats false`
- Chroma 파일 잠금(Windows) 방지를 위해 인덱스 폴더 버전 분리 운영

## 7. 한계 (현재 기준)
- 에러코드 표기 변형(EC23/에러23/pc7 ec75) 정규화 미흡
- 벡터 단독 검색으로 exact keyword 질의 성능 한계
- reranker 및 confidence score 미구현
- 답변 포맷의 완전한 구조화(JSON schema) 미적용

## 8. 프로토타입 → 프로덕션 Gap 요약
| 레이어 | 현재 (PoC) | 프로덕션 목표 | Gap |
|--------|-----------|-------------|:---:|
| UI | Streamlit | Next.js | 🔴 |
| Backend | Streamlit 내장 | FastAPI | 🔴 |
| Vector DB | Chroma (로컬 파일) | pgvector/OpenSearch | 🔴 |
| LLM | OpenAI gpt-4o-mini | Ollama qwen2.5:14b | ⚠️ |
| Embedding | text-embedding-3-small | bge-m3 (로컬) | ⚠️ |
| 검색 방식 | Dense only | Hybrid (Dense+BM25) | ⚠️ |
| Reranker | 없음 | bge-reranker-v2-m3 | 🔴 |
| 신뢰도 | 없음 | Confidence Score | 🔴 |
| 인증/권한 | 없음 | RBAC | 🔴 |
| 멀티테넌트 | 없음 | 테넌트별 분리 | 🔴 |

## 9. 현재 상태 요약
- AS 이력 기반 RAG 파이프라인과 데모 UI는 동작 확인 완료
- 인덱스 생성 및 검색/응답 흐름 정상
- 다음 단계는 정확도 개선(정규화/하이브리드 검색/rerank/신뢰도/템플릿 강제)
- 프로덕션 전환은 [web-migration-local-llm-plan.md](web-migration-local-llm-plan.md) 참조

