@echo off@echo off@echo off@echo off

REM ============================================

REM  KPMG Credentials Management SystemREM ============================================

REM  Self-Installing Launcher with Python Auto-Install

REM ============================================REM  KPMG Credentials Management SystemREM ============================================REM ============================================



echo.REM  Self-Installing Launcher with Python Auto-Install

echo =============================================

echo  KPMG Credentials Management SystemREM ============================================REM  KPMG Credentials Management SystemREM  KPMG Credentials Management System

echo  Automatic Installer

echo =============================================

echo.

echo.REM  Self-Installing LauncherREM  Automatic Launcher with Dependency Check

REM Check if Python is installed

python --version >nul 2>&1echo =============================================

if errorlevel 1 (

    echo [INFO] Python is not installed. Installing Python automatically...echo  KPMG Credentials Management SystemREM ============================================REM ============================================

    echo This will take a few minutes...

    echo.echo  Automatic Installer

    

    REM Download Python installerecho =============================================

    set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"

    echo Downloading Python 3.11...echo.

    curl -L -o "%PYTHON_INSTALLER%" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" 2>nul

    echo.echo.

    if errorlevel 1 (

        echo [ERROR] Failed to download Python installer.REM Check if Python is installed

        echo Please check your internet connection and try again.

        echo.python --version >nul 2>&1echo =============================================echo =============================================

        echo Alternatively, you can manually install Python from:

        echo https://www.python.org/downloads/if errorlevel 1 (

        echo.

        pause    echo [INFO] Python is not installed. Installing Python automatically...echo  KPMG Credentials Management Systemecho  KPMG Credentials Management System

        exit /b 1

    )    echo This will take a few minutes...

    

    echo [OK] Python installer downloaded    echo.echo  Automatic Installerecho =============================================

    echo.

    echo Installing Python (this may take 3-5 minutes)...    

    echo Please wait - DO NOT CLOSE THIS WINDOW...

    echo.    REM Download Python installerecho =============================================echo.

    

    REM Install Python silently with PATH and wait for completion    set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"

    start /wait "" "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

        echo Downloading Python 3.11...echo.

    REM Cleanup installer

    del "%PYTHON_INSTALLER%" >nul 2>&1    curl -L -o "%PYTHON_INSTALLER%" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" 2>nul

    

    echo [OK] Python installed successfully!    REM Check if Python is installed

    echo.

        if errorlevel 1 (

    REM Refresh PATH by re-reading environment

    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"        echo [ERROR] Failed to download Python installer.REM Check if Python is installedpython --version >nul 2>&1

    

    REM Verify Python is now available        echo Please check your internet connection and try again.

    python --version >nul 2>&1

    if errorlevel 1 (        echo.python --version >nul 2>&1if errorlevel 1 (

        echo [INFO] Python installed successfully!

        echo Please CLOSE THIS WINDOW and run the BAT file again to start the application.        echo Alternatively, you can manually install Python from:

        echo.

        pause        echo https://www.python.org/downloads/if errorlevel 1 (    echo [ERROR] Python is not installed!

        exit /b 0

    )        echo.

    

    echo Python is now ready!        pause    echo [ERROR] Python is not installed!    echo.

    echo.

)        exit /b 1



echo [OK] Python found    )    echo.    echo Please install Python 3.8 or higher from:

python --version

echo.    



REM Create application directory    echo [OK] Python installer downloaded    echo Please install Python 3.8 or higher from:    echo https://www.python.org/downloads/

set "APP_DIR=%USERPROFILE%\KPMG_Credentials_System"

if not exist "%APP_DIR%" (    echo.

    echo Creating application directory...

    mkdir "%APP_DIR%"    echo Installing Python (this may take 3-5 minutes)...    echo https://www.python.org/downloads/    echo.

    mkdir "%APP_DIR%\pages"

    mkdir "%APP_DIR%\.streamlit"    echo Please wait...

)

    echo.    echo.    echo Make sure to check "Add Python to PATH" during installation.

echo [OK] Application directory ready: %APP_DIR%

echo.    



REM Download files from GitHub    REM Install Python silently with PATH    echo Make sure to check "Add Python to PATH" during installation.    echo.

echo Downloading application files from GitHub...

echo This may take a moment...    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

echo.

        echo.    pause

REM Download the entire repository as ZIP

curl -L -o "%APP_DIR%\temp.zip" "https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip" 2>nul    REM Wait for installation to complete



if errorlevel 1 (    timeout /t 10 /nobreak >nul    pause    exit /b 1

    echo [ERROR] Failed to download files. Please check your internet connection.

    pause    

    exit /b 1

)    REM Cleanup installer    exit /b 1)



echo [OK] Files downloaded    del "%PYTHON_INSTALLER%" >nul 2>&1

echo.

    )

REM Extract only the standalone folder

echo Extracting files...    echo [OK] Python installed successfully!

powershell -Command "Expand-Archive -Path '%APP_DIR%\temp.zip' -DestinationPath '%APP_DIR%\temp' -Force" 2>nul

    echo.echo [OK] Python found

REM Copy standalone folder contents to APP_DIR

xcopy /E /I /Y "%APP_DIR%\temp\room_allocator_strategy_2-main\standalone\*" "%APP_DIR%" >nul    echo Refreshing environment variables...



REM Cleanup    echo [OK] Python foundecho.

del "%APP_DIR%\temp.zip" >nul 2>&1

rmdir /S /Q "%APP_DIR%\temp" >nul 2>&1    REM Refresh PATH by re-reading environment



echo [OK] Files extracted and ready    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"echo.

echo.

    

REM Check and install dependencies

echo Checking Python dependencies...    REM Verify Python is now availableREM Check if required packages are installed

python -c "import streamlit" >nul 2>&1

if errorlevel 1 (    python --version >nul 2>&1

    echo [INSTALLING] Required packages not found. Installing now...

    echo This may take a few minutes on first run...    if errorlevel 1 (REM Create application directoryecho Checking dependencies...

    echo.

    python -m pip install --quiet --upgrade pip        echo [WARNING] Python installed but not yet in PATH.

    python -m pip install --quiet streamlit pandas openpyxl plotly requests python-pptx

    echo.        echo Please close this window and run the BAT file again.set "APP_DIR=%USERPROFILE%\KPMG_Credentials_System"python -c "import streamlit" >nul 2>&1

    echo [OK] Dependencies installed successfully!

    echo.        echo.

) else (

    echo [OK] All dependencies found        pauseif not exist "%APP_DIR%" (if errorlevel 1 (

    echo.

)        exit /b 0



REM Start the application    )    echo Creating application directory...    echo [INSTALLING] Required packages not found. Installing now...

echo =============================================

echo  Starting Credentials System...)

echo =============================================

echo.    mkdir "%APP_DIR%"    echo This may take a few minutes on first run...

echo The application will open in your browser shortly.

echo Password for all tools: bud123echo [OK] Python found

echo.

echo To stop: Close this window or press Ctrl+Cpython --version    mkdir "%APP_DIR%\pages"    echo.

echo =============================================

echo.echo.



REM Change to app directory and start Streamlit    mkdir "%APP_DIR%\.streamlit"    python -m pip install --upgrade pip

cd /d "%APP_DIR%"

python -m streamlit run app.py --server.headless=true --browser.gatherUsageStats=false --server.port=8501 --server.address=localhostREM Create application directory



REM If Streamlit exits, pause to show any errorsset "APP_DIR=%USERPROFILE%\KPMG_Credentials_System")    python -m pip install streamlit pandas openpyxl plotly requests python-pptx

echo.

echo Application stopped.if not exist "%APP_DIR%" (

pause

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
