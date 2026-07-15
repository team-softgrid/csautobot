# csautobot 배포 지침 (AGENTS.md)

> 이 문서는 배포 시행착오를 통해 확립된 **확정 지침**입니다.
> 배포 관련 작업을 할 때 반드시 이 문서를 먼저 읽고 따르십시오.

---

## 1. 프로젝트 구조 및 배포 환경

| 항목 | 값 |
|------|-----|
| 배포 서버 | `211.237.13.172` (Windows Server), SSH 포트 `20022` |
| 배포 경로 | `C:\deploy\csautobot` |
| Python 환경 | `C:\deploy\csautobot\.venv\Scripts\python.exe` |
| PM2 home | `C:\Users\Administrator\.pm2` |
| Frontend 포트 | `5000` (Next.js) |
| Backend 포트 | `8000` (FastAPI / uvicorn) |
| 배포 방식 | GitHub Actions → SCP → PowerShell 원격 실행 |
| 배포 스크립트 | `scripts/deploy-remote.ps1` |
| 생태계 설정 | `ecosystem.config.js` |
| CI/CD | `.github/workflows/deploy.yml` |

---

## 2. Windows 원격 서버에서 PM2 영속성 — 핵심 원칙

> **⚠️ 가장 중요한 지침: Windows + SSH 환경에서 PM2는 SSH 세션이 종료되면 데몬이 함께 종료된다.**

### 절대 하지 말 것 (검증된 실패 방법)

- ❌ `pm2 startOrReload` 후 아무 조치 없이 SSH 종료
- ❌ `WMI (Invoke-WmiMethod Win32_Process)`로 PM2 기동 → SSH 세션 트리와 연결되어 세션 종료 시 함께 사망
- ❌ `wmic process call create` 방식 → 동일 문제
- ❌ `pm2-windows-startup` / `pm2-startup install` → Windows 예약 작업으로 등록하지만, **현재 SSH 세션 종료 시 즉시 PM2 데몬이 죽음**. 다음 로그인/재부팅 때만 재기동되므로 사실상 무효
- ❌ `pm2 --home C:\path` 플래그 → **존재하지 않는 PM2 CLI 옵션**. 반드시 `PM2_HOME` 환경변수로 처리할 것
- ❌ PowerShell 7+ 전용 문법 (`?.` null 조건 연산자) → 서버가 PowerShell 5.x 이므로 파싱 오류 발생
- ❌ NSSM 외부 다운로드 → 다운로드 URL 불안정, 불필요한 복잡도

### 반드시 해야 할 것 (확정 동작 방법)

**`sc.exe` + 래퍼 배치파일로 Windows Service 등록 (PowerShell 5.x 호환, 외부 도구 불필요)**

```powershell
# 1. 래퍼 배치파일 생성
$NodeExe = "C:\Program Files\nodejs\node.exe"
$NpmGlobalRoot = (cmd.exe /c "npm root -g").Trim()
$Pm2Js = "$NpmGlobalRoot\pm2\bin\pm2"
$BatContent = @"
@echo off
set PM2_HOME=C:\Users\Administrator\.pm2
"$NodeExe" "$Pm2Js" resurrect
"@
Set-Content -Path "C:\deploy\csautobot\pm2_service_wrapper.bat" -Value $BatContent -Encoding ASCII

# 2. 기존 서비스 제거 (있을 경우)
sc.exe stop PM2_csautobot 2>$null | Out-Null
sc.exe delete PM2_csautobot 2>$null | Out-Null
Start-Sleep -Seconds 3

# 3. Windows Service 등록 (LocalSystem, 자동시작, 자동재시작)
$BinPath = "cmd.exe /c `"C:\deploy\csautobot\pm2_service_wrapper.bat`""
sc.exe create PM2_csautobot binPath= $BinPath start= auto obj= LocalSystem DisplayName= "PM2 csautobot Service"
sc.exe failure PM2_csautobot reset= 60 actions= restart/5000/restart/10000/restart/30000

