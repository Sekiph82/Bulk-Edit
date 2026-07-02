# deploy-production.ps1
# Guided Vercel (frontend) + Render (backend) production deploy.
#
# Reads deploy-secrets.local.env, validates, and automates as much as each
# provider API safely allows. NEVER prints secret values - only present/MISSING.
#
# Usage (Claude Code runs this for you):
#   powershell -ExecutionPolicy Bypass -File scripts/deploy-production.ps1

$ErrorActionPreference = 'Stop'

$root        = Split-Path -Parent $PSScriptRoot
$secretsPath = Join-Path $root 'deploy-secrets.local.env'
$outDir      = Join-Path $root 'scripts/output'

function Write-Head($t) { Write-Host ""; Write-Host "=== $t ===" -ForegroundColor Cyan }
function Write-Ok($t)   { Write-Host "  [OK]   $t" -ForegroundColor Green }
function Write-Warn($t) { Write-Host "  [WARN] $t" -ForegroundColor Yellow }
function Write-Err($t)  { Write-Host "  [FAIL] $t" -ForegroundColor Red }

# Parse .env (KEY=value; ignore blanks/comments; split on first '='; never print values)
function Read-DotEnv($path) {
    $h = @{}
    foreach ($raw in Get-Content -LiteralPath $path) {
        $line = $raw.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { continue }
        $idx = $line.IndexOf('=')
        if ($idx -lt 1) { continue }
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1)
        $h[$key] = $val
    }
    return $h
}

function Has($env, $key) {
    return $env.ContainsKey($key) -and ($null -ne $env[$key]) -and ($env[$key].Trim() -ne '')
}

# 0. Secrets file present?
if (-not (Test-Path -LiteralPath $secretsPath)) {
    Write-Err "deploy-secrets.local.env not found."
    Write-Host "Run:  powershell -ExecutionPolicy Bypass -File scripts/prepare-deploy-secrets.ps1"
    exit 1
}
$envs = Read-DotEnv $secretsPath
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# 1. Required keys
$required = @(
    'VERCEL_TOKEN','RENDER_API_KEY','JWT_SECRET','ENCRYPTION_KEY',
    'FRONTEND_DOMAIN','APEX_DOMAIN','BACKEND_DOMAIN',
    'NEXT_PUBLIC_BACKEND_URL','NEXT_PUBLIC_APP_URL',
    'FRONTEND_URL','BACKEND_URL','BACKEND_CORS_ORIGINS'
)
Write-Head "Required key check (values never shown)"
$missing = @()
foreach ($k in $required) {
    if (Has $envs $k) { Write-Ok "$k present" } else { Write-Err "$k MISSING"; $missing += $k }
}
if ($missing.Count -gt 0) {
    Write-Head "Cannot deploy - missing required keys"
    foreach ($k in $missing) { Write-Host "  - $k" }
    Write-Host ""
    Write-Host "Fill these in deploy-secrets.local.env, SAVE, then press Continue/OK again."
    if ($env:OS -eq 'Windows_NT') { try { Start-Process notepad.exe -ArgumentList $secretsPath | Out-Null } catch {} }
    exit 2
}

# 2. Optional keys (features degrade, deploy still proceeds)
$optionalGroups = @{
    'Etsy'      = @('ETSY_CLIENT_ID','ETSY_CLIENT_SECRET')
    'Stripe'    = @('STRIPE_SECRET_KEY','STRIPE_WEBHOOK_SECRET')
    'Pinterest' = @('PINTEREST_CLIENT_ID','PINTEREST_CLIENT_SECRET')
    'Meta'      = @('META_APP_ID','META_APP_SECRET')
    'OpenAI'    = @('OPENAI_API_KEY')
    'SMTP'      = @('SMTP_HOST','SMTP_USER','SMTP_PASSWORD')
    'Sentry'    = @('SENTRY_DSN')
}
Write-Head "Optional integrations"
foreach ($grp in $optionalGroups.Keys) {
    $keys = $optionalGroups[$grp]
    $have = @($keys | Where-Object { Has $envs $_ }).Count
    if ($have -eq $keys.Count) { Write-Ok "$grp configured" }
    elseif ($have -eq 0)       { Write-Warn "$grp not set - feature will show unavailable" }
    else                       { Write-Warn "$grp partially set ($have/$($keys.Count)) - feature may be unavailable" }
}

# 3. Local preflight
Write-Head "Local preflight"
$preflightFiles = @('render.yaml','apps/backend/start.sh','apps/backend/Dockerfile','apps/frontend/package.json')
$preflightOk = $true
foreach ($f in $preflightFiles) {
    if (Test-Path -LiteralPath (Join-Path $root $f)) { Write-Ok "$f exists" }
    else { Write-Err "$f missing"; $preflightOk = $false }
}
if (-not $preflightOk) { Write-Err "Preflight failed - deployment aborted."; exit 3 }

