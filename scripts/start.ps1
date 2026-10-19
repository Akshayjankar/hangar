# scripts/start.ps1 - Start Hangar server
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = "$Root\backend"

& "$Root\.venv\Scripts\python.exe" -m hangar @args

