@echo off
setlocal enabledelayedexpansion
title Bulk-Edit One-Click Local Setup
cd /d "%~dp0"

echo.
echo ============================================================
echo  Bulk-Edit One-Click Local Setup
echo ============================================================
echo.

:: ── Repo root check ──────────────────────────────────────────
if not exist "docker-compose.yml" goto BAD_ROOT
if not exist ".env.example"       goto BAD_ROOT
if not exist "apps"               goto BAD_ROOT
goto ROOT_OK

:BAD_ROOT
echo [ERROR] This file must be run from the Bulk-Edit project folder.
echo.
echo Make sure setup-and-start.bat is in the repo root
echo (next to docker-compose.yml) and double-click it there.
echo.
pause
exit /b 1

:ROOT_OK
echo [OK] Repo root verified.
echo.

:: ── Step 1: Docker CLI check / install ───────────────────────
echo [STEP 1/8] Checking Docker...
docker --version >nul 2>&1
if not errorlevel 1 goto DOCKER_CLI_OK

echo [INFO] Docker Desktop not found on PATH.
winget --version >nul 2>&1
if errorlevel 1 goto NO_WINGET

echo [INFO] Installing Docker Desktop via winget (may take several minutes)...
echo        You may see a UAC prompt -- click Yes.
echo.
winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
echo.
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
)
if exist "%LocalAppData%\Docker\Docker Desktop.exe" (
    start "" "%LocalAppData%\Docker\Docker Desktop.exe"
)
echo.
echo Docker Desktop was installed or installation was started.
echo If Windows asks for a restart, restart then double-click setup-and-start.bat again.
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

:: ── Step 2: Docker daemon check ──────────────────────────────
echo [STEP 2/8] Checking Docker engine...
docker info >nul 2>&1
if not errorlevel 1 goto DOCKER_READY

echo [INFO] Docker engine not running. Starting Docker Desktop...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
) else if exist "%LocalAppData%\Docker\Docker Desktop.exe" (
    start "" "%LocalAppData%\Docker\Docker Desktop.exe"
) else (
    echo [WARN] Docker Desktop executable not found. Start it manually from the taskbar.
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
echo Please wait until Docker Desktop finishes starting
echo (icon in system tray stops animating), then double-click
echo setup-and-start.bat again.
echo.
pause
exit /b 1

:DOCKER_READY
echo [OK] Docker engine ready.
echo.

:: ── Compose command detection ─────────────────────────────────
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
echo [ERROR] Docker Compose not found. Update Docker Desktop to a recent version.
echo.
pause
exit /b 1

:COMPOSE_OK
echo [OK] Docker Compose ready.
echo.

:: ── Step 3: Create .env if missing ───────────────────────────
echo [STEP 3/8] Checking environment file...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [OK] Created .env from .env.example.
) else (
    echo [OK] .env already exists. Keeping existing values.
)
echo.

:: ── Step 4: Ensure placeholder vars in .env ──────────────────
echo [STEP 4/8] Ensuring required placeholders in .env...
if not exist "scripts\windows\ensure-env.ps1" (
    echo [ERROR] scripts\windows\ensure-env.ps1 not found.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\windows\ensure-env.ps1"
if errorlevel 1 (
    echo [ERROR] ensure-env.ps1 failed. See output above.
    pause
    exit /b 1
)
echo.

:: ── Step 5: Create demo seed file if missing ─────────────────
echo [STEP 5/8] Checking demo user seed...
if not exist "scripts\windows\create-seed.ps1" (
    echo [ERROR] scripts\windows\create-seed.ps1 not found.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\windows\create-seed.ps1"
if errorlevel 1 (
    echo [ERROR] create-seed.ps1 failed. See output above.
    pause
    exit /b 1
)
echo.

:: ── Step 6: Build and start all services ─────────────────────
echo [STEP 6/8] Starting Bulk-Edit services...
echo.
echo This may take several minutes on first run while Docker builds images.
echo.

%DC% -p bulk-edit up -d --build --remove-orphans
set "COMPOSE_EXIT=!errorlevel!"
if !COMPOSE_EXIT! neq 0 (
    echo.
    echo [ERROR] docker compose up failed ^(exit code !COMPOSE_EXIT!^).
    echo See output above for details.
    echo.
    echo Common fixes:
    echo   - Make sure Docker Desktop is fully started
    echo   - Check ports 3100 and 8100 are not in use by another app
    echo   - Run: %DC% -p bulk-edit logs
    echo.
    pause
    exit /b 1
)
echo.
echo [OK] Containers started.
echo.

:: ── Step 7a: Wait for backend health ─────────────────────────
echo [STEP 7/8] Waiting for services to be ready...
echo.

set /a B_WAIT=0
echo [INFO] Waiting for backend health endpoint...
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

:: ── Step 7b: Wait for backend readiness ──────────────────────
set /a R_WAIT=0
echo [INFO] Waiting for database readiness (migrations)...
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
echo [ERROR] Backend readiness check timed out after 180 seconds.
echo.
%DC% -p bulk-edit logs --tail=80 backend
echo.
pause
exit /b 1

:READY_OK
echo [OK] Backend ready (database connected, migrations applied).

:: ── Step 7c: Wait for frontend ────────────────────────────────
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

:: ── Step 8: Open browser and show login info ──────────────────
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
echo  Backend health:    http://localhost:8100/api/v1/health
echo  Backend readiness: http://localhost:8100/api/v1/health/ready
echo.
echo  To stop services later, run:
echo    docker compose -p bulk-edit down
echo.
echo ============================================================
echo.
pause
exit /b 0
