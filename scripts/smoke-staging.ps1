# smoke-staging.ps1
# Post-provision smoke test for the STAGING environment. PASS/FAIL/SKIP per check.
# No secrets. Read-only.
#
#   powershell -ExecutionPolicy Bypass -File scripts/smoke-staging.ps1

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$frontend = 'https://staging.bulkeditapp.com'
$api      = 'https://api-staging.bulkeditapp.com'
$health   = "$api/api/v1/health"

$pass = 0; $fail = 0; $skip = 0
function P($t){ Write-Host "  PASS  $t" -ForegroundColor Green; $script:pass++ }
function F($t){ Write-Host "  FAIL  $t" -ForegroundColor Red;   $script:fail++ }
function S($t){ Write-Host "  SKIP  $t" -ForegroundColor Yellow; $script:skip++ }

Write-Host "=== STAGING smoke test ==="

# Backend health endpoints
foreach ($p in @('/api/v1/health','/api/v1/health/ready','/api/v1/health/db','/api/v1/health/redis')) {
    try {
        $r = Invoke-WebRequest -Uri "$api$p" -TimeoutSec 20 -UseBasicParsing
        if ($r.StatusCode -eq 200) { P "$api$p -> 200" } else { F "$api$p -> $($r.StatusCode)" }
    } catch { F "$api$p unreachable ($($_.Exception.Message))" }
}

# CORS: allowed origin
try {
    $h = @{ 'Origin' = $frontend; 'Access-Control-Request-Method' = 'GET' }
    $r = Invoke-WebRequest -Uri $health -Method Options -Headers $h -TimeoutSec 20 -UseBasicParsing
    $acao = $r.Headers['Access-Control-Allow-Origin']
    if ($acao -eq $frontend) { P "CORS allows $frontend" } else { F "CORS Allow-Origin unexpected: '$acao'" }
} catch { F "CORS preflight (allowed) failed ($($_.Exception.Message))" }

# CORS: random origin must NOT be echoed/allowed
try {
    $bad = 'https://evil.example.com'
    $h = @{ 'Origin' = $bad; 'Access-Control-Request-Method' = 'GET' }
    $r = Invoke-WebRequest -Uri $health -Method Options -Headers $h -TimeoutSec 20 -UseBasicParsing
    $acao = $r.Headers['Access-Control-Allow-Origin']
    if ($acao -eq $bad -or $acao -eq '*') { F "CORS wrongly allows $bad (got '$acao')" } else { P "CORS rejects random origin" }
} catch { P "CORS rejects random origin (preflight refused)" }

# Determine whether Cloudflare Access is gating the frontend root.
# Access-protected requests come back as either:
#   - a redirect (3xx) to a *.cloudflareaccess.com login URL, or
#   - a same-origin 200/403 response whose body/headers identify the Access login page
#     (Invoke-WebRequest follows redirects by default, landing on the login page).
$accessGated = $false
$frontendResp = $null
$frontendErr = $null
try {
    $frontendResp = Invoke-WebRequest -Uri $frontend -TimeoutSec 20 -UseBasicParsing
    $bodySnippet = $frontendResp.Content
    $server = $frontendResp.Headers['Server']
    $wwwAuth = $frontendResp.Headers['Www-Authenticate']
    if (($wwwAuth -match 'Cloudflare-Access') -or
        ($bodySnippet -match 'cloudflareaccess\.com') -or
        ($bodySnippet -match 'Cloudflare Access') -or
        ($frontendResp.BaseResponse.ResponseUri.Host -match 'cloudflareaccess\.com')) {
        $accessGated = $true
    }
} catch {
    $frontendErr = $_
    # A raw 302/403 with no auto-follow (or a WebException carrying the response) also indicates gating.
    if ($_.Exception.Response) {
        $respUri = $_.Exception.Response.ResponseUri
        $status = [int]$_.Exception.Response.StatusCode
        if (($respUri -and $respUri.Host -match 'cloudflareaccess\.com') -or $status -eq 403 -or $status -eq 302) {
            $accessGated = $true
        }
    }
}

