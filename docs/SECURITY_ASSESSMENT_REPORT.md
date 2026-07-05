# 보안 점검 및 조치 보고서

## 1. 점검 범위
- 인증/권한
- 환경 변수 노출
- 의존성 취약점
- 서버 설정
- 운영 환경
- 구현 로직 내 보안 취약성(CWE 기반 검토)

## 2. 점검 결과 요약
### 2.1 주요 취약점 발견
- `csautobot/app/pages/data_management.py`
  - 업로드된 파일명 `uploaded_file.name`을 그대로 파일 경로에 사용
  - `CS_DIR / uploaded_file.name` 형태로 경로가 생성되어 경로 탐색(Path Traversal) 또는 파일 덮어쓰기 위험

- `csautobot/main.py`
  - CORS가 `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`로 설정되어 있음
  - 운영 환경에서 모든 출처를 허용하면 CSRF/데이터 유출 위험이 증가

- 인증/권한 미적용 영역
  - `csautobot/app/routes/auth.py`는 관리자 전용 API에만 권한 체크를 적용
  - `inspection`, `search`, `quotation`, `feedback`, `dashboard` 등의 API 엔드포인트는 별도 인증/권한 검증이 없는 상태로 확인됨

- `.env_sample`
  - 샘플 파일에 실제 API 키 또는 키 형태 문자열이 포함되어 있음
  - 공개 저장소에 민감 정보가 남아있지 않아야 함

- `auth_service.py`
  - `JWT_SECRET_KEY`가 설정되지 않으면 임시 랜덤 키를 생성
  - 운영 환경에서는 고정된 비밀키가 반드시 필요

- `auth_db.py`
  - 기본 관리자 계정의 초기 비밀번호가 `admin123`으로 하드코딩되어 있음
  - 초기 시스템의 보안 초기화가 취약함

- 의존성 관리
  - `pyproject.toml` 및 `requirements-prod.txt` 모두 매우 느슨한 버전 제약(`0.*`, `*`, `>=`)을 사용
  - 취약점이 포함된 버전 설치 가능성이 높음

- 프론트엔드 인증 연동
  - 로그인 시 쿠키 설정은 `httpOnly`로 안전하나, 백엔드 API 호출에 `credentials: 'include'`가 없음
  - 쿠키 기반 인증을 제대로 사용하려면 API 호출과 CORS 설정이 일치해야 함

### 2.2 추가 점검된 취약점
- `CWE-79` (XSS) 및 `CWE-89` (SQL Injection)은 이번 코드베이스 분석에서 직접적인 취약 지점이 확인되지 않음
  - 그러나 Streamlit `unsafe_allow_html=True` 사용이 일부 있어 출력 컨텐츠에 대한 주의 필요
  - SQL 쿼리는 대부분 파라미터화되어 있음

## 3. 권장 조치 사항
### 3.1 구현 로직 수정
- 파일 업로드 시 안전한 파일명 생성
  - 사용자 제공 파일명을 그대로 사용하지 않고, UUID 기반 파일명 또는 정규화된 이름 사용
  - 경로 탐색 문자를 제거하고 저장 폴더를 고정 경로로 제한

- 인증/권한 강화
  - 모든 민감 API 엔드포인트에 `get_current_user` 또는 `get_current_admin_user` 의존 적용
  - 공개 API가 필요한 경우 별도 공용 엔드포인트로 분리

- CORS 및 쿠키 설정
  - 운영 환경에서는 허용 origin을 명시적으로 제한
  - `allow_credentials=True`로 쿠키 인증 지원
  - 프론트엔드 fetch 요청에 `credentials: 'include'` 추가
  - 쿠키 `Secure` 옵션은 HTTPS 운영 환경에서 활성화

- 환경 변수 및 시크릿 관리
  - `.env_sample`에서 실제 키와 토큰을 제거
  - 운영용 시크릿은 GitHub Secrets 또는 배포 환경 변수로 관리
  - 배포 스크립트가 `.env` 파일에 민감값을 쓰는 경우, 해당 파일을 Git 추적에서 제외하고 안전하게 보관

- JWT 및 관리자 계정
  - `JWT_SECRET_KEY`를 필수 환경 변수로 강제
  - 기본 관리자 계정 비밀번호를 임시 단순값에서 안전한 랜덤 초기값 또는 계정 생성 워크플로로 변경

- 의존성 관리
  - 주요 패키지는 취약점이 검증된 최소 지원 버전으로 고정
  - 정기적으로 `pip-audit`, `safety` 또는 GitHub Dependabot을 이용한 취약점 스캔 수행

## 4. 진행 계획
### 4.1 단기 계획 (우선 적용)
1. `csautobot/app/pages/data_management.py`에서 업로드 파일명 보안 처리
2. `main.py` CORS 설정 개선 및 `allow_credentials` 일치화
3. 프론트엔드 API 호출에 `credentials: 'include'` 적용
4. `JWT_SECRET_KEY` 환경 변수 필수화 및 임시 키 생성 제거
5. `.env_sample`에서 실제 키 제거 및 샘플 값만 유지

### 4.2 중기 계획
1. 모든 API 경로에 인증/권한 요구사항 재검토
2. `auth_db.py` 초기 관리자 계정 암호 보안 재설계
3. `requirements-prod.txt` 기반으로 취약점 스캔 및 버전 고정
4. 운영 환경 배포 문서에 보안 체크리스트 추가

### 4.3 장기 계획
1. 배포 환경에 대한 보안 감사 및 접근 통제 재검토
2. 정기 보안 점검/취약점 스캔 프로세스 수립
3. 민감 정보 유출 방지를 위한 코드 및 저장소 정책 강화

## 5. 보고서 파일 정보
- 파일명: `docs/SECURITY_ASSESSMENT_REPORT.md`
- 작성일: 2026-07-01
- 작성자: 보안 점검 AI 리뷰어
