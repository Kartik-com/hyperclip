@echo off
setlocal
cd /d "%~dp0"
title HyperClip Studio Local Server

set PATH=%~dp0bin;%PATH%

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY=%~dp0.venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PY=python"
    ) else (
        set "PY=py"
    )
)

echo =========================================================
echo   Starting HyperClip Swiss Studio (Local Web App)
echo   Opening: http://localhost:8484
echo =========================================================

start "" "http://localhost:8484"
"%PY%" studio.py

pause
