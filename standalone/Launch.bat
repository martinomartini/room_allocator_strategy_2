@echo off@echo off@echo off

REM ============================================

REM  KPMG Credentials Management SystemREM ============================================REM ============================================

REM  Self-Installing Launcher with Python Auto-Install

REM ============================================REM  KPMG Credentials Management SystemREM  KPMG Credentials Management System



echo.REM  Self-Installing LauncherREM  Automatic Launcher with Dependency Check

echo =============================================

echo  KPMG Credentials Management SystemREM ============================================REM ============================================

echo  Automatic Installer

echo =============================================

echo.

echo.echo.

REM Check if Python is installed

python --version >nul 2>&1echo =============================================echo =============================================

if errorlevel 1 (

    echo [INFO] Python is not installed. Installing Python automatically...echo  KPMG Credentials Management Systemecho  KPMG Credentials Management System

    echo This will take a few minutes...

    echo.echo  Automatic Installerecho =============================================

    

    REM Download Python installerecho =============================================echo.

    set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"

    echo Downloading Python 3.11...echo.

    curl -L -o "%PYTHON_INSTALLER%" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" 2>nul

    REM Check if Python is installed

    if errorlevel 1 (

        echo [ERROR] Failed to download Python installer.REM Check if Python is installedpython --version >nul 2>&1

        echo Please check your internet connection and try again.

        echo.python --version >nul 2>&1if errorlevel 1 (

        echo Alternatively, you can manually install Python from:

        echo https://www.python.org/downloads/if errorlevel 1 (    echo [ERROR] Python is not installed!

        echo.

        pause    echo [ERROR] Python is not installed!    echo.

        exit /b 1

    )    echo.    echo Please install Python 3.8 or higher from:

    

    echo [OK] Python installer downloaded    echo Please install Python 3.8 or higher from:    echo https://www.python.org/downloads/

    echo.

    echo Installing Python (this may take 3-5 minutes)...    echo https://www.python.org/downloads/    echo.

    echo Please wait...

    echo.    echo.    echo Make sure to check "Add Python to PATH" during installation.

    

    REM Install Python silently with PATH    echo Make sure to check "Add Python to PATH" during installation.    echo.

    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

        echo.    pause

    REM Wait for installation to complete

    timeout /t 10 /nobreak >nul    pause    exit /b 1

    

    REM Cleanup installer    exit /b 1)

    del "%PYTHON_INSTALLER%" >nul 2>&1

    )

    echo [OK] Python installed successfully!

    echo.echo [OK] Python found

    echo Refreshing environment variables...

    echo [OK] Python foundecho.

    REM Refresh PATH by re-reading environment

    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"echo.

    

    REM Verify Python is now availableREM Check if required packages are installed

    python --version >nul 2>&1

    if errorlevel 1 (REM Create application directoryecho Checking dependencies...

        echo [WARNING] Python installed but not yet in PATH.

        echo Please close this window and run the BAT file again.set "APP_DIR=%USERPROFILE%\KPMG_Credentials_System"python -c "import streamlit" >nul 2>&1

        echo.

        pauseif not exist "%APP_DIR%" (if errorlevel 1 (

        exit /b 0

    )    echo Creating application directory...    echo [INSTALLING] Required packages not found. Installing now...

)

    mkdir "%APP_DIR%"    echo This may take a few minutes on first run...

echo [OK] Python found

python --version    mkdir "%APP_DIR%\pages"    echo.

echo.

    mkdir "%APP_DIR%\.streamlit"    python -m pip install --upgrade pip

REM Create application directory

set "APP_DIR=%USERPROFILE%\KPMG_Credentials_System")    python -m pip install streamlit pandas openpyxl plotly requests python-pptx

if not exist "%APP_DIR%" (

    echo Creating application directory...    echo.

    mkdir "%APP_DIR%"

    mkdir "%APP_DIR%\pages"echo [OK] Application directory ready: %APP_DIR%    echo [OK] Dependencies installed successfully!

    mkdir "%APP_DIR%\.streamlit"

)echo.    echo.



