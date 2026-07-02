# prepare-deploy-secrets.ps1
# Creates the local secrets file from the template (if missing) and opens it for
# the user to fill. Never overwrites an existing filled file. Prints no secrets.
#
# Usage (Claude Code runs this for you):
#   powershell -ExecutionPolicy Bypass -File scripts/prepare-deploy-secrets.ps1

$ErrorActionPreference = 'Stop'

$root     = Split-Path -Parent $PSScriptRoot
$example  = Join-Path $root 'deploy-secrets.local.env.example'
$target   = Join-Path $root 'deploy-secrets.local.env'

if (-not (Test-Path -LiteralPath $example)) {
    Write-Host "ERROR: template not found: deploy-secrets.local.env.example" -ForegroundColor Red
    exit 1
}

if (Test-Path -LiteralPath $target) {
    Write-Host "deploy-secrets.local.env already exists - keeping your current values." -ForegroundColor Yellow
} else {
    Copy-Item -LiteralPath $example -Destination $target
    Write-Host "Created deploy-secrets.local.env from template." -ForegroundColor Green
}

Write-Host ""
Write-Host "File path: $target"
Write-Host ""
Write-Host "NEXT: fill the blanks, SAVE the file, then press Continue/OK in Claude Code."
Write-Host "This file is gitignored and will never be committed."

# Open in Notepad on Windows so the user can fill it without touching a terminal.
if ($env:OS -eq 'Windows_NT') {
    try {
        Start-Process notepad.exe -ArgumentList $target | Out-Null
        Write-Host "Opened in Notepad."
    } catch {
        Write-Host "Could not auto-open Notepad. Open this file manually: $target" -ForegroundColor Yellow
    }
}
