@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo    Agent Swarm Launcher
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [Error] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Starting API server...
echo [Info] Server will run at http://localhost:5000
echo.

python api_server.py

pause
