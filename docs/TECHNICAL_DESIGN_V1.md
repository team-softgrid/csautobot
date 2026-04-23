# 전기차 충전소 AI 점검관리 서비스 기술설계 V1

> 목적: 현재 `csautobot`을 검색형 PoC에서 데이터 기반 점검/AS 관리 서비스로 확장하기 위한 실제 구현 단위를 정의한다.

## 1. 목표 아키텍처

## 현재

- UI: Streamlit 단일 앱
- 데이터: `csData/*.xlsx`
- 검색 인덱스: Chroma + BM25
- 생성: OpenAI API

## 목표

- UI:
  - 단기: Streamlit MVP 유지
  - 중기: 웹 프론트 + API 서버
- 데이터:
  - 원본, 정규화 데이터, 검색 인덱스 분리
- 저장소:
  - SQLite로 시작, 이후 Postgres 전환
- 검색:
  - 구조화 필터 + 하이브리드 검색
- 생성:
  - 무료/유료 모델 라우팅 가능 구조

## 2. 권장 디렉터리 구조

```text
langchain-kr/
  csData/                       # 원본
  csautobot/
    app/
      streamlit_app.py
      pages/
        search.py
        inspection_log.py
        dashboard.py
    pipeline/
      ingest_raw.py
      normalize_records.py
      build_search_docs.py
      build_index.py
    storage/
      db.py
      repositories.py
      schema.sql
    domain/
      models.py
      enums.py
    services/
      retrieval_service.py
      inspection_service.py
      summarization_service.py
      billing_metering.py
    prompts/
      as_answer.yaml
      inspection_summary.yaml
  docs/
```

## 3. DB 초안

## core tables

### tenant

- `tenant_id` text primary key
- `tenant_name` text not null
- `plan_code` text not null
- `created_at` datetime not null

### app_user

- `user_id` text primary key
- `tenant_id` text not null
- `email` text not null
- `role` text not null
- `status` text not null
- `created_at` datetime not null

### site

- `site_id` text primary key
- `tenant_id` text not null
- `site_name` text not null
- `operator_name` text
- `address` text
- `region` text

### charger

- `charger_id` text primary key
- `tenant_id` text not null
- `site_id` text not null
- `manufacturer` text
- `model_name` text
- `serial_no` text
- `install_date` date
- `status` text not null

### incident

- `incident_id` text primary key
- `tenant_id` text not null
- `site_id` text
- `charger_id` text
- `occurred_at` datetime
- `reported_at` datetime
- `symptom_raw` text not null
- `symptom_norm` text
- `error_code_raw` text
- `error_code_norm` text
- `severity` text
- `source_file` text
- `source_sheet` text
- `source_row` text
- `created_at` datetime not null

### action

- `action_id` text primary key
- `incident_id` text not null
- `action_at` datetime
- `action_type` text not null
- `action_detail` text not null
- `result` text
- `downtime_min` integer
- `engineer_name` text

### part_usage

- `part_usage_id` text primary key
- `action_id` text not null
- `part_code` text
- `part_name` text
- `qty` integer
- `unit_cost` numeric

### inspection_log

- `inspection_id` text primary key
- `tenant_id` text not null
- `site_id` text not null
- `charger_id` text
- `inspection_cycle` text not null
- `inspection_type` text not null
- `checklist_json` text not null
- `memo_text` text
- `photo_urls_json` text
- `ai_summary` text
- `status` text not null
- `confirmed_by` text
- `created_at` datetime not null
- `updated_at` datetime not null

### usage_meter

- `usage_id` text primary key
- `tenant_id` text not null
- `user_id` text
- `feature_code` text not null
- `model_name` text
- `input_tokens` integer
- `output_tokens` integer
- `request_count` integer not null
- `measured_at` datetime not null

### audit_log

- `audit_id` text primary key
- `tenant_id` text not null
- `user_id` text
- `action_code` text not null
- `resource_type` text not null
- `resource_id` text not null
- `payload_json` text
- `created_at` datetime not null

## 4. 파일별 구현 대상

## 기존 파일

### [`csautobot/ingest.py`](C:\MyProject\langchain-kr\csautobot\ingest.py)

- 현재 역할:
  - 엑셀 -> 검색용 JSONL
- 변경 방향:
  - 엑셀 -> 구조화 엔터티 + 검색용 문서
- 추가 필요:
  - `site_id`, `charger_id` 생성 규칙
  - 시간 파싱
  - 개인정보 마스킹
  - 예외 행 리포트

### [`csautobot/build_index.py`](C:\MyProject\langchain-kr\csautobot\build_index.py)

- 현재 역할:
  - JSONL -> Chroma/BM25
