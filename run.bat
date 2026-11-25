@echo off
setlocal
cd /d "%~dp0"

:: 1. Add embedded bin (ffmpeg) to PATH
set "PATH=%~dp0bin;%PATH%"

:: 2. Check if .venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [HyperClip] Virtual environment not found. Setting up...
    python -m venv .venv 2>nul || py -3 -m venv .venv 2>nul || "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

:: 3. Run HyperClip with all passed arguments
python run.py %*

endlocal