echo [OK] Application directory ready: %APP_DIR%) else (

echo.

REM Download files from GitHub    echo [OK] All dependencies found

REM Download files from GitHub

echo Downloading application files from GitHub...echo Downloading application files from GitHub...    echo.

echo This may take a moment...

echo.echo This may take a moment...)



REM Download the entire repository as ZIPecho.

curl -L -o "%APP_DIR%\temp.zip" "https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip" 2>nul

REM Start the application

if errorlevel 1 (

    echo [ERROR] Failed to download files. Please check your internet connection.REM Download the entire repository as ZIPecho =============================================

    pause

    exit /b 1curl -L -o "%APP_DIR%\temp.zip" "https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip" 2>nulecho  Starting Credentials System...

)

echo =============================================

echo [OK] Files downloaded

echo.if errorlevel 1 (echo.



REM Extract only the standalone folder    echo [ERROR] Failed to download files. Please check your internet connection.echo The application will open in your browser shortly.

echo Extracting files...

powershell -Command "Expand-Archive -Path '%APP_DIR%\temp.zip' -DestinationPath '%APP_DIR%\temp' -Force" 2>nul    pauseecho Password: bud123



REM Copy standalone folder contents to APP_DIR    exit /b 1echo.

xcopy /E /I /Y "%APP_DIR%\temp\room_allocator_strategy_2-main\standalone\*" "%APP_DIR%" >nul

)echo To stop the application: Close this window or press Ctrl+C

REM Cleanup

del "%APP_DIR%\temp.zip" >nul 2>&1echo =============================================

rmdir /S /Q "%APP_DIR%\temp" >nul 2>&1

echo [OK] Files downloadedecho.

echo [OK] Files extracted and ready

echo.echo.



REM Check and install dependenciesREM Start Streamlit with proper settings

echo Checking Python dependencies...

python -c "import streamlit" >nul 2>&1REM Extract only the standalone folderpython -m streamlit run "%~dp0app.py" --server.headless=true --browser.gatherUsageStats=false --server.port=8501 --server.address=localhost

if errorlevel 1 (

    echo [INSTALLING] Required packages not found. Installing now...echo Extracting files...

    echo This may take a few minutes on first run...

    echo.powershell -Command "Expand-Archive -Path '%APP_DIR%\temp.zip' -DestinationPath '%APP_DIR%\temp' -Force" 2>nulREM If Streamlit exits, pause to show any errors

    python -m pip install --quiet --upgrade pip

    python -m pip install --quiet streamlit pandas openpyxl plotly requests python-pptxecho.

    echo.

    echo [OK] Dependencies installed successfully!REM Copy standalone folder contents to APP_DIRecho Application stopped.

    echo.

) else (xcopy /E /I /Y "%APP_DIR%\temp\room_allocator_strategy_2-main\standalone\*" "%APP_DIR%" >nulpause

    echo [OK] All dependencies found

    echo.

)REM Cleanup

del "%APP_DIR%\temp.zip" >nul 2>&1

REM Start the applicationrmdir /S /Q "%APP_DIR%\temp" >nul 2>&1

echo =============================================

echo  Starting Credentials System...echo [OK] Files extracted and ready

echo =============================================echo.

echo.

echo The application will open in your browser shortly.REM Check and install dependencies

echo Password for all tools: bud123echo Checking Python dependencies...

echo.python -c "import streamlit" >nul 2>&1

echo To stop: Close this window or press Ctrl+Cif errorlevel 1 (

echo =============================================    echo [INSTALLING] Required packages not found. Installing now...

echo.    echo This may take a few minutes on first run...

    echo.

REM Change to app directory and start Streamlit    python -m pip install --quiet --upgrade pip

cd /d "%APP_DIR%"    python -m pip install --quiet streamlit pandas openpyxl plotly requests python-pptx

python -m streamlit run app.py --server.headless=true --browser.gatherUsageStats=false --server.port=8501 --server.address=localhost    echo.

    echo [OK] Dependencies installed successfully!

REM If Streamlit exits, pause to show any errors    echo.

echo.) else (

echo Application stopped.    echo [OK] All dependencies found

pause    echo.

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
