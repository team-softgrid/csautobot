$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $false)]
        [string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath $($Arguments -join ' ') failed with exit code $LASTEXITCODE."
    }
}

function Set-DotEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Key,
        [AllowEmptyString()]
        [string]$Value = ""
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return
    }

    $Lines = @()
    if (Test-Path -LiteralPath $Path) {
        $Lines = @(Get-Content -LiteralPath $Path)
    }

    $Pattern = "^\s*$([regex]::Escape($Key))\s*="
    $Updated = $false
    $Lines = @($Lines | ForEach-Object {
        if ($_ -match $Pattern) {
            $Updated = $true
            "$Key=$Value"
        }
        else {
            $_
        }
    })

    if (-not $Updated) {
        $Lines += "$Key=$Value"
    }

    $Utf8NoBom = New-Object System.Text.UTF8Encoding $False
    [System.IO.File]::WriteAllLines($Path, $Lines, $Utf8NoBom)
}

function Test-DotEnvKey {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Key
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    $Pattern = "^\s*$([regex]::Escape($Key))\s*=\s*\S+"
    return [bool](Select-String -LiteralPath $Path -Pattern $Pattern -Quiet)
}

# ─── 배포 경로 설정 ───────────────────────────────────────────────────
$DeployRoot = $env:CSAUTOBOT_DEPLOY_ROOT
if ([string]::IsNullOrWhiteSpace($DeployRoot)) {
    $DeployRoot = "C:\deploy\csautobot"
}

$PythonExecutable = $env:CSAUTOBOT_PYTHON
if ([string]::IsNullOrWhiteSpace($PythonExecutable)) {
    $PythonExecutable = "C:\PYTHON314\PYTHON.EXE"
}

if (-not (Test-Path -LiteralPath $PythonExecutable)) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $PythonCommand) {
        throw "Python executable not found. Set CSAUTOBOT_PYTHON or install Python at C:\PYTHON314\PYTHON.EXE."
    }
    $PythonExecutable = $PythonCommand.Source
}

$env:CSAUTOBOT_DEPLOY_ROOT = $DeployRoot
$env:CSAUTOBOT_PYTHON = $PythonExecutable

Write-Host "Deploy root: $DeployRoot"
Write-Host "Python: $PythonExecutable"

# ─── .env 시크릿 주입 ─────────────────────────────────────────────────
$EnvPath = Join-Path $DeployRoot ".env"

Set-DotEnvValue -Path $EnvPath -Key "OPENAI_API_KEY" -Value $env:OPENAI_API_KEY
Set-DotEnvValue -Path $EnvPath -Key "ANTHROPIC_API_KEY" -Value $env:ANTHROPIC_API_KEY
Set-DotEnvValue -Path $EnvPath -Key "GOOGLE_API_KEY" -Value $env:GOOGLE_API_KEY
Set-DotEnvValue -Path $EnvPath -Key "TAVILY_API_KEY" -Value $env:TAVILY_API_KEY
Set-DotEnvValue -Path $EnvPath -Key "LANGSMITH_API_KEY" -Value $env:LANGSMITH_API_KEY
Set-DotEnvValue -Path $EnvPath -Key "LANGSMITH_TRACING" -Value "true"
Set-DotEnvValue -Path $EnvPath -Key "LANGSMITH_ENDPOINT" -Value "https://api.smith.langchain.com"
Set-DotEnvValue -Path $EnvPath -Key "LANGSMITH_PROJECT" -Value "ragproject"

$HasOpenAIKey = -not [string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)
if (-not $HasOpenAIKey) {
    Write-Host "Warning: OPENAI_API_KEY is not configured."
} else {
    Write-Host "OPENAI_API_KEY configuration: present"
}

$HasAnthropicKey = -not [string]::IsNullOrWhiteSpace($env:ANTHROPIC_API_KEY)
if (-not $HasAnthropicKey) {
    Write-Host "Warning: ANTHROPIC_API_KEY is not configured."
} else {
    Write-Host "ANTHROPIC_API_KEY configuration: present"
}

if (-not $HasOpenAIKey) {
    $HasOpenAIKey = Test-DotEnvKey -Path $EnvPath -Key "OPENAI_API_KEY"
}
if (-not $HasOpenAIKey) {
    throw "OPENAI_API_KEY is not configured. Add it to GitHub Actions secrets or $EnvPath before deploying."
}

# ─── 기존 PM2 프로세스 중지 ───────────────────────────────────────────
Push-Location $DeployRoot
try {
    Invoke-Checked "npm" @("install", "-g", "pm2")

    pm2 delete csautobot -s
    if ($LASTEXITCODE -ne 0) { $global:LASTEXITCODE = 0 }

    Start-Sleep -Seconds 3
}
finally {
    Pop-Location
}

# ─── pip install ──────────────────────────────────────────────────────
Push-Location $DeployRoot
try {
    Invoke-Checked $PythonExecutable @("-m", "pip", "install", "-r", "requirements-mini.txt")
}
finally {
    Pop-Location
}

# ─── ChromaDB 압축 해제 (최초 배포 시에만) ────────────────────────────
Push-Location $DeployRoot
try {
    $ChromaZip = Join-Path $DeployRoot "csautobot\chroma_db.zip"
    $ChromaDir = Join-Path $DeployRoot "csautobot\chroma_db"

    if ((Test-Path $ChromaZip) -and -not (Test-Path $ChromaDir)) {
        Write-Output "chroma_db not found. Extracting initial Vector DB from zip..."
        New-Item -ItemType Directory -Force -Path $ChromaDir | Out-Null
        Expand-Archive -Path $ChromaZip -DestinationPath $ChromaDir -Force
        Write-Output "Vector DB extraction complete."

        # active_chroma_dir.txt 업데이트 — 상대 경로가 아닌 서버 절대 경로로
        $ActiveChromaPath = Join-Path $DeployRoot "csautobot\active_chroma_dir.txt"
        $Utf8NoBom = New-Object System.Text.UTF8Encoding $False
        [System.IO.File]::WriteAllText($ActiveChromaPath, $ChromaDir, $Utf8NoBom)
        Write-Output "active_chroma_dir.txt updated to: $ChromaDir"
    } elseif (Test-Path $ChromaDir) {
        Write-Output "chroma_db already exists — skipping zip extraction to preserve production data."
    }

    Remove-Item -Recurse -Force (Join-Path $DeployRoot "csautobot\__pycache__") -ErrorAction SilentlyContinue

    # ─── PM2로 앱 시작 ────────────────────────────────────────────────
    Invoke-Checked "pm2" @("start", "ecosystem.config.js", "--update-env")
    Invoke-Checked "pm2" @("save")

    # ─── Health Check ─────────────────────────────────────────────────
    Start-Sleep -Seconds 15
    try {
        $Response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 30 -Uri "http://127.0.0.1:8501/"
        Write-Host "Streamlit health check status: $($Response.StatusCode)"
    }
    catch {
        Write-Host "Streamlit health check failed. Recent PM2 logs:"
        pm2 logs csautobot --lines 80 --nostream
        throw
    }

    pm2 status
}
finally {
    Pop-Location
}
