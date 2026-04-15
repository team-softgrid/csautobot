# 로컬 RAG용 LLM·임베딩·리랭커 선정 가이드

> **문서 버전**: v1.0  
> **최종 수정일**: 2026-04-15  
> **범위**: 전기차 충전기 AS RAG(한국어 민원·조치 서술, 에러코드·부품명 혼재) 기준 권장안  
> **연계**: [web-migration-local-llm-plan.md](web-migration-local-llm-plan.md) §2와 동일 방향을 보강한 실무용 요약입니다.

## 1. 설계 원칙

- **검색·인덱스는 로컬**로 두고 민감 데이터 유출면을 줄인다.
- **생성(답변)** 은 로컬 LLM을 기본으로 하되, 품질·지연 SLA에 따라 **클라우드 fallback**을 허용한다.
- 한국어 **기술 서술**(증상·조치·교체 부품)과 **짧은 키워드·에러코드** 질의가 함께 오므로, **지시 따르기 + 한영 혼합**에 강한 계열을 우선한다.

## 2. 권장 스택 (기본값)

| 역할 | 권장 | 비고 |
|------|------|------|
| 생성 (Chat) | **Qwen2.5 14B Instruct** | Ollama 예: `qwen2.5:14b` 계열. 한국어·지시 수행·기술 문맥 균형이 좋음. |
| 임베딩 | **BGE-M3** (`BAAI/bge-m3`) | 다국어·긴 문맥·dense 검색 기준으로 AS 문서와 잘 맞음. |
| 리랭커 | **bge-reranker-v2-m3** | Top-K 재정렬 품질 향상. VRAM 부담 큼 → 단계 도입 가능. |

운영·비용 관점의 단계 전략은 [web-migration-local-llm-plan.md](web-migration-local-llm-plan.md) §10을 따른다.

## 3. VRAM별 생성 모델 대안

| GPU VRAM(대략) | 생성 모델 제안 | 메모 |
|----------------|----------------|------|
| **~24GB** | **Qwen2.5 14B Instruct** | 파일럿~소규모 운영의 기본 선택. |
| **~16GB** | **Qwen2.5 7B Instruct** | 14B가 OOM이거나 지연이 크면 타협. 답변 정밀도는 다소 하락. |
| **32~48GB+** | **Qwen2.5 32B Instruct** (또는 동급) | 품질 여유·긴 컨텍스트가 필요할 때. |

**비권장/주의**

- **Llama 3.1 8B** 등 영어 편향 모델만으로 한국 AS 문서 전용 RAG를 구성하면, 동일 VRAM에서 한국어 체감이 Qwen 계다 불리한 경우가 많다.
- **CPU-only**는 PoC는 가능하나, 운영 SLA 관점에서는 비권장(응답 시간).

## 4. Ollama 기준 실행 예시

```bash
ollama pull qwen2.5:14b
```

실제 태그는 `ollama.com` 라이브러리 및 `ollama list` 출력과 맞출 것. LangChain에서는 `ChatOllama` 등으로 연결한다.

## 5. 임베딩·리랭커 실무 메모

- **임베딩**: OpenAI `text-embedding-3-small`에서 로컬로 넘길 때, 인덱스를 **재생성**해야 한다(벡터 공간 불일치).
- **리랭커**: 크로스인코더는 지연·VRAM을 쓴다. PoC에서는 **경량 rerank**(예: FlashRank) 또는 **임베딩 코사인 재순위**로 시작하고, 품질 한계가 보이면 BGE reranker를 추가하는 방식이 안전하다.
- **컨텍스트 길이**: AS 본문이 길면 청크 길이·Top-K·rerank 후 Top-N을 함께 튜닝한다.

## 6. 현재 레포(`scripts/csdata_as_bot`)와의 관계

- 현재 PoC는 **OpenAI 임베딩 + gpt-4o-mini** 기준으로 동작한다. 상세는 [rag-implementation-current.md](rag-implementation-current.md).
- 로컬 생성·임베딩으로 바꿀 때는 **환경 변수·빌드 파이프라인·인덱스 재구축**을 한 묶음으로 계획한다. 전환 로드맵은 [web-migration-local-llm-plan.md](web-migration-local-llm-plan.md) §3~§5를 따른다.

## 7. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-15 | v1.0 초안 — 로컬 RAG용 모델 스택·VRAM 대안·연계 문서 정리 |
