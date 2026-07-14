# csautobot 수동 배포 — .github/workflows/deploy.yml 와 동일한 절차를 로컬 PC에서 실행
# GitHub Actions Billing 장애 시 사용 (aiCsms/aiCallCenter의 deploy-manual.ps1과 동일 패턴).
#
#   $env:DEPLOY_SSH_USER = "<SERVER_USER>"
#   $env:DEPLOY_SSH_PASSWORD = "<SERVER_PASSWORD>"
#   .\scripts\deploy-manual.ps1                     # full (frontend 빌드 포함, ~15~30분)
#   .\scripts\deploy-manual.ps1 -SkipFrontendBuild  # 로컬 npm build 생략
#   .\scripts\deploy-manual.ps1 -IncludeEnv         # .env(API 키)도 재업로드 (기본은 서버 기존 .env 보존)
#
# API 키를 .env에 새로 반영해야 할 때는 -IncludeEnv 와 함께 아래 환경변수를 설정:
#   OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, TAVILY_API_KEY, LANGSMITH_API_KEY, JWT_SECRET_KEY
#
# pm2 kill / pm2 delete all 금지 — csautobot-backend/frontend 만 재시작.
# 서버 데이터(csautobot.db, chroma_db) 보존 — deploy-remote.ps1이 이미 존재하면 건드리지 않음.
param(
    [string]$HostName = "211.237.13.172",
    [int]$Port = 20022,
    [string]$RemoteDir = "C:/deploy/csautobot",
    [switch]$SkipFrontendBuild,
    [switch]$IncludeEnv
)

$ErrorActionPreference = "Stop"
Import-Module Posh-SSH -ErrorAction Stop

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

$user = $env:DEPLOY_SSH_USER
if (-not $user) { $user = $env:SERVER_USER }
$pass = $env:DEPLOY_SSH_PASSWORD
if (-not $pass) { $pass = $env:SERVER_PASSWORD }
if (-not $user -or -not $pass) {
    throw "DEPLOY_SSH_USER / DEPLOY_SSH_PASSWORD 환경변수가 필요합니다."
}

$secure = ConvertTo-SecureString $pass -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ($user, $secure)

if (-not $SkipFrontendBuild) {
    Write-Host "[build] frontend npm install + build..." -ForegroundColor Yellow
    Push-Location (Join-Path $RepoRoot "frontend")
    try {
        if (Test-Path "package-lock.json") { npm ci } else { npm install --legacy-peer-deps }
        if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "npm run build failed" }
    } finally {
        Pop-Location
    }
    Remove-Item -Recurse -Force (Join-Path $RepoRoot "frontend\node_modules") -ErrorAction SilentlyContinue
}

$Stage = Join-Path $env:TEMP "csautobot-deploy-$(Get-Date -Format 'yyyyMMddHHmmss')"
New-Item -ItemType Directory -Path $Stage -Force | Out-Null

function Copy-DeployTree {
    param([string]$Name)
    $src = Join-Path $RepoRoot $Name
    $dst = Join-Path $Stage $Name
    if (-not (Test-Path $src)) { throw "Missing: $src" }
    $robocopyArgs = @(
        $src, $dst, "/E",
        "/XD", "node_modules", "__pycache__", ".pytest_cache", "chroma_db", ".git", ".claude", ".venv",
        "/XF", ".env", "*.pyc", "csautobot.db", "auth.db",
        "/NFL", "/NDL", "/NJH", "/NJS", "/nc", "/ns", "/np"
    )
    & robocopy @robocopyArgs | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed for $Name (exit $LASTEXITCODE)" }
}

Copy-DeployTree "csautobot"
Copy-DeployTree "scripts"
Copy-DeployTree "frontend"
Copy-Item (Join-Path $RepoRoot "requirements-prod.txt") (Join-Path $Stage "requirements-prod.txt")
Copy-Item (Join-Path $RepoRoot "ecosystem.config.js") (Join-Path $Stage "ecosystem.config.js")
if (Test-Path (Join-Path $RepoRoot "csautobot_initial.db")) {
    Copy-Item (Join-Path $RepoRoot "csautobot_initial.db") (Join-Path $Stage "csautobot_initial.db")
}

if ($IncludeEnv) {
    Write-Host "[env] .env 재생성 — 서버 기존 값을 덮어씁니다" -ForegroundColor Yellow
    $envLines = @()
    foreach ($key in @("OPENAI_API_KEY","ANTHROPIC_API_KEY","GOOGLE_API_KEY","TAVILY_API_KEY","LANGSMITH_API_KEY","JWT_SECRET_KEY")) {
        $val = [System.Environment]::GetEnvironmentVariable($key)
        if ($val) { $envLines += "$key=$val" }
    }
    $envLines += "LANGSMITH_TRACING=true"
    $envLines += "LANGSMITH_ENDPOINT=https://api.smith.langchain.com"
    $envLines += "LANGSMITH_PROJECT=ragproject"
    $Utf8NoBom = New-Object System.Text.UTF8Encoding $False
    [System.IO.File]::WriteAllLines((Join-Path $Stage ".env"), $envLines, $Utf8NoBom)
}

