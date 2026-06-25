@echo off
setlocal enabledelayedexpansion
title Bulk-Edit One-Click Clean Setup and Start

set "PROJECT_DIR=%USERPROFILE%\Desktop\Bulk-Edit"
set "REPO_URL=https://github.com/Sekiph82/Bulk-Edit.git"

echo.
echo ============================================================
echo  Bulk-Edit - One-Click Clean Setup and Start
echo  Docker Compose project: bulk-edit
echo ============================================================
echo.
echo  WARNING: This script will DELETE all local database volumes.
echo  All PostgreSQL data stored locally will be permanently lost.
echo  Use setup-and-start.bat instead to keep your data.
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

:: Step 1: Check winget
echo [STEP 1/7] Checking winget...
winget --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] winget is not installed.
    echo Please install App Installer from the Microsoft Store, then run this script again.
    echo.
    pause
    exit /b 1
)
echo [OK] winget found.
echo.

:: Step 2: Check / Install Git
echo [STEP 2/7] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Git not found. Installing via winget...
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    echo.
    git --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Git still not found after install.
        echo Close this window, open a new CMD window, and run this script again.
        echo.
        pause
        exit /b 1
    )
)
echo [OK] Git found.
echo.

:: Step 3: Check / Install Docker Desktop
echo [STEP 3/7] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Docker not found. Installing Docker Desktop via winget...
    winget install --id Docker.DockerDesktop -e --source winget --accept-package-agreements --accept-source-agreements
    echo.
    echo [WARN] Docker Desktop may require a Windows restart and WSL2 setup.
    echo [WARN] If Docker does not start, restart your computer and run this script again.
    echo.
    docker --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker still not found. Restart your computer and run this script again.
        echo.
        pause
        exit /b 1
    )
)
echo [OK] Docker CLI found.
echo.

:: Step 4: Clone or update repository
echo [STEP 4/7] Setting up repository...

if not exist "%PROJECT_DIR%" (
    echo [INFO] Project folder not found. Cloning from GitHub...
    git clone "%REPO_URL%" "%PROJECT_DIR%"
    if errorlevel 1 (
        echo [ERROR] Git clone failed. Check your internet connection and try again.
        echo.
        pause
        exit /b 1
    )
    echo [OK] Repository cloned to: %PROJECT_DIR%
) else (
    if exist "%PROJECT_DIR%\.git" (
        echo [INFO] Project folder found. Pulling latest changes...
        cd /d "%PROJECT_DIR%"
        git pull origin main
        if errorlevel 1 (
            echo [WARN] git pull failed. Continuing with existing files.
        )
        echo [OK] Repository up to date.
    ) else (
        echo.
        echo [ERROR] A folder already exists at:
        echo         %PROJECT_DIR%
        echo         but it is not a git repository.
        echo Please move or rename that folder manually, then run this script again.
        echo Your files have NOT been deleted.
        echo.
        pause
        exit /b 1
    )
)
echo.

cd /d "%PROJECT_DIR%"

:: Step 5: Configure environment
echo [STEP 5/7] Configuring environment...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [INFO] .env created from .env.example
    ) else (
        echo [ERROR] .env.example not found in project folder.
        echo.
        pause
        exit /b 1
    )
) else (
    echo [INFO] .env already exists.
)

findstr /i /b "COMPOSE_PROJECT_NAME=" ".env" >nul 2>&1
if errorlevel 1 (
    echo COMPOSE_PROJECT_NAME=bulk-edit>> ".env"
    echo [INFO] Added COMPOSE_PROJECT_NAME=bulk-edit to .env
)
echo.

:: Step 6: Start Docker Desktop and wait for engine
echo [STEP 6/7] Starting Docker Desktop...

set "DOCKER_DESKTOP_EXE=C:\Program Files\Docker\Docker\Docker Desktop.exe"
if exist "%DOCKER_DESKTOP_EXE%" (
    echo [INFO] Starting Docker Desktop...
    start "" "%DOCKER_DESKTOP_EXE%"
) else (
    echo [WARN] Docker Desktop executable not found at default path.
    echo [WARN] If Docker is installed elsewhere, start Docker Desktop manually or update this script.
)

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
echo.

:: Step 7: Clean reset and start
echo [STEP 7/7] Starting Bulk-Edit services (clean reset)...

echo [INFO] Checking old ERP Docker project...
docker compose -p fmcg-erp-system-main down --remove-orphans >nul 2>&1

echo [INFO] Removing existing bulk-edit containers and volumes...
docker compose -p bulk-edit down -v --remove-orphans

echo.
echo ============================================================
echo  Building and starting Bulk-Edit from scratch...
echo  This may take several minutes.
echo.
echo  Your browser will open automatically at:
echo    http://localhost:3100
echo.
echo  Other URLs:
echo    Backend API : http://localhost:8100
echo    API Docs    : http://localhost:8100/docs
echo    Health      : http://localhost:8100/api/v1/health
echo.
echo  Docker Compose project name: bulk-edit
echo.
echo  Press Ctrl+C to stop all services.
echo ============================================================
echo.

start "" cmd /c "timeout /t 12 /nobreak >nul && start http://localhost:3100"

docker compose -p bulk-edit up --build

echo.
echo [INFO] Docker stopped. Check logs above for any errors.
echo.
pause
