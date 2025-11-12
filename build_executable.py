# Project Database Viewer - Executable Builder
# This creates a standalone .exe that runs the Streamlit app

import PyInstaller.__main__
import os
import sys

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the executable
PyInstaller.__main__.run([
    'run_project_database.py',  # The main script
    '--onefile',  # Single executable file
    '--windowed',  # No console window (GUI only)
    '--name=ProjectDatabaseViewer',  # Name of the executable
    '--icon=NONE',  # You can add an icon later
    '--add-data=pages;pages',  # Include pages folder
    '--add-data=credentials_full.xlsx;.',  # Include the Excel file
    '--add-data=.streamlit;.streamlit',  # Include streamlit config
    '--hidden-import=streamlit',
    '--hidden-import=pandas',
    '--hidden-import=openpyxl',
    '--hidden-import=plotly',
    '--hidden-import=requests',
    '--hidden-import=urllib3',
    '--collect-all=streamlit',
    '--collect-all=plotly',
    '--noconfirm',  # Overwrite without asking
])

print("\n" + "="*70)
print("✅ Executable created successfully!")
print("="*70)
print(f"\n📁 Location: {os.path.join(current_dir, 'dist', 'ProjectDatabaseViewer.exe')}")
print("\n📝 To use:")
print("   1. Double-click ProjectDatabaseViewer.exe")
print("   2. Browser opens automatically to the app")
print("   3. Navigate to Project Database page")
print("   4. Enter password: bud123")
print("   5. AI Chat works because it runs locally!")
print("\n" + "="*70)
