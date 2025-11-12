"""
Project Database Viewer - Standalone Application
Simple app that only shows the Project Database with AI chat
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Project Database Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import and run the Project Database page directly
import sys
import os

# Add pages directory to path
pages_dir = os.path.join(os.path.dirname(__file__), 'pages')
if pages_dir not in sys.path:
    sys.path.insert(0, pages_dir)

# Read the Project Database code and execute it
project_db_file = os.path.join(os.path.dirname(__file__), 'pages', '4_Project_Database.py')

# Execute the Project Database page code
with open(project_db_file, 'r', encoding='utf-8') as f:
    code = f.read()
    # Remove the st.set_page_config from the imported file if it exists
    code = code.replace('st.set_page_config(', '# st.set_page_config(')
    exec(code)
