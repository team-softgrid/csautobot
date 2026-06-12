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

function Resolve-PythonExecutable {
    param(
        [AllowEmptyString()]
        [string]$RequestedPython = ""
    )

    if (-not [string]::IsNullOrWhiteSpace($RequestedPython)) {
        if (Test-Path -LiteralPath $RequestedPython) {
            return (Resolve-Path -LiteralPath $RequestedPython).Path
        }
        throw "CSAUTOBOT_PYTHON points to a missing file: $RequestedPython"
    }

    $CandidatePaths = @(
        "C:\Python312\python.exe",
        "C:\PYTHON312\PYTHON.EXE",
        "C:\Python311\python.exe",
        "C:\PYTHON311\PYTHON.EXE",
        "C:\PYTHON314\PYTHON.EXE"
    )

    foreach ($Candidate in $CandidatePaths) {
        if (Test-Path -LiteralPath $Candidate) {
            return (Resolve-Path -LiteralPath $Candidate).Path
        }
    }

    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $PyLauncher) {
        foreach ($Version in @("3.12", "3.11", "3.14", "3")) {
            $Output = & $PyLauncher.Source "-$Version" "-c" "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $Output) {
                $Resolved = [string]($Output | Select-Object -Last 1)
                if (Test-Path -LiteralPath $Resolved) {
                    return (Resolve-Path -LiteralPath $Resolved).Path
                }
            }
        }
    }

    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $PythonCommand) {
        return $PythonCommand.Source
    }

    throw "Python executable not found. Install Python 3.11+ or set CSAUTOBOT_PYTHON."
}

function Get-PythonVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExecutable
    )

    $Version = & $PythonExecutable -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Version)) {
        throw "Unable to read Python version from $PythonExecutable"
    }
    return [string]($Version | Select-Object -Last 1)
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

$DeployRoot = $env:CSAUTOBOT_DEPLOY_ROOT
if ([string]::IsNullOrWhiteSpace($DeployRoot)) {
    $DeployRoot = "C:\deploy\csautobot"
}

$BasePythonExecutable = Resolve-PythonExecutable -RequestedPython $env:CSAUTOBOT_PYTHON
$BasePythonVersion = Get-PythonVersion -PythonExecutable $BasePythonExecutable
$VersionParts = $BasePythonVersion.Split(".")
$Major = [int]$VersionParts[0]
$Minor = [int]$VersionParts[1]

if ($Major -ne 3 -or $Minor -lt 11) {
    throw "Python 3.11+ is required. Found $BasePythonVersion at $BasePythonExecutable."
}
if ($Minor -ge 13) {
    Write-Host "Warning: Python $BasePythonVersion is newer than the local project target. Using production requirements with flexible versions."
}

$VenvPath = Join-Path $DeployRoot ".venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$RequirementsPath = Join-Path $DeployRoot "requirements-prod.txt"

if (-not (Test-Path -LiteralPath $RequirementsPath)) {
    throw "Production requirements file not found: $RequirementsPath"
}

$env:CSAUTOBOT_DEPLOY_ROOT = $DeployRoot
$env:CSAUTOBOT_PYTHON = $VenvPython

Write-Host "Deploy root: $DeployRoot"
Write-Host "Base Python: $BasePythonExecutable ($BasePythonVersion)"
Write-Host "App Python: $VenvPython"
Write-Host "Requirements: $RequirementsPath"

$EnvPath = Join-Path $DeployRoot ".env"

Set-DotEnvValue -Path $EnvPath -Key "OPENAI_API_KEY" -Value $env:OPENAI_API_KEY
Set-DotEnvValue -Path $EnvPath -Key "ANTHROPIC_API_KEY" -Value $env:ANTHROPIC_API_KEY
Set-DotEnvValue -Path $EnvPath -Key "GOOGLE_API_KEY" -Value $env:GOOGLE_API_KEY
Set-DotEnvValue -Path $EnvPath -Key "TAVILY_API_KEY" -Value $env:TAVILY_API_KEY
Set-DotEnvValue -Path $EnvPath -Key "LANGSMITH_API_KEY" -Value $env:LANGSMITH_API_KEY
Set-DotEnvValue -Path $EnvPath -Key "LANGSMITH_TRACING" -Value "true"
Set-DotEnvValue -Path $EnvPath -Key "LANGSMITH_ENDPOINT" -Value "https://api.smith.langchain.com"
Set-DotEnvValue -Path $EnvPath -Key "LANGSMITH_PROJECT" -Value "ragproject"

if (-not (Test-DotEnvKey -Path $EnvPath -Key "OPENAI_API_KEY")) {
    throw "OPENAI_API_KEY is not configured. Add it to GitHub Actions secrets or $EnvPath before deploying."
}
Write-Host "OPENAI_API_KEY configuration: present"

Push-Location $DeployRoot
try {
    $Pm2Command = Get-Command pm2 -ErrorAction SilentlyContinue
    if ($null -eq $Pm2Command) {
        Invoke-Checked "npm" @("install", "-g", "pm2")
    }
    else {
        Write-Host "PM2 found: $($Pm2Command.Source)"
    }
}
finally {
    Pop-Location
}

Push-Location $DeployRoot
try {
    Write-Host "Creating C:\tmp for short temp path to avoid Long Path errors..."
    New-Item -ItemType Directory -Force -Path "C:\tmp" -ErrorAction SilentlyContinue | Out-Null
    $env:TMP = "C:\tmp"
    $env:TEMP = "C:\tmp"

    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Write-Host "Creating isolated virtual environment..."
        Invoke-Checked $BasePythonExecutable @("-m", "venv", $VenvPath)
    }

    Invoke-Checked $VenvPython @("-m", "pip", "install", "--disable-pip-version-check", "--upgrade", "pip", "setuptools", "wheel")
    Invoke-Checked $VenvPython @("-m", "pip", "install", "--disable-pip-version-check", "--upgrade", "--prefer-binary", "-r", $RequirementsPath)
}
finally {
    Pop-Location
}

Push-Location $DeployRoot
try {
    $ChromaZip = Join-Path $DeployRoot "csautobot\chroma_db.zip"
    $ChromaDir = Join-Path $DeployRoot "csautobot\chroma_db"

    if ((Test-Path -LiteralPath $ChromaZip) -and -not (Test-Path -LiteralPath $ChromaDir)) {
        Write-Output "chroma_db not found. Extracting initial vector DB from zip..."
        New-Item -ItemType Directory -Force -Path $ChromaDir | Out-Null
        Expand-Archive -Path $ChromaZip -DestinationPath $ChromaDir -Force
        Write-Output "Vector DB extraction complete."

        $ActiveChromaPath = Join-Path $DeployRoot "csautobot\active_chroma_dir.txt"
        $Utf8NoBom = New-Object System.Text.UTF8Encoding $False
        [System.IO.File]::WriteAllText($ActiveChromaPath, $ChromaDir, $Utf8NoBom)
        Write-Output "active_chroma_dir.txt updated to: $ChromaDir"
    }
    elseif (Test-Path -LiteralPath $ChromaDir) {
        Write-Output "chroma_db already exists; skipping zip extraction to preserve production data."
    }

    Remove-Item -Recurse -Force (Join-Path $DeployRoot "csautobot\__pycache__") -ErrorAction SilentlyContinue

    Invoke-Checked "pm2" @("startOrReload", "ecosystem.config.js", "--update-env")

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

    Invoke-Checked "pm2" @("save")
    pm2 status
}
finally {
    Pop-Location
}
