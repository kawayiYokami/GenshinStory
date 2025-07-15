@echo off
:: Switch command prompt to UTF-8 to prevent garbled characters
chcp 65001 > nul

title Frontend Server

set "PROJECT_ROOT=%~dp0"

echo ==================================================
echo  Starting Frontend Development Server
echo ==================================================
echo Project Root: %PROJECT_ROOT%
echo.

set "FRONTEND_DIR=%PROJECT_ROOT%web\frontend"
cd /d "%FRONTEND_DIR%"

if not exist "package.json" (
    echo [ERROR] package.json not found in %FRONTEND_DIR%
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo 'node_modules' directory not found. Running 'npm install'...
    npm install
    if %errorlevel% neq 0 (
        echo [ERROR] 'npm install' failed. Please check for errors.
        pause
        exit /b 1
    )
)

echo Starting Vite development server...
echo.

npm run dev

echo Server stopped.
pause