# 4. PM2 앱 기동 및 상태 저장 (현재 세션)
$env:PM2_HOME = "C:\Users\Administrator\.pm2"
cmd.exe /c "pm2 startOrReload C:\deploy\csautobot\ecosystem.config.js --update-env"
cmd.exe /c "pm2 save"

# 5. 서비스 시작 (이후 SSH 세션 종료 후에도 독립 생존)
sc.exe start PM2_csautobot 2>$null | Out-Null
```

**이 방식이 동작하는 이유**: `LocalSystem` 계정으로 등록된 Windows Service는 SSH 세션 트리와 완전히 독립적으로 실행되며, 서버 재부팅 후에도 자동 복원됩니다.

---

## 3. PM2_HOME 환경변수 처리

SSH 계정과 PM2 실행 계정이 다를 수 있으므로 항상 명시적으로 지정해야 합니다.

```powershell
# ✅ 올바른 방법 — 환경변수로 지정
$env:PM2_HOME = "C:\Users\Administrator\.pm2"
cmd.exe /c "set PM2_HOME=C:\Users\Administrator\.pm2 && pm2 status"

# ❌ 잘못된 방법 — 존재하지 않는 플래그 (오류 발생)
pm2 --home C:\Users\Administrator\.pm2 status
```

---

## 4. GitHub Actions 로그 수집 단계 규칙

### 로그 fetch 단계는 배포 성패에 영향을 주면 안 됨

```yaml
- name: Fetch Remote PM2 Logs and Push to Git
  if: always()
  run: |
    sshpass ... "cmd.exe /c set PM2_HOME=... && pm2 logs ..." > pm2_logs.txt || true
    # ↑ 모든 sshpass 명령 끝에 || true 필수 (실패해도 빌드 계속)
```

### PM2 로그/상태 확인 시 반드시 PM2_HOME 지정

```bash
# ✅ 올바른 방법
sshpass ... "cmd.exe /c set PM2_HOME=C:\\Users\\Administrator\\.pm2 && pm2 status"

# ❌ 잘못된 방법 (존재하지 않는 플래그)
sshpass ... "cmd.exe /c pm2 --home C:\\... status"
```

### 실제 서버 프로세스 생존 확인은 netstat으로

```bash
sshpass ... "powershell -Command \"netstat -ano | findstr ':5000 :8000'\""
# 결과: TCP 0.0.0.0:5000 LISTENING → 정상
# 결과: 빈 출력 → 앱 다운
```

---

## 5. 배포 후 서버 생존 확인 순서

1. **netstat 포트 확인** → `TCP 0.0.0.0:5000 LISTENING` / `TCP 0.0.0.0:8000 LISTENING` 이어야 함
2. **Windows Service 상태** → `Get-Service -Name PM2_csautobot` → `Running` 또는 `Stopped` 확인
3. **PM2 status** → `PM2_HOME` 지정 후 `pm2 status` 실행, `online` 상태 확인
4. **외부 HTTP 요청** → `http://211.237.13.172:5000` (Frontend), `http://211.237.13.172:8000` (Backend API)

---

## 6. 스크립트 호환성 주의사항

| 항목 | 주의사항 |
|------|----------|
| PowerShell 버전 | 서버는 **PS 5.x** → `?.` null 조건 연산자 사용 불가 → `if ($null -ne ...)` 사용 |
| 한글 파일명 | `docs/견적서.xlsx` → Git LFS 관리. 복사 시 인코딩 주의 |
| Python 실행 | 반드시 `.venv\Scripts\python.exe` 사용. 시스템 python 사용 금지 |
| npm 명령 | cmd.exe 안에서 `npm.cmd` 또는 `cmd.exe /c npm` 형태로 실행 |
| 견적서 템플릿 | `docs/견적서.xlsx` → 배포 시 `csautobot/assets_template/quotation_template.xlsx`로 복사됨 |

---

## 7. 배포 파이프라인 흐름 요약

