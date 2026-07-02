# provision-staging.ps1
# Provision the STAGING DigitalOcean + Cloudflare environment from
# deploy-staging.local.env and the committed .do/app.staging-*.yaml specs.
#
# SAFETY: never prints secrets; refuses production-looking / live values;
# staging-only; never touches production. Logs resource names + status only.
#
#   powershell -ExecutionPolicy Bypass -File scripts/provision-staging.ps1
#
# Requires: deploy-staging.local.env filled (see prepare-staging-secrets.ps1),
#           doctl installed + a Cloudflare API token in the env file.

$ErrorActionPreference = 'Stop'

$root        = Split-Path -Parent $PSScriptRoot
$envPath     = Join-Path $root 'deploy-staging.local.env'
$beSpec      = Join-Path $root '.do/app.staging-backend.yaml'
$feSpec      = Join-Path $root '.do/app.staging-frontend.yaml'
$PUBLIC_CI_FERNET = 'uOv7K6PYL6v4G77O0WqJrA5BrM42x3NCAQZUSO2rTio='

function Head($t) { Write-Host ""; Write-Host "=== $t ===" -ForegroundColor Cyan }
function Ok($t)   { Write-Host "  [OK]   $t" -ForegroundColor Green }
function Warn($t) { Write-Host "  [WARN] $t" -ForegroundColor Yellow }
function Fail($t) { Write-Host "  [FAIL] $t" -ForegroundColor Red }
function Stop-Provision($t) { Fail $t; Write-Host "STOP: $t" -ForegroundColor Red; exit 1 }

function Read-DotEnv($path) {
    $h = @{}
    foreach ($raw in Get-Content -LiteralPath $path) {
        $line = $raw.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { continue }
        $i = $line.IndexOf('='); if ($i -lt 1) { continue }
        $h[$line.Substring(0,$i).Trim()] = $line.Substring($i+1)
    }
    return $h
}
function Has($h,$k){ return $h.ContainsKey($k) -and ($null -ne $h[$k]) -and ($h[$k].Trim() -ne '') }

# --- 0. Load env -------------------------------------------------------------
if (-not (Test-Path -LiteralPath $envPath)) {
    Stop-Provision "deploy-staging.local.env not found. Run scripts/prepare-staging-secrets.ps1 first."
}
$envs = Read-DotEnv $envPath

# --- 1. Required values ------------------------------------------------------
Head "Required values (secrets shown as present/MISSING only)"
$required = @(
    'DIGITALOCEAN_ACCESS_TOKEN','DIGITALOCEAN_REGION',
    'DIGITALOCEAN_STAGING_BACKEND_APP_NAME','DIGITALOCEAN_STAGING_FRONTEND_APP_NAME',
    'CLOUDFLARE_API_TOKEN','CLOUDFLARE_ZONE_ID','CLOUDFLARE_ACCOUNT_ID',
    'STAGING_DOMAIN','API_STAGING_DOMAIN','STAGING_FRONTEND_URL','STAGING_BACKEND_URL'
)
$missing = @()
foreach ($k in $required) { if (Has $envs $k) { Ok "$k present" } else { Fail "$k MISSING"; $missing += $k } }
if ($missing.Count) {
    Warn "Fill missing values in deploy-staging.local.env, then re-run."
    if ($env:OS -eq 'Windows_NT') { try { Start-Process notepad.exe -ArgumentList $envPath | Out-Null } catch {} }
    exit 2
}

