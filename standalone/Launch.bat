@echo off
REM ============================================
REM  KPMG Credentials Management System
REM  Automatic Launcher with Dependency Check
REM ============================================

echo.
echo =============================================
echo  KPMG Credentials Management System
echo =============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check if required packages are installed
echo Checking dependencies...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [INSTALLING] Required packages not found. Installing now...
    echo This may take a few minutes on first run...
    echo.
    python -m pip install --upgrade pip
    python -m pip install streamlit pandas openpyxl plotly requests python-pptx
    echo.
    echo [OK] Dependencies installed successfully!
    echo.
) else (
    echo [OK] All dependencies found
    echo.
)

REM Start the application
echo =============================================
echo  Starting Credentials System...
echo =============================================
echo.
echo The application will open in your browser shortly.
echo Password: bud123
echo.
echo To stop the application: Close this window or press Ctrl+C
echo =============================================
echo.

REM Start Streamlit with proper settings
python -m streamlit run "%~dp0app.py" --server.headless=true --browser.gatherUsageStats=false --server.port=8501 --server.address=localhost

REM If Streamlit exits, pause to show any errors
echo.
echo Application stopped.
pause
