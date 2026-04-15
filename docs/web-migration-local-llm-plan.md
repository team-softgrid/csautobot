# 웹 전환 상세 계획 (로컬 LLM 선정 포함)

> **문서 버전**: v2.0  
> **최종 수정일**: 2026-04-14

## 1. 목표
- Streamlit 기반 데모를 운영형 웹 서비스로 전환
- 멀티 사용자/권한/로그/KPI/배포 자동화 지원
- 민감 AS 데이터를 고려해 로컬 LLM 중심 아키텍처 적용
- 필요 시 클라우드 fallback 가능한 하이브리드 구조 유지

## 2. 로컬 LLM 모델 선정
### 2.1 권장 조합
- 생성 LLM: `qwen2.5:14b-instruct` (Ollama)
- 임베딩: `bge-m3`
- Reranker: `bge-reranker-v2-m3`
- VRAM별 대안·실무 메모·현재 PoC와의 연계: [local-llm-rag-models.md](local-llm-rag-models.md)

### 2.2 선정 이유
- 한국어 및 기술 문맥(에러코드/정비 지시) 처리 안정성
- 7B 대비 14B의 추론 정확도 우위
- 코드+키워드 혼합 질의에 유리한 검색 품질

### 2.3 하드웨어 가이드
- 최소: GPU 24GB 1장 (개발/파일럿)
- 권장: GPU 48GB 이상 또는 24GB x 2 (운영)
- CPU-only는 가능하나 응답 지연 증가로 비권장

## 3. 아키텍처 설계
- Frontend: Next.js
- Backend API: FastAPI
- RAG Core: Python 모듈(`ingest`, `retrieve`, `rank`, `answer`)
- Vector DB:
  - 초기: Chroma
  - 상용: pgvector 또는 OpenSearch
- Metadata DB: PostgreSQL
- Worker: Celery/RQ (인덱싱/배치 작업)
- LLM Serving: Ollama 전용 추론 노드
- Observability: Prometheus + Grafana + Loki

## 4. 전환 범위
### 4.1 MVP (6주)
- 로그인/권한(관리자, 콜센터, 엔지니어)
- 질의 API + 근거 문서 표시
- 에러코드 정규화 + 하이브리드 검색 + reranker
- 신뢰도 점수 및 저신뢰 fallback
- 질의/응답 로그 저장

### 4.2 Pilot (8~12주)
- 멀티 테넌트(고객사별 분리)
- 인덱스 증분 업데이트
- KPI 대시보드(오접수율, 재출동률, FTFR, MTTR)
- 피드백 루프(좋음/나쁨 -> 개선 반영)

### 4.3 Production (3~6개월)
- 전문가 매칭 모듈
- AS 자재 추천/판매 연동
- AI 기술콜센터(음성/채팅) 연동
- 충전소 점검관리 SaaS 통합

## 5. RAG 정확도 개선 5개 축
### 5.1 에러코드 정규화
- 표기 변형 통합: `EC23`, `에러코드 23`, `pc7 ec75`
- 쿼리/문서 모두 동일 정규화 적용

### 5.2 하이브리드 검색 (Dense + Sparse)
- Dense: 임베딩 검색
- Sparse: BM25/TF-IDF 검색
- 결합 점수 + exact code match 가중치

### 5.3 Reranker
- 1차 Top 30 후보를 재정렬
- 최종 Top 5만 생성 컨텍스트로 사용

### 5.4 신뢰도 스코어
- 검색 점수 분포, 코드 일치, rerank margin 기반
- 임계값으로 응답 레벨 제어:
  - High: 확신 답변
  - Mid: 제한 답변 + 확인 권고
  - Low: 근거 부족 안내 + 현장 점검 권고

### 5.5 답변 템플릿 강제
- 고정 구조:
  1) 증상 요약
  2) 원인 Top 3
  3) 점검 순서
  4) 필요 부품
  5) 근거 사례
  6) 신뢰도/주의사항

## 6. API 초안
- `POST /api/v1/ask`
  - 입력: tenant_id, query, device_model, error_code(optional)
  - 출력: structured_answer, confidence, evidence[]
