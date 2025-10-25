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


# eBay Sandbox API URLs
SANDBOX_INVENTORY_BASE = "https://api.sandbox.ebay.com/sell/inventory/v1"
SANDBOX_ACCOUNT_BASE = "https://api.sandbox.ebay.com/sell/account/v1"


# Models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None


class ProductDetails(BaseModel):
    title: str
    description: str
    brand: Optional[str] = None
    mpn: Optional[str] = None
    imageUrls: List[str]
    aspects: Optional[dict] = None


class CreateInventoryItemRequest(BaseModel):
    sku: str
    condition: str = "NEW"  # NEW, USED_EXCELLENT, etc.
    product: ProductDetails
    availability_quantity: int


class CreateOfferRequest(BaseModel):
    sku: str
    categoryId: str
    price: float
    currency: str = "USD"
    listingDuration: str = "GTC"  # Good 'Til Cancelled
    merchantLocationKey: str = "default_location"


class CreateListingRequest(BaseModel):
    sku: str
    title: str
    description: str
    price: float
    quantity: int
    categoryId: str
    condition: str = "NEW"
    imageUrls: List[str]
    brand: Optional[str] = None
    currency: str = "USD"


# Helper Functions
def get_access_token():
    """Get the current access token from storage"""
    if not token_storage["current_token"]:
        raise HTTPException(
            status_code=401,
            detail="No access token available. Please authorize first via /start-auth"
        )
    return token_storage["current_token"]["access_token"]


def get_or_create_policies():
    """Get existing policies or create default ones for sandbox testing"""
    access_token = get_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Content-Language": "en-US"
    }

    policies = {}

    # Check for existing fulfillment policy
    fulfillment_url = f"{SANDBOX_ACCOUNT_BASE}/fulfillment_policy?marketplace_id=EBAY_US"
    fulfillment_response = requests.get(fulfillment_url, headers=headers)

    if fulfillment_response.status_code == 200:
        fulfillment_data = fulfillment_response.json()
        if fulfillment_data.get("total", 0) > 0:
            policies["fulfillmentPolicyId"] = fulfillment_data["fulfillmentPolicies"][0]["fulfillmentPolicyId"]
            print(f"[POLICY] Using existing fulfillment policy: {policies['fulfillmentPolicyId']}")
        else:
            # Create default fulfillment policy
            fulfillment_payload = {
                "name": "Default Free Shipping",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "handlingTime": {"unit": "DAY", "value": 1},
                "shippingOptions": [{
                    "optionType": "DOMESTIC",
                    "costType": "FLAT_RATE",
                    "shippingServices": [{
                        "shippingServiceCode": "USPSPriority",
                        "freeShipping": True
                    }]
                }]
            }
            create_response = requests.post(
                f"{SANDBOX_ACCOUNT_BASE}/fulfillment_policy/",
                headers=headers,
                json=fulfillment_payload
            )
            if create_response.status_code in [200, 201]:
                policies["fulfillmentPolicyId"] = create_response.json()["fulfillmentPolicyId"]
                print(f"[POLICY] Created new fulfillment policy: {policies['fulfillmentPolicyId']}")

    # Check for existing payment policy
    payment_url = f"{SANDBOX_ACCOUNT_BASE}/payment_policy?marketplace_id=EBAY_US"
    payment_response = requests.get(payment_url, headers=headers)

    if payment_response.status_code == 200:
        payment_data = payment_response.json()
        if payment_data.get("total", 0) > 0:
            policies["paymentPolicyId"] = payment_data["paymentPolicies"][0]["paymentPolicyId"]
            print(f"[POLICY] Using existing payment policy: {policies['paymentPolicyId']}")
        else:
            # Create default payment policy
            payment_payload = {
                "name": "Default Payment Policy",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "paymentMethods": [{"paymentMethodType": "PAYPAL"}],
                "immediatePay": False
            }
            create_response = requests.post(
                f"{SANDBOX_ACCOUNT_BASE}/payment_policy/",
                headers=headers,
                json=payment_payload
            )
            if create_response.status_code in [200, 201]:
                policies["paymentPolicyId"] = create_response.json()["paymentPolicyId"]
                print(f"[POLICY] Created new payment policy: {policies['paymentPolicyId']}")

    # Check for existing return policy
    return_url = f"{SANDBOX_ACCOUNT_BASE}/return_policy?marketplace_id=EBAY_US"
    return_response = requests.get(return_url, headers=headers)

    if return_response.status_code == 200:
        return_data = return_response.json()
        if return_data.get("total", 0) > 0:
            policies["returnPolicyId"] = return_data["returnPolicies"][0]["returnPolicyId"]
            print(f"[POLICY] Using existing return policy: {policies['returnPolicyId']}")
        else:
            # Create default return policy
            return_payload = {
                "name": "Default Return Policy",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "returnsAccepted": True,
                "returnPeriod": {"unit": "DAY", "value": 30},
                "refundMethod": "MONEY_BACK",
                "returnShippingCostPayer": "BUYER"
            }
            create_response = requests.post(
                f"{SANDBOX_ACCOUNT_BASE}/return_policy/",
                headers=headers,
                json=return_payload
            )
            if create_response.status_code in [200, 201]:
                policies["returnPolicyId"] = create_response.json()["returnPolicyId"]
                print(f"[POLICY] Created new return policy: {policies['returnPolicyId']}")

    return policies


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


