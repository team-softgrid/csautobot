# CSAutobot ↔ aiCSMS 연동 방식

---

## 1. 데이터 흐름

```
[환경부 API]          [고객 CSMS]
     │                    │
     ▼                    ▼
  ┌──────────────────────────┐
  │         aiCSMS           │
  │  (수집 · 저장 · 분석)    │
  └──────────┬───────────────┘
             │  내부 API (읽기전용)
             ▼
  ┌──────────────────┐
  │   CSAutobot      │
  │  (설명 · 보고)   │
  └────┬────────┬────┘
       │        │
       ▼        ▼
  [운영팀    [고객
   챗봇]     포털]
```

---

## 2. CSAutobot이 사용하는 aiCSMS API

### 조회 가능 데이터

```
GET /api/v1/chargers/{id}/status
  → 단일 충전기 현재 상태

GET /api/v1/chargers/{id}/anomalies
  → 탐지된 이상징후 목록

GET /api/v1/tickets/{id}
  → 티켓 상세 (처리 이력 포함)

GET /api/v1/kpi/summary?customer_id=xxx
  → 고객사별 KPI 요약 (MTTR, 가동률 등)

GET /api/v1/reports/monthly?customer_id=xxx&month=2026-07
  → 월간 보고서 데이터
```

### 접근 불가 데이터

```
❌ Zone 2 원시 CSMS 데이터 (고객사 미동의 항목)
❌ 개인정보·RFID·결제정보
❌ 타 고객사 데이터
❌ 정진 내부 운영 원가 데이터
```

---

## 3. 멀티테넌트 격리 원칙

```
CSAutobot 요청 시 반드시 customer_id 또는 user_id 포함.
aiCSMS는 요청자의 권한 범위 내 데이터만 반환.
CSAutobot은 반환된 데이터의 범위를 초과하는 추론·비교 금지.
```

---

## 4. 보고서 자동 생성 트리거

| 이벤트 | CSAutobot 동작 |
|--------|---------------|
| 티켓 완료 처리 | 완료 보고서 초안 생성 → 운영담당 검토 후 발송 |
| 이상징후 24시간 지속 | 알림 메시지 생성 → aiCSMS가 발송 |
| 월 마지막 날 | 월간 가동현황 보고서 생성 → 고객 이메일 발송 |
| 영업 미팅 요청 | 해당 CPO 현황 요약 1페이지 생성 |

---

## 5. aiCallCenter 연동

```
[영업 리드 or CS 인입]
        ↓
[aiCallCenter] → CSAutobot에 현황 조회 요청
        ↓
[CSAutobot] → aiCSMS API 조회 → 자연어 요약 반환
        ↓
[aiCallCenter] → 상담원 화면에 현황 브리핑 표시
```

CSAutobot은 aiCallCenter가 요청한 데이터를 설명해주는 역할만 한다.  
통화 연결·AI 자동 발신 결정은 aiCallCenter가 담당한다.
