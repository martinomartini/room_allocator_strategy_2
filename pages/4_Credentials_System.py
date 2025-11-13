"""
Credentials Management System - Download

Download the standalone application with all three AI-powered tools.
"""

import streamlit as st

st.set_page_config(
    page_title="Credentials System - Download",
    page_icon="📥",
    layout="wide"
)

# Password protection
if "credentials_download_authenticated" not in st.session_state:
    st.session_state.credentials_download_authenticated = False

if not st.session_state.credentials_download_authenticated:
    st.title("🔒 Access Credentials Download")
    st.markdown("Please enter the password to access the credentials system download.")
    
    password = st.text_input("Password", type="password", key="download_password")
    
    if st.button("Submit", key="download_submit"):
        if password == "bud123":
            st.session_state.credentials_download_authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password. Please try again.")
    
    st.stop()

st.title("📥 Credentials Management System")
st.markdown("One-click installer with all AI-powered tools")
st.markdown("---")

# Create columns for centered download button
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### 🚀 One-Click Download")
    
    # Read the Launch.bat file content
    bat_content = """@echo off
REM ============================================
REM  KPMG Credentials Management System
REM  Self-Installing Launcher with Python Auto-Install
REM ============================================

echo.
echo =============================================
echo  KPMG Credentials Management System
echo  Automatic Installer
echo =============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Python is not installed. Installing Python automatically...
    echo.
    
    REM Download Python installer using PowerShell
    set "PYTHON_INSTALLER=%TEMP%\\python-installer.exe"
    echo Downloading Python 3.11 installer (approx. 25 MB)...
    echo This may take 1-2 minutes depending on your connection...
    echo.
    
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing}"
    
    if errorlevel 1 (
        echo [ERROR] Failed to download Python installer.
        echo Please check your internet connection and try again.
        echo.
        echo Alternatively, you can manually install Python from:
        echo https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    
    echo [OK] Python installer downloaded successfully!
    echo.
    echo =============================================
    echo  Python Installation Window Opening
    echo =============================================
    echo.
    echo A Python installer window will now open.
    echo Please follow these steps:
    echo.
    echo 1. CHECK "Add Python to PATH" (IMPORTANT!)
    echo 2. Click "Install Now"
    echo 3. Wait for installation to complete
    echo 4. Click "Close" when done
    echo.
    echo After installation completes, return to this window.
    echo =============================================
    echo.
    pause
    
    REM Install Python with GUI and wait for completion
    start /wait "" "%PYTHON_INSTALLER%" InstallAllUsers=0 PrependPath=1 Include_test=0
    
    REM Cleanup installer
    del "%PYTHON_INSTALLER%" >nul 2>&1
    
    echo.
    echo [OK] Python installation completed!
    echo.
    
    REM Refresh PATH by re-reading environment
    set "PATH=%PATH%;%LOCALAPPDATA%\\Programs\\Python\\Python311;%LOCALAPPDATA%\\Programs\\Python\\Python311\\Scripts"
    
    REM Verify Python is now available
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Python installed successfully!
        echo Please CLOSE THIS WINDOW and run the BAT file again to start the application.
        echo.
        pause
        exit /b 0
    )
    
    echo Python is now ready!
    echo.
)

echo [OK] Python found
python --version
echo.

REM Create application directory
set "APP_DIR=%USERPROFILE%\\KPMG_Credentials_System"
if not exist "%APP_DIR%" (
    echo Creating application directory...
    mkdir "%APP_DIR%"
    mkdir "%APP_DIR%\\pages"
    mkdir "%APP_DIR%\\.streamlit"
)

echo [OK] Application directory ready: %APP_DIR%
echo.

REM Download files from GitHub using PowerShell
echo Downloading application files from GitHub...
echo This may take a moment...
echo.

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip' -OutFile '%APP_DIR%\\temp.zip' -UseBasicParsing}"

if errorlevel 1 (
    echo [ERROR] Failed to download files. Please check your internet connection.
    pause
    exit /b 1
)

echo [OK] Files downloaded
echo.

REM Extract only the standalone folder
echo Extracting files...
powershell -Command "Expand-Archive -Path '%APP_DIR%\\temp.zip' -DestinationPath '%APP_DIR%\\temp' -Force" 2>nul

REM Copy standalone folder contents to APP_DIR
xcopy /E /I /Y "%APP_DIR%\\temp\\room_allocator_strategy_2-main\\standalone\\*" "%APP_DIR%" >nul

REM Cleanup
del "%APP_DIR%\\temp.zip" >nul 2>&1
rmdir /S /Q "%APP_DIR%\\temp" >nul 2>&1

echo [OK] Files extracted and ready
echo.

REM Check and install dependencies
echo Checking Python dependencies...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [INSTALLING] Required packages not found. Installing now...
    echo This may take a few minutes...
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
"""
    
    # Offer direct download of BAT file
    st.download_button(
        label="⬇️ Download Credentials System",
        data=bat_content,
        file_name="KPMG_Credentials_System.bat",
        mime="application/bat",
        type="primary",
        use_container_width=True
    )
    
    st.info("""
    **What you get:**
    - ✅ Self-installing application
    - ✅ All 3 AI-powered tools
    - ✅ Automatic Python installation (if needed)
    - ✅ Automatic file download from GitHub
    - ✅ Automatic dependency installation
    - ✅ Zero manual setup required!
    """)
    
    st.markdown("""
    **Installation Steps:**
    1. Click the download button above
    2. Save the `.bat` file anywhere
    3. Double-click the downloaded file
    4. Wait for automatic setup:
       - Installs Python if not found (3-5 minutes)
       - Downloads all files from GitHub
       - Installs all dependencies
    5. Application opens in browser automatically
    6. Enter password: **bud123**
    
    **Requirements:**
    - Windows PC
    - Internet connection (for downloads)
    - KPMG network access (VPN or on-premises) for AI features
    
    💡 **No Python needed!** The launcher will install Python automatically if it's not found.
    """)

st.markdown("---")

# Show what's included
st.markdown("### 📦 Included Tools")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("#### 📊 Project Database")
    st.markdown("""
    - AI chat for natural language queries
    - Filter by industry, partner, year
    - Export to CSV/Excel
    - Password protected
    """)

with col_b:
    st.markdown("#### 🔍 Credential Browser")
    st.markdown("""
    - Fast search and filtering
    - Search by person name
    - Filter by multiple criteria
    - Quick export options
    """)

with col_c:
    st.markdown("#### 📝 PowerPoint Generator")
    st.markdown("""
    - AI-powered presentations
    - Natural language requests
    - Smart project selection
    - Professional output
    """)

st.markdown("---")
st.caption("⚠️ AI features require KPMG network access (VPN or on-premises) • Password for all tools: bud123")
