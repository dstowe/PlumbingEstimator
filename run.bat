@echo off
REM Plumbing Estimator - Quick Start Script
REM Double-click this file to run the application

echo ============================================================
echo Plumbing Estimator - Starting Application
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run install.ps1 first or create it manually with:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if app.py exists
if not exist "app.py" (
    echo ERROR: app.py not found!
    echo Make sure you're in the correct directory.
    pause
    exit /b 1
)

REM Start the application
echo.
echo Starting server...
echo.
echo ============================================================
echo Server will be available at: http://localhost:5000
echo.
echo Default admin login:
echo   Email: admin@example.com
echo   Password: admin123
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

python app.py

pause