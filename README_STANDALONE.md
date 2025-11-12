# 📊 Project Database Viewer - Standalone Application

Welcome! You've downloaded the Project Database Viewer with AI Chat functionality.

## 🚀 Quick Start (3 Steps)

### 1. Check Requirements
- ✅ Windows PC
- ✅ KPMG network access (VPN or on-premises)
- ✅ Python with Streamlit installed

### 2. Launch the Application
**Double-click:** `Launch_Project_Database.bat`

That's it! The browser will open automatically.

### 3. Use the App
- Enter password: **bud123**
- Start using AI Chat!

---

## 💬 AI Chat Examples

Try these natural language queries:

```
"Show me all projects in the technology industry"
"Give me all projects of Tim Kramer"
"All projects from 2024"
"Find projects for client Microsoft"
```

The AI understands your questions and filters the database automatically!

---

## 📋 Features

### AI Chat (Local Only)
- 🤖 Natural language queries
- 🔍 Smart filtering based on your questions
- 💡 Contextual understanding

### Filter Tabs (Work Everywhere)
- 📊 Statistics & Charts
- 🏭 Industry Filter
- 👤 Partner Filter
- 👔 Manager Filter

### Export & Customization
- 📥 Export to CSV/Excel
- ⚙️ Select columns to display
- 📈 Interactive visualizations

---

## 🔧 Troubleshooting

### "Python not found" or "Streamlit not found"

Install Python and Streamlit:

```powershell
# Install Streamlit
pip install streamlit pandas openpyxl plotly requests

# Or install all requirements
pip install -r requirements.txt
```

### AI Chat Not Working?

1. **Check VPN:** Ensure you're connected to KPMG VPN
2. **Check Network:** Try accessing other KPMG internal services
3. **Refresh Page:** Sometimes a page refresh helps

### Browser Doesn't Open?

Manually navigate to: http://localhost:8501

---

## 📁 File Structure

```
room_allocator_strategy_2/
├── Launch_Project_Database.bat  ← Double-click this!
├── app_standalone.py             ← Standalone app
├── credentials_full.xlsx         ← Project database
├── requirements.txt              ← Dependencies
├── pages/
│   └── 4_Project_Database.py    ← Main application code
└── .streamlit/
    └── config.toml              ← Configuration
```

---

## 🔐 Security

- Password: **bud123** (KPMG internal only)
- Data stays on KPMG network
- No external connections except KPMG Workbench API

---

## 💡 Tips

### Keep It Running
Leave the command window open while using the app. Closing it stops the application.

### Update the Database
Replace `credentials_full.xlsx` with a new version to update the project database.

### Share with Colleagues
Copy the entire folder to colleagues' computers. They can use it the same way!

---

## 📞 Support

**Technical Issues:**
- Check this README first
- Contact IT support for Python/Streamlit installation
- Check KPMG VPN connection

**Application Questions:**
- Review the examples above
- Try the filter tabs (work without AI chat)
- Use the Statistics tab for overview

---

## 🎯 Why Run Locally?

| Feature | Streamlit Cloud | Local (This Version) |
|---------|----------------|---------------------|
| View Projects | ✅ | ✅ |
| Filter Tabs | ✅ | ✅ |
| Export Data | ✅ | ✅ |
| AI Chat | ❌ | ✅ **Works!** |

**Bottom line:** Running locally gives you access to KPMG Workbench API for AI Chat!

---

## 🔄 Updates

To get the latest version:
1. Download again from Streamlit Cloud
2. Or pull from: https://github.com/martinomartini/room_allocator_strategy_2

---

**Enjoy using the Project Database Viewer with AI Chat! 🎉**
