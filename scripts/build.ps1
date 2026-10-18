# scripts/build.ps1 - Build Next.js frontend into static export
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

if (Test-Path "$Root\.tools\node-v20.18.0-win-x64") {
    $env:PATH = "$Root\.tools\node-v20.18.0-win-x64;$env:PATH"
}

Write-Host "Building Hangar frontend static export..." -ForegroundColor Cyan
& npm.cmd run build --prefix "$Root\frontend"
Write-Host "Frontend build complete." -ForegroundColor Green

