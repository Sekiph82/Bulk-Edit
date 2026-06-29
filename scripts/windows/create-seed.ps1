# scripts/windows/create-seed.ps1
# Creates apps/backend/.local-superusers.env with local demo credentials if missing.
# These are intentionally shared local-only demo accounts, not production secrets.
# Called by setup-and-start.bat. Must run from repo root.

$seedFile = "apps/backend/.local-superusers.env"

if (Test-Path $seedFile) {
    Write-Host "[OK] Demo seed file exists."
    exit 0
}

$content = @"
FREE_SUPERUSER_EMAIL=test@example.com
FREE_SUPERUSER_PASSWORD=Test1234!
FREE_SUPERUSER_FULL_NAME=Free Test User
FREE_SUPERUSER_ORG_NAME=Test Shop

PAID_SUPERUSER_EMAIL=test-su@example.com
PAID_SUPERUSER_PASSWORD=Test1234!
PAID_SUPERUSER_FULL_NAME=Paid Test User
PAID_SUPERUSER_ORG_NAME=Super Test Shop
PAID_SUPERUSER_PLAN=pro_monthly
"@

Set-Content -Path $seedFile -Value $content -Encoding UTF8
Write-Host "[OK] Created demo seed file. Accounts seeded automatically on first start."
