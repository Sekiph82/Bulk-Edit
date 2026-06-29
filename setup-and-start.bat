@echo off
setlocal enabledelayedexpansion
title Bulk-Edit One-Click Local Setup

:: Always run from the folder where this .bat file lives
cd /d "%~dp0"

echo.
echo ============================================================
echo  Bulk-Edit One-Click Local Setup
echo ============================================================
echo.

:: ── Verify repo root ────────────────────────────────────────
if not exist "docker-compose.yml" goto BAD_ROOT
if not exist ".env.example"      goto BAD_ROOT
if not exist "apps"              goto BAD_ROOT
goto ROOT_OK

:BAD_ROOT
echo [ERROR] This file must be run from the Bulk-Edit project folder.
echo.
echo Make sure setup-and-start.bat is in the repo root (next to
echo docker-compose.yml) and double-click it there.
echo.
pause
exit /b 1

:ROOT_OK
echo [OK] Repo root verified.
echo.

:: ── Step 1: Docker CLI check / install ──────────────────────
echo [STEP 1/8] Checking Docker...
docker --version >nul 2>&1
if not errorlevel 1 goto DOCKER_CLI_OK

echo [INFO] Docker Desktop not found on PATH.
winget --version >nul 2>&1
if errorlevel 1 goto NO_WINGET

echo [INFO] Docker Desktop is not installed. Installing automatically via winget...
echo        This may take several minutes. You may see a UAC prompt -- click Yes.
echo.
winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
echo.

:: Try to start after install
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
)
if exist "%LocalAppData%\Docker\Docker Desktop.exe" (
    start "" "%LocalAppData%\Docker\Docker Desktop.exe"
)

:: Check if Docker CLI is now available
docker --version >nul 2>&1
if not errorlevel 1 goto DOCKER_CLI_OK

echo.
echo [WARN] Docker Desktop was installed. A Windows restart may be required
echo        (WSL2 setup). Please restart Windows if prompted, then
echo        double-click setup-and-start.bat again.
echo.
pause
exit /b 0

:NO_WINGET
echo [INFO] winget not found. Opening Docker Desktop download page...
start https://www.docker.com/products/docker-desktop/
echo.
echo Docker Desktop is required. Please:
echo   1. Download and install Docker Desktop from the page that just opened.
echo   2. Start Docker Desktop.
echo   3. Double-click setup-and-start.bat again.
echo.
pause
exit /b 1

:DOCKER_CLI_OK
echo [OK] Docker CLI found.
echo.

:: ── Step 2: Ensure Docker daemon is running ─────────────────
echo [STEP 2/8] Checking Docker engine...
docker info >nul 2>&1
if not errorlevel 1 goto DOCKER_READY

echo [INFO] Docker engine not running. Starting Docker Desktop...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
) else if exist "%LocalAppData%\Docker\Docker Desktop.exe" (
    start "" "%LocalAppData%\Docker\Docker Desktop.exe"
) else (
    echo [WARN] Docker Desktop executable not found at expected paths.
    echo        Please start Docker Desktop manually from the taskbar.
)

echo.
set /a DOCKER_WAIT=0
:WAIT_DOCKER
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto DOCKER_READY
set /a DOCKER_WAIT+=5
if %DOCKER_WAIT% GEQ 180 goto DOCKER_TIMEOUT
echo [INFO] Waiting for Docker Desktop... %DOCKER_WAIT%/180s
goto WAIT_DOCKER

:DOCKER_TIMEOUT
echo.
echo [ERROR] Docker Desktop did not become ready within 180 seconds.
echo.
echo Please wait until Docker Desktop finishes starting (icon in system tray
echo stops animating), then double-click setup-and-start.bat again.
echo.
pause
exit /b 1

:DOCKER_READY
echo [OK] Docker engine ready.
echo.

:: ── Detect compose command ───────────────────────────────────
docker compose version >nul 2>&1
if not errorlevel 1 (
    set "DC=docker compose"
    goto COMPOSE_OK
)
docker-compose --version >nul 2>&1
if not errorlevel 1 (
    set "DC=docker-compose"
    goto COMPOSE_OK
)
echo [ERROR] Docker Compose not found. Please update Docker Desktop to a recent version.
echo.
pause
exit /b 1

:COMPOSE_OK
echo [OK] Docker Compose ready.
echo.

:: ── Step 3: Create .env if missing ──────────────────────────
echo [STEP 3/8] Checking environment file...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [OK] Created .env from .env.example.
) else (
    echo [OK] .env already exists. Keeping existing values.
)
echo.

