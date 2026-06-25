@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Bulk-Edit One-Click Clean Setup and Start

set "PROJECT_DIR=%USERPROFILE%\Desktop\Bulk-Edit"
set "REPO_URL=https://github.com/Sekiph82/Bulk-Edit.git"
set "FRONTEND_URL=http://localhost:3100"

echo.
echo ============================================================
echo  Bulk-Edit - One-Click CLEAN Setup and Start
echo  Docker Compose project: bulk-edit
echo ============================================================
echo.
echo  WARNING: This script will DELETE all local database volumes.
echo  All PostgreSQL data stored locally will be permanently lost.
echo.
echo  Use setup-and-start.bat instead if you want to keep your data.
echo.
echo ============================================================
echo.

set /p CONFIRM=This will delete local database volumes. Type YES to continue:
if /I not "%CONFIRM%"=="YES" (
    echo.
    echo [CANCELLED] No changes made. Run setup-and-start.bat to start without data loss.
    echo.
    pause
    exit /b 1
)
echo.

:: ============================================================
:: STEP 1: Check winget
:: ============================================================
echo [STEP 1/7] Checking winget (Windows Package Manager)...
winget --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] winget is not installed.
    echo         Please install "App Installer" from the Microsoft Store,
    echo         then run this script again.
    echo.
    pause
    exit /b 1
)
echo [OK] winget found.
echo.

:: ============================================================
:: STEP 2: Check / Install Git
:: ============================================================
echo [STEP 2/7] Checking Git...
git --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Git not found. Installing via winget...
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    echo.
    git --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Git still not found after install.
        echo         Close this window, open a new CMD, and run this script again.
        echo.
        pause
        exit /b 1
    )
)
echo [OK] Git found.
echo.

:: ============================================================
:: STEP 3: Check / Install Docker Desktop
:: ============================================================
echo [STEP 3/7] Checking Docker...
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Docker not found. Installing Docker Desktop via winget...
    winget install --id Docker.DockerDesktop -e --source winget --accept-package-agreements --accept-source-agreements
    echo.
    echo [WARN] Docker Desktop may require a Windows restart and WSL2 setup.
    echo        If Docker does not start, restart your computer and run this script again.
    echo.
    docker --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Docker still not found. Restart your computer and run this script again.
        echo.
        pause
        exit /b 1
    )
)
echo [OK] Docker found.
echo.

:: ============================================================
:: STEP 4: Start Docker Desktop and wait for engine
:: ============================================================
echo [STEP 4/7] Starting Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" >nul 2>&1
echo [INFO] Waiting for Docker engine to start...
timeout /t 10 /nobreak >nul

docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo [WAIT] Docker engine is not running yet.
    echo        Please wait until Docker Desktop shows "Engine running" in its tray icon,
    echo        then press any key to continue.
    echo.
    pause
    docker info >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Docker engine is still not running.
        echo         Make sure Docker Desktop is fully started, then run this script again.
        echo.
        pause
        exit /b 1
    )
)
echo [OK] Docker engine is running.
echo.

:: ============================================================
:: STEP 5: Check Docker Compose
:: ============================================================
echo [STEP 5/7] Checking Docker Compose...
docker compose version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker Compose is not available.
    echo         Docker Desktop must be fully installed and running.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker Compose found.
echo.

:: ============================================================
:: STEP 6: Clone or update repository
:: ============================================================
echo [STEP 6/7] Setting up repository...

if not exist "%PROJECT_DIR%" (
    echo [INFO] Project folder not found. Cloning from GitHub...
    git clone "%REPO_URL%" "%PROJECT_DIR%"
    if %ERRORLEVEL% neq 0 (
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
        if %ERRORLEVEL% neq 0 (
            echo [WARN] git pull failed. Continuing with existing files.
        )
        echo [OK] Repository up to date.
    ) else (
        echo.
        echo [ERROR] A folder already exists at:
        echo         %PROJECT_DIR%
        echo         but it is not a git repository.
        echo.
        echo         Please move or rename that folder manually, then run this script again.
        echo         Your files have NOT been deleted.
        echo.
        pause
        exit /b 1
    )
)
echo.

:: ============================================================
:: STEP 7: Configure environment and start services (clean reset)
:: ============================================================
cd /d "%PROJECT_DIR%"

echo [STEP 7/7] Configuring environment...
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
echo [INFO] Removing existing bulk-edit containers and volumes (clean reset)...
docker compose -p bulk-edit down -v --remove-orphans

echo.
echo ============================================================
echo  Building and starting Bulk-Edit from scratch...
echo  This may take several minutes.
echo.
echo  Once ready, your browser will open automatically at:
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

:: Open browser after delay in background, then stream Docker logs
start "" cmd /c "timeout /t 12 /nobreak >nul && start http://localhost:3100"

docker compose -p bulk-edit up --build

echo.
echo [INFO] Docker stopped. Check logs above for any errors.
echo.
pause