# eBay Listing Endpoints

@app.post("/inventory/create-location")
async def create_inventory_location(
    location_key: str = "default_location",
    name: str = "Default Location",
    address_line1: str = "123 Main St",
    city: str = "San Jose",
    state_or_province: str = "CA",
    postal_code: str = "95050",
    country: str = "US"
):
    """
    Create an inventory location. Required before creating offers.
    eBay requires at least one location to be set up for your account.
    """
    try:
        access_token = get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US"
        }

        payload = {
            "location": {
                "address": {
                    "addressLine1": address_line1,
                    "city": city,
                    "stateOrProvince": state_or_province,
                    "postalCode": postal_code,
                    "country": country
                }
            },
            "locationInstructions": "Items ship from this location",
            "name": name,
            "merchantLocationStatus": "ENABLED",
            "locationTypes": ["WAREHOUSE"]
        }

        url = f"{SANDBOX_INVENTORY_BASE}/location/{location_key}"
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201, 204]:
            return {
                "success": True,
                "message": "Inventory location created successfully",
                "location_key": location_key
            }
        else:
            # Location might already exist
            if response.status_code == 409:
                return {
                    "success": True,
                    "message": "Location already exists",
                    "location_key": location_key
                }
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create location: {response.text}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/inventory/create-item")
async def create_inventory_item(request: CreateInventoryItemRequest):
    """
    Step 1: Create an inventory item with product details.
    This is the first step in creating an eBay listing.
    """
    try:
        access_token = get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US"
        }

        # Prepare the inventory item payload
        payload = {
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": request.availability_quantity
                }
            },
            "condition": request.condition,
            "product": {
                "title": request.product.title,
                "description": request.product.description,
                "imageUrls": request.product.imageUrls
            }
        }

        # Add optional fields if provided
        if request.product.brand:
            payload["product"]["brand"] = request.product.brand
        if request.product.mpn:
            payload["product"]["mpn"] = request.product.mpn
        if request.product.aspects:
            payload["product"]["aspects"] = request.product.aspects

        # Create inventory item
        url = f"{SANDBOX_INVENTORY_BASE}/inventory_item/{request.sku}"
        response = requests.put(url, headers=headers, json=payload)

        if response.status_code in [200, 201, 204]:
            return {
                "success": True,
                "message": "Inventory item created successfully",
                "sku": request.sku,
                "status_code": response.status_code
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create inventory item: {response.text}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/inventory/create-offer")
async def create_offer(request: CreateOfferRequest):
    """
    Step 2: Create an offer for an inventory item.
    The offer includes pricing and marketplace information.
    """
    try:
        access_token = get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US"
        }

        # Prepare the offer payload
        payload = {
            "sku": request.sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingDescription": f"Listed via API for SKU {request.sku}",
            "categoryId": request.categoryId,
            "merchantLocationKey": request.merchantLocationKey,
            "listingDuration": request.listingDuration,
            "pricingSummary": {
                "price": {
                    "value": str(request.price),
                    "currency": request.currency
                }
            }
        }

        # Create offer
        url = f"{SANDBOX_INVENTORY_BASE}/offer"
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            offer_data = response.json()
            return {
                "success": True,
                "message": "Offer created successfully",
                "offerId": offer_data.get("offerId"),
                "status": offer_data.get("status"),
                "data": offer_data
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create offer: {response.text}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/inventory/publish-offer/{offer_id}")
async def publish_offer(offer_id: str):
    """
    Step 3: Publish an offer to create a live eBay listing.
    This makes the listing visible on eBay.
    """
    try:
        access_token = get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Publish offer
        url = f"{SANDBOX_INVENTORY_BASE}/offer/{offer_id}/publish"
        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            listing_data = response.json()
            return {
                "success": True,
                "message": "Offer published successfully!",
                "listingId": listing_data.get("listingId"),
                "warnings": listing_data.get("warnings", []),
                "data": listing_data
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to publish offer: {response.text}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/listing/create")
async def create_complete_listing(request: CreateListingRequest):
    """
    Simplified endpoint: Create a complete eBay listing in one call.
    This combines all three steps: create item, create offer, and publish.

    Example request:
    {
        "sku": "GOPRO-HERO-001",
        "title": "GoPro Hero4 Helmet Cam",
        "description": "New unopened box. Perfect condition.",
        "price": 299.99,
        "quantity": 10,
        "categoryId": "31388",
        "condition": "NEW",
        "imageUrls": ["https://example.com/image.jpg"],
        "brand": "GoPro",
        "currency": "USD"
    }
    """
    try:
        access_token = get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US"
        }

        # Step 0: Ensure location exists
        print(f"[LISTING] Step 0: Ensuring inventory location exists")
        location_payload = {
            "location": {
                "address": {
                    "addressLine1": "123 Main Street",
                    "city": "San Jose",
                    "stateOrProvince": "CA",
                    "postalCode": "95050",
                    "country": "US"
                }
            },
            "locationInstructions": "Items ship from this location",
            "name": "Default Location",
            "merchantLocationStatus": "ENABLED",
            "locationTypes": ["WAREHOUSE"]
        }

        location_url = f"{SANDBOX_INVENTORY_BASE}/location/default_location"
        location_response = requests.post(location_url, headers=headers, json=location_payload)

        # 409 means location already exists, which is fine
        if location_response.status_code not in [200, 201, 204, 409]:
            print(f"[LISTING] ⚠️ Location creation warning: {location_response.status_code} - {location_response.text}")
        else:
            print(f"[LISTING] ✓ Location ready")

        # Step 1: Create Inventory Item
        print(f"[LISTING] Step 1: Creating inventory item for SKU {request.sku}")
        inventory_payload = {
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": request.quantity
                }
            },
            "condition": request.condition,
            "product": {
                "title": request.title,
                "description": request.description,
                "imageUrls": request.imageUrls
            }
        }

        if request.brand:
            inventory_payload["product"]["brand"] = request.brand

        inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item/{request.sku}"
        inventory_response = requests.put(inventory_url, headers=headers, json=inventory_payload)

        if inventory_response.status_code not in [200, 201, 204]:
            raise HTTPException(
                status_code=inventory_response.status_code,
                detail=f"Step 1 failed - Create inventory item: {inventory_response.text}"
            )

        print(f"[LISTING] ✓ Inventory item created")

        # Step 1.5: Try to get policies (optional for sandbox)
        print(f"[LISTING] Step 1.5: Checking for business policies")
        try:
            policies = get_or_create_policies()
            use_policies = all(k in policies for k in ["fulfillmentPolicyId", "paymentPolicyId", "returnPolicyId"])
            if use_policies:
                print(f"[LISTING] ✓ Will use business policies")
            else:
                print(f"[LISTING] ⚠️ Business policies not available (common in sandbox)")
        except Exception as e:
            print(f"[LISTING] ⚠️ Could not get policies: {str(e)}")
            policies = {}
            use_policies = False

        # Step 2: Create Offer
        print(f"[LISTING] Step 2: Creating offer")
        offer_payload = {
            "sku": request.sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingDescription": request.description,
            "categoryId": request.categoryId,
            "merchantLocationKey": "default_location",
            "listingDuration": "GTC",
            "pricingSummary": {
                "price": {
                    "value": str(request.price),
                    "currency": request.currency
                }
            }
        }

        # Add policies if available
        if use_policies:
            offer_payload["listingPolicies"] = {
                "fulfillmentPolicyId": policies["fulfillmentPolicyId"],
                "paymentPolicyId": policies["paymentPolicyId"],
                "returnPolicyId": policies["returnPolicyId"]
            }

        offer_url = f"{SANDBOX_INVENTORY_BASE}/offer"
        offer_response = requests.post(offer_url, headers=headers, json=offer_payload)

        if offer_response.status_code not in [200, 201]:
            raise HTTPException(
                status_code=offer_response.status_code,
                detail=f"Step 2 failed - Create offer: {offer_response.text}"
            )

        offer_data = offer_response.json()
        offer_id = offer_data.get("offerId")
        print(f"[LISTING] ✓ Offer created: {offer_id}")

        # Step 3: Publish Offer
        print(f"[LISTING] Step 3: Publishing offer")
        publish_url = f"{SANDBOX_INVENTORY_BASE}/offer/{offer_id}/publish"
        publish_response = requests.post(publish_url, headers=headers)

        if publish_response.status_code == 200:
            listing_data = publish_response.json()
            listing_id = listing_data.get("listingId")
            print(f"[LISTING] ✓ Listing published: {listing_id}")

            return {
                "success": True,
                "message": "Listing created and published successfully!",
                "sku": request.sku,
                "offerId": offer_id,
                "listingId": listing_id,
                "sandbox_url": f"https://www.sandbox.ebay.com/itm/{listing_id}",
                "warnings": listing_data.get("warnings", [])
            }
        else:
            raise HTTPException(
                status_code=publish_response.status_code,
                detail=f"Step 3 failed - Publish offer: {publish_response.text}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