# --- 2. Forbidden / production-looking values (refuse) -----------------------
Head "Safety guards (refuse production/live values)"
# Stripe live key
if ((Has $envs 'STRIPE_SECRET_KEY') -and ($envs['STRIPE_SECRET_KEY'].Trim() -like 'sk_live_*')) {
    Stop-Provision "STRIPE_SECRET_KEY is a LIVE key (sk_live_). Staging must use sk_test_ only."
}
if ((Has $envs 'STRIPE_SECRET_KEY') -and (-not ($envs['STRIPE_SECRET_KEY'].Trim() -like 'sk_test_*'))) {
    Stop-Provision "STRIPE_SECRET_KEY set but not sk_test_. Use a test key or leave blank."
}
Ok "Stripe key: test-mode or blank"
# ENCRYPTION_KEY must not be the public CI dummy
if ((Has $envs 'ENCRYPTION_KEY') -and ($envs['ENCRYPTION_KEY'].Trim() -eq $PUBLIC_CI_FERNET)) {
    Stop-Provision "ENCRYPTION_KEY equals the PUBLIC CI dummy key. Generate a fresh private staging key."
}
Ok "ENCRYPTION_KEY: not the public CI key"
# URLs must be staging
foreach ($k in @('STAGING_BACKEND_URL','STAGING_FRONTEND_URL','API_STAGING_DOMAIN','STAGING_DOMAIN')) {
    if ($envs[$k] -notmatch 'staging') { Stop-Provision "$k does not contain 'staging' ($($envs[$k])). Refusing (looks like production)." }
}
# Explicit prod hosts must never appear
foreach ($k in $envs.Keys) {
    $v = "$($envs[$k])"
    if ($v -match 'https://(www\.)?bulkeditapp\.com' -or $v -match 'api\.bulkeditapp\.com') {
        Stop-Provision "$k contains a PRODUCTION host ($v). Staging must use *-staging hosts only."
    }
}
Ok "No production hosts / DB / Redis in env"
# DATABASE_URL / REDIS_URL must NOT be hand-set (auto-wired by DO spec)
foreach ($k in @('DATABASE_URL','REDIS_URL')) {
    if (Has $envs $k) { Stop-Provision "$k is set manually. Staging DB/Redis must auto-wire from the DO spec; remove it." }
}
Ok "DATABASE_URL / REDIS_URL not hand-set (auto-wired)"

# --- 3. Generate missing secrets locally (never printed) ---------------------
Head "Backend secrets (generate if missing; values never shown)"
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
function New-UrlSafe([int]$bytes,[bool]$pad) {
    $b = New-Object byte[] $bytes; $rng.GetBytes($b)
    $s = [Convert]::ToBase64String($b).Replace('+','-').Replace('/','_')
    if (-not $pad) { $s = $s.TrimEnd('=') }
    return $s
}
function Set-EnvFileValue($path,$key,$value) {
    $content = Get-Content -LiteralPath $path -Raw
    if ($content -match "(?m)^$key=.*$") {
        $content = [regex]::Replace($content, "(?m)^$key=.*$", "$key=$value")
    } else { $content = $content.TrimEnd() + "`r`n$key=$value`r`n" }
    Set-Content -LiteralPath $path -Value $content -Encoding utf8 -NoNewline
}
if (-not (Has $envs 'JWT_SECRET')) {
    Set-EnvFileValue $envPath 'JWT_SECRET' (New-UrlSafe 48 $false); $envs['JWT_SECRET']='(generated)'; Ok "JWT_SECRET generated (stored locally)"
} else { Ok "JWT_SECRET present" }
if (-not (Has $envs 'ENCRYPTION_KEY')) {
    $fk = New-UrlSafe 32 $true
    if ($fk -eq $PUBLIC_CI_FERNET) { Stop-Provision "generated key collided with CI dummy (retry)" }
    Set-EnvFileValue $envPath 'ENCRYPTION_KEY' $fk; $envs['ENCRYPTION_KEY']='(generated)'; Ok "ENCRYPTION_KEY generated (fresh Fernet, stored locally)"
} else { Ok "ENCRYPTION_KEY present" }