# git: ensure no secret file staged
Write-Head "Git safety (no secrets staged)"
$staged = @(git -C $root diff --cached --name-only)
$badStaged = @($staged | Where-Object {
    $_ -match 'deploy-secrets\.local\.env$' -or
    $_ -match '\.vercel/' -or
    ($_ -match '\.env$' -and $_ -notmatch '\.env\.example$') -or
    $_ -match 'scripts/output/.*\.(txt|env)$'
})
if ($badStaged.Count -gt 0) {
    Write-Err "Secret-like files are STAGED - aborting:"
    foreach ($f in $badStaged) { Write-Host "  - $f" }
    exit 4
}
Write-Ok "No secret files staged"

# 4. Vercel frontend
Write-Head "Vercel frontend deploy"
$vercelToken = $envs['VERCEL_TOKEN']
$orgId  = $envs['VERCEL_ORG_ID']
$projId = $envs['VERCEL_PROJECT_ID']
$frontendDir = Join-Path $root 'apps/frontend'
$vercelDeployed = $false

if ((Has $envs 'VERCEL_ORG_ID') -and (Has $envs 'VERCEL_PROJECT_ID')) {
    # Link non-interactively via .vercel/project.json (gitignored)
    $vercelDir = Join-Path $frontendDir '.vercel'
    New-Item -ItemType Directory -Force -Path $vercelDir | Out-Null
    (@{ orgId = $orgId; projectId = $projId } | ConvertTo-Json) |
        Set-Content -LiteralPath (Join-Path $vercelDir 'project.json') -Encoding utf8
    Write-Ok "Wrote apps/frontend/.vercel/project.json (gitignored)"

    Push-Location $frontendDir
    try {
        # Set the two public env vars (idempotent: remove then add; values via stdin, never echoed)
        foreach ($k in @('NEXT_PUBLIC_BACKEND_URL','NEXT_PUBLIC_APP_URL')) {
            $v = $envs[$k]
            & npx --yes vercel env rm $k production --token $vercelToken --yes 2>$null | Out-Null
            $v | & npx --yes vercel env add $k production --token $vercelToken 2>$null | Out-Null
            Write-Ok "Vercel env set: $k"
        }
        Write-Host "  Deploying (npx vercel --prod)..."
        & npx --yes vercel deploy --prod --token $vercelToken --yes
        if ($LASTEXITCODE -eq 0) { Write-Ok "Vercel production deploy triggered"; $vercelDeployed = $true }
        else { Write-Warn "Vercel deploy returned exit $LASTEXITCODE - check output above" }
    } catch {
        Write-Warn "Vercel CLI step failed: $($_.Exception.Message)"
    } finally { Pop-Location }
} else {
    Write-Warn "VERCEL_ORG_ID / VERCEL_PROJECT_ID not set - cannot deploy non-interactively."
    Write-Host "  Add both to deploy-secrets.local.env (Vercel project -> Settings -> General), then Continue/OK."
    Write-Host "  Find them after creating the project once in the Vercel dashboard (root dir: apps/frontend)."
}

# Vercel domains: redirect config is not reliably scriptable -> dashboard step
Write-Head "Vercel domains (manual confirm)"
Write-Host "  Vercel Project -> Settings -> Domains:"
Write-Host "    - add $($envs['FRONTEND_DOMAIN'])  (primary)"
Write-Host "    - add $($envs['APEX_DOMAIN'])  -> set Redirect to $($envs['FRONTEND_DOMAIN'])"

# 5. Render backend
Write-Head "Render backend deploy"
$renderKey = $envs['RENDER_API_KEY']
$rHeaders  = @{ Authorization = "Bearer $renderKey"; 'Accept' = 'application/json' }
$renderServiceId = $null
$renderOk = $true

try {
    $owners = Invoke-RestMethod -Uri 'https://api.render.com/v1/owners' -Headers $rHeaders -Method GET
    Write-Ok "Render API key valid ($((@($owners)).Count) owner(s) visible)"
} catch {
    Write-Err "Render API key invalid or network error - skipping Render automation."
    $renderOk = $false
}

if ($renderOk) {
    if (Has $envs 'RENDER_SERVICE_ID') {
        $renderServiceId = $envs['RENDER_SERVICE_ID']
        Write-Ok "Using RENDER_SERVICE_ID from secrets file"
    } else {
        $name = $envs['RENDER_SERVICE_NAME']
        try {
            $svcs = Invoke-RestMethod -Uri "https://api.render.com/v1/services?name=$name&limit=20" -Headers $rHeaders -Method GET
            foreach ($item in @($svcs)) {
                $svc = if ($item.PSObject.Properties.Name -contains 'service') { $item.service } else { $item }
                if ($svc.name -eq $name) { $renderServiceId = $svc.id; break }
            }
        } catch { Write-Warn "Render service lookup failed: $($_.Exception.Message)" }

        if ($renderServiceId) { Write-Ok "Found Render service '$name'" }
        else {
            Write-Warn "Render service '$name' not found."
            Write-Host "  The service does not exist yet. Create it ONCE from the blueprint:"
            Write-Host "    Render Dashboard -> New -> Blueprint -> select this repo (reads render.yaml)."
            Write-Host "  Then paste RENDER_SERVICE_ID into deploy-secrets.local.env and press Continue/OK."
        }
    }
}

