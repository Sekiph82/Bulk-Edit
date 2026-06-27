<#
.SYNOPSIS
    Smoke test a Bulk-Edit deployment.

.DESCRIPTION
    Checks health, readiness, and key frontend routes for a deployed instance.
    Does not require secrets. Reports pass/fail and exits non-zero on failure.

.PARAMETER FrontendUrl
    Base URL for the frontend (e.g. http://localhost:3100 or https://bulk-edit.com)

.PARAMETER BackendUrl
    Base URL for the backend API (e.g. http://localhost:8100 or https://api.bulk-edit.com)

.EXAMPLE
    .\scripts\smoke_test_deployment.ps1 -FrontendUrl http://localhost:3100 -BackendUrl http://localhost:8100
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$FrontendUrl,
    [Parameter(Mandatory=$true)]
    [string]$BackendUrl
)

$FrontendUrl = $FrontendUrl.TrimEnd("/")
$BackendUrl = $BackendUrl.TrimEnd("/")

$passed = 0
$failed = 0
$report = @()

function Check-Url {
    param([string]$Name, [string]$Url, [int]$ExpectedStatus = 200)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
        if ($response.StatusCode -eq $ExpectedStatus) {
            $script:passed++
            $script:report += "  PASS  $Name ($($response.StatusCode))"
        } else {
            $script:failed++
            $script:report += "  FAIL  $Name - expected $ExpectedStatus, got $($response.StatusCode)"
        }
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($null -ne $code -and $code -eq $ExpectedStatus) {
            $script:passed++
            $script:report += "  PASS  $Name ($code)"
        } else {
            $script:failed++
            $script:report += "  FAIL  $Name - $($_.Exception.Message)"
        }
    }
}

function Check-JsonField {
    param([string]$Name, [string]$Url, [string]$Field, [string]$ExpectedValue)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
        $json = $response.Content | ConvertFrom-Json
        $actual = $json.$Field
        if ($actual -eq $ExpectedValue) {
            $script:passed++
            $script:report += "  PASS  $Name ($Field=$actual)"
        } else {
            $script:failed++
            $script:report += "  FAIL  $Name - $Field expected '$ExpectedValue' got '$actual'"
        }
    } catch {
        $script:failed++
        $script:report += "  FAIL  $Name - $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "  Bulk-Edit Deployment Smoke Test"
Write-Host "  Frontend: $FrontendUrl"
Write-Host "  Backend:  $BackendUrl"
Write-Host "============================================================"
Write-Host ""

# Backend health
Check-JsonField "Backend /health"       "$BackendUrl/api/v1/health"       "status" "ok"
Check-JsonField "Backend /health/ready" "$BackendUrl/api/v1/health/ready" "status" "ready"

# Frontend routes
$routes = @("/", "/pricing", "/features", "/faq", "/contact-us", "/login", "/register",
            "/dashboard", "/admin", "/shops", "/listings")
foreach ($route in $routes) {
    Check-Url "Frontend $route" "$FrontendUrl$route"
}

# Output results
Write-Host ""
foreach ($line in $report) {
    if ($line -match "PASS") {
        Write-Host $line -ForegroundColor Green
    } elseif ($line -match "FAIL") {
        Write-Host $line -ForegroundColor Red
    } else {
        Write-Host $line
    }
}

Write-Host ""
Write-Host "============================================================"
if ($failed -eq 0) {
    Write-Host "  PASS  All $passed checks passed" -ForegroundColor Green
} else {
    Write-Host "  FAIL  $passed passed, $failed failed" -ForegroundColor Red
}
Write-Host "============================================================"
Write-Host ""

if ($failed -gt 0) { exit 1 }
exit 0
