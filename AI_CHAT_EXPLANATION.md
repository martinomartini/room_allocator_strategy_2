# AI Chat Feature - How It Works

## Summary

**✅ AI Chat works perfectly when running locally on KPMG network**  
**❌ AI Chat is disabled on Streamlit Cloud (by design)**

This is the **simplest and most reliable solution** - no proxy servers, no ngrok, no maintenance.

---

## Why This Approach?

### The Technical Reality:
- KPMG Workbench API is **only accessible from KPMG network** (internal API)
- Streamlit Cloud runs on **public internet** (cannot reach internal KPMG APIs)
- This is a **network/firewall restriction** - cannot be bypassed with code tricks

### The Simple Solution:
- **Local (KPMG network):** Full AI chat capabilities ✅
- **Streamlit Cloud:** All other features, AI chat disabled ✅
- Clear messaging tells users how to get AI chat if needed

---

## Features Comparison

| Feature | Streamlit Cloud | Running Locally |
|---------|----------------|----------------|
| View projects | ✅ Works | ✅ Works |
| Filter by industry | ✅ Works | ✅ Works |
| Filter by partner | ✅ Works | ✅ Works |
| Filter by manager | ✅ Works | ✅ Works |
| Statistics & charts | ✅ Works | ✅ Works |
| Export to CSV/Excel | ✅ Works | ✅ Works |
| Column selection | ✅ Works | ✅ Works |
| **AI Chat** | ❌ Disabled | ✅ **Works!** |

**Bottom line:** 95% of features work everywhere. AI chat works where it matters (locally).

---

## For Users

### On Streamlit Cloud:
You'll see:
```
ℹ️ AI Chat is disabled on Streamlit Cloud - KPMG Workbench API 
is only accessible from KPMG network.

To use AI Chat: Run locally with `streamlit run app.py` 
(all other tabs work perfectly!)
```

The chat input box is grayed out and disabled.

### Running Locally:
You'll see:
```
🤖 AI-Powered Search: Ask questions in natural language! 
Running locally with KPMG network access.
```

Chat works perfectly! Try:
- "Show me all projects in technology"
- "Give me all projects of Tim Kramer"
- "All projects from 2024"

---

## Quick Start Guide

### Option 1: Streamlit Cloud (Most Features)
Just visit: [Your Streamlit Cloud URL]
- Password: `bud123`
- All features except AI chat
- Always available, no setup

### Option 2: Run Locally (Full Features)
```powershell
cd "room_allocator_strategy_2"
streamlit run app.py
```
- Password: `bud123`
- ALL features including AI chat
- Requires KPMG network/VPN

---

## Why Not Use a Proxy?

We **could** set up a proxy server (see `PROXY_SETUP.md` if interested), but it adds complexity:

**Proxy Approach:**
- ❌ Need to keep local proxy server running 24/7
- ❌ Need ngrok or similar for public URL  
- ❌ Ngrok free URLs change on every restart
- ❌ Security concerns (exposing local API access)
- ❌ Maintenance burden

**Current Approach:**
- ✅ Zero maintenance
- ✅ Zero security concerns
- ✅ Works reliably when you need it
- ✅ Clean, simple code

---

## Developer Notes

### Environment Detection

The app automatically detects its environment:

```python
def is_running_locally():
    """Detect if app is running locally vs Streamlit Cloud"""
    return os.environ.get("STREAMLIT_SHARING_MODE") is None
```

### AI Chat Toggle

```python
if is_running_locally():
    # Enable AI chat
    if prompt := st.chat_input("Ask about projects..."):
        # Process with KPMG Workbench API
else:
    # Disable AI chat
    st.chat_input("AI Chat disabled on Cloud", disabled=True)
```

### API Connection

When running locally:
1. App calls `call_workbench_api()`
2. Uses browser-like headers to avoid blocking
3. Connects to `https://api.workbench.kpmg/...`
4. Returns AI-parsed filters

When on Streamlit Cloud:
1. `is_running_locally()` returns `False`
2. `call_workbench_api()` returns `None` immediately
3. User sees friendly disabled message
4. No failed API calls, no error logs

---

## Conclusion

This is the **pragmatic solution**: 
- Works great where users need it (locally)
- Doesn't pretend to work where it can't (cloud)
- No complex workarounds that break
- Clear communication to users

**If you really need AI chat on the cloud**, see `PROXY_SETUP.md`, but for 99% of use cases, this local-only approach is perfect!
