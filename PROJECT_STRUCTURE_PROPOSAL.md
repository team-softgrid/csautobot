# 프로젝트 구조 개선안

현재 저장소는 학습용 노트북과 실무형 데이터봇 산출물이 함께 존재해, 기여/리뷰/배포 관점에서 경계가 모호합니다. 아래 구조로 역할을 분리하면 유지보수가 쉬워집니다.

## 목표

- 학습 콘텐츠(튜토리얼)와 실행형 애플리케이션(봇/서비스)의 책임 분리
- 데이터 원본/생성 산출물의 Git 오염 최소화
- 신규 기여자의 진입 경로 단순화

## 제안 구조

```text
langchain-kr/
  tutorials/                  # 기존 01~99 학습 섹션
    01-Basic/
    04-Model/
    ...
  csautobot/                  # 실행형 앱(메인 제품 코드, 구: csdata-as-bot)
    ingest.py
    build_index.py
    streamlit_app.py
    retrieval.py
  data/                       # 로컬 데이터(기본 gitignore)
    raw/
    processed/
  tutorials/                  # 학습용 튜토리얼 자산(01~99)
  docs/
    onboarding.md
    architecture.md
  README.md
```

## 단계별 이전 계획

### 1단계 (즉시)

- **완료:** 학습용 폴더를 `tutorials/` 아래로 이동해 서비스 코드와 물리 분리
- **완료:** 제품 코드 `csautobot/`를 루트로 승격 *(2026-04 에 `csdata-as-bot/` → `csautobot/` 리네임)*
- **완료:** `.gitignore`로 데이터/인덱스 산출물 커밋 방지

### 2단계 (점진)

- **완료:** `README.md` 실행 경로를 `tutorials/` 및 `csautobot/` 기준으로 정리
- (선택) `csautobot` 내부를 `app/`·`pipeline/`로 더 쪼개기
- (선택) Streamlit UI를 API 서버 + 웹 프론트 구조로 분리

### 3단계 (안정화)

- `docs/onboarding.md`에 신규 기여자 체크리스트 고정
- 데이터 샘플 정책 정리(공개 가능 샘플만 `data/sample`로 추출)
- CI에서 금지 파일 확장자(`.xlsx`, `.zip`, `.pptx`, 인덱스 폴더) 검사 추가

## 운영 원칙

- 저장소에는 "재생성 가능한 산출물"을 올리지 않음
- 노트북 변경은 "입력 코드 변경"과 "출력 셀 변경"을 가능한 분리
- 앱 코드 변경 PR과 튜토리얼 콘텐츠 PR을 목적별로 분리

## 기대 효과

- 리뷰 범위 축소 및 충돌 감소
- 저장소 용량 증가 속도 완화
- 학습 사용자와 개발 기여자 모두에게 더 명확한 탐색 경험 제공