:: ── Step 4: Append missing placeholder variables to .env ────
echo [STEP 4/8] Ensuring required placeholders in .env...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\windows\ensure-env.ps1"
echo.

:: ── Step 5: Create demo seed file if missing ────────────────
echo [STEP 5/8] Checking demo user seed...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\windows\create-seed.ps1"
echo.

:: ── Step 6: Build and start all services ─────────────────────
echo [STEP 6/8] Starting Bulk-Edit services...
echo.
echo This may take several minutes on first run while Docker builds images.
echo.

:: Stop old ERP project silently (prevents port conflict if user had it)
%DC% -p fmcg-erp-system-main down --remove-orphans >nul 2>&1

%DC% -p bulk-edit up -d --build --remove-orphans
if errorlevel 1 (
    echo.
    echo [ERROR] docker compose up failed. See output above.
    echo.
    echo Common fixes:
    echo   - Make sure Docker Desktop is fully started (icon in system tray)
    echo   - Try double-clicking setup-and-start.bat again
    echo.
    pause
    exit /b 1
)
echo.
echo [OK] Containers started.
echo.

:: ── Step 7: Wait for backend health ─────────────────────────
echo [STEP 7/8] Waiting for services to be ready...
echo.

set /a B_WAIT=0
echo [INFO] Waiting for backend...
:WAIT_HEALTH
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8100/api/v1/health' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto HEALTH_OK
set /a B_WAIT+=5
if %B_WAIT% GEQ 180 goto HEALTH_TIMEOUT
if %B_WAIT% EQU 5  echo [INFO] Building and starting backend... (first run can take 2-5 minutes)
echo [INFO] Backend not ready yet... %B_WAIT%/180s
timeout /t 5 /nobreak >nul
goto WAIT_HEALTH

:HEALTH_TIMEOUT
echo.
echo [ERROR] Backend did not respond within 180 seconds.
echo.
%DC% -p bulk-edit logs --tail=80 backend
echo.
pause
exit /b 1

:HEALTH_OK
echo [OK] Backend healthy.

:: ── Wait for database readiness ──────────────────────────────
set /a R_WAIT=0
echo [INFO] Waiting for database...
:WAIT_READY
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8100/api/v1/health/ready' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto READY_OK
set /a R_WAIT+=5
if %R_WAIT% GEQ 180 goto READY_TIMEOUT
echo [INFO] Database not ready yet... %R_WAIT%/180s
timeout /t 5 /nobreak >nul
goto WAIT_READY

:READY_TIMEOUT
echo.
echo [ERROR] Database did not become ready within 180 seconds.
echo.
%DC% -p bulk-edit logs --tail=80 backend
echo.
pause
exit /b 1

:READY_OK
echo [OK] Backend ready (database connected, migrations applied).

:: ── Wait for frontend ────────────────────────────────────────
set /a F_WAIT=0
echo [INFO] Waiting for frontend...
:WAIT_FRONTEND
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $null = Invoke-WebRequest -Uri 'http://localhost:3100' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop; exit 0 } catch [System.Net.WebException] { if ($_.Exception.Response) { exit 0 } exit 1 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto FRONTEND_OK
set /a F_WAIT+=5
if %F_WAIT% GEQ 180 goto FRONTEND_TIMEOUT
if %F_WAIT% EQU 5  echo [INFO] Building frontend... (first run can take 3-6 minutes)
echo [INFO] Frontend not ready yet... %F_WAIT%/180s
timeout /t 5 /nobreak >nul
goto WAIT_FRONTEND

:FRONTEND_TIMEOUT
echo.
echo [ERROR] Frontend did not respond within 180 seconds.
echo.
%DC% -p bulk-edit logs --tail=80 frontend
echo.
pause
exit /b 1

:FRONTEND_OK
echo [OK] Frontend ready.
echo.

:: ── Step 8: Open browser and show login info ─────────────────
echo [STEP 8/8] Opening browser...
start "" "http://localhost:3100"

echo.
echo ============================================================
echo  Bulk-Edit is running!
echo ============================================================
echo.
echo  Open:   http://localhost:3100
echo.
echo  Login accounts:
echo.
echo    Normal user
echo      Email:    test@example.com
echo      Password: Test1234!
echo.
echo    Superuser (admin access)
echo      Email:    test-su@example.com
echo      Password: Test1234!
echo.
echo  Backend health:  http://localhost:8100/api/v1/health
echo.
echo  To stop services later, run:
echo    docker compose -p bulk-edit down
echo.
echo ============================================================
echo.
pause
