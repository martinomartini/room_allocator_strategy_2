# Proxy Server Setup - Enable AI Chat on Streamlit Cloud

## The Problem
KPMG Workbench API is only accessible from within the KPMG network. Streamlit Cloud (public internet) cannot reach it.

## The Solution
Run a **proxy server** on your local KPMG machine that forwards requests from Streamlit Cloud to KPMG Workbench API.

```
Streamlit Cloud → Your Local Proxy → KPMG Workbench API
(public internet)   (KPMG network)      (internal API)
```

---

## Step 1: Generate Security Token

On your local machine, generate a secure random token:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Save this token!** You'll need it in Step 3 and Step 5.

Example output: `xK9mP2vL8qR4tN7wS3fH6jD1gY5bC0aZ`

---

## Step 2: Install Proxy Dependencies

```powershell
cd "c:\Users\mmartini1\OneDrive - KPMG\Documents\Python Scripts\room_allocator_strategy_2"
pip install -r proxy_requirements.txt
```

---

## Step 3: Set Environment Variable

Set the token as an environment variable (replace with your token from Step 1):

```powershell
$env:PROXY_TOKEN = "xK9mP2vL8qR4tN7wS3fH6jD1gY5bC0aZ"
```

---

## Step 4: Run the Proxy Server

```powershell
python proxy_server.py
```

You should see:
```
🚀 KPMG Workbench API Proxy Server
Proxy Token: xK9mP2vL8q...Y5bC0aZ
🔗 Proxy running at: http://localhost:5000
```

**Keep this terminal window open!** The proxy runs as long as this window stays open.

---

## Step 5: Expose Proxy to Internet (using ngrok)

Since Streamlit Cloud needs to reach your local machine, use **ngrok** to create a public URL:

### Install ngrok:
1. Download from: https://ngrok.com/download
2. Extract and run: `ngrok.exe`
3. Sign up for free account at https://ngrok.com
4. Get your authtoken from dashboard
5. Run: `ngrok authtoken YOUR_AUTH_TOKEN`

### Start ngrok tunnel:

```powershell
# Open NEW terminal window
ngrok http 5000
```

You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`) - you'll need this in Step 6.

**Keep this window open too!**

---

## Step 6: Configure Streamlit Cloud

1. Go to your Streamlit Cloud dashboard: https://share.streamlit.io
2. Find your app: `room_allocator_strategy_2`
3. Click the **⚙️ Settings** button
4. Go to **Secrets** section
5. Add the following (replace with your values):

```toml
PROXY_URL = "https://abc123.ngrok.io"
PROXY_TOKEN = "xK9mP2vL8qR4tN7wS3fH6jD1gY5bC0aZ"
```

6. Click **Save**
7. App will automatically restart

---

## Step 7: Test It!

1. Go to your Streamlit Cloud app
2. Navigate to **Project Database** page
3. Enter password: `bud123`
4. Go to **💬 AI Chat Feature** tab
5. Ask: "Give me all projects of Tim Kramer"
6. **It should work!** 🎉

---

## Keeping It Running

### Daily Usage:
```powershell
# Terminal 1: Start proxy
$env:PROXY_TOKEN = "your-token-here"
cd "c:\Users\mmartini1\OneDrive - KPMG\Documents\Python Scripts\room_allocator_strategy_2"
python proxy_server.py

# Terminal 2: Start ngrok (in a new window)
ngrok http 5000
```

### Stopping:
- Press `Ctrl+C` in both terminal windows
- Or just close the windows

---

## Troubleshooting

### "Unauthorized" error on Streamlit Cloud
- Check that PROXY_TOKEN in Streamlit secrets matches your environment variable
- Make sure both terminals (proxy + ngrok) are running

### "Connection refused" error
- Check ngrok is running and URL hasn't changed
- Update PROXY_URL in Streamlit secrets if ngrok URL changed
- Ngrok free URLs change every time you restart ngrok

### "KPMG API error: 403"
- Make sure you're connected to KPMG VPN
- Verify proxy can reach KPMG Workbench API locally

### Ngrok URL keeps changing
- **Free ngrok accounts** get a new URL each restart
- **Paid ngrok** ($8/month) gives you a permanent URL
- Alternative: Update Streamlit secrets each time ngrok restarts

---

## Security Notes

✅ **Good:**
- Token authentication prevents unauthorized access
- HTTPS encryption via ngrok
- Proxy only forwards to KPMG API (can't access other services)

⚠️ **Be aware:**
- Anyone with your ngrok URL + token can use your proxy
- Keep token secret!
- Don't commit token to git
- Consider paid ngrok for stable URL with password protection

---

## Alternative: No Proxy Setup

If you don't want to run a proxy, the app works fine without it:
- **Locally:** Full AI chat features ✅
- **Streamlit Cloud:** All features except AI chat ✅
- Users see friendly message explaining AI chat requires local run

This is the current setup and works well for most use cases!
