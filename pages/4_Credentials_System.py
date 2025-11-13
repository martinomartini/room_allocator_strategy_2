import streamlit as st

# Set page config
st.set_page_config(
    page_title="Credentials System - Download",
    page_icon="🔐",
    layout="wide"
)

# Initialize session state for authentication
if 'credentials_authenticated' not in st.session_state:
    st.session_state.credentials_authenticated = False

# Password protection
def check_password():
    """Returns True if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["credentials_password"] == "bud123":
            st.session_state.credentials_authenticated = True
            del st.session_state["credentials_password"]
        else:
            st.session_state.credentials_authenticated = False

    if not st.session_state.credentials_authenticated:
        st.text_input(
            "🔒 Enter Password", 
            type="password", 
            on_change=password_entered, 
            key="credentials_password"
        )
        st.warning("Please enter the password to access the Credentials System Download page.")
        return False
    else:
        return True

# Main app
if check_password():
    st.title("🔐 KPMG Credentials Management System")
    st.markdown("### Download Local Version")
    
    st.info("""
    **Important:** This system is designed to run locally on your Windows PC.
    The tools include AI-powered features that require KPMG network access.
    """)
    
    # Features section
    st.markdown("---")
    st.markdown("### 📦 What You'll Get")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📊 Project Database")
        st.markdown("""
        - AI-powered chat for project insights
        - Search 114+ strategy projects
        - Advanced filtering options
        - Export capabilities
        """)
    
    with col2:
        st.markdown("#### 🔍 Credential Browser")
        st.markdown("""
        - Fast credential filtering
        - Person-specific searches
        - Project relationship mapping
        - Interactive data views
        """)
    
    with col3:
        st.markdown("#### 🎯 PowerPoint Generator")
        st.markdown("""
        - AI-generated presentations
        - Custom templates
        - Project-specific content
        - One-click export
        """)
    
    st.markdown("---")
    
    # Requirements section
    st.markdown("### ⚙️ Requirements")
    requirements_col1, requirements_col2 = st.columns(2)
    
    with requirements_col1:
        st.markdown("""
        **System Requirements:**
        - Windows PC
        - Python 3.8 or higher ([Download here](https://www.python.org/downloads/))
        - Internet connection (for initial setup)
        - KPMG network access (for AI features)
        """)
    
    with requirements_col2:
        st.markdown("""
        **Automatic Setup:**
        - Downloads all files from GitHub
        - Installs required packages automatically
        - Sets up local environment
        - Launches web interface
        """)
    
    st.markdown("---")
    
    # Download section
    st.markdown("### 📥 Download & Installation")
    
    # Read the BAT file content from the standalone folder
    bat_file_path = "c:\\Users\\mmartini1\\OneDrive - KPMG\\Documents\\Python Scripts\\room_allocator_strategy_2\\standalone\\Launch.bat"
    try:
        with open(bat_file_path, 'r', encoding='ascii') as f:
            bat_content = f.read()
    except:
        # Fallback content if file can't be read
        bat_content = """@echo off
REM ERROR: Could not load BAT file content
REM Please contact support
pause
"""
    
    # Create download button
    st.download_button(
        label="⬇️ Download KPMG_Credentials_System.bat",
        data=bat_content,
        file_name="KPMG_Credentials_System.bat",
        mime="application/bat",
        help="Download the launcher file to install and run the system locally"
    )
    
    # Installation instructions
    st.markdown("---")
    st.markdown("### 📖 Installation Steps")
    
    with st.expander("**Step 1: Install Python** (if not already installed)", expanded=False):
        st.markdown("""
        1. Go to [python.org/downloads](https://www.python.org/downloads/)
        2. Download Python 3.8 or higher for Windows
        3. Run the installer
        4. **Important:** Check the box "Add Python to PATH"
        5. Click "Install Now"
        6. Wait for installation to complete
        """)
    
    with st.expander("**Step 2: Download the Launcher**", expanded=True):
        st.markdown("""
        1. Click the **"Download KPMG_Credentials_System.bat"** button above
        2. Save the file to a location you can easily find (e.g., Desktop or Downloads)
        3. The file is a Windows batch script that will set everything up automatically
        """)
    
    with st.expander("**Step 3: Run the Launcher**", expanded=False):
        st.markdown("""
        1. Double-click the downloaded `KPMG_Credentials_System.bat` file
        2. Windows may show a security warning - click "More info" then "Run anyway"
        3. The launcher will:
           - Check your Python installation
           - Download all application files from GitHub
           - Install required packages (first time only - takes 2-3 minutes)
           - Start the local web server
        4. Your browser will open automatically to `http://localhost:8501`
        5. Use password: **bud123** to access all tools
        """)
    
    with st.expander("**Step 4: Using the System**", expanded=False):
        st.markdown("""
        **After first installation:**
        - All files are saved to: `C:\\Users\\YourUsername\\KPMG_Credentials_System`
        - Next time, just double-click the BAT file to launch
        - No re-download needed (unless you delete the folder)
        - Packages are already installed (launches instantly)
        
        **Available tools:**
        1. **Project Database** - AI chat and project search
        2. **Credential Browser** - Fast filtering and person search
        3. **PowerPoint Generator** - AI-powered presentations
        
        **Password for all tools:** bud123
        
        **To stop the system:**
        - Close the terminal window, or
        - Press Ctrl+C in the terminal
        """)
    
    st.markdown("---")
    
    # Troubleshooting section
    st.markdown("### 🔧 Troubleshooting")
    
    with st.expander("Common Issues & Solutions"):
        st.markdown("""
        **Problem: "Python is not installed" error**
        - Solution: Install Python from [python.org](https://www.python.org/downloads/)
        - Make sure to check "Add Python to PATH" during installation
        
        **Problem: Download fails**
        - Solution: Check your internet connection
        - Try running the BAT file again
        - Make sure you're not behind a firewall blocking GitHub
        
        **Problem: Package installation fails**
        - Solution: Open Command Prompt and run:
          ```
          python -m pip install --upgrade pip
          python -m pip install streamlit pandas openpyxl plotly requests python-pptx
          ```
        
        **Problem: AI features don't work**
        - Solution: You must be on the KPMG network
        - The system uses KPMG's internal API which requires network access
        
        **Problem: Browser doesn't open automatically**
        - Solution: Manually open your browser and go to:
          `http://localhost:8501`
        
        **Problem: Want to update to latest version**
        - Solution: Delete the folder `C:\\Users\\YourUsername\\KPMG_Credentials_System`
        - Run the BAT file again to download fresh files
        """)
    
    st.markdown("---")
    
    # Support section
    st.markdown("### 📞 Support")
    st.info("""
    **Questions or Issues?**
    
    Contact the development team or check the project repository for updates:
    [github.com/martinomartini/room_allocator_strategy_2](https://github.com/martinomartini/room_allocator_strategy_2)
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("*KPMG Credentials Management System - Local Installation Package*")
