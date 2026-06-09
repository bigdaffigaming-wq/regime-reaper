@echo off
title REGIME REAPER — INSTALL
color 06

echo.
echo  ===============================================
echo   ☠  REGIME REAPER — FIRST TIME SETUP
echo  ===============================================
echo.

cd /d "d:\REGIME PROJECT\regime-reaper"

:: Backend deps
echo  [1/3] Installing Python dependencies...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo  ERROR: pip install failed. Make sure Python is installed.
    pause
    exit /b 1
)
cd ..

:: Create backend .env if missing
if not exist "backend\.env" (
    echo  [2/3] Creating backend .env from example...
    copy "backend\.env.example" "backend\.env"
    echo  *** IMPORTANT: Edit backend\.env and add your API keys ***
) else (
    echo  [2/3] backend\.env already exists, skipping.
)

:: Frontend deps
echo  [3/3] Installing Node dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo  ERROR: npm install failed. Make sure Node.js is installed.
    pause
    exit /b 1
)

:: Create frontend .env if missing
if not exist ".env" (
    copy ".env.example" ".env"
)
cd ..

:: Discord bot deps
echo  [4/4] Installing Discord bot dependencies...
cd discord_bot
pip install -r requirements.txt
cd ..

echo.
echo  ===============================================
echo   INSTALL COMPLETE
echo.
echo   Next steps:
echo   1. Edit backend\.env and add your API keys
echo   2. Run start-reaper.bat to launch
echo  ===============================================
echo.
pause