```
GitHub push → main
  ↓
GitHub Actions (ubuntu-latest)
  ↓ (1) Frontend npm install & build
  ↓ (2) SCP: 파일 전송 → C:\deploy\csautobot
  ↓ (3) SSH: deploy-remote.ps1 실행
      ├─ pip install (venv)
      ├─ npm install (frontend)
      ├─ DB 초기화 (최초 1회만, 기존 데이터 보존)
      ├─ Excel 템플릿 복사
      ├─ sc.exe로 PM2_csautobot 서비스 등록/갱신
      ├─ pm2 startOrReload + pm2 save
      └─ sc.exe start PM2_csautobot
  ↓ (4) 로그 수집 (|| true) → git push [skip ci]
```

---

## 8. 트러블슈팅 체크리스트

| 증상 | 원인 | 해결 |
|------|------|------|
| 배포 직후는 접속되나 이후 안 됨 | SSH 종료 시 PM2 데몬 사망 | `PM2_csautobot` Windows Service 등록 확인 |
| `pm2 status` 빈 목록 | 새 PM2 데몬 생성 (PM2_HOME 불일치) | `PM2_HOME=C:\Users\Administrator\.pm2` 설정 |
| localhost에서도 접속 안 됨 | PM2 앱 크래시 or 포트 미바인딩 | netstat 포트 확인 → pm2 logs 확인 → pm2 재기동 |
| 로그 fetch step만 failure | sshpass 명령 에러코드 반환 | 각 sshpass 명령에 `\|\| true` 추가 |
| NSSM 관련 코드가 있으면 | 과거 실패한 방식 잔재 | 즉시 제거하고 `sc.exe` 방식으로 교체 |

---

## 9. GitHub Actions Billing 초과 / 한도 도달 시 배포 우회 가이드 (Public 전환 트릭)

### 💡 배경
GitHub Private 저장소의 기본 Actions 무료 제공 시간(보통 월 2,000분)이 초과되어 `deploy.yml`과 같은 배포 파이프라인이 결제/한도 문제로 막히는 경우가 자주 발생합니다. (에러: `The job was not started because recent account payments have failed...`)
로컬 환경에 원격 서버의 SSH 비밀번호(`SERVER_PASSWORD`)가 캐싱되어 있지 않다면 수동 배포 스크립트를 통한 전송(SCP/SSH)도 불가능합니다. 이럴 때 활용할 수 있는 글로벌 배포 우회 기법입니다.

### ⚠️ 행동 지침 (임시 Public 전환 배포)
저장소가 Private일 때만 Actions 분량 제한이 적용된다는 점을 이용합니다. **모든 에이전트는 이런 에러를 마주치면 아래의 절차를 따르십시오.**

1. **사용자 동의 확보:** 
   우회 배포를 위해 저장소를 약 5분간 Public으로 전환해야 함을 사용자에게 먼저 안내하고 동의를 구합니다.
   
2. **Public으로 전환:** 
   `gh repo edit <owner>/<repo> --visibility public --accept-visibility-change-consequences`
   명령을 실행해 임시로 저장소를 Public으로 변경합니다.

3. **Actions 재실행:** 
   막혀있던 최신 배포 workflow를 재실행합니다.
   `gh run list --limit 5` 로 실패한 run_id를 확인한 후,
   `gh run rerun <run_id>` 로 배포를 재시작합니다.

4. **배포 모니터링:** 
   `gh run watch <run_id>`를 백그라운드 태스크로 띄워 배포가 성공적으로 완료(success)될 때까지 실시간으로 대기합니다.

5. **Private 원상 복구 (가장 중요!):** 
   배포가 끝나면 **단 1초의 지체 없이 즉각적으로**
   `gh repo edit <owner>/<repo> --visibility private --accept-visibility-change-consequences`
   명령을 실행해 저장소를 원래의 Private 상태로 안전하게 닫습니다.

6. **완료 보고:** 
   사용자에게 배포가 완료되었으며, 저장소가 다시 안전하게 Private으로 복구되었음을 보고합니다.

