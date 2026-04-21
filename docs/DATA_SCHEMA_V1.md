# CS 데이터 스키마 V1 (권장)

## 목적

4년치 AS/점검 데이터를 일관된 구조로 통합해 검색 품질과 분석 신뢰도를 높입니다.

## 엔터티

## 1) site (충전소)

- `site_id` (string, PK)
- `site_name` (string)
- `operator_name` (string)
- `address` (string)
- `region` (string)

## 2) charger (설비)

- `charger_id` (string, PK)
- `site_id` (string, FK -> site.site_id)
- `manufacturer` (string)
- `model_name` (string)
- `install_date` (date)
- `status` (enum: active, inactive, retired)

## 3) incident (장애/민원 접수)

- `incident_id` (string, PK)
- `charger_id` (string, FK -> charger.charger_id)
- `occurred_at` (datetime)
- `reported_at` (datetime)
- `symptom_raw` (text)
- `symptom_norm` (text)
- `error_code_raw` (string)
- `error_code_norm` (string, 예: `EC23|PC7`)
- `severity` (enum: low, mid, high, critical)
- `source_file` (string)
- `source_sheet` (string)
- `source_row` (string/int)

## 4) action (조치 이력)

- `action_id` (string, PK)
- `incident_id` (string, FK -> incident.incident_id)
- `action_at` (datetime)
- `action_type` (enum: reset, replace, firmware, wiring, inspection, other)
- `action_detail` (text)
- `result` (enum: resolved, unresolved, monitor)
- `downtime_min` (int)
- `engineer_id` (string)

## 5) part_usage (부품 사용)

- `part_usage_id` (string, PK)
- `action_id` (string, FK -> action.action_id)
- `part_code` (string)
- `part_name` (string)
- `qty` (int)
- `unit_cost` (number)

## 6) inspection_log (점검일지)

- `inspection_id` (string, PK)
- `charger_id` (string, FK -> charger.charger_id)
- `inspection_cycle` (enum: daily, weekly, monthly, quarterly, halfyearly, yearly)
- `checklist_json` (json)
- `memo_text` (text)
- `photo_urls` (json array)
- `ai_summary` (text)
- `created_at` (datetime)
- `updated_at` (datetime)

## 검색 인덱스 최소 메타

- `doc_id`
- `chunk_index`
- `source`
- `sheet`
- `row`
- `symptom_norm`
- `error_code_norm`
- `charger_id` (가능하면)
- `site_id` (가능하면)

## 데이터 품질 규칙

- 필수: `incident_id`, `charger_id`, `symptom_raw`, `action_detail`
- 정규화:
  - 에러코드 표기 통합(`에러 23`, `EC23`, `Error-23` -> `EC23`)
  - 동의어 통합(`긴급정지`, `비상정지`, `emergency stop`)
- 시간값은 로컬 타임존 기준 ISO8601으로 저장

## 운영 원칙

- 원본 파일은 `csData/`에 보관하고, 변환 산출물은 `csdata-as-bot/`에서 생성
- 원본/산출물 버전 태깅으로 재현 가능성 확보
- 민감정보(개인정보, 전화번호)는 저장 전 마스킹
