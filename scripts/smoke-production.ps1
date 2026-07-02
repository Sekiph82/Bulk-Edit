# smoke-production.ps1
# Post-deploy smoke test against the live bulkeditapp.com domain.
# PASS/FAIL per check. No secrets involved.
#
#   powershell -ExecutionPolicy Bypass -File scripts/smoke-production.ps1

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$frontend = 'https://www.bulkeditapp.com'
$apex     = 'https://bulkeditapp.com'
$health   = 'https://api.bulkeditapp.com/api/v1/health'
$ready    = 'https://api.bulkeditapp.com/api/v1/health/ready'

$pass = 0; $fail = 0
function Pass($t) { Write-Host "  PASS  $t" -ForegroundColor Green; $script:pass++ }
function Fail($t) { Write-Host "  FAIL  $t" -ForegroundColor Red;   $script:fail++ }

Write-Host "=== Production smoke test ==="

# 1. Frontend loads
try {
    $r = Invoke-WebRequest -Uri $frontend -Method GET -TimeoutSec 20 -UseBasicParsing
    if ($r.StatusCode -eq 200) { Pass "$frontend -> 200" } else { Fail "$frontend -> $($r.StatusCode)" }
} catch { Fail "$frontend unreachable ($($_.Exception.Message))" }

# 2. Apex redirects to www
try {
    $r = Invoke-WebRequest -Uri $apex -Method GET -TimeoutSec 20 -MaximumRedirection 0 -UseBasicParsing -ErrorAction Stop
    Fail "$apex did not redirect (status $($r.StatusCode))"
} catch {
    $resp = $_.Exception.Response
    if ($resp -and [int]$resp.StatusCode -ge 300 -and [int]$resp.StatusCode -lt 400) {
        $loc = $resp.Headers['Location']
        if ($loc -like "*www.bulkeditapp.com*") { Pass "$apex -> redirects to www ($([int]$resp.StatusCode))" }
        else { Fail "$apex redirects but not to www (Location: $loc)" }
    } else { Fail "$apex no redirect / unreachable" }
}

# 3. Backend health
try {
    $r = Invoke-WebRequest -Uri $health -Method GET -TimeoutSec 20 -UseBasicParsing
    if ($r.StatusCode -eq 200) { Pass "$health -> 200" } else { Fail "$health -> $($r.StatusCode)" }
} catch { Fail "$health unreachable ($($_.Exception.Message))" }

# 4. Backend readiness
try {
    $r = Invoke-WebRequest -Uri $ready -Method GET -TimeoutSec 20 -UseBasicParsing
    if ($r.StatusCode -eq 200) { Pass "$ready -> 200" } else { Fail "$ready -> $($r.StatusCode)" }
} catch { Fail "$ready unreachable ($($_.Exception.Message))" }

# 5. CORS preflight from www origin
try {
    $h = @{ 'Origin' = $frontend; 'Access-Control-Request-Method' = 'GET' }
    $r = Invoke-WebRequest -Uri $health -Method Options -Headers $h -TimeoutSec 20 -UseBasicParsing
    $acao = $r.Headers['Access-Control-Allow-Origin']
    if ($acao -and ($acao -eq $frontend -or $acao -eq '*')) { Pass "CORS preflight allows $frontend" }
    else { Fail "CORS preflight missing/incorrect Allow-Origin (got '$acao')" }
} catch { Fail "CORS preflight failed ($($_.Exception.Message))" }

Write-Host ""
Write-Host "=== Result: $pass passed, $fail failed ==="
if ($fail -gt 0) {
    Write-Host "If failures are 'unreachable' / no-redirect, DNS or TLS may not be live yet." -ForegroundColor Yellow
    exit 1
}
exit 0
