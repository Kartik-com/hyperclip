@echo off
setlocal
cd /d "%~dp0"
title HyperClip Studio Local Server

set PATH=%~dp0bin;%PATH%

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY=%~dp0.venv\Scripts\python.exe"
) else (
    set "PY=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
)

echo =========================================================
echo   Starting HyperClip Swiss Studio (Local Web App)
echo   Opening: http://localhost:8484
echo =========================================================

start "" "http://localhost:8484"
"%PY%" studio.py

pause
