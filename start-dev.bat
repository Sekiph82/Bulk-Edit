@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================================
echo  Bulk-Edit - Local Dev Startup
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

echo.
echo [STEP 1/3] Stopping existing services...
docker compose down --remove-orphans

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
echo ============================================================
echo.

echo [STEP 3/3] Starting docker compose up --build (logs below)...
echo            Press Ctrl+C to stop all services.
echo.

docker compose up --build

echo.
echo [INFO] Services stopped.
echo.
pause