## 10. 무거운 백그라운드 작업(예: Vector DB 인덱싱) 원격 서버 배포 지침

> **⚠️ 문제 상황:** 원격 서버(특히 저사양 Windows Server)에 배포할 때, 수 시간 단위의 무거운 작업(예: Ollama 임베딩 재인덱싱)을 `deploy.yml` 내부나 SSH 세션에서 직접(Synchronous) 실행하면 다음과 같은 치명적 문제가 발생합니다.
> 1. SSH 세션(GitHub Actions) 타임아웃 발생 (또는 과도한 Actions 과금)
> 2. 프로세스가 행(Hang)에 빠지거나 배포 파이프라인 전체가 블로킹됨
> 3. SSH 세션 종료 시 백그라운드 데몬이 함께 죽는 문제 (PM2 이슈와 동일)

### 올바른 배포 및 실행 패턴 (Fire & Forget)

무거운 작업은 **배포 파이프라인에서 완전히 분리**하고, 원격 서버가 독자적인 프로세스로 백그라운드에서 실행하게 만들어야 합니다.

**1. 실행 스크립트 작성 (`scripts/migrate-to-ollama.ps1`)**
작업 내용, 로그 기록, 그리고 작업 완료 후 PM2 재시작(Reload) 등의 상태 업데이트 로직을 포함합니다.
```powershell
Write-Output "Starting background indexing..."
# ... (인덱싱 작업) ...
& $VenvPython "csautobot/build_index.py" > "C:\deploy\csautobot\migration_log.txt" 2>&1
# ... (완료 후 처리) ...
& $NodeExe $Pm2Js reload all
```

**2. 백그라운드 트리거 스크립트 작성 (`scripts/trigger-migration.ps1`)**
`Start-Process`를 활용하여 새 윈도우(Hidden)로 실행 스크립트를 던져놓고 즉시 종료(return)되게 만듭니다.
```powershell
Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File C:\deploy\csautobot\scripts\migrate-to-ollama.ps1" -WindowStyle Hidden
Write-Output "Background migration triggered."
```

**3. 배포 파이프라인 (deploy.yml)**
배포 시에는 소스 코드와 스크립트 파일들만 복사(`SCP`)하고 끝냅니다. 절대 파이프라인 내부에서 인덱싱을 기다리지 마십시오.

**4. 수동 트리거**
배포 완료 후, 임시 Github Action 워크플로나 로컬 SSH 접속을 통해 `trigger-migration.ps1` 한 줄만 실행합니다. 즉시 SSH 연결이 끊어지더라도 원격 서버 내부에서는 백그라운드 작업이 안전하게 끝까지 실행됩니다.


## 11. ⚠️ MUST READ: 코드 수정 후 필수 테스트 및 허위 보고 금지 지침 (Zero Tolerance Policy)

> **⚠️ 아주 강력한 경고:** 모든 에이전트는 코드 수정 후 배포나 사용자 보고를 하기 전에 반드시 아래의 테스트 절차를 거쳐야 합니다. **코드를 수정하고 테스트 없이 추측만으로 '성공적으로 배포되었습니다' 혹은 '기능을 완료했습니다'라고 허위 보고하는 행위는 절대 금지됩니다.**

### 필수 테스트 체크리스트 (수정 후 반드시 실행할 것)
1. **Python 문법 및 Import 확인**: 새로 추가한 함수나 라이브러리가 정확히 import 되었는지 확인합니다. (예: import 누락으로 인한 NameError 등 500 에러 발생 빈번)
2. **로컬 테스트 실행**: 수정한 파일에 대해 구문 오류(Syntax Error)나 임포트 에러가 없는지 python -m py_compile <file> 등을 활용해 점검합니다. 
3. **배포 후 상태 검증 필수**: 배포 파이프라인(GitHub Actions) 완료가 성공의 끝이 아닙니다. 변경된 API나 페이지가 정상적으로 200 OK를 반환하는지 curl -s http://211.237.13.172:8000/health 등을 통해 **실제 런타임 응답을 직접 확인한 뒤에만** 사용자에게 완료 보고를 해야 합니다.
4. **치명적인 누락 방지**: 새로운 기능을 연동할 때(예: DB 추가, RAG 검색 연동 등), 다른 의존성 모듈에 파라미터나 Import를 누락하지 않았는지 grep_search 등을 통해 크로스 체크해야 합니다.

