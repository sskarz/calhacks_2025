import base64
from dotenv import load_dotenv
import os
import requests
import secrets
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(title="eBay OAuth API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# eBay Sandbox Credentials
CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
REDIRECT_URI = "Sanskar_Thapa-SanskarT-Tetsy--ttepui"  # This is the RuName
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000")  # Set to your ngrok URL
SANDBOX_TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
SANDBOX_AUTH_URL = "https://auth.sandbox.ebay.com/oauth2/authorize"

# Scopes needed for creating listings, managing inventory, and messaging
REQUIRED_SCOPES = [
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
    "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
    "https://api.ebay.com/oauth/api_scope/sell.account",
    "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
    "https://api.ebay.com/oauth/api_scope/sell.marketing",
    "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly",
    "https://api.ebay.com/oauth/api_scope/sell.item",
]

# In-memory storage for OAuth state and tokens
oauth_sessions = {}
token_storage = {"current_token": None}


# Models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None


# Endpoints
@app.get("/", response_class=HTMLResponse)
async def root(
    code: Optional[str] = Query(None, description="Authorization code from eBay"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection")
):
    """Root endpoint with test flow instructions. Also handles OAuth callback."""
    
    # If code and state are present, this is an OAuth callback - forward to handler
    if code and state:
        return await oauth_callback(code=code, state=state)
    
    # Otherwise, show the normal HTML page
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>eBay OAuth Test Flow</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #0064d2;
            }
            .step {
                background-color: #f9f9f9;
                padding: 15px;
                margin: 15px 0;
                border-left: 4px solid #0064d2;
            }
            .step-number {
                font-weight: bold;
                color: #0064d2;
            }
            button {
                background-color: #0064d2;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                margin: 10px 0;
            }
            button:hover {
                background-color: #0053b8;
            }
            .code {
                background-color: #f4f4f4;
                padding: 10px;
                border-radius: 4px;
                font-family: monospace;
                overflow-x: auto;
            }
            .success {
                color: #28a745;
            }
            .warning {
                color: #ffc107;
                background-color: #fff3cd;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 eBay OAuth Authorization Test Flow</h1>

            <div class="warning">
                ⚠️ <strong>Important:</strong> This uses eBay's Sandbox environment. You'll need a sandbox account to test.
            </div>

            <h2>📋 Test Flow Instructions</h2>

            <div class="step">
                <span class="step-number">STEP 1:</span> Click the button below to start authorization
                <br><br>
                <button onclick="startAuth()">Start eBay Authorization</button>
            </div>

            <div class="step">
                <span class="step-number">STEP 2:</span> You'll be redirected to eBay Sandbox login page
                <ul>
                    <li>Sign in with your eBay Sandbox account</li>
                    <li>Grant permissions for the app</li>
                    <li>You'll be redirected back automatically</li>
                </ul>
            </div>

            <div class="step">
                <span class="step-number">STEP 3:</span> Check your token status
                <br><br>
                <button onclick="checkToken()">Check Token Status</button>
                <div id="token-status"></div>
            </div>

            <h2>🔧 API Endpoints</h2>
            <div class="code">
GET  /start-auth          - Start authorization flow<br>
GET  /oauth/callback      - OAuth callback (automatic)<br>
GET  /token/status        - Check current token<br>
POST /oauth/refresh       - Refresh expired token
            </div>

            <h2>📦 Scopes Requested</h2>
            <div class="code">
✅ sell.inventory - Create/manage listings<br>
✅ sell.account - Account management<br>
✅ sell.fulfillment - Order management<br>
✅ sell.marketing - Marketing tools<br>
✅ sell.item - Item operations
            </div>
        </div>

        <script>
            function startAuth() {
                window.location.href = '/start-auth';
            }

            async function checkToken() {
                const statusDiv = document.getElementById('token-status');
                statusDiv.innerHTML = '<p>Checking...</p>';

                try {
                    const response = await fetch('/token/status');
                    const data = await response.json();

                    if (data.has_token) {
                        statusDiv.innerHTML = `
                            <div style="margin-top: 15px; padding: 15px; background-color: #d4edda; border-radius: 4px;">
                                <strong class="success">✅ Token Active!</strong><br>
                                <small>Expires in: ${data.expires_in} seconds</small><br>
                                <small>Token type: ${data.token_type}</small><br>
                                <small style="word-break: break-all;">Access token: ${data.access_token.substring(0, 50)}...</small>
                            </div>
                        `;
                    } else {
                        statusDiv.innerHTML = `
                            <div style="margin-top: 15px; padding: 15px; background-color: #f8d7da; border-radius: 4px;">
                                <strong style="color: #721c24;">❌ No Token Found</strong><br>
                                <small>Please complete Step 1 and Step 2 first</small>
                            </div>
                        `;
                    }
                } catch (error) {
                    statusDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/start-auth")
async def start_auth():
    """
    Simple endpoint to start the authorization flow.
    Redirects user directly to eBay's authorization page.
    """
    from fastapi.responses import RedirectResponse

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Use required scopes
    scope_string = " ".join(REQUIRED_SCOPES)

    # Store state for callback validation
    oauth_sessions[state] = {
        "scopes": scope_string
    }

    # Build authorization URL
    auth_params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": scope_string,
        "state": state
    }

    # Manually build query string to preserve scope formatting
    from urllib.parse import urlencode
    query_string = urlencode(auth_params)
    full_auth_url = f"{SANDBOX_AUTH_URL}?{query_string}"

    return RedirectResponse(url=full_auth_url)


@app.get("/oauth/callback", response_class=HTMLResponse)
async def oauth_callback(
    code: str = Query(..., description="Authorization code from eBay"),
    state: str = Query(..., description="State parameter for CSRF protection")
):
    """
    OAuth callback endpoint that exchanges the authorization code for tokens.
    eBay redirects here after user authorization.
    """
    # Verify state
    if state not in oauth_sessions:
        return HTMLResponse(
            content="""
            <html>
                <body style="font-family: Arial; padding: 50px; text-align: center;">
                    <h1 style="color: red;">❌ Authorization Failed</h1>
                    <p>Invalid state parameter. Please try again.</p>
                    <a href="/" style="padding: 10px 20px; background-color: #0064d2; color: white; text-decoration: none; border-radius: 4px;">Go Back</a>
                </body>
            </html>
            """,
            status_code=400
        )

    try:
        # Debug logging
        print(f"\n[DEBUG] Processing OAuth callback")
        print(f"[DEBUG] State: {state}")
        print(f"[DEBUG] Code received: {code[:20]}...")
        print(f"[DEBUG] REDIRECT_URI (RuName): {REDIRECT_URI}")

        # Encode credentials in Base64
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Prepare headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }

        # Prepare token exchange request
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }

        print(f"[DEBUG] Requesting token from: {SANDBOX_TOKEN_URL}")

        # Exchange code for token
        response = requests.post(
            SANDBOX_TOKEN_URL,
            headers=headers,
            data=body
        )

        print(f"[DEBUG] Token response status: {response.status_code}")

        if response.status_code != 200:
            print(f"[DEBUG] Token exchange failed: {response.text}")
            return HTMLResponse(
                content=f"""
                <html>
                    <body style="font-family: Arial; padding: 50px; text-align: center;">
                        <h1 style="color: red;">❌ Token Exchange Failed</h1>
                        <p>Error: {response.text}</p>
                        <a href="/" style="padding: 10px 20px; background-color: #0064d2; color: white; text-decoration: none; border-radius: 4px;">Go Back</a>
                    </body>
                </html>
                """,
                status_code=500
            )

        token_data = response.json()

        # Store token
        token_storage["current_token"] = token_data

        print(f"[DEBUG] Token successfully stored!")
        print(f"[DEBUG] Token type: {token_data.get('token_type')}")
        print(f"[DEBUG] Expires in: {token_data.get('expires_in')} seconds")
        print(f"[DEBUG] Has refresh token: {bool(token_data.get('refresh_token'))}")
        print(f"[DEBUG] Current token storage: {bool(token_storage['current_token'])}")

        # Clean up session
        del oauth_sessions[state]

        return HTMLResponse(
            content=f"""
            <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            max-width: 800px;
                            margin: 50px auto;
                            padding: 20px;
                            background-color: #f5f5f5;
                        }}
                        .success-box {{
                            background-color: white;
                            padding: 30px;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            text-align: center;
                        }}
                        .token-info {{
                            background-color: #f9f9f9;
                            padding: 15px;
                            margin: 20px 0;
                            border-radius: 4px;
                            text-align: left;
                            word-break: break-all;
                        }}
                        button {{
                            background-color: #0064d2;
                            color: white;
                            padding: 12px 24px;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 16px;
                            margin: 10px;
                        }}
                        button:hover {{
                            background-color: #0053b8;
                        }}
                    </style>
                </head>
                <body>
                    <div class="success-box">
                        <h1 style="color: #28a745;">✅ Authorization Successful!</h1>
                        <p>Your eBay OAuth token has been generated and stored.</p>

                        <div class="token-info">
                            <strong>Access Token:</strong><br>
                            <code>{token_data.get('access_token')[:100]}...</code><br><br>

                            <strong>Token Type:</strong> {token_data.get('token_type')}<br>
                            <strong>Expires In:</strong> {token_data.get('expires_in')} seconds ({token_data.get('expires_in') // 3600} hours)<br>
                            <strong>Has Refresh Token:</strong> {'Yes' if token_data.get('refresh_token') else 'No'}
                        </div>

                        <p>You can now use this token to:</p>
                        <ul style="text-align: left;">
                            <li>Create listings on eBay</li>
                            <li>Update existing listings</li>
                            <li>Manage inventory and prices</li>
                            <li>Handle fulfillment and orders</li>
                        </ul>

                        <button onclick="window.location.href='/'">Back to Home</button>
                        <button onclick="window.location.href='/token/status'">View Token JSON</button>
                    </div>
                </body>
            </html>
            """
        )

    except requests.exceptions.RequestException as e:
        return HTMLResponse(
            content=f"""
            <html>
                <body style="font-family: Arial; padding: 50px; text-align: center;">
                    <h1 style="color: red;">❌ Request Failed</h1>
                    <p>Error: {str(e)}</p>
                    <a href="/" style="padding: 10px 20px; background-color: #0064d2; color: white; text-decoration: none; border-radius: 4px;">Go Back</a>
                </body>
            </html>
            """,
            status_code=500
        )


@app.get("/token/status")
async def get_token_status():
    """
    Check the current token status.
    Returns token information if available.
    """
    print(f"\n[DEBUG] Token status check")
    print(f"[DEBUG] token_storage contents: {token_storage}")
    print(f"[DEBUG] Has token: {bool(token_storage['current_token'])}")

    if token_storage["current_token"]:
        token_data = token_storage["current_token"]
        print(f"[DEBUG] Returning token data")
        return {
            "has_token": True,
            "access_token": token_data.get("access_token"),
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in"),
            "refresh_token": token_data.get("refresh_token")
        }
    else:
        print(f"[DEBUG] No token found in storage")
        return {
            "has_token": False,
            "message": "No token available. Please authorize first."
        }


@app.post("/oauth/refresh")
async def refresh_token(refresh_token: Optional[str] = None):
    """
    Refresh an expired access token using a refresh token.
    If no refresh_token is provided, uses the stored one.
    """
    # Use provided token or get from storage
    token_to_refresh = refresh_token or (
        token_storage["current_token"].get("refresh_token") if token_storage["current_token"] else None
    )

    if not token_to_refresh:
        raise HTTPException(
            status_code=400,
            detail="No refresh token available. Please provide one or authorize first."
        )

    try:
        # Encode credentials in Base64
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Prepare headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }

        # Prepare refresh request
        body = {
            "grant_type": "refresh_token",
            "refresh_token": token_to_refresh
        }

        # Request new token
        response = requests.post(
            SANDBOX_TOKEN_URL,
            headers=headers,
            data=body
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Token refresh failed: {response.text}"
            )

        new_token_data = response.json()

        # Update stored token
        token_storage["current_token"] = new_token_data

        return new_token_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Request failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 eBay OAuth Test Server Starting...")
    print("="*60)
    print("\n📋 Quick Start:")
    print(f"   1. Open your browser to: {PUBLIC_URL}")
    if "localhost" in PUBLIC_URL:
        print("\n   ⚠️  IMPORTANT: eBay requires HTTPS for OAuth!")
        print("   Run 'ngrok http 8001' and set PUBLIC_URL env var")
        print("   Example: PUBLIC_URL=https://abc123.ngrok.io")
    print("\n   2. Click 'Start eBay Authorization'")
    print("   3. Sign in with your eBay Sandbox account")
    print("   4. Grant permissions")
    print("   5. You'll get your OAuth token!")
    print("\n" + "="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)
