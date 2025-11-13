@echo off
REM ============================================
REM  KPMG Credentials Management System
REM  Simple Launcher
REM ============================================

echo.
echo =============================================
echo  KPMG Credentials Management System
echo =============================================
echo.

REM Try py launcher first (most reliable)
py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    goto :python_found
)

REM Try python command
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :python_found
)

echo [ERROR] Python not found. Please install Python 3.8+ from python.org
pause
exit /b 1

:python_found
echo [OK] Python found
%PYTHON_CMD% --version
echo.

REM Set up directory
set "APP_DIR=%USERPROFILE%\KPMG_Credentials_System"
if not exist "%APP_DIR%" mkdir "%APP_DIR%"

echo [OK] Application directory: %APP_DIR%
echo.

REM Download from GitHub
echo Downloading from GitHub...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip' -OutFile '%APP_DIR%\temp.zip'"

if errorlevel 1 (
    echo [ERROR] Download failed
    pause
    exit /b 1
)

REM Extract
echo Extracting...
powershell -Command "Expand-Archive -Path '%APP_DIR%\temp.zip' -DestinationPath '%APP_DIR%\temp' -Force"
xcopy /E /I /Y "%APP_DIR%\temp\room_allocator_strategy_2-main\standalone\*" "%APP_DIR%" >nul
del "%APP_DIR%\temp.zip" >nul 2>&1
rmdir /S /Q "%APP_DIR%\temp" >nul 2>&1

echo [OK] Files ready
echo.

REM Install packages
echo Installing Python packages...
%PYTHON_CMD% -m pip install --user streamlit pandas openpyxl plotly requests python-pptx

echo.
echo =============================================
echo  Starting Application...
echo =============================================
echo.
echo Browser will open at http://localhost:8501
echo Password: bud123
echo.
echo Press Ctrl+C to stop
echo =============================================
echo.

REM Run Streamlit
cd /d "%APP_DIR%"
%PYTHON_CMD% -m streamlit run app.py

pause
