@echo off
echo ==============================================================
echo        HyperClip 1-Click Windows Setup (NVIDIA GPU Ready)
echo ==============================================================

python -V >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in PATH! Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment (.venv)...
python -m venv .venv
call .venv\Scripts\activate.bat

echo [2/4] Installing core dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/4] Installing PyTorch with CUDA for RTX GPU acceleration...
nvidia-smi >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] NVIDIA GPU detected! Installing CUDA 12.1 PyTorch...
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo [INFO] No NVIDIA GPU detected. Installing CPU PyTorch...
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
)

echo [4/4] Setting up environment configuration...
if not exist .env (
    copy .env.example .env
    echo [INFO] Created .env file. Please edit .env with your FreeLLMAPI or Gemini key!
)

echo ==============================================================
echo        HyperClip is Ready!
echo ==============================================================
echo Run: .venv\Scripts\python run.py "https://youtu.be/..."
pause
