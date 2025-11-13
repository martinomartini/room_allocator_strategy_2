@echo off@echo off@echo off@echo off@echo off@echo off

REM ============================================

REM  KPMG Credentials Management SystemREM ============================================

REM  Self-Installing Launcher with Python Auto-Install

REM ============================================REM  KPMG Credentials Management SystemREM ============================================



echo.REM  Self-Installing Launcher with Python Auto-Install

echo =============================================

echo  KPMG Credentials Management SystemREM ============================================REM  KPMG Credentials Management SystemREM ============================================

echo  Automatic Installer

echo =============================================

echo.

echo.REM  Self-Installing Launcher with Python Auto-Install

REM Check if Python is installed

python --version >nul 2>&1echo =============================================

if errorlevel 1 (

    echo [INFO] Python is not installed. Installing Python automatically...echo  KPMG Credentials Management SystemREM ============================================REM  KPMG Credentials Management SystemREM ============================================REM ============================================

    echo.

    echo  Automatic Installer

    REM Download Python installer using PowerShell

    set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"echo =============================================

    echo Downloading Python 3.11 installer (approx. 25 MB)...

    echo This may take 1-2 minutes depending on your connection...echo.

    echo.

    echo.REM  Self-Installing Launcher with Python Auto-Install

    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing}"

    REM Check if Python is installed

    if errorlevel 1 (

        echo [ERROR] Failed to download Python installer.python --version >nul 2>&1echo =============================================

        echo Please check your internet connection and try again.

        echo.if errorlevel 1 (

        echo Alternatively, you can manually install Python from:

        echo https://www.python.org/downloads/    echo [INFO] Python is not installed. Installing Python automatically...echo  KPMG Credentials Management SystemREM ============================================REM  KPMG Credentials Management SystemREM  KPMG Credentials Management System

        echo.

        pause    echo.

        exit /b 1

    )    echo  Automatic Installer

    

    echo [OK] Python installer downloaded successfully!    REM Download Python installer

    echo.

    echo =============================================    set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"echo =============================================

    echo  Python Installation Window Opening

    echo =============================================    echo Downloading Python 3.11 installer...

    echo.

    echo A Python installer window will now open.    curl -L -o "%PYTHON_INSTALLER%" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" 2>nulecho.

    echo Please follow these steps:

    echo.    

    echo 1. CHECK "Add Python to PATH" (IMPORTANT!)

    echo 2. Click "Install Now"    if errorlevel 1 (echo.REM  Self-Installing LauncherREM  Automatic Launcher with Dependency Check

    echo 3. Wait for installation to complete

    echo 4. Click "Close" when done        echo [ERROR] Failed to download Python installer.

    echo.

    echo After installation completes, return to this window.        echo Please check your internet connection and try again.REM Check if Python is installed

    echo =============================================

    echo.        echo.

    pause

            echo Alternatively, you can manually install Python from:python --version >nul 2>&1echo =============================================

    REM Install Python with GUI and wait for completion

    start /wait "" "%PYTHON_INSTALLER%" InstallAllUsers=0 PrependPath=1 Include_test=0        echo https://www.python.org/downloads/

    

    REM Cleanup installer        echo.if errorlevel 1 (

    del "%PYTHON_INSTALLER%" >nul 2>&1

            pause

    echo.

    echo [OK] Python installation completed!        exit /b 1    echo [INFO] Python is not installed. Installing Python automatically...echo  KPMG Credentials Management SystemREM ============================================REM ============================================

    echo.

        )

    REM Refresh PATH by re-reading environment

    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"        echo This will take a few minutes...

    

    REM Verify Python is now available    echo [OK] Python installer downloaded

    python --version >nul 2>&1

    if errorlevel 1 (    echo.    echo.echo  Automatic Installer

        echo [INFO] Python installed successfully!

        echo Please CLOSE THIS WINDOW and run the BAT file again to start the application.    echo =============================================

        echo.

        pause    echo  Python Installation Window Opening    

        exit /b 0

    )    echo =============================================

    

    echo Python is now ready!    echo.    REM Download Python installerecho =============================================

    echo.

)    echo A Python installer window will now open.



echo [OK] Python found    echo Please follow these steps:    set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"

python --version

echo.    echo.



REM Create application directory    echo 1. CHECK "Add Python to PATH" (IMPORTANT!)    echo Downloading Python 3.11...echo.

set "APP_DIR=%USERPROFILE%\KPMG_Credentials_System"

if not exist "%APP_DIR%" (    echo 2. Click "Install Now"

    echo Creating application directory...

    mkdir "%APP_DIR%"    echo 3. Wait for installation to complete    curl -L -o "%PYTHON_INSTALLER%" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" 2>nul

    mkdir "%APP_DIR%\pages"

    mkdir "%APP_DIR%\.streamlit"    echo 4. Click "Close" when done

)

    echo.    echo.echo.

echo [OK] Application directory ready: %APP_DIR%

echo.    echo After installation completes, return to this window.



REM Download files from GitHub using PowerShell    echo =============================================    if errorlevel 1 (

echo Downloading application files from GitHub...

echo This may take a moment...    echo.

echo.

    pause        echo [ERROR] Failed to download Python installer.REM Check if Python is installed

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip' -OutFile '%APP_DIR%\temp.zip' -UseBasicParsing}"

    

if errorlevel 1 (

    echo [ERROR] Failed to download files. Please check your internet connection.    REM Install Python with GUI and wait for completion        echo Please check your internet connection and try again.

    pause

    exit /b 1    start /wait "" "%PYTHON_INSTALLER%" InstallAllUsers=0 PrependPath=1 Include_test=0

)

            echo.python --version >nul 2>&1echo =============================================echo =============================================

echo [OK] Files downloaded

echo.    REM Cleanup installer



REM Extract only the standalone folder    del "%PYTHON_INSTALLER%" >nul 2>&1        echo Alternatively, you can manually install Python from:

echo Extracting files...

powershell -Command "Expand-Archive -Path '%APP_DIR%\temp.zip' -DestinationPath '%APP_DIR%\temp' -Force" 2>nul    



REM Copy standalone folder contents to APP_DIR    echo.        echo https://www.python.org/downloads/if errorlevel 1 (

xcopy /E /I /Y "%APP_DIR%\temp\room_allocator_strategy_2-main\standalone\*" "%APP_DIR%" >nul

    echo [OK] Python installation completed!

REM Cleanup

del "%APP_DIR%\temp.zip" >nul 2>&1    echo.        echo.

rmdir /S /Q "%APP_DIR%\temp" >nul 2>&1

    

echo [OK] Files extracted and ready

echo.    REM Refresh PATH by re-reading environment        pause    echo [INFO] Python is not installed. Installing Python automatically...echo  KPMG Credentials Management Systemecho  KPMG Credentials Management System



REM Check and install dependencies    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"

echo Checking Python dependencies...

python -c "import streamlit" >nul 2>&1            exit /b 1

if errorlevel 1 (

    echo [INSTALLING] Required packages not found. Installing now...    REM Verify Python is now available

    echo This may take a few minutes...

    echo.    python --version >nul 2>&1    )    echo This will take a few minutes...

    python -m pip install --upgrade pip

    python -m pip install streamlit pandas openpyxl plotly requests python-pptx    if errorlevel 1 (

    echo.

    echo [OK] Dependencies installed successfully!        echo [INFO] Python installed successfully!    

    echo.

) else (        echo Please CLOSE THIS WINDOW and run the BAT file again to start the application.

    echo [OK] All dependencies found

    echo.        echo.    echo [OK] Python installer downloaded    echo.echo  Automatic Installerecho =============================================

)

        pause

REM Start the application

echo =============================================        exit /b 0    echo.

echo  Starting Credentials System...

echo =============================================    )

echo.

echo The application will open in your browser shortly.        echo Installing Python (this may take 3-5 minutes)...    

echo Password for all tools: bud123

echo.    echo Python is now ready!

echo To stop: Close this window or press Ctrl+C

echo =============================================    echo.    echo Please wait - DO NOT CLOSE THIS WINDOW...

echo.

)

