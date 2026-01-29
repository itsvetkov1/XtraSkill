@echo off
echo ===================================
echo BA Assistant - System Prompt Tests
echo ===================================
echo.

echo Step 1: Checking Python environment...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo Step 2: Starting backend server...
echo (This will open in a new window)
start "BA Assistant Backend" cmd /k "cd /d %~dp0 && python -m uvicorn app.main:app --reload --port 8000"

echo.
echo Waiting 10 seconds for backend to start...
timeout /t 10 /nobreak > nul

echo.
echo Step 3: Running automated tests...
python test_system_prompt.py

echo.
echo ===================================
echo Tests complete!
echo ===================================
echo.
echo The backend server is still running in the other window.
echo Close that window when you're done testing.
echo.
pause
