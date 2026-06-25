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

:: Check Docker
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker not found. Install Docker Desktop first.
    echo         https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

:: Check Docker Compose
docker compose version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker Compose not available. Update Docker Desktop.
    echo.
    pause
    exit /b 1
)

:: Check .env
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

:: Ensure COMPOSE_PROJECT_NAME is in .env
findstr /i "COMPOSE_PROJECT_NAME" ".env" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo COMPOSE_PROJECT_NAME=bulk-edit>> ".env"
    echo [INFO] Added COMPOSE_PROJECT_NAME=bulk-edit to .env
)

echo.
echo [INFO] Checking for old ERP Docker project: fmcg-erp-system-main
docker compose -p fmcg-erp-system-main down --remove-orphans >nul 2>&1
echo [INFO] Old ERP project check done.

echo.
echo [STEP 1/3] Stopping existing bulk-edit services...
docker compose -p bulk-edit down --remove-orphans

echo.
echo [STEP 2/3] Building and starting services...
echo            This may take a few minutes on first run.
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

echo [STEP 3/3] Starting docker compose -p bulk-edit up --build (logs below)...
echo            Press Ctrl+C to stop all services.
echo.

docker compose -p bulk-edit up --build

echo.
echo [INFO] Services stopped.
echo.
pause