# --- 4. doctl availability + auth (token via env, never printed) -------------
Head "DigitalOcean CLI (doctl)"
$doctl = (Get-Command doctl -ErrorAction SilentlyContinue).Source
if (-not $doctl) {
    Warn "doctl not installed. Install (pick one), then re-run:"
    Write-Host "    scoop install doctl"
    Write-Host "    choco install doctl"
    Write-Host "    or download: https://github.com/digitalocean/doctl/releases (add to PATH)"
    Stop-Provision "doctl missing - install it and re-run (no changes made)."
}
$env:DIGITALOCEAN_ACCESS_TOKEN = $envs['DIGITALOCEAN_ACCESS_TOKEN']  # doctl reads this; not printed
try { & $doctl account get --no-header 2>$null | Out-Null; if ($LASTEXITCODE -ne 0) { throw "auth failed" }; Ok "doctl authenticated" }
catch { Stop-Provision "doctl auth failed - check DIGITALOCEAN_ACCESS_TOKEN scopes (read+write)." }

# --- 5. Create/verify staging apps from committed specs (idempotent) ---------
# NOTE: paid resources. This creates the staging apps + dev DB/Redis from the
# specs' `databases:` blocks. Confirm the price DO shows in the dashboard.
Head "DigitalOcean staging apps"
function Get-AppId($name) {
    $list = & $doctl apps list --no-header --format ID,Spec.Name 2>$null
    foreach ($ln in $list) { $p = $ln -split '\s+'; if ($p[1] -eq $name) { return $p[0] } }
    return $null
}
$beName = $envs['DIGITALOCEAN_STAGING_BACKEND_APP_NAME']
$feName = $envs['DIGITALOCEAN_STAGING_FRONTEND_APP_NAME']

$beId = Get-AppId $beName
if ($beId) { Ok "Backend app exists: $beName ($beId)" }
else {
    Warn "Creating backend app '$beName' from $beSpec (PAID - confirm cost in DO dashboard)."
    $beId = (& $doctl apps create --spec $beSpec --format ID --no-header 2>&1 | Select-Object -Last 1)
    if ($LASTEXITCODE -ne 0 -or -not $beId) { Stop-Provision "backend app create failed: $beId" }
    Ok "Backend app created: $beName ($beId)"
}

$feId = Get-AppId $feName
if ($feId) { Ok "Frontend app exists: $feName ($feId)" }
else {
    Warn "Creating frontend app '$feName' from $feSpec (PAID - confirm cost in DO dashboard)."
    $feId = (& $doctl apps create --spec $feSpec --format ID --no-header 2>&1 | Select-Object -Last 1)
    if ($LASTEXITCODE -ne 0 -or -not $feId) { Stop-Provision "frontend app create failed: $feId" }
    Ok "Frontend app created: $feName ($feId)"
}

# --- 6. Backend SECRET env vars ---------------------------------------------
# doctl sets env only via full-spec update. Rather than fragile YAML surgery on
# the committed spec, secrets are set in the DO dashboard (encrypted). The values
# are in deploy-staging.local.env (gitignored) - copy them into the app's env.
Head "Backend secret env vars (manual, one-time)"
Warn "Set these as ENCRYPTED env vars on '$beName' (DO -> App -> Settings -> Env):"
Write-Host "    JWT_SECRET, ENCRYPTION_KEY  (values in deploy-staging.local.env - do not print/paste to chat)"
Write-Host "    STRIPE_* / ETSY_* / OPENAI/ANTHROPIC / SENTRY_DSN  (only the test/staging ones you filled)"
Write-Host "    (DATABASE_URL / REDIS_URL auto-wire from the spec - do not set by hand)"

# --- 7. DO ingress hostnames (for DNS) --------------------------------------
Head "DigitalOcean ingress targets"
$beIngress = (& $doctl apps get $beId --format DefaultIngress --no-header 2>$null) -replace 'https?://',''
$feIngress = (& $doctl apps get $feId --format DefaultIngress --no-header 2>$null) -replace 'https?://',''
if ($beIngress) { Ok "Backend ingress: $beIngress" } else { Warn "Backend ingress not ready yet (retry after deploy)." }
if ($feIngress) { Ok "Frontend ingress: $feIngress" } else { Warn "Frontend ingress not ready yet (retry after deploy)." }

