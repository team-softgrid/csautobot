Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File C:\deploy\csautobot\scripts\migrate-to-ollama.ps1" -WindowStyle Hidden
Write-Output "Background migration triggered. Check C:\deploy\csautobot\ollama_migration_log.txt for progress."

