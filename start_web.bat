@echo off
echo Starting local web server...

:: Navigate to the directory of the static site
cd /d "%~dp0\web\docs-site\dist"

echo Launching site at http://localhost:8000
:: Open the default browser to the local server URL
start http://localhost:8000

:: Start Python's built-in HTTP server on port 8000
python -m http.server 8000