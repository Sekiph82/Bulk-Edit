@echo off
setlocal enabledelayedexpansion
title Bulk-Edit Clean Dev Reset

cd /d "%~dp0"

echo.
echo ============================================================
echo  Bulk-Edit - Clean Dev Reset
echo  Docker Compose project: bulk-edit
echo ============================================================
echo.
echo  WARNING: This will DELETE all local database volumes.
echo  All PostgreSQL data will be permanently destroyed.
echo  Use start-dev.bat instead to keep your data.
echo.
echo ============================================================
echo.

set /p CONFIRM=This will delete local database volumes. Type YES to continue:
if /I not "%CONFIRM%"=="YES" (
    echo [INFO] Clean reset canceled.
    echo.
    pause
    exit /b 0
)
echo.

:: Check Docker CLI
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker CLI not found.
    echo Please install Docker Desktop first:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)
echo [OK] Docker CLI found.

:: Start Docker Desktop if not already running
set "DOCKER_DESKTOP_EXE=C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker info >nul 2>&1
if errorlevel 1 (
    if exist "%DOCKER_DESKTOP_EXE%" (
        echo [INFO] Starting Docker Desktop...
        start "" "%DOCKER_DESKTOP_EXE%"
    ) else (
        echo [WARN] Docker Desktop not found at default path. Start it manually if needed.
    )
)

:: Wait for Docker engine
echo.
echo [INFO] Waiting for Docker engine to be ready...
set /a DOCKER_WAIT=0

:WAIT_DOCKER
docker info >nul 2>&1
if not errorlevel 1 goto DOCKER_READY
set /a DOCKER_WAIT+=5
if %DOCKER_WAIT% GEQ 180 goto DOCKER_TIMEOUT
echo [INFO] Docker not ready yet... %DOCKER_WAIT%/180s
timeout /t 5 /nobreak >nul
goto WAIT_DOCKER

:DOCKER_TIMEOUT
echo.
echo [ERROR] Docker did not become ready within 180 seconds.
echo Check Docker Desktop and WSL2. Restart Windows if Docker was just installed.
echo.
pause
exit /b 1

:DOCKER_READY
echo [OK] Docker engine is ready.

:: Check Docker Compose
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose not available. Please update Docker Desktop.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker Compose found.

:: Ensure .env exists
echo.
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [INFO] .env created from .env.example
    ) else (
        echo [ERROR] .env.example not found.
        echo.
        pause
        exit /b 1
    )
) else (
    echo [INFO] .env found.
)

:: Ensure COMPOSE_PROJECT_NAME in .env
findstr /i /b "COMPOSE_PROJECT_NAME=" ".env" >nul 2>&1
if errorlevel 1 (
    echo COMPOSE_PROJECT_NAME=bulk-edit>> ".env"
    echo [INFO] Added COMPOSE_PROJECT_NAME=bulk-edit to .env
)

:: Stop old containers
echo.
echo [INFO] Checking old ERP Docker project...
docker compose -p fmcg-erp-system-main down --remove-orphans >nul 2>&1
echo [INFO] Removing bulk-edit containers and volumes...
docker compose -p bulk-edit down -v --remove-orphans

:: Show URLs
echo.
echo ============================================================
echo  Local URLs (available once services are ready):
echo    Frontend  : http://localhost:3100
echo    Backend   : http://localhost:8100
echo    API Docs  : http://localhost:8100/docs
echo    Health    : http://localhost:8100/api/v1/health
echo    PostgreSQL: localhost:55432
echo    Redis     : localhost:56379
echo.
echo  Docker Compose project: bulk-edit
echo ============================================================
echo.

:: Start services detached
echo [INFO] Building and starting services (clean)...
docker compose -p bulk-edit up -d --build
if errorlevel 1 (
    echo [ERROR] docker compose up failed. Check Docker logs above.
    echo.
    pause
    exit /b 1
)
echo [OK] Containers started. Running readiness checks...
echo.

:: Wait for backend health endpoint
echo [INFO] Waiting for backend at http://localhost:8100/api/v1/health
set /a BACKEND_WAIT=0

:WAIT_BACKEND
powershell -NoProfile -Command "try { $null = Invoke-WebRequest -Uri 'http://localhost:8100/api/v1/health' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto BACKEND_READY
set /a BACKEND_WAIT+=5
if %BACKEND_WAIT% GEQ 180 goto BACKEND_TIMEOUT
echo [INFO] Backend not ready yet... %BACKEND_WAIT%/180s
timeout /t 5 /nobreak >nul
goto WAIT_BACKEND

:BACKEND_TIMEOUT
echo.
echo [ERROR] Backend did not respond within 180 seconds.
echo Run to see logs: docker compose -p bulk-edit logs backend
echo.
pause
exit /b 1

:BACKEND_READY
echo [OK] Backend is ready.

:: Wait for frontend
echo [INFO] Waiting for frontend at http://localhost:3100
set /a FRONTEND_WAIT=0

:WAIT_FRONTEND
powershell -NoProfile -Command "try { $null = Invoke-WebRequest -Uri 'http://localhost:3100' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto FRONTEND_READY
set /a FRONTEND_WAIT+=5
if %FRONTEND_WAIT% GEQ 180 goto FRONTEND_TIMEOUT
echo [INFO] Frontend not ready yet... %FRONTEND_WAIT%/180s
timeout /t 5 /nobreak >nul
goto WAIT_FRONTEND

:FRONTEND_TIMEOUT
echo.
echo [ERROR] Frontend did not respond within 180 seconds.
echo Run to see logs: docker compose -p bulk-edit logs frontend
echo.
pause
exit /b 1

:FRONTEND_READY
echo [OK] Frontend is ready.
echo.

:: Optional local superuser seed
if exist "apps\backend\.local-superusers.env" (
    echo [INFO] Local superuser seed file found: apps\backend\.local-superusers.env
    set "SEED_CHOICE=N"
    set /p SEED_CHOICE=Run local superuser seed? [Y/N] (default N):
    if /I "!SEED_CHOICE!"=="Y" (
        echo [INFO] Running seed...
        docker compose -p bulk-edit exec -T backend python scripts/seed_local_superusers.py
        echo.
    ) else (
        echo [INFO] Skipping seed.
        echo.
    )
)

:: All ready - open browser
echo [INFO] All services are ready.
echo [INFO] Opening http://localhost:3100 ...
start "" "http://localhost:3100"
echo.

:: Stream logs
echo [INFO] Streaming logs. Press Ctrl+C to stop streaming.
echo [INFO] To stop all services: docker compose -p bulk-edit down
echo.
docker compose -p bulk-edit logs -f

echo.
echo [INFO] Log streaming stopped. Services may still be running.
echo [INFO] To stop all services: docker compose -p bulk-edit down
echo.
pause
