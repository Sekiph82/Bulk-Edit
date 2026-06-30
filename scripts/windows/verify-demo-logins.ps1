# scripts/windows/verify-demo-logins.ps1
# Verifies that demo login accounts respond correctly via the auth API.
# Called by setup-and-start.bat after backend readiness. Must run from repo root.
# Exits 0 when both logins succeed, 1 when either fails.

param(
    [string]$BackendUrl = "http://localhost:8100"
)

$loginUrl = "$BackendUrl/api/v1/auth/login"
$allOk = $true

function Test-DemoLogin {
    param([string]$Email, [string]$Label)
    $body = ([ordered]@{email=$Email; password="Test1234!"} | ConvertTo-Json -Compress)
    try {
        $r = Invoke-WebRequest -Uri $loginUrl -Method POST -Body $body `
            -ContentType "application/json" -UseBasicParsing -TimeoutSec 8 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            Write-Host "[OK] Demo login verified: $Label ($Email)"
            return $true
        }
        Write-Host "[FAIL] Demo login $Label ($Email): HTTP $($r.StatusCode)"
    } catch {
        Write-Host "[FAIL] Demo login $Label ($Email): $($_.Exception.Message)"
    }
    return $false
}

if (-not (Test-DemoLogin -Email "test@example.com"    -Label "Normal user")) { $allOk = $false }
if (-not (Test-DemoLogin -Email "test-su@example.com" -Label "Superuser"))    { $allOk = $false }

if ($allOk) {
    exit 0
}

Write-Host ""
Write-Host "[ERROR] Demo login accounts were not created correctly."
Write-Host "        This usually means the seed file was not loaded on backend startup."
Write-Host "        Check backend logs above for seed errors."
exit 1