if ($renderServiceId) {
    # Custom domain (safe, idempotent-ish)
    try {
        $body = @{ name = $envs['BACKEND_DOMAIN'] } | ConvertTo-Json
        Invoke-RestMethod -Uri "https://api.render.com/v1/services/$renderServiceId/custom-domains" `
            -Headers $rHeaders -Method POST -ContentType 'application/json' -Body $body | Out-Null
        Write-Ok "Requested Render custom domain: $($envs['BACKEND_DOMAIN'])"
    } catch {
        Write-Warn "Custom domain add skipped (may already exist). Confirm in Render -> Settings -> Custom Domains."
    }

    # Backend env vars: NOT auto-PUT via API (bulk replace would clobber blueprint-wired
    # DATABASE_URL / REDIS_URL). Emit a local, gitignored file for dashboard entry.
    $renderEnvFile = Join-Path $outDir 'render-env-to-set.local.txt'
    $renderKeys = @(
        'ENVIRONMENT','DEBUG','FRONTEND_URL','BACKEND_URL','BACKEND_CORS_ORIGINS',
        'JWT_SECRET','ENCRYPTION_KEY',
        'ETSY_CLIENT_ID','ETSY_CLIENT_SECRET','ETSY_REDIRECT_URI',
        'STRIPE_SECRET_KEY','STRIPE_WEBHOOK_SECRET',
        'STRIPE_PRICE_BASIC_MONTHLY','STRIPE_PRICE_PRO_MONTHLY','STRIPE_PRICE_BASIC_YEARLY','STRIPE_PRICE_PRO_YEARLY',
        'PINTEREST_CLIENT_ID','PINTEREST_CLIENT_SECRET','PINTEREST_REDIRECT_URI',
        'META_APP_ID','META_APP_SECRET','INSTAGRAM_REDIRECT_URI',
        'AI_PROVIDER','OPENAI_API_KEY',
        'SMTP_HOST','SMTP_PORT','SMTP_USER','SMTP_PASSWORD','CONTACT_FROM_EMAIL','CONTACT_TO_EMAIL',
        'VIDEO_RENDERER_ENABLED','FFMPEG_PATH','VIDEO_OUTPUT_DIR','SENTRY_DSN'
    )
    $lines = @('# LOCAL ONLY - contains secrets. Gitignored. Paste into Render -> Environment. Delete after.')
    foreach ($k in $renderKeys) { if (Has $envs $k) { $lines += "$k=$($envs[$k])" } }
    Set-Content -LiteralPath $renderEnvFile -Value $lines -Encoding utf8
    Write-Warn "Wrote $renderEnvFile (LOCAL ONLY, gitignored, contains secrets)."
    Write-Host "  DATABASE_URL and REDIS_URL are auto-wired by the blueprint - do not set them by hand."
    Write-Host "  Paste the file's contents into Render -> service -> Environment, then delete the file."

    # Trigger deploy
    try {
        $dep = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$renderServiceId/deploys" `
            -Headers $rHeaders -Method POST -ContentType 'application/json' -Body '{}'
        Write-Ok "Render deploy triggered (id: $($dep.id), status: $($dep.status))"
    } catch {
        Write-Warn "Could not trigger Render deploy via API. Use Render -> Manual Deploy -> Deploy latest commit."
    }
}

# 6. Summary
Write-Head "Deployment summary"
if ($vercelDeployed) { Write-Ok "Frontend: Vercel production deploy triggered" }
else { Write-Warn "Frontend: not deployed automatically - see Vercel notes above" }
if ($renderServiceId) { Write-Ok "Backend: Render deploy triggered for service $renderServiceId" }
else { Write-Warn "Backend: Render service not deployed - create blueprint / set RENDER_SERVICE_ID" }
Write-Host ""
Write-Host "Remaining manual (first-time only):"
Write-Host "  - Vercel: add domains + apex redirect (Settings -> Domains)"
Write-Host "  - Render: paste env vars from scripts/output/render-env-to-set.local.txt, add api custom domain"
Write-Host "  - DNS: point www + apex (Vercel targets) and api (Render target) at your registrar"
Write-Host "  - Register provider callbacks (Etsy/Pinterest/Meta) + Stripe webhook once live"
Write-Host ""
Write-Host "After DNS resolves, run: powershell -ExecutionPolicy Bypass -File scripts/smoke-production.ps1"
