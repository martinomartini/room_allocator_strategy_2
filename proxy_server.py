"""
KPMG Workbench API Proxy Server

This proxy runs on your local KPMG machine and forwards requests from Streamlit Cloud
to the KPMG Workbench API (which is only accessible from KPMG network).

How it works:
1. You run this proxy on your local machine (connected to KPMG network/VPN)
2. Streamlit Cloud sends requests to this proxy
3. Proxy forwards to KPMG Workbench API
4. Proxy returns the response to Streamlit Cloud

Security: Uses a secret token to ensure only your Streamlit app can use this proxy
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging

app = Flask(__name__)
CORS(app)  # Allow requests from Streamlit Cloud

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# KPMG Workbench API configuration
API_URL = "https://api.workbench.kpmg/genai/azure/inference/chat/completions"
DEFAULT_SUBSCRIPTION_KEY = "b82fef87872349b981d5c0d58afb55c1"
DEFAULT_CHARGE_CODE = "1"
DEFAULT_DEPLOYMENT = "gpt-4o-2024-08-06-dzs-we"

# Security token - set this as environment variable or Streamlit secret
# Generate a random token: python -c "import secrets; print(secrets.token_urlsafe(32))"
PROXY_TOKEN = os.environ.get("PROXY_TOKEN", "change-this-to-a-secure-random-token")

def get_api_headers():
    """Get headers for KPMG Workbench API"""
    return {
        'Ocp-Apim-Subscription-Key': DEFAULT_SUBSCRIPTION_KEY,
        'x-kpmg-charge-code': DEFAULT_CHARGE_CODE,
        'azureml-model-deployment': DEFAULT_DEPLOYMENT,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "KPMG Workbench Proxy is running"
    })

@app.route('/api/chat', methods=['POST'])
def proxy_chat():
    """Proxy endpoint for chat completions"""
    try:
        # Verify token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            logger.warning("Missing or invalid Authorization header")
            return jsonify({"error": "Unauthorized - Missing token"}), 401
        
        token = auth_header.replace('Bearer ', '')
        if token != PROXY_TOKEN:
            logger.warning("Invalid proxy token")
            return jsonify({"error": "Unauthorized - Invalid token"}), 401
        
        # Get request body
        body = request.get_json()
        if not body:
            return jsonify({"error": "No request body provided"}), 400
        
        logger.info(f"Forwarding request to KPMG Workbench API")
        
        # Forward to KPMG Workbench API
        response = requests.post(
            API_URL,
            headers=get_api_headers(),
            json=body,
            timeout=30
        )
        
        logger.info(f"KPMG API responded with status: {response.status_code}")
        
        # Return the response
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({
                "error": f"KPMG API error: {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({"error": f"Request failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@app.route('/')
def index():
    """Info page"""
    return """
    <html>
    <head><title>KPMG Workbench Proxy</title></head>
    <body>
        <h1>KPMG Workbench API Proxy</h1>
        <p>This proxy forwards requests from Streamlit Cloud to KPMG Workbench API.</p>
        <h2>Status</h2>
        <ul>
            <li>Proxy is running ✓</li>
            <li>KPMG Network: Connected (if this page loads)</li>
        </ul>
        <h2>Endpoints</h2>
        <ul>
            <li><code>GET /health</code> - Health check</li>
            <li><code>POST /api/chat</code> - Chat completions (requires auth token)</li>
        </ul>
        <p><small>Keep this window/terminal open to keep the proxy running</small></p>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Check if token is still default
    if PROXY_TOKEN == "change-this-to-a-secure-random-token":
        print("\n" + "="*70)
        print("⚠️  WARNING: Using default proxy token!")
        print("="*70)
        print("\nFor security, generate a secure token:")
        print("  python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        print("\nThen set it as environment variable:")
        print("  set PROXY_TOKEN=your-generated-token")
        print("  python proxy_server.py")
        print("\n" + "="*70 + "\n")
    
    print("\n" + "="*70)
    print("🚀 KPMG Workbench API Proxy Server")
    print("="*70)
    print(f"\nProxy Token: {PROXY_TOKEN[:10]}...{PROXY_TOKEN[-10:]}")
    print("\n📝 To make this accessible from Streamlit Cloud:")
    print("   1. Make sure you're on KPMG VPN")
    print("   2. You may need to expose this using ngrok or similar:")
    print("      ngrok http 5000")
    print("   3. Add the ngrok URL to Streamlit secrets as PROXY_URL")
    print("   4. Add this token to Streamlit secrets as PROXY_TOKEN")
    print("\n🔗 Proxy running at: http://localhost:5000")
    print("="*70 + "\n")
    
    # Run on all interfaces so it can be accessed externally
    app.run(host='0.0.0.0', port=5000, debug=False)