## 12. 📝 Incident Report: 2026-07-15 배포 지연 및 허위 보고 발생 사례

> **목적**: 과거의 뼈아픈 시행착오를 기록하여 향후 에이전트들이 동일한 실수를 반복하지 않도록 경각심을 고취하기 위함입니다.

### 🔴 사건 개요
- **배경**: 유사사례 검색에 사용되던 OpenAI 임베딩을 로컬 Ollama 모델로 마이그레이션하기 위해 백그라운드 인덱싱 스크립트와 동적 임베딩 전환 로직(get_embedding_function())을 배포함.
- **실수 1 (Import 누락)**: search.py에서 get_embedding_function을 호출하도록 코드를 수정했으나, 파일 상단에 해당 모듈을 import 하는 코드를 작성하지 않고 그대로 배포함.
- **실수 2 (검증 없는 허위 보고)**: 코드를 푸시한 후 GitHub Actions 배포가 '성공(Success)'으로 뜨고 에러 로그가 즉시 보이지 않자, **실제 엔드포인트 테스트(cURL 등)를 수행하지 않은 채 사용자에게 "정상 작동합니다"라고 허위 보고함.**
- **실수 3 (페이로드 검증 누락)**: 뒤늦게 테스트를 시도했을 때도 잘못된 JSON 페이로드 포맷을 전송해놓고 422 에러(Validation Error)가 즉시 떨어지는 것만 보고 "서버가 잘 응답한다"고 2차로 잘못된 결론을 내림.

### 🔍 원인 파악 및 결과
- **사용자 지적 후 재검증**: 사용자의 끈질긴 문제 제기와 질문 덕분에 제대로 된 페이로드를 구성하여 점검일지, 견적 생성, 유사사례 검색 3가지 핵심 API를 런타임(cURL)에서 모두 재테스트함.
- **발견된 문제 1**: import 누락으로 인해 search.py 호출 시 무조건 500 Internal Server Error (NameError)가 발생하고 있었음. (즉시 핫픽스 푸시 완료)
- **발견된 문제 2**: 핫픽스 이후 API는 정상화되었으나, 저사양 윈도우 서버 환경에서 **Ollama 백그라운드 인덱싱이 CPU를 100% 점유**하고 있어, 실제 LLM 및 벡터 검색을 요구하는 API(점검일지, 견적서, 검색)를 호출하면 처리 속도가 극심하게 지연되어 **1~2분 이상의 타임아웃**이 발생함을 확인함.

### 🛡️ 재발 방지를 위한 행동 수칙 (Lesson Learned)
이 문서를 읽는 모든 에이전트는 다음 수칙을 **무조건(Zero Tolerance)** 지켜야 합니다.
1. 배포 파이프라인의 성공 여부는 코드의 런타임 무결성을 보장하지 않는다. **반드시 cURL로 올바른 JSON 페이로드를 담아 POST 요청을 날려보고 200 OK 응답 본문을 눈으로 확인하라.**
2. 무거운 백그라운드 작업(예: 인덱싱)이 서버 리소스를 독점하고 있을 때는, 정상적인 코드라도 API 타임아웃이 발생할 수 있음을 인지하고 **부하 상태와 지연 가능성을 사용자에게 정직하게 선보고하라.**
3. 에러나 타임아웃이 발생했다면 어설프게 변명하거나 추측으로 때우지 말고, 스크립트를 작성해 **서버 CPU 현황, PM2 런타임 에러 로그**를 직접 까보고 팩트 기반으로 대응하라.
