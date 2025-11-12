# How to Run the Room Allocator Application

## 🌐 Option 1: Access Online (Streamlit Cloud)

**URL:** [Your Streamlit Cloud URL]

✅ **What works:**
- Room allocation system
- Historical analytics
- Project database viewer (all filters, statistics, export)

❌ **What doesn't work:**
- AI Chat feature in Project Database (requires KPMG network)

---

## 💻 Option 2: Run Locally (Full Features)

Running locally on a KPMG machine gives you **ALL features including AI Chat**!

### Prerequisites
- Python 3.8 or higher
- KPMG network access (VPN if remote)
- Git

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/martinomartini/room-allocator-strategy-2.git
cd room-allocator-strategy-2

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
streamlit run app.py
```

### What You'll Get Locally

✅ **Everything from cloud, PLUS:**
- 🤖 **AI Chat in Project Database** - Ask questions in natural language
- 🚀 **Faster performance** - No cloud latency
- 🔒 **Full KPMG API access** - Workbench AI features work

### Using the Project Database AI Chat

Once running locally:
1. Navigate to "Project Database" page
2. Enter password: `bud123`
3. Use the "💬 AI Chat Feature" tab
4. Ask questions like:
   - "Show me all projects in the technology industry"
   - "Give me all projects of Tim Kramer"
   - "Find projects from 2025"

The AI will understand your questions and filter the database automatically!

---

## 🔧 Configuration

### Database Connection

The app uses Streamlit secrets for database connection. Create `.streamlit/secrets.toml`:

```toml
SUPABASE_DB_URI = "your_database_connection_string"
OFFICE_TIMEZONE = "Europe/Amsterdam"
```

### API Keys (Already Pre-configured)

The KPMG Workbench API credentials are pre-configured in the code. They work automatically when on KPMG network.

---

## 🆘 Troubleshooting

### AI Chat Not Working Locally?

1. **Check VPN:** Ensure you're connected to KPMG VPN
2. **Check Network:** Verify you can access internal KPMG services
3. **Refresh:** Sometimes a page refresh helps

### Other Issues?

- Check you're using Python 3.8+: `python --version`
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Check logs in terminal for detailed error messages

---

## 📚 More Documentation

- `README_STRATEGY2.md` - Strategy 2 allocation logic
- `OASIS_CONFIRMATION_SETUP.md` - Oasis confirmation system
- `LOCAL_SETUP.md` - Detailed local development setup

---

## 🎯 Key Features

### Room Allocator (Main App)
- Weekly project room allocation
- Oasis booking system
- Preference submission
- Admin controls

### Project Database Viewer
- 📊 Statistics and visualizations
- 🏭 Filter by industry
- 👤 Filter by partner
- 👔 Filter by manager
- 💬 AI Chat (local only)
- 📥 Export to CSV/Excel
- ⚙️ Column selection