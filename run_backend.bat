@echo off
:: Switch command prompt to UTF-8 to prevent garbled characters
chcp 65001 > nul

title Backend Server

set "PROJECT_ROOT=%~dp0"
set "VENV_PATH=%PROJECT_ROOT%.venv"

echo ==================================================
echo  Starting Backend Server
echo ==================================================
echo Project Root: %PROJECT_ROOT%
echo Virtual Env:  %VENV_PATH%
echo.

if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at %VENV_PATH%
    echo Please run 'python -m venv .venv' in the root directory first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call "%VENV_PATH%\Scripts\activate.bat"

where uvicorn >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] uvicorn is not installed in the virtual environment.
    echo Please run 'pip install uvicorn' after activating the venv.
    pause
    exit /b 1
)

cd /d "%PROJECT_ROOT%web\backend"

echo Starting FastAPI server with Uvicorn...
echo Visit http://127.0.0.1:8666 in your browser.
echo Press CTRL+C to stop the server.
echo.

uvicorn main:app --host 0.0.0.0 --port 8666 --reload

echo Server stopped.
pause