Write-Host "=== csautobot manual deploy ===" -ForegroundColor Cyan
Write-Host "Stage: $Stage"
Write-Host "Target: ${user}@${HostName}:${Port} -> $RemoteDir"

Write-Host "[1/5] SSH connect..." -ForegroundColor Yellow
$session = New-SSHSession -ComputerName $HostName -Port $Port -Credential $cred -AcceptKey -ConnectionTimeout 30
if (-not $session) { throw "SSH session failed" }
$ZipPath = $null

try {
    Write-Host "[2/5] Stop csautobot PM2 apps..." -ForegroundColor Yellow
    $stopCmd = @"
powershell -Command "Stop-Process -Name excel -EA SilentlyContinue"
sc.exe stop PM2_csautobot 2>nul
cmd /c "set PM2_HOME=C:\Users\Administrator\.pm2&& pm2 stop csautobot-backend csautobot-frontend 2>nul & exit 0"
cmd /c "set PM2_HOME=C:\Users\Administrator\.pm2&& pm2 delete csautobot-backend csautobot-frontend 2>nul & exit 0"
powershell -Command "Start-Sleep -Seconds 3"
"@
    Invoke-SSHCommand -SessionId $session.SessionId -Command $stopCmd | Out-Null

    Write-Host "[3/5] Ensure remote dir..." -ForegroundColor Yellow
    Invoke-SSHCommand -SessionId $session.SessionId -Command "powershell -Command `"New-Item -ItemType Directory -Force -Path '$RemoteDir' | Out-Null`"" | Out-Null

    Write-Host "[4/5] Upload bundle (zip — Posh-SSH folder upload bug workaround)..." -ForegroundColor Yellow
    $ZipPath = Join-Path $env:TEMP "csautobot-deploy-$(Get-Date -Format 'yyyyMMddHHmmss').zip"
    if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
    Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $ZipPath -CompressionLevel Fastest
    $ZipName = Split-Path $ZipPath -Leaf
    $RemoteZip = "$RemoteDir/$ZipName"
    Set-SCPItem -ComputerName $HostName -Port $Port -Credential $cred -Path $ZipPath -Destination $RemoteDir -AcceptKey
    $extract = Invoke-SSHCommand -SessionId $session.SessionId -TimeOut 600 -Command @"
powershell -NoProfile -Command "`$z='$RemoteZip'; `$d='$RemoteDir'; Expand-Archive -Path `$z -DestinationPath `$d -Force; Remove-Item -Force `$z"
"@
    if ($extract.ExitStatus -ne 0) {
        if ($extract.Error) { Write-Host $extract.Error -ForegroundColor Red }
        throw "Expand-Archive on server failed (exit $($extract.ExitStatus))"
    }
    Remove-Item -Force $ZipPath -ErrorAction SilentlyContinue

    Write-Host "[5/5] deploy-remote.ps1 (pip install/venv/pm2 — up to ~30m)..." -ForegroundColor Yellow
    $deploy = Invoke-SSHCommand -SessionId $session.SessionId -TimeOut 3600 -Command "powershell -NoProfile -ExecutionPolicy Bypass -File `"$RemoteDir/scripts/deploy-remote.ps1`""
    if ($deploy.Output) { $deploy.Output | ForEach-Object { Write-Host $_ } }
    if ($deploy.ExitStatus -ne 0) {
        if ($deploy.Error) { Write-Host $deploy.Error -ForegroundColor Red }
        throw "deploy-remote.ps1 failed (exit $($deploy.ExitStatus))"
    }
} finally {
    Remove-SSHSession -SessionId $session.SessionId -ErrorAction SilentlyContinue | Out-Null
    Remove-Item -Recurse -Force $Stage -ErrorAction SilentlyContinue
    Remove-Item -Force $ZipPath -ErrorAction SilentlyContinue
}

Write-Host "[health] checking backend/frontend..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
foreach ($check in @(@{Url="http://211.237.13.172:8000/health"; Name="backend"}, @{Url="http://211.237.13.172:5000/"; Name="frontend"})) {
    try {
        $r = Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 30
        Write-Host "Health OK: $($check.Name) -> $($r.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Warning "$($check.Name) health check failed: $($_.Exception.Message)"
    }
}

Write-Host "=== Deploy complete ===" -ForegroundColor Cyan
