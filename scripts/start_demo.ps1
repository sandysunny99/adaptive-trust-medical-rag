# Start the live app for a demo: backend, wait until it is ready, check the model catalog, then the frontend.
# Usage (from the repository root):  powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1
# Reads no .env file itself; the backend loads .env.local / .env on its own. Logs go to logs\.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$logs = Join-Path $root 'logs'
New-Item -ItemType Directory -Force $logs | Out-Null

# Old servers left on these ports make a restart talk to stale code or fail to bind.
foreach ($port in 8000, 5173) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Write-Host "Stopping old process $($_.OwningProcess) on port $port"; Stop-Process -Id $_.OwningProcess -Force }
}

Write-Host 'Starting backend on http://127.0.0.1:8000 (first start takes about a minute)...'
Start-Process -WindowStyle Minimized -FilePath uv -WorkingDirectory $root `
    -ArgumentList 'run','python','-m','uvicorn','--app-dir','src','adaptive_trust_medical_rag.api.app:app','--host','127.0.0.1','--port','8000' `
    -RedirectStandardError (Join-Path $logs 'backend.log') -RedirectStandardOutput (Join-Path $logs 'backend.out.log')

$deadline = (Get-Date).AddSeconds(180)
$ready = $false
while ((Get-Date) -lt $deadline) {
    try { $r = Invoke-RestMethod http://127.0.0.1:8000/health/ready -TimeoutSec 3; if ($r.status -eq 'ready') { $ready = $true; break } } catch {}
    Start-Sleep 2
}
if (-not $ready) { Write-Host "Backend did not become ready in 180 s. See $logs\backend.log" -ForegroundColor Red; exit 1 }

Write-Host "`nProviders the backend registered:"
Select-String -Path (Join-Path $logs 'backend.log') -Pattern 'LLM providers \(in order\)|Vision extraction:|is not configured|No vision API key' |
    ForEach-Object { '  ' + ($_.Line -replace '^.*?api\.app: ', '') }

Write-Host "`nModel catalog shown in the app:"
(Invoke-RestMethod http://127.0.0.1:8000/api/v1/llm/models).models | Where-Object provider -ne 'mock' |
    ForEach-Object { '  {0,-38} {1}' -f $_.name, $(if ($_.is_available) { 'available' } else { 'not configured' }) }

Write-Host "`nStarting frontend on http://localhost:5173 ..."
Start-Process -WindowStyle Minimized -FilePath cmd.exe -WorkingDirectory (Join-Path $root 'frontend') `
    -ArgumentList '/c','npm run dev -- --port 5173 --strictPort > ..\logs\frontend.log 2>&1'
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
    try { Invoke-WebRequest -UseBasicParsing http://localhost:5173/api/v1/llm/models -TimeoutSec 3 | Out-Null; break } catch { Start-Sleep 2 }
}
Start-Process http://localhost:5173
Write-Host 'Ready. To stop: close the two minimized windows, or run this script again (it stops old servers first).'
