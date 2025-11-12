# Project Database Viewer - Standalone Package

## 📦 What You Need

When you download from GitHub, you get the entire repository. For the **clean single-page app**, use the **`standalone/`** folder.

## 🚀 Quick Start

### From GitHub ZIP Download:

1. **Download:** https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip
2. **Extract** the ZIP file
3. **Navigate to:** `room-allocator-strategy-2-main/standalone/`
4. **Double-click:** `Launch.bat`
5. **Enter password:** bud123

**Result:** Clean single-page app with only Project Database!

---

## 📂 Folder Structure

```
room-allocator-strategy-2-main/
├── standalone/              ← USE THIS FOLDER!
│   ├── Launch.bat          ← Double-click this!
│   ├── app.py
│   ├── credentials_full.xlsx
│   ├── README.md
│   └── .streamlit/
│       └── config.toml
├── pages/                   ← Don't use (has multiple pages)
├── app.py                   ← Don't use (main room allocator app)
└── ...other files
```

---

## ✅ Why Use Standalone Folder?

| Location | Pages Shown | Sidebar | Use For |
|----------|------------|---------|---------|
| **`standalone/`** | ✅ **Project Database only** | ❌ Hidden | **Credentials viewer** |
| Root folder | ❌ App + Historical + Database | ✅ Shown | Room allocator system |

---

## 💡 Best Practice for Distribution

**Share with colleagues:**

1. Extract the GitHub ZIP
2. **Copy just the `standalone/` folder**
3. Share that folder (it's self-contained)
4. They double-click `Launch.bat`

Or upload to shared drive:
```
\\kpmg-share\tools\ProjectDatabase\
    ├── Launch.bat
    ├── app.py
    ├── credentials_full.xlsx
    └── .streamlit\config.toml
```

---

## 🔧 If BAT File Shows Multiple Pages

**Problem:** You're running the wrong BAT file

**Solutions:**

1. **Use:** `standalone/Launch.bat` (single page)
2. **Not:** `Launch_Project_Database.bat` (all pages - for room allocator)

**Or manually run:**
```powershell
cd standalone
streamlit run app.py
```

---

## 📥 Download Options

### Option 1: Full GitHub ZIP
- Download: https://github.com/martinomartini/room_allocator_strategy_2/archive/refs/heads/main.zip
- Navigate to `standalone/` folder
- Use `Launch.bat` there

### Option 2: Direct from Streamlit Cloud
- Go to: https://strategy-room-allocator.streamlit.app/Project_Database
- Password: bud123
- Click "📥 Download Standalone Package"
- Download individual files (`Launch.bat`, `app.py`, `credentials_full.xlsx`)

---

## 🆘 Troubleshooting

**Still seeing multiple pages?**
- Check you're in the `standalone/` folder
- Check you're using `standalone/Launch.bat`
- Delete Streamlit cache: `streamlit cache clear`

**Files missing?**
- Make sure to extract ALL files from ZIP
- Ensure `credentials_full.xlsx` is in same folder as `app.py`

---

**Password:** bud123  
**AI Chat:** Works when on KPMG network/VPN
