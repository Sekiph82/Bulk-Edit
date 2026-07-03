# smoke-staging.ps1
# Post-provision smoke test for the STAGING environment. PASS/FAIL per check.
# No secrets. Read-only.
#
#   powershell -ExecutionPolicy Bypass -File scripts/smoke-staging.ps1

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$frontend = 'https://staging.bulkeditapp.com'
$api      = 'https://api-staging.bulkeditapp.com'
$health   = "$api/api/v1/health"

$pass = 0; $fail = 0
function P($t){ Write-Host "  PASS  $t" -ForegroundColor Green; $script:pass++ }
function F($t){ Write-Host "  FAIL  $t" -ForegroundColor Red;   $script:fail++ }

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

# robots.txt Disallow: /
try {
    $r = Invoke-WebRequest -Uri "$frontend/robots.txt" -TimeoutSec 20 -UseBasicParsing
    if ($r.Content -match 'Disallow:\s*/') { P "robots.txt Disallow: /" } else { F "robots.txt missing Disallow: / (got: $($r.Content.Trim()))" }
} catch { F "robots.txt unreachable ($($_.Exception.Message))" }

# X-Robots-Tag noindex on frontend
try {
    $r = Invoke-WebRequest -Uri $frontend -TimeoutSec 20 -UseBasicParsing
    $xr = $r.Headers['X-Robots-Tag']
    if ($xr -and $xr -match 'noindex') { P "X-Robots-Tag: noindex present" } else { F "X-Robots-Tag missing/incorrect (got '$xr')" }
} catch { F "frontend unreachable for X-Robots-Tag ($($_.Exception.Message))" }

# Frontend must NOT reference production API in served HTML
try {
    $r = Invoke-WebRequest -Uri $frontend -TimeoutSec 20 -UseBasicParsing
    if ($r.Content -match 'api\.bulkeditapp\.com') { F "frontend HTML references PRODUCTION api.bulkeditapp.com" }
    else { P "frontend does not reference production API" }
} catch { F "frontend unreachable for prod-API check ($($_.Exception.Message))" }

# Local env: no sk_live_ (if the local env file is present)
$envPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'deploy-staging.local.env'
if (Test-Path -LiteralPath $envPath) {
    if ((Get-Content -Raw $envPath) -match 'sk_live_') { F "deploy-staging.local.env contains sk_live_ key" }
    else { P "no sk_live_ in staging env file" }
}

Write-Host ""
Write-Host "=== Result: $pass passed, $fail failed ==="
if ($fail -gt 0) { Write-Host "If 'unreachable', DNS/TLS/deploy may not be live yet." -ForegroundColor Yellow; exit 1 }
exit 0
