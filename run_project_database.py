"""
Project Database Viewer - Standalone Launcher
This script launches the Streamlit app and opens the browser automatically
"""

import streamlit.web.cli as stcli
import sys
import os
import webbrowser
import time
from threading import Timer

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)  # Wait for Streamlit to start
    webbrowser.open('http://localhost:8501')

if __name__ == '__main__':
    # Get the directory where this script is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = sys._MEIPASS
    else:
        # Running as script
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the application directory
    os.chdir(application_path)
    
    # Open browser in background
    Timer(2, open_browser).start()
    
    # Run Streamlit with standalone app
    sys.argv = [
        "streamlit",
        "run",
        "project_database_standalone.py",
        "--server.headless=true",
        "--server.port=8501",
        "--browser.gatherUsageStats=false"
    ]
    
    sys.exit(stcli.main())