if ($accessGated) {
    P "staging frontend is Cloudflare Access-gated (unauthenticated request redirected/blocked, no raw app HTML)"
} else {
    if ($frontendResp -and $frontendResp.StatusCode -eq 200 -and $frontendResp.Content -notmatch 'cloudflareaccess\.com') {
        F "staging frontend served raw app HTML unauthenticated (Access not enforcing)"
    } else {
        F "could not determine Access status ($($frontendErr.Exception.Message))"
    }
}

if ($accessGated) {
    # Raw-frontend-body checks are meaningless behind Access (the body is the Access
    # login page, not the app). Skip with a clear reason rather than false-failing.
    S "robots.txt Disallow check - Access-gated, skipped unauthenticated raw frontend checks"
    S "X-Robots-Tag noindex check - Access-gated, skipped unauthenticated raw frontend checks"
} else {
    # Access disabled: fall back to the original raw-HTML checks.
    try {
        $r = Invoke-WebRequest -Uri "$frontend/robots.txt" -TimeoutSec 20 -UseBasicParsing
        if ($r.Content -match 'Disallow:\s*/') { P "robots.txt Disallow: /" } else { F "robots.txt missing Disallow: / (got: $($r.Content.Trim()))" }
    } catch { F "robots.txt unreachable ($($_.Exception.Message))" }

    try {
        $r = Invoke-WebRequest -Uri $frontend -TimeoutSec 20 -UseBasicParsing
        $xr = $r.Headers['X-Robots-Tag']
        if ($xr -and $xr -match 'noindex') { P "X-Robots-Tag: noindex present" } else { F "X-Robots-Tag missing/incorrect (got '$xr')" }
    } catch { F "frontend unreachable for X-Robots-Tag ($($_.Exception.Message))" }
}

# Frontend must NOT reference production API. Safe to check even behind Access:
# if gated, the fetched body is the Access login page (never contains the prod API
# string, by construction), so this only meaningfully fails when Access is off and
# the real app HTML leaks a production reference.
try {
    $r = Invoke-WebRequest -Uri $frontend -TimeoutSec 20 -UseBasicParsing
    if ($r.Content -match 'api\.bulkeditapp\.com') { F "frontend response references PRODUCTION api.bulkeditapp.com" }
    elseif ($accessGated) { P "frontend does not reference production API (checked via Access login response; re-verify once authenticated)" }
    else { P "frontend does not reference production API" }
} catch { F "frontend unreachable for prod-API check ($($_.Exception.Message))" }

# Local env: no sk_live_ (if the local env file is present).
# Only fail on a real uncommented KEY=value assignment containing sk_live_ -
# ignore blank lines and full-line comments (e.g. the rule description itself
# mentions "sk_live_" in a warning comment, which must not trip this check).
$envPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'deploy-staging.local.env'
if (Test-Path -LiteralPath $envPath) {
    $liveKeyFound = $false
    foreach ($line in Get-Content -LiteralPath $envPath) {
        $trimmed = $line.Trim()
        if ($trimmed -eq '') { continue }
        if ($trimmed.StartsWith('#')) { continue }
        if ($trimmed -match '^[A-Za-z_][A-Za-z0-9_]*=.*sk_live_') { $liveKeyFound = $true }
    }
    if ($liveKeyFound) { F "deploy-staging.local.env contains an sk_live_ key in an active assignment" }
    else { P "no sk_live_ key in any active deploy-staging.local.env assignment" }
}

Write-Host ""
Write-Host "=== Result: $pass passed, $fail failed, $skip skipped ==="
if ($fail -gt 0) { Write-Host "If 'unreachable', DNS/TLS/deploy may not be live yet." -ForegroundColor Yellow; exit 1 }
exit 0