- `POST /api/v1/ingest`
- `POST /api/v1/reindex`
- `GET /api/v1/kpi`
- `POST /api/v1/feedback`

## 7. 보안/운영 설계
- 테넌트별 데이터 및 인덱스 분리
- 전송/저장 암호화(TLS, at-rest)
- RBAC + 감사 로그
- AI 권고/사람 최종판단 책임 분리
- 모델/인덱스 버전 관리 및 롤백 절차

## 8. 12주 실행 일정
- 1~2주: 아키텍처 확정, 모델 벤치마크, 인프라 준비
- 3~4주: API/인증/기본 UI + 로컬 LLM 연동
- 5~6주: 하이브리드 검색 + reranker + confidence
- 7~8주: KPI/로그/피드백 루프 구현
- 9~10주: 파일럿 배포 및 튜닝
- 11~12주: 안정화, 운영 매뉴얼, 상용 전환 기준 확정

## 10. 인프라 비용 시뮬레이션

### 10.1 클라우드 GPU (AWS 기준)
| 인스턴스 | 스펙 | 용도 | 월 비용 (On-Demand) | 월 비용 (Reserved 1y) |
|-----------|------|------|:------------------:|:--------------------:|
| g5.xlarge | GPU 24GB (A10G) | 개발/파일럿 | ~$800 | ~$500 |
| g5.2xlarge | GPU 24GB + vCPU 8 | 운영 (소규모) | ~$1,100 | ~$700 |
| g5.12xlarge | GPU 96GB (A10G x4) | 운영 (대규모) | ~$4,500 | ~$2,800 |
| p4d.24xlarge | GPU 320GB (A100 x8) | 모델 학습/고성능 | ~$25,000 | ~$16,000 |

### 10.2 온프레미스 GPU 서버
| 구성 | 스펙 | 초기 구매비 | 월 운영비 |
|------|------|:--------:|:--------:|
| 최소 | RTX 4090 24GB + CPU 16코어 + RAM 64GB | ~400만 원 | ~20만 원 (전기/네트워크) |
| 권장 | RTX A6000 48GB + CPU 32코어 + RAM 128GB | ~800만 원 | ~30만 원 |
| 고성능 | A100 80GB x2 + CPU 64코어 + RAM 256GB | ~4,000만 원 | ~50만 원 |

### 10.3 OpenAI API 비용 (클라우드 fallback)
| 모델 | 용도 | 월 1만건 기준 비용 |
|------|------|:-------------------:|
| gpt-4o-mini | 응답 생성 (fallback) | ~$150 (~20만 원) |
| text-embedding-3-small | 임베딩 (fallback) | ~$2 (~3천 원) |

### 10.4 단계별 권장 전략
| 단계 | 권장 구성 | 월 비용 | 근거 |
|------|----------|:------:|------|
| 파일럿 (0~3개월) | OpenAI API 100% | ~30만 원 | 초기 투자 최소화 |
| 상용 초기 (4~6개월) | 온프레미스 최소 + OpenAI fallback | ~70만 원 | 데이터 보안 강화 |
| 상용 안정기 (7개월~) | 온프레미스 권장 + OpenAI fallback | ~100만 원 | 성능/비용 최적 |

> **핵심**: 파일럿에서는 GPU 투자 없이 OpenAI API로 빠르게 검증하고, 상용화 확정 후에 로컬 전환하는 것이 자금 효율적

## 11. 성공 기준 (Go/No-Go)
- Top-3 정답 포함률 목표 달성
- FTFR/MTTR 개선 확인
- 응답시간 SLA 충족
- 저신뢰 응답 안전 처리율 확보

## 12. 결론
권장 전략은 **로컬 중심 하이브리드**입니다.  
단, 파일럿 단계에서는 OpenAI API로 빠르게 검증하고,  
상용화 확정 후 로컬 LLM으로 전환하여 데이터 통제를 강화하는 것이 자금 효율적입니다.  
검색/인덱스는 로컬에서 처리해 데이터 통제를 강화하고, 생성 품질은 로컬 LLM으로 우선 운영하되 필요 시 클라우드 fallback을 적용해 안정성을 확보합니다.