- 변경 방향:
  - 검색문서 전용 입력셋 사용
  - 인덱스 버전 메타 추가
  - 인덱스 대상 tenant/site 범위 옵션 추가

### [`csautobot/retrieval.py`](C:\MyProject\langchain-kr\csautobot\retrieval.py)

- 현재 역할:
  - 하이브리드 검색 + 재순위 + 신뢰도
- 변경 방향:
  - 구조화 필터 지원
  - `site_id`, `charger_id`, `manufacturer`, `inspection_cycle` 필터 추가
  - 향후 예지정비 feature 계산 입력으로 재사용

### [`csautobot/streamlit_app.py`](C:\MyProject\langchain-kr\csautobot\streamlit_app.py)

- 현재 역할:
  - 단일 검색 UI
- 변경 방향:
  - 페이지 분리
  - 검색/점검일지/대시보드 3개 화면으로 확장

## 신규 권장 파일

### `csautobot/storage/db.py`

- 역할:
  - SQLite/Postgres 연결
  - 세션 관리

### `csautobot/storage/schema.sql`

- 역할:
  - 초기 테이블 생성

### `csautobot/storage/repositories.py`

- 역할:
  - `incident`, `inspection_log`, `usage_meter` CRUD

### `csautobot/services/inspection_service.py`

- 역할:
  - 점검일지 저장
  - AI 초안 생성
  - 상태 변경(`draft`, `confirmed`)

### `csautobot/services/billing_metering.py`

- 역할:
  - 질의 수
  - 토큰 사용량
  - tenant별 월 집계

### `csautobot/app/pages/inspection_log.py`

- 역할:
  - 체크리스트
  - 메모
  - 사진 경로 입력
  - AI 요약 생성

### `csautobot/app/pages/dashboard.py`

- 역할:
  - 설비별 재발 현황
  - 사이트별 장애 추이
  - 점검일지 작성 시간

## 5. 1차 API 초안

## ingestion

- `POST /api/v1/ingest/run`
- `GET /api/v1/ingest/jobs/{job_id}`

## search

- `POST /api/v1/search/as-cases`
  - input:
    - `query`
    - `tenant_id`
    - `site_id`
    - `charger_id`

## inspection

- `POST /api/v1/inspection-logs`
- `PATCH /api/v1/inspection-logs/{inspection_id}`
- `GET /api/v1/inspection-logs/{inspection_id}`
- `GET /api/v1/inspection-logs`

## dashboards

- `GET /api/v1/dashboard/incidents`
- `GET /api/v1/dashboard/inspection-productivity`

## billing

- `GET /api/v1/billing/usage/monthly`

## 6. 점검일지 AI 어시스턴트 플로우

1. 사용자가 설비/충전소/점검주기 선택
2. 체크리스트 입력
3. 메모와 사진 첨부
4. AI가 이상징후 요약, 권장 조치, 후속 점검 항목 초안 생성
5. 엔지니어가 수정 후 확정
6. 확정본 저장
7. 사용량과 감사로그 기록

## 7. 무료/유료 모델 전략

## Free

- 검색 위주
- 짧은 요약만 생성
- 일일/월간 요청 제한

## Pro

- 점검일지 AI 초안
- 사진 기반 요약
- 월간 분석 리포트

## Enterprise

- 전용 모델 라우팅
- 온프렘/VPC
- 커스텀 룰과 전용 SLA

## 8. 구현 우선순위

1. 저장소 계층 도입
2. 구조화 인제스트
3. 점검일지 저장
4. 검색 필터 확장
5. 사용량 계측
6. 인증/테넌시

## 9. 비기능 요구사항

- 개인정보 마스킹 필수
- tenant 간 데이터 격리
- 인덱스 재생성 가능성 보장
- 산출물 버전 관리
- 검색 결과 근거 추적 가능

## 10. 바로 수정할 파일 목록

- 수정:
  - `csautobot/ingest.py`
  - `csautobot/build_index.py`
  - `csautobot/retrieval.py`
  - `csautobot/streamlit_app.py`
  - `csautobot/README.md`
- 추가:
  - `csautobot/storage/db.py`
  - `csautobot/storage/schema.sql`
  - `csautobot/storage/repositories.py`
  - `csautobot/services/inspection_service.py`
  - `csautobot/services/billing_metering.py`
  - `csautobot/app/pages/inspection_log.py`
  - `csautobot/app/pages/dashboard.py`

## 11. 권장 다음 액션

- 먼저 SQLite 기반으로 `inspection_log`, `incident`, `usage_meter` 3개 축을 넣는다.
- 그 다음 Streamlit에서 검색과 점검일지 화면을 분리한다.
- 이후 FastAPI로 백엔드를 분리하면서 과금과 인증을 붙인다.
