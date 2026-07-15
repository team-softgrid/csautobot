Write-Output "Starting background Ollama indexing..."
$DeployRoot = "C:\deploy"
$CsautobotDir = Join-Path $DeployRoot "csautobot"
$VenvPython = Join-Path $CsautobotDir ".venv\Scripts\python.exe"

Set-Location -Path $CsautobotDir

# 1. Run indexing with Ollama
$env:USE_OLLAMA_EMBEDDING = "true"
Write-Output "Running build_index.py to reindex with Ollama (this will take 2-3 hours)..."
& $VenvPython "csautobot/build_index.py" > "C:\deploy\csautobot\ollama_migration_log.txt" 2>&1
$LASTEXITCODE = $?

if (-not $LASTEXITCODE) {
    Write-Output "Indexing failed! See ollama_migration_log.txt for details."
    exit 1
}

Write-Output "Indexing completed successfully!"

# 2. Update .env to use Ollama by default
$EnvPath = Join-Path $CsautobotDir ".env"
Add-Content -Path $EnvPath -Value "`nUSE_OLLAMA_EMBEDDING=true"
Write-Output "Added USE_OLLAMA_EMBEDDING=true to .env"

# 3. Reload PM2
Write-Output "Reloading PM2 apps..."
$NpmGlobalRoot = (cmd.exe /c "npm root -g").Trim()
$Pm2Js = "$NpmGlobalRoot\pm2\bin\pm2"
$NodeExe = "C:\Program Files\nodejs\node.exe"
$env:PM2_HOME = "C:\Users\Administrator\.pm2"

& $NodeExe $Pm2Js reload csautobot-backend csautobot-frontend --update-env

Write-Output "Migration complete! The service is now using Ollama."