# --- 8. Cloudflare DNS (staging records only) --------------------------------
Head "Cloudflare DNS (staging only)"
$cfToken = $envs['CLOUDFLARE_API_TOKEN']
$zone    = $envs['CLOUDFLARE_ZONE_ID']
$cfHdr   = @{ Authorization = "Bearer $cfToken"; 'Content-Type' = 'application/json' }
function Set-CfCname($fqdn,$target) {
    if (-not $target) { Warn "skip $fqdn (no DO target yet)"; return }
    if ($fqdn -notmatch 'staging') { Warn "refusing non-staging DNS record: $fqdn"; return }  # guard prod DNS
    try {
        $existing = Invoke-RestMethod -Headers $cfHdr -Method GET `
            -Uri "https://api.cloudflare.com/client/v4/zones/$zone/dns_records?type=CNAME&name=$fqdn"
        $body = @{ type='CNAME'; name=$fqdn; content=$target; proxied=$true } | ConvertTo-Json
        if ($existing.result.Count -gt 0) {
            $id = $existing.result[0].id
            Invoke-RestMethod -Headers $cfHdr -Method PUT -Body $body `
                -Uri "https://api.cloudflare.com/client/v4/zones/$zone/dns_records/$id" | Out-Null
            Ok "Updated CNAME $fqdn -> $target (proxied)"
        } else {
            Invoke-RestMethod -Headers $cfHdr -Method POST -Body $body `
                -Uri "https://api.cloudflare.com/client/v4/zones/$zone/dns_records" | Out-Null
            Ok "Created CNAME $fqdn -> $target (proxied)"
        }
    } catch { Warn "CF DNS for $fqdn failed: $($_.Exception.Message)" }
}
Set-CfCname $envs['API_STAGING_DOMAIN'] $beIngress
Set-CfCname $envs['STAGING_DOMAIN']     $feIngress
Write-Host "  Reminder: Cloudflare SSL/TLS mode must be Full (strict), never Flexible."

# --- 9. Attach custom domains to DO apps (via dashboard/spec) -----------------
Head "Custom domains on DO apps"
Warn "In each DO app -> Settings -> Domains, add:"
Write-Host "    $beName -> $($envs['API_STAGING_DOMAIN'])"
Write-Host "    $feName -> $($envs['STAGING_DOMAIN'])"
Write-Host "  (doctl domain attach varies by version; dashboard is the reliable path.)"

# --- 10. Cloudflare Access (best-effort; else manual) ------------------------
Head "Cloudflare Access for staging frontend"
if ((Has $envs 'CLOUDFLARE_ACCOUNT_ID') -and (Has $envs 'CLOUDFLARE_STAGING_ACCESS_ALLOWED_EMAILS')) {
    Warn "Cloudflare Access app+policy creation is account-shape specific."
    Write-Host "  Recommended manual (Zero Trust -> Access -> Applications):"
    Write-Host "    - Self-hosted app for $($envs['STAGING_DOMAIN'])"
    Write-Host "    - Policy: Allow -> emails: $($envs['CLOUDFLARE_STAGING_ACCESS_ALLOWED_EMAILS'])"
    Write-Host "  Do NOT Access-gate $($envs['API_STAGING_DOMAIN']) (would block browser XHR)."
} else {
    Warn "Access emails/account not set - configure Cloudflare Access manually later."
}

Head "Provisioning pass complete"
Write-Host "Next:"
Write-Host "  - Set backend secret env vars in DO (step 6)."
Write-Host "  - Add custom domains in DO apps (step 9); confirm DO issues TLS."
Write-Host "  - Confirm Cloudflare SSL/TLS = Full (strict) + Access on staging."
Write-Host "  - Wait for deploys + pre-deploy migrate job, then run:"
Write-Host "      powershell -ExecutionPolicy Bypass -File scripts/smoke-staging.ps1"
Write-Host "Production was NOT touched. No secret values were printed."