REM Change to app directory and start Streamlit

cd /d "%APP_DIR%"    echo.    REM Download Python installerecho =============================================echo.

python -m streamlit run app.py --server.headless=true --browser.gatherUsageStats=false --server.port=8501 --server.address=localhost

echo [OK] Python found

REM If Streamlit exits, pause to show any errors

echo.python --version    

echo Application stopped.

pauseecho.


    REM Install Python silently with PATH and wait for completion    set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"

REM Create application directory

set "APP_DIR=%USERPROFILE%\KPMG_Credentials_System"    start /wait "" "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

if not exist "%APP_DIR%" (

    echo Creating application directory...        echo Downloading Python 3.11...echo.

    mkdir "%APP_DIR%"

    mkdir "%APP_DIR%\pages"    REM Cleanup installer

    mkdir "%APP_DIR%\.streamlit"

)    del "%PYTHON_INSTALLER%" >nul 2>&1    curl -L -o "%PYTHON_INSTALLER%" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" 2>nul



echo [OK] Application directory ready: %APP_DIR%    

echo.

    echo [OK] Python installed successfully!    REM Check if Python is installed

REM Download files from GitHub

echo Downloading application files from GitHub...    echo.

echo This may take a moment...

echo.        if errorlevel 1 (



REM Download the entire repository as ZIP    REM Refresh PATH by re-reading environment

curl -L -o "%APP_DIR%\temp.zip" "https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip" 2>nul

    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"        echo [ERROR] Failed to download Python installer.REM Check if Python is installedpython --version >nul 2>&1

if errorlevel 1 (

    echo [ERROR] Failed to download files. Please check your internet connection.    

    pause

    exit /b 1    REM Verify Python is now available        echo Please check your internet connection and try again.

)

    python --version >nul 2>&1

echo [OK] Files downloaded

echo.    if errorlevel 1 (        echo.python --version >nul 2>&1if errorlevel 1 (



REM Extract only the standalone folder        echo [INFO] Python installed successfully!

echo Extracting files...

powershell -Command "Expand-Archive -Path '%APP_DIR%\temp.zip' -DestinationPath '%APP_DIR%\temp' -Force" 2>nul        echo Please CLOSE THIS WINDOW and run the BAT file again to start the application.        echo Alternatively, you can manually install Python from:



REM Copy standalone folder contents to APP_DIR        echo.

xcopy /E /I /Y "%APP_DIR%\temp\room_allocator_strategy_2-main\standalone\*" "%APP_DIR%" >nul

        pause        echo https://www.python.org/downloads/if errorlevel 1 (    echo [ERROR] Python is not installed!

REM Cleanup

del "%APP_DIR%\temp.zip" >nul 2>&1        exit /b 0

rmdir /S /Q "%APP_DIR%\temp" >nul 2>&1

    )        echo.

echo [OK] Files extracted and ready

echo.    



REM Check and install dependencies    echo Python is now ready!        pause    echo [ERROR] Python is not installed!    echo.

echo Checking Python dependencies...

python -c "import streamlit" >nul 2>&1    echo.

if errorlevel 1 (

    echo [INSTALLING] Required packages not found. Installing now...)        exit /b 1

    echo This may take a few minutes...

    echo.

    python -m pip install --upgrade pip

    python -m pip install streamlit pandas openpyxl plotly requests python-pptxecho [OK] Python found    )    echo.    echo Please install Python 3.8 or higher from:

    echo.

    echo [OK] Dependencies installed successfully!python --version

    echo.

) else (echo.    

    echo [OK] All dependencies found

    echo.

)

REM Create application directory    echo [OK] Python installer downloaded    echo Please install Python 3.8 or higher from:    echo https://www.python.org/downloads/

REM Start the application

echo =============================================set "APP_DIR=%USERPROFILE%\KPMG_Credentials_System"

echo  Starting Credentials System...

echo =============================================if not exist "%APP_DIR%" (    echo.

echo.

echo The application will open in your browser shortly.    echo Creating application directory...

echo Password for all tools: bud123

echo.    mkdir "%APP_DIR%"    echo Installing Python (this may take 3-5 minutes)...    echo https://www.python.org/downloads/    echo.

echo To stop: Close this window or press Ctrl+C

echo =============================================    mkdir "%APP_DIR%\pages"

echo.

    mkdir "%APP_DIR%\.streamlit"    echo Please wait...

REM Change to app directory and start Streamlit

cd /d "%APP_DIR%")

python -m streamlit run app.py --server.headless=true --browser.gatherUsageStats=false --server.port=8501 --server.address=localhost

    echo.    echo.    echo Make sure to check "Add Python to PATH" during installation.

REM If Streamlit exits, pause to show any errors

echo.echo [OK] Application directory ready: %APP_DIR%

echo Application stopped.

pauseecho.    




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
