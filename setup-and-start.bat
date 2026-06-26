@echo off
setlocal enabledelayedexpansion
title Bulk-Edit One-Click Setup and Start

set "PROJECT_DIR=%USERPROFILE%\Desktop\Bulk-Edit"
set "REPO_URL=https://github.com/Sekiph82/Bulk-Edit.git"

echo.
echo ============================================================
echo  Bulk-Edit - One-Click Setup and Start
echo  Docker Compose project: bulk-edit
echo ============================================================
echo.
echo  This script will:
echo    1. Check and install required tools (Git, Docker Desktop)
echo    2. Clone or update the project repository
echo    3. Create .env from .env.example if missing
echo    4. Start Docker Desktop and wait for engine
echo    5. Build and start all services
echo    6. Wait for backend and frontend to be ready
echo    7. Open http://localhost:3100 in your browser
echo.
echo ============================================================
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
        echo The repository may not have downloaded correctly.
        echo Delete the project folder and run this script again.
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
docker info >nul 2>&1
if errorlevel 1 (
    if exist "%DOCKER_DESKTOP_EXE%" (
        echo [INFO] Starting Docker Desktop...
        start "" "%DOCKER_DESKTOP_EXE%"
    ) else (
        echo [WARN] Docker Desktop not found at default path. Start it manually if needed.
    )
)

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
echo.

:: Step 7: Start services
echo [STEP 7/7] Starting Bulk-Edit services...

echo [INFO] Checking old ERP Docker project...
docker compose -p fmcg-erp-system-main down --remove-orphans >nul 2>&1

echo [INFO] Stopping any existing bulk-edit services...
docker compose -p bulk-edit down --remove-orphans

echo.
echo ============================================================
echo  Building and starting Bulk-Edit...
echo  This may take several minutes on first run.
echo.
echo  Other URLs once ready:
echo    Backend API : http://localhost:8100
echo    API Docs    : http://localhost:8100/docs
echo    Health      : http://localhost:8100/api/v1/health
echo.
echo  Docker Compose project: bulk-edit
echo ============================================================
echo.

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

:: All ready - open browser
echo [INFO] All services are ready.
echo [INFO] Opening http://localhost:3100 ...
start "" "http://localhost:3100"
echo.

echo [INFO] Docker Compose is running in the background.
echo [INFO] To see logs: docker compose -p bulk-edit logs -f
echo [INFO] To stop services: docker compose -p bulk-edit down
echo.
pause
