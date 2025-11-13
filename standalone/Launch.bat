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

REM Check if Python is installed - try multiple locations
set "PYTHON_CMD="

REM Try python command (if in PATH)
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :python_found
)

REM Try py launcher (Windows Python Launcher)
py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    goto :python_found
)

REM Search for any Python version in %LOCALAPPDATA%\Programs\Python\
if exist "%LOCALAPPDATA%\Programs\Python\" (
    for /f "delims=" %%i in ('dir /b /ad "%LOCALAPPDATA%\Programs\Python\Python3*" 2^>nul') do (
        if exist "%LOCALAPPDATA%\Programs\Python\%%i\python.exe" (
            set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\%%i\python.exe"
            goto :python_found
        )
    )
)

REM Search for any Python version in C:\Program Files\Python\
if exist "C:\Program Files\Python\" (
    for /f "delims=" %%i in ('dir /b /ad "C:\Program Files\Python\Python3*" 2^>nul') do (
        if exist "C:\Program Files\Python\%%i\python.exe" (
            set "PYTHON_CMD=C:\Program Files\Python\%%i\python.exe"
            goto :python_found
        )
    )
)

REM Search for any Python version in C:\
for /f "delims=" %%i in ('dir /b /ad "C:\Python3*" 2^>nul') do (
    if exist "C:\%%i\python.exe" (
        set "PYTHON_CMD=C:\%%i\python.exe"
        goto :python_found
    )
)

REM If we get here, Python was not found
echo [ERROR] Python is not installed or not found!
echo.
echo Please install Python 3.8 or higher from:
echo https://www.python.org/downloads/
echo.
echo Make sure to check "Add Python to PATH" during installation.
echo.
echo Searched locations:
echo - python command in PATH
echo - py launcher
echo - %%LOCALAPPDATA%%\Programs\Python\
echo - C:\Program Files\Python\
echo - C:\Python3*
echo.
pause
exit /b 1

:python_found
echo [OK] Python found
"%PYTHON_CMD%" --version
echo.

REM Add Python and Scripts to PATH for this session
for %%i in ("%PYTHON_CMD%") do set "PYTHON_DIR=%%~dpi"
set "PYTHON_DIR=%PYTHON_DIR:~0,-1%"
set "PATH=%PYTHON_DIR%;%PYTHON_DIR%\Scripts;%PATH%"

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
"%PYTHON_CMD%" -m pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo [INSTALLING] Required packages not found. Installing now...
    echo This may take a few minutes on first run...
    echo.
    echo NOTE: You may see build warnings for some packages ^(like pyarrow^).
    echo These warnings are normal and do not affect the application.
    echo.
    echo Installing pip...
    "%PYTHON_CMD%" -m pip install --upgrade pip >nul 2>&1
    echo Installing packages...
    echo This will take 2-3 minutes, please wait...
    "%PYTHON_CMD%" -m pip install --user streamlit pandas openpyxl plotly requests python-pptx
    echo.
    echo [OK] Package installation complete!
    echo.
    
    REM Verify streamlit is now accessible
    "%PYTHON_CMD%" -m pip show streamlit >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Streamlit may not have installed correctly.
        echo The launcher will try to start it anyway.
        echo.
    )
) else (
    echo [OK] All dependencies found
    echo.
)

REM Start the application
echo =============================================
echo  Starting Credentials System...
echo =============================================
echo.
echo NOTE: You may see some warnings above (like pyarrow build errors).
echo These are normal and don't affect the application functionality.
echo.
echo The application will open in your browser shortly.
echo Password for all tools: bud123
echo.
echo To stop: Close this window or press Ctrl+C
echo =============================================
echo.

REM Change to app directory and start Streamlit
cd /d "%APP_DIR%"

REM Try to launch Streamlit
"%PYTHON_CMD%" -m streamlit run app.py --server.headless=true --browser.gatherUsageStats=false --server.port=8501 --server.address=localhost

REM If we get here, Streamlit exited
if errorlevel 1 (
    echo.
    echo [ERROR] Streamlit failed to start. This might be because:
    echo 1. Streamlit is not installed correctly
    echo 2. Port 8501 is already in use
    echo 3. There is an error in the application code
    echo.
    echo Try installing packages manually:
    echo   "%PYTHON_CMD%" -m pip install streamlit pandas openpyxl plotly requests python-pptx
    echo.
    pause
)

REM If Streamlit exits, pause to show any errors
echo.
echo Application stopped.
pause
