@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================================
echo  Bulk-Edit - Local Dev Startup
echo  Docker Compose project: bulk-edit
echo ============================================================
echo.

:: ── 1. Check Docker CLI ─────────────────────────────────────
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker CLI not found. Install Docker Desktop first.
    echo         https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)
echo [OK] Docker CLI found.

:: ── 2. Start Docker Desktop ─────────────────────────────────
echo.
echo [INFO] Starting Docker Desktop if it is not already running...

set "DOCKER_DESKTOP_EXE=C:\Program Files\Docker\Docker\Docker Desktop.exe"

if exist "%DOCKER_DESKTOP_EXE%" (
    start "" "%DOCKER_DESKTOP_EXE%"
    echo [INFO] Docker Desktop start command sent.
) else (
    echo [WARN] Docker Desktop executable was not found at:
    echo        %DOCKER_DESKTOP_EXE%
    echo [WARN] If Docker Desktop is installed in another location, please update this script.
)

:: ── 3. Wait for Docker engine ────────────────────────────────
echo.
echo [INFO] Waiting for Docker engine to become ready...
echo [INFO] This may take 30-120 seconds when Docker Desktop is closed.

set /a DOCKER_WAIT_SECONDS=0

:WAIT_FOR_DOCKER_ENGINE
docker info >nul 2>&1
if not errorlevel 1 goto DOCKER_ENGINE_READY

set /a DOCKER_WAIT_SECONDS+=5
if %DOCKER_WAIT_SECONDS% GEQ 180 goto DOCKER_ENGINE_NOT_READY

echo [INFO] Docker engine is not ready yet. Waiting 5 seconds... %DOCKER_WAIT_SECONDS%/180
timeout /t 5 /nobreak >nul
goto WAIT_FOR_DOCKER_ENGINE

:DOCKER_ENGINE_NOT_READY
echo.
echo [ERROR] Docker Desktop did not become ready within 180 seconds.
echo.
echo Please check:
echo   1. Docker Desktop opened successfully.
echo   2. Docker Desktop finished starting.
echo   3. WSL2 is installed and working.
echo   4. If Docker Desktop was just installed, restart Windows and run this script again.
echo.
pause
exit /b 1

:DOCKER_ENGINE_READY
echo [OK] Docker engine is ready.

:: ── 4. Check Docker Compose ──────────────────────────────────
docker compose version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker Compose is not available. Update Docker Desktop.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker Compose found.

:: ── 5. Ensure .env exists ────────────────────────────────────
echo.
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [INFO] .env created from .env.example
    ) else (
        echo [WARN] .env.example not found. Create .env manually before running.
    )
) else (
    echo [INFO] .env found.
)

:: ── 6. Ensure COMPOSE_PROJECT_NAME in .env ───────────────────
findstr /i "COMPOSE_PROJECT_NAME" ".env" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo COMPOSE_PROJECT_NAME=bulk-edit>> ".env"
    echo [INFO] Added COMPOSE_PROJECT_NAME=bulk-edit to .env
)

:: ── 7. Stop old ERP project ──────────────────────────────────
echo.
echo [INFO] Checking for old ERP Docker project: fmcg-erp-system-main
docker compose -p fmcg-erp-system-main down --remove-orphans >nul 2>&1
echo [INFO] Old ERP project check done.

:: ── 8. Stop existing bulk-edit containers ────────────────────
echo.
echo [INFO] Stopping existing bulk-edit services...
docker compose -p bulk-edit down --remove-orphans

:: ── 9. Show URLs ─────────────────────────────────────────────
echo.
echo ============================================================
echo  Local URLs (available once services are ready):
echo.
echo   Frontend  : http://localhost:3100
echo   Backend   : http://localhost:8100
echo   API Docs  : http://localhost:8100/docs
echo   Health    : http://localhost:8100/api/v1/health
echo   PostgreSQL: localhost:55432
echo   Redis     : localhost:56379
echo.
echo   Docker Compose project name: bulk-edit
echo ============================================================
echo.

:: ── 10. Open browser after delay (background) ────────────────
start "" cmd /c "timeout /t 12 /nobreak >nul && start http://localhost:3100"

:: ── 11. Start services ───────────────────────────────────────
echo [INFO] Starting docker compose -p bulk-edit up --build (logs below)...
echo        Press Ctrl+C to stop all services.
echo.

docker compose -p bulk-edit up --build

echo.
echo [INFO] Services stopped.
echo.
pause
