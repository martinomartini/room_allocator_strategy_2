@echo off
REM Project Database Viewer - Easy Launcher
REM Double-click this file to start the app

echo.
echo ========================================
echo  Project Database Viewer
echo ========================================
echo.
echo Starting application...
echo.

REM Start Streamlit standalone app in background
start /B streamlit run "%~dp0app_standalone.py" --server.headless=true --browser.gatherUsageStats=false

REM Wait a moment for server to start
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:8501

echo.
echo Browser should open automatically!
echo If not, navigate to: http://localhost:8501
echo.
echo Password: bud123
echo.
echo Press Ctrl+C to stop the application
echo.
pause
