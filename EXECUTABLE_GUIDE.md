# Building a Standalone Executable for Project Database Viewer

This guide explains how to create a standalone Windows executable that runs the Project Database with AI chat working locally.

## Two Options

### ⚡ Option 1: Simple Batch File (Easiest)

**Best for:** Quick setup, easy to distribute to colleagues

1. **Share these files:**
   - `Launch_Project_Database.bat`
   - Entire `room_allocator_strategy_2` folder

2. **Users just:**
   - Double-click `Launch_Project_Database.bat`
   - Browser opens automatically
   - App runs with full AI chat!

**Advantages:**
- ✅ No building needed
- ✅ Easy to update (just replace files)
- ✅ Small file size
- ✅ Works immediately

**Requirements:**
- Python and Streamlit installed on user's machine

---

### 🎁 Option 2: True Executable (No Python Required)

**Best for:** Users without Python installed

#### Step 1: Install PyInstaller

```powershell
cd "c:\Users\mmartini1\OneDrive - KPMG\Documents\Python Scripts\room_allocator_strategy_2"
pip install -r build_requirements.txt
```

#### Step 2: Build the Executable

```powershell
python build_executable.py
```

This will create: `dist\ProjectDatabaseViewer.exe`

#### Step 3: Distribute

Share the entire `dist` folder with users. They can:
1. Double-click `ProjectDatabaseViewer.exe`
2. Browser opens automatically
3. AI chat works!

**Advantages:**
- ✅ Users don't need Python
- ✅ Single executable file (with data folder)
- ✅ Professional look

**Disadvantages:**
- ❌ Large file size (~100-200MB)
- ❌ Slower startup
- ❌ Harder to update
- ❌ May trigger antivirus warnings

---

## Method Comparison

| Feature | Batch File | Executable |
|---------|-----------|-----------|
| Setup time | 1 minute | 10 minutes |
| File size | Small (~1MB) | Large (~150MB) |
| Requires Python | Yes | No |
| Easy to update | Yes | No |
| Professional | Medium | High |
| Startup speed | Fast | Slower |
| Distribution | Folder | Folder |

---

## Recommended Approach

**For KPMG internal use:** Use the **Batch File** method

Why?
- Everyone has Python (required for other work)
- Easy to update when you fix bugs
- Faster and smaller
- Less antivirus issues

### Quick Distribution Package:

Create a folder with:
```
ProjectDatabase/
├── Launch_Project_Database.bat  ← Double-click this!
├── app.py
├── requirements.txt
├── credentials_full.xlsx
├── pages/
│   └── 4_Project_Database.py
└── .streamlit/
    └── config.toml
```

**Instructions for users:**
1. Copy the `ProjectDatabase` folder to your computer
2. Double-click `Launch_Project_Database.bat`
3. Browser opens automatically
4. Go to "Project Database" page
5. Enter password: `bud123`
6. Use AI chat!

---

## Troubleshooting

### Batch File Issues

**"Python not found"**
```powershell
# Install Python or use full path
"C:\Python311\Scripts\streamlit.exe" run app.py
```

**"Streamlit not found"**
```powershell
pip install -r requirements.txt
```

### Executable Issues

**"Antivirus blocked it"**
- Add exception in antivirus
- Or use batch file method instead

**"Module not found"**
- Rebuild with: `python build_executable.py`
- Make sure all dependencies in requirements.txt

**"Excel file not found"**
- Ensure `credentials_full.xlsx` is in same folder as .exe

---

## Auto-Start on Login (Optional)

To make it start automatically when you log in:

1. Press `Win+R`
2. Type: `shell:startup`
3. Create shortcut to `Launch_Project_Database.bat`
4. App starts automatically when you log in!

---

## For IT Department

If deploying organization-wide:

1. **Use batch file method**
2. **Place in network share:** `\\kpmg-share\tools\ProjectDatabase`
3. **Create desktop shortcut** for users
4. **No installation needed** - just works!

Users access via:
- Desktop shortcut
- Or: `\\kpmg-share\tools\ProjectDatabase\Launch_Project_Database.bat`

---

## Security Notes

✅ **Good:**
- Runs locally on user's machine
- No external connections (except KPMG Workbench API)
- Password protected
- Data stays on KPMG network

⚠️ **Important:**
- Excel file contains project data - secure it appropriately
- Keep password (`bud123`) internal only
- Consider adding user authentication if needed
