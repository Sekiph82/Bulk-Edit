@echo off
setlocal enabledelayedexpansion
title Bulk-Edit Local Dev Startup

cd /d "%~dp0"

echo.
echo ============================================================
echo  Bulk-Edit - Local Dev Startup
echo  Docker Compose project: bulk-edit
echo ============================================================
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

:: Start Docker Desktop
set "DOCKER_DESKTOP_EXE=C:\Program Files\Docker\Docker\Docker Desktop.exe"
if exist "%DOCKER_DESKTOP_EXE%" (
    echo [INFO] Starting Docker Desktop...
    start "" "%DOCKER_DESKTOP_EXE%"
) else (
    echo [WARN] Docker Desktop executable not found at default path.
    echo [WARN] If Docker is installed elsewhere, start Docker Desktop manually or update this script.
)

:: Wait for Docker engine
echo.
echo [INFO] Waiting for Docker engine...
set /a DOCKER_WAIT_SECONDS=0

:WAIT_FOR_DOCKER
docker info >nul 2>&1
if not errorlevel 1 goto DOCKER_READY

set /a DOCKER_WAIT_SECONDS+=5
if %DOCKER_WAIT_SECONDS% GEQ 180 goto DOCKER_NOT_READY

echo [INFO] Docker is not ready yet. Waiting 5 seconds... %DOCKER_WAIT_SECONDS%/180
timeout /t 5 /nobreak >nul
goto WAIT_FOR_DOCKER

:DOCKER_NOT_READY
echo.
echo [ERROR] Docker Desktop did not become ready within 180 seconds.
echo Please check Docker Desktop, WSL2, or restart Windows if Docker was just installed.
echo.
pause
exit /b 1

:DOCKER_READY
echo [OK] Docker engine is ready.

:: Check Docker Compose
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not available.
    echo Please update Docker Desktop.
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

:: Stop old ERP project safely
echo.
echo [INFO] Checking old ERP Docker project...
docker compose -p fmcg-erp-system-main down --remove-orphans >nul 2>&1

:: Stop old bulk-edit containers
echo [INFO] Stopping old bulk-edit containers...
docker compose -p bulk-edit down --remove-orphans

:: Show URLs
echo.
echo ============================================================
echo  Local URLs (available once services are ready):
echo.
echo    Frontend  : http://localhost:3100
echo    Backend   : http://localhost:8100
echo    API Docs  : http://localhost:8100/docs
echo    Health    : http://localhost:8100/api/v1/health
echo    PostgreSQL: localhost:55432
echo    Redis     : localhost:56379
echo.
echo    Docker Compose project name: bulk-edit
echo ============================================================
echo.

:: Open browser after delay in background
start "" cmd /c "timeout /t 12 /nobreak >nul && start http://localhost:3100"

:: Start services
echo [INFO] Starting docker compose -p bulk-edit up --build ...
echo [INFO] Press Ctrl+C to stop all services.
echo.
docker compose -p bulk-edit up --build

echo.
echo [INFO] Services stopped.
echo.
pause
