@echo off@echo off

REM ============================================REM ============================================

REM  KPMG Credentials Management SystemREM  KPMG Credentials Management System

REM  Self-Installing LauncherREM  Automatic Launcher with Dependency Check

REM ============================================REM ============================================



echo.echo.

echo =============================================echo =============================================

echo  KPMG Credentials Management Systemecho  KPMG Credentials Management System

echo  Automatic Installerecho =============================================

echo =============================================echo.

echo.

REM Check if Python is installed

REM Check if Python is installedpython --version >nul 2>&1

python --version >nul 2>&1if errorlevel 1 (

if errorlevel 1 (    echo [ERROR] Python is not installed!

    echo [ERROR] Python is not installed!    echo.

    echo.    echo Please install Python 3.8 or higher from:

    echo Please install Python 3.8 or higher from:    echo https://www.python.org/downloads/

    echo https://www.python.org/downloads/    echo.

    echo.    echo Make sure to check "Add Python to PATH" during installation.

    echo Make sure to check "Add Python to PATH" during installation.    echo.

    echo.    pause

    pause    exit /b 1

    exit /b 1)

)

echo [OK] Python found

echo [OK] Python foundecho.

echo.

REM Check if required packages are installed

REM Create application directoryecho Checking dependencies...

set "APP_DIR=%USERPROFILE%\KPMG_Credentials_System"python -c "import streamlit" >nul 2>&1

if not exist "%APP_DIR%" (if errorlevel 1 (

    echo Creating application directory...    echo [INSTALLING] Required packages not found. Installing now...

    mkdir "%APP_DIR%"    echo This may take a few minutes on first run...

    mkdir "%APP_DIR%\pages"    echo.

    mkdir "%APP_DIR%\.streamlit"    python -m pip install --upgrade pip

)    python -m pip install streamlit pandas openpyxl plotly requests python-pptx

    echo.

echo [OK] Application directory ready: %APP_DIR%    echo [OK] Dependencies installed successfully!

echo.    echo.

) else (

REM Download files from GitHub    echo [OK] All dependencies found

echo Downloading application files from GitHub...    echo.

echo This may take a moment...)

echo.

REM Start the application

REM Download the entire repository as ZIPecho =============================================

curl -L -o "%APP_DIR%\temp.zip" "https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip" 2>nulecho  Starting Credentials System...

echo =============================================

if errorlevel 1 (echo.

    echo [ERROR] Failed to download files. Please check your internet connection.echo The application will open in your browser shortly.

    pauseecho Password: bud123

    exit /b 1echo.

)echo To stop the application: Close this window or press Ctrl+C

echo =============================================

echo [OK] Files downloadedecho.

echo.

REM Start Streamlit with proper settings

REM Extract only the standalone folderpython -m streamlit run "%~dp0app.py" --server.headless=true --browser.gatherUsageStats=false --server.port=8501 --server.address=localhost

echo Extracting files...

powershell -Command "Expand-Archive -Path '%APP_DIR%\temp.zip' -DestinationPath '%APP_DIR%\temp' -Force" 2>nulREM If Streamlit exits, pause to show any errors

echo.

REM Copy standalone folder contents to APP_DIRecho Application stopped.

xcopy /E /I /Y "%APP_DIR%\temp\room_allocator_strategy_2-main\standalone\*" "%APP_DIR%" >nulpause


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
