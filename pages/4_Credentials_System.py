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
REM  Automatic Installer and Launcher
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

REM Create a temporary directory for the application
set "APP_DIR=%USERPROFILE%\\KPMG_Credentials_System"
if not exist "%APP_DIR%" (
    echo Creating application directory...
    mkdir "%APP_DIR%"
    mkdir "%APP_DIR%\\pages"
    mkdir "%APP_DIR%\\.streamlit"
)

echo [OK] Application directory ready
echo.

REM Download files from GitHub
echo Downloading application files...
echo This may take a moment...
echo.

curl -L -o "%APP_DIR%\\credentials.zip" "https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip"

if errorlevel 1 (
    echo [ERROR] Failed to download files. Please check your internet connection.
    pause
    exit /b 1
)

echo [OK] Files downloaded
echo.

REM Extract the standalone folder
echo Extracting files...
powershell -Command "Expand-Archive -Path '%APP_DIR%\\credentials.zip' -DestinationPath '%APP_DIR%' -Force"
xcopy /E /I /Y "%APP_DIR%\\room_allocator_strategy_2-main\\standalone\\*" "%APP_DIR%"
del "%APP_DIR%\\credentials.zip"
rmdir /S /Q "%APP_DIR%\\room_allocator_strategy_2-main"

echo [OK] Files extracted
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
    - ✅ Automatic file download & setup
    - ✅ No manual setup required!
    """)
    
    st.markdown("""
    **Installation Steps:**
    1. Click the download button above
    2. Save the `.bat` file anywhere
    3. Double-click the downloaded file
    4. Wait for automatic setup (downloads & installs everything)
    5. Enter password: **bud123**
    
    **Requirements:**
    - Windows PC
    - Python 3.8+ ([Download here](https://www.python.org/downloads/) if needed)
    - Internet connection (for first-time setup)
    - KPMG network access for AI features
    
    💡 The launcher will automatically download all files and install dependencies!
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
