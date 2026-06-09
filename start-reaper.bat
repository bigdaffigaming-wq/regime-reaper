@echo off
title REGIME REAPER LAUNCHER
color 06

echo.
echo  ===============================================
echo   ☠  REGIME REAPER — STARTING UP
echo  ===============================================
echo.

cd /d "d:\REGIME PROJECT\regime-reaper"

:: Backend
echo  [1/3] Starting Backend (port 8093)...
start "REAPER BACKEND" cmd /k "title REAPER BACKEND && cd /d d:\REGIME PROJECT\regime-reaper\backend && color 06 && echo Starting FastAPI... && python -m uvicorn app.main:app --reload --port 8093"

timeout /t 3 /nobreak >nul

:: Frontend
echo  [2/3] Starting Frontend (port 8094)...
start "REAPER FRONTEND" cmd /k "title REAPER FRONTEND && cd /d d:\REGIME PROJECT\regime-reaper\frontend && color 06 && echo Starting React... && npm run dev"

timeout /t 2 /nobreak >nul

:: Discord Bot (only if .env has token)
echo  [3/3] Starting Discord Bot...
start "REAPER DISCORD" cmd /k "title REAPER DISCORD && cd /d d:\REGIME PROJECT\regime-reaper\discord_bot && color 06 && echo Starting Discord Bot... && python bot.py"

timeout /t 4 /nobreak >nul

:: Open dashboard
echo.
echo  Opening dashboard...
start http://localhost:8094

echo.
echo  ===============================================
echo   ☠  ALL SYSTEMS ONLINE
echo   Backend  → http://localhost:8093
echo   Frontend → http://localhost:8094
echo   API Docs → http://localhost:8093/docs
echo  ===============================================
echo.
pause
