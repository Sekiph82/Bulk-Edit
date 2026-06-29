# scripts/windows/ensure-env.ps1
# Appends missing placeholder env vars to .env without duplicates or overwrites.
# Called by setup-and-start.bat. Must run from repo root.

$envFile = ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "[WARN] .env not found — skipping placeholder check."
    exit 0
}

$required = @(
    "VIDEO_RENDERER_ENABLED=false",
    "FFMPEG_PATH=",
    "VIDEO_OUTPUT_DIR=",
    "PINTEREST_CLIENT_ID=",
    "PINTEREST_CLIENT_SECRET=",
    "PINTEREST_REDIRECT_URI=http://localhost:8100/api/v1/promote/pinterest/callback",
    "META_APP_ID=",
    "META_APP_SECRET=",
    "INSTAGRAM_REDIRECT_URI=http://localhost:8100/api/v1/promote/instagram/callback"
)

$content = Get-Content $envFile -Raw -ErrorAction SilentlyContinue
if ($null -eq $content) { $content = "" }

$appended = 0
foreach ($line in $required) {
    $key = ($line -split "=")[0]
    $keyPattern = "(?m)^$([regex]::Escape($key))="
    if ($content -notmatch $keyPattern) {
        Add-Content -Path $envFile -Value $line -Encoding UTF8
        $appended++
    }
}

if ($appended -gt 0) {
    Write-Host "[OK] Appended $appended missing placeholder(s) to .env."
} else {
    Write-Host "[OK] All required placeholders already in .env."
}
