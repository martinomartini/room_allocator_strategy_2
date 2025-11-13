@echo off
REM ============================================
REM  KPMG Credentials Management System
REM  Automatic Launcher
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
python --version
echo.

REM Create application directory
set "APP_DIR=%USERPROFILE%\KPMG_Credentials_System"
if not exist "%APP_DIR%" (
    echo Creating application directory...
    mkdir "%APP_DIR%"
    mkdir "%APP_DIR%\pages"
    mkdir "%APP_DIR%\.streamlit"
)

echo [OK] Application directory ready: %APP_DIR%
echo.

REM Download files from GitHub
echo Downloading application files from GitHub...
echo This may take a moment...
echo.

powershell -Command "$ProgressPreference = 'SilentlyContinue'; try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host 'Downloading...'; Invoke-WebRequest -Uri 'https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip' -OutFile '%APP_DIR%\temp.zip' -UseBasicParsing; Write-Host 'Download complete!'; exit 0 } catch { Write-Host 'Error:' $_.Exception.Message; exit 1 }"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to download files. Please check your internet connection.
    echo.
    pause
    exit /b 1
)

echo [OK] Files downloaded
echo.

REM Extract files
echo Extracting files...
powershell -Command "$ProgressPreference = 'SilentlyContinue'; try { Expand-Archive -Path '%APP_DIR%\temp.zip' -DestinationPath '%APP_DIR%\temp' -Force; Write-Host 'Extraction complete!'; exit 0 } catch { Write-Host 'Error:' $_.Exception.Message; exit 1 }"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to extract files.
    echo.
    pause
    exit /b 1
)

REM Copy standalone folder contents
xcopy /E /I /Y "%APP_DIR%\temp\room_allocator_strategy_2-main\standalone\*" "%APP_DIR%" >nul 2>&1

REM Cleanup
del "%APP_DIR%\temp.zip" >nul 2>&1
rmdir /S /Q "%APP_DIR%\temp" >nul 2>&1

echo [OK] Files extracted and ready
echo.

REM Check and install dependencies
echo Checking Python dependencies...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [INSTALLING] Required packages not found. Installing now...
    echo This may take a few minutes on first run...
    echo.
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet streamlit pandas openpyxl plotly requests python-pptx
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
echo Password for all tools: bud123
echo.
echo To stop: Close this window or press Ctrl+C
echo =============================================
echo.

REM Change to app directory and start Streamlit
cd /d "%APP_DIR%"
python -m streamlit run app.py --server.headless=true --browser.gatherUsageStats=false --server.port=8501 --server.address=localhost

REM If Streamlit exits, pause to show any errors
echo.
echo Application stopped.
pause
