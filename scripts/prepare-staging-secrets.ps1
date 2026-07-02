# prepare-staging-secrets.ps1
# Copies the staging env template to the local (gitignored) file and opens it for
# editing. Does NOT validate or provision anything. Prints no secrets.
#
#   powershell -ExecutionPolicy Bypass -File scripts/prepare-staging-secrets.ps1

$ErrorActionPreference = 'Stop'

$root    = Split-Path -Parent $PSScriptRoot
$example = Join-Path $root 'deploy-staging.local.env.example'
$target  = Join-Path $root 'deploy-staging.local.env'

if (-not (Test-Path -LiteralPath $example)) {
    Write-Host "ERROR: template not found: deploy-staging.local.env.example" -ForegroundColor Red
    exit 1
}

if (Test-Path -LiteralPath $target) {
    Write-Host "deploy-staging.local.env already exists - keeping your current values." -ForegroundColor Yellow
} else {
    Copy-Item -LiteralPath $example -Destination $target
    Write-Host "Created deploy-staging.local.env from template." -ForegroundColor Green
}

Write-Host ""
Write-Host "File: $target  (gitignored - never committed)"
Write-Host ""
Write-Host "FILL THESE (required):"
Write-Host "  - DIGITALOCEAN_ACCESS_TOKEN   (DO -> API -> Tokens; read+write)"
Write-Host "  - CLOUDFLARE_API_TOKEN        (CF -> API Tokens; Zone:DNS:Edit + Zone:Read)"
Write-Host "  - CLOUDFLARE_ZONE_ID          (CF -> bulkeditapp.com -> Overview)"
Write-Host "  - CLOUDFLARE_ACCOUNT_ID       (CF -> Overview / Access)"
Write-Host "OPTIONAL (staging/test only): STRIPE_SECRET_KEY (sk_test_ only), ETSY_*, OPENAI/ANTHROPIC, SENTRY_DSN"
Write-Host "AUTO-GENERATED if left blank:  JWT_SECRET, ENCRYPTION_KEY (never printed)"
Write-Host ""
Write-Host "Then run: powershell -ExecutionPolicy Bypass -File scripts/provision-staging.ps1"
Write-Host "Do NOT paste any token into chat. Do NOT commit this file."

if ($env:OS -eq 'Windows_NT') {
    try { Start-Process notepad.exe -ArgumentList $target | Out-Null; Write-Host "Opened in Notepad." }
    catch { Write-Host "Open the file manually: $target" -ForegroundColor Yellow }
}
