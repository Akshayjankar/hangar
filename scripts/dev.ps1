# scripts/dev.ps1 - Launch the app on a configurable localhost port
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$env:HANGAR_PORT = if ($env:HANGAR_PORT) { $env:HANGAR_PORT } else { "7777" }
$env:PYTHONPATH = "$Root\backend"
$env:HANGAR_DEV_ORIGIN = "http://localhost:3000"
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:$($env:HANGAR_PORT)"
$env:NEXT_PUBLIC_WS_URL = "ws://127.0.0.1:$($env:HANGAR_PORT)/ws"

# Add portable node if local
if (Test-Path "$Root\.tools\node-v20.18.0-win-x64") {
    $env:PATH = "$Root\.tools\node-v20.18.0-win-x64;$env:PATH"
}

Write-Host "Starting Hangar dev servers on port $($env:HANGAR_PORT)..." -ForegroundColor Cyan

$backend = Start-Process -FilePath "$Root\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "hangar.main:app", "--reload", "--host", "127.0.0.1", "--port", $env:HANGAR_PORT -PassThru -NoNewWindow
$frontend = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev", "--prefix", "$Root\frontend" -PassThru -NoNewWindow

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
}

