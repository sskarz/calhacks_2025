from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
import os
import httpx
import secrets
import hashlib
import base64
from pydantic import BaseModel

# Load environment variables
load_dotenv()

app = FastAPI(title="Etsy OAuth Backend")

# Configuration from .env
ETSY_API_KEY = os.getenv("ETSY_API_KEY")
ETSY_SHARED_SECRET = os.getenv("ETSY_SHARED_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/oauth/callback")

# In-memory storage for PKCE verifiers and tokens (use database in production)
oauth_sessions = {}
token_storage = {}


# Models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


# PKCE Helper Functions
def generate_code_verifier() -> str:
    """Generate a PKCE code verifier (random string)"""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')


def generate_code_challenge(verifier: str) -> str:
    """Generate a PKCE code challenge from verifier using SHA256"""
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Etsy OAuth Backend API",
        "endpoints": {
            "health": "/health",
            "authorize": "/oauth/authorize",
            "callback": "/oauth/callback",
            "refresh": "/oauth/refresh",
            "ping": "/ping"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/oauth/authorize")
async def authorize(
    scopes: str = Query(default="email_r listings_r", description="Space-separated scopes")
):
    """
    Initiate OAuth flow by redirecting to Etsy's authorization page.

    Parameters:
    - scopes: Space-separated list of scopes (default: "email_r listings_r")

    Common scopes:
    - email_r: Read email address
    - listings_r: Read shop listings
    - listings_w: Write shop listings
    - transactions_r: Read transactions
    - transactions_w: Write transactions
    """
    if not ETSY_API_KEY:
        raise HTTPException(status_code=500, detail="ETSY_API_KEY not configured")

    # Generate PKCE parameters
    state = secrets.token_urlsafe(32)
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    # Store the verifier and scopes for later use in callback
    oauth_sessions[state] = {
        "code_verifier": code_verifier,
        "scopes": scopes
    }

    # Build authorization URL
    auth_params = {
        "response_type": "code",
        "client_id": ETSY_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "scope": scopes,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }

    auth_url = "https://www.etsy.com/oauth/connect"
    query_string = "&".join([f"{k}={v}" for k, v in auth_params.items()])
    full_auth_url = f"{auth_url}?{query_string}"

    return {
        "authorization_url": full_auth_url,
        "state": state,
        "message": "Visit the authorization_url to grant access"
    }


@app.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Etsy"),
    state: str = Query(..., description="State parameter for CSRF protection")
):
    """
    OAuth callback endpoint that exchanges the authorization code for tokens.
    This is where Etsy redirects after user authorization.
    """
    # Verify state and retrieve session
    if state not in oauth_sessions:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    session = oauth_sessions[state]
    code_verifier = session["code_verifier"]

    # Exchange authorization code for tokens
    token_url = "https://api.etsy.com/v3/public/oauth/token"

    token_data = {
        "grant_type": "authorization_code",
        "client_id": ETSY_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "code_verifier": code_verifier
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Token exchange failed: {response.text}"
            )

        token_response = response.json()

    # Extract user_id from access token (prefix before the dot)
    access_token = token_response.get("access_token", "")
    user_id = access_token.split('.')[0] if '.' in access_token else None

    # Store tokens (in production, use secure database)
    if user_id:
        token_storage[user_id] = token_response

    # Clean up session
    del oauth_sessions[state]

    return {
        "message": "Authorization successful",
        "user_id": user_id,
        "access_token": token_response.get("access_token"),
        "token_type": token_response.get("token_type"),
        "expires_in": token_response.get("expires_in"),
        "refresh_token": token_response.get("refresh_token")
    }


@app.post("/oauth/refresh")
async def refresh_token(refresh_token: str):
    """
    Refresh an expired access token using a refresh token.

    Parameters:
    - refresh_token: The refresh token received during authorization
    """
    if not ETSY_API_KEY:
        raise HTTPException(status_code=500, detail="ETSY_API_KEY not configured")

    token_url = "https://api.etsy.com/v3/public/oauth/token"

    refresh_data = {
        "grant_type": "refresh_token",
        "client_id": ETSY_API_KEY,
        "refresh_token": refresh_token
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=refresh_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Token refresh failed: {response.text}"
            )

        return response.json()


@app.get("/ping")
async def ping_etsy():
    """
    Test the connection to Etsy API using the API key.
    This endpoint doesn't require OAuth.
    """
    if not ETSY_API_KEY:
        raise HTTPException(status_code=500, detail="ETSY_API_KEY not configured")

    ping_url = "https://api.etsy.com/v3/application/openapi-ping"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            ping_url,
            headers={"x-api-key": ETSY_API_KEY}
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ping failed: {response.text}"
            )

        return response.json()


@app.get("/user/{user_id}")
async def get_user_info(
    user_id: str,
    access_token: str = Query(..., description="OAuth access token")
):
    """
    Get user information from Etsy API.
    Requires a valid access token.
    """
    if not ETSY_API_KEY:
        raise HTTPException(status_code=500, detail="ETSY_API_KEY not configured")

    user_url = f"https://api.etsy.com/v3/application/users/{user_id}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            user_url,
            headers={
                "x-api-key": ETSY_API_KEY,
                "Authorization": f"Bearer {access_token}"
            }
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch user info: {response.text}"
            )

        return response.json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
