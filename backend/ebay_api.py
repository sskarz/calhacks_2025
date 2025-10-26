"""
eBay API Comprehensive Test Suite

This application tests all major eBay Inventory API endpoints including OAuth,
inventory management, offers, and listing publication.

IMPORTANT eBay API Requirements (learned from testing):

1. Business Policies Opt-in - REQUIRED FIRST STEP:
   - MUST opt-in to SELLING_POLICY_MANAGEMENT program via Account API
   - Without opt-in: Error 20403 "Seller is not opted in to business policies"
   - Use /check-optin-status to check if already opted in
   - Use /optin-to-business-policies to opt-in programmatically
   - Manual opt-in URL: http://www.bizpolicy.sandbox.ebay.com/businesspolicy/policyoptin
   - Processing can take a few minutes in sandbox (up to 24 hours in production)

2. Business Policies Required for Publishing:
   - Fulfillment Policy (with shipping services) - Error 25007 if missing/invalid
   - Payment Policy - Error 20403 if not opted in
   - Return Policy - Error 20403 if not opted in
   - ALL THREE policies must be created BEFORE publishing an offer
   - Inline shipping options are NOT sufficient - business policies are mandatory
   - Policies are reusable across multiple offers

3. SKU Format: ONLY alphanumeric characters allowed (A-Z, a-z, 0-9)
   - NO hyphens, underscores, or special characters
   - Max length: 50 characters
   - Error 25707 occurs if SKU contains invalid characters

4. Product Specifics: Many categories require specific item attributes
   - Category 31388 (Cameras & Photo) requires: Brand, Model, AND Type (via aspects)
   - Note: Brand must be in BOTH the product.brand field AND aspects.Brand array
   - Error 25002 occurs if required product specifics are missing
   - Use the "aspects" field to provide category-specific attributes
   - Example Type values for cameras: "Digital Camera", "Action Camera", "DSLR", "Mirrorless Camera"

5. Getting Offers: Query by SKU to avoid errors from old invalid SKUs
   - Use GET /offer?sku={sku} instead of GET /offer
   - Prevents error 25707 from old inventory items with invalid SKU formats
"""

import base64
from dotenv import load_dotenv
import os
import requests
import secrets
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

# Initialize FastAPI app
app = FastAPI(title="eBay OAuth API - Comprehensive Test Suite")

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
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000")
SANDBOX_TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
SANDBOX_AUTH_URL = "https://auth.sandbox.ebay.com/oauth2/authorize"

# Scopes needed for comprehensive testing
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

# In-memory storage
oauth_sessions = {}
token_storage = {"current_token": None}

# eBay Sandbox API URLs
SANDBOX_INVENTORY_BASE = "https://api.sandbox.ebay.com/sell/inventory/v1"
SANDBOX_ACCOUNT_BASE = "https://api.sandbox.ebay.com/sell/account/v1"
SANDBOX_FULFILLMENT_BASE = "https://api.sandbox.ebay.com/sell/fulfillment/v1"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_access_token():
    """Get the current access token from storage"""
    if not token_storage["current_token"]:
        raise HTTPException(
            status_code=401,
            detail="No access token available. Please authorize first via /start-auth"
        )
    return token_storage["current_token"]["access_token"]


def get_headers():
    """Get standard headers with authorization"""
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
        "Content-Language": "en-US"
    }


def log_test(step: str, message: str, success: bool = True):
    """Log test progress"""
    symbol = "✓" if success else "✗"
    print(f"[TEST {step}] {symbol} {message}")


def check_opted_in_programs():
    """
    Check which seller programs the account is opted into.
    Returns the list of opted-in programs or None if the call fails.
    """
    try:
        headers = get_headers()
        url = f"{SANDBOX_ACCOUNT_BASE}/program/get_opted_in_programs"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            programs = data.get("programs", [])
            return [p.get("programType") for p in programs]
        else:
            log_test("OPT-IN CHECK", f"Failed to check opt-in status: {response.text}", False)
            return None
    except Exception as e:
        log_test("OPT-IN CHECK", f"Error checking opt-in status: {str(e)}", False)
        return None


def opt_in_to_selling_policies():
    """
    Opt-in to SELLING_POLICY_MANAGEMENT program.
    This is required to create and use business policies (fulfillment, payment, return).

    Returns:
        dict: Status of the opt-in attempt
    """
    try:
        headers = get_headers()
        url = f"{SANDBOX_ACCOUNT_BASE}/program/opt_in"
        payload = {"programType": "SELLING_POLICY_MANAGEMENT"}

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            log_test("OPT-IN", "Successfully opted in to SELLING_POLICY_MANAGEMENT", True)
            return {
                "success": True,
                "message": "Successfully opted in to SELLING_POLICY_MANAGEMENT",
                "note": "It may take a few minutes for the opt-in to take effect in sandbox"
            }
        else:
            log_test("OPT-IN", f"Failed to opt-in: {response.text}", False)
            return {
                "success": False,
                "message": "Failed to opt-in",
                "error": response.text,
                "manual_optin_url": "http://www.bizpolicy.sandbox.ebay.com/businesspolicy/policyoptin"
            }
    except Exception as e:
        log_test("OPT-IN", f"Error during opt-in: {str(e)}", False)
        return {
            "success": False,
            "message": "Error during opt-in",
            "error": str(e),
            "manual_optin_url": "http://www.bizpolicy.sandbox.ebay.com/businesspolicy/policyoptin"
        }


# ============================================================================
# OAUTH ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
):
    """Root endpoint with OAuth callback handling"""
    if code and state:
        return await oauth_callback(code=code, state=state)

    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>eBay API Comprehensive Test Suite</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; background-color: #f5f5f5; }
            .container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #0064d2; }
            button { background-color: #0064d2; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin: 5px; }
            button:hover { background-color: #0053b8; }
            .test-btn { background-color: #28a745; }
            .test-btn:hover { background-color: #218838; }
            .section { margin: 20px 0; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #0064d2; }
            .result { margin-top: 20px; padding: 15px; background-color: #f0f0f0; border-radius: 4px; max-height: 400px; overflow-y: auto; }
            pre { white-space: pre-wrap; word-wrap: break-word; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 eBay API Comprehensive Test Suite</h1>

            <div class="section">
                <h2>Step 1: Authorize</h2>
                <button onclick="window.location.href='/start-auth'">Start OAuth Authorization</button>
                <button onclick="checkToken()">Check Token Status</button>
            </div>

            <div class="section">
                <h2>Step 2: Run Comprehensive Tests</h2>
                <button class="test-btn" onclick="runTest('/test-all')">🚀 Run All Tests</button>
                <button class="test-btn" onclick="runTest('/test-inventory-location')">Test Inventory Location</button>
                <button class="test-btn" onclick="runTest('/test-create-listing')">Test Create Listing</button>
                <button class="test-btn" onclick="runTest('/test-get-listing')">Test Get Listing</button>
                <button class="test-btn" onclick="runTest('/test-publish-flow')">📤 Test Publish Endpoint Flow</button>
                <button class="test-btn" onclick="runTest('/test-policies')">Test Policies</button>
                <button class="test-btn" onclick="runTest('/test-inventory-operations')">Test Inventory Operations</button>
            </div>

            <div class="section">
                <h2>Business Policies Setup</h2>
                <button onclick="runTest('/check-optin-status')">Check Opt-in Status</button>
                <button onclick="runTestPost('/optin-to-business-policies')">Opt-in to Business Policies</button>
                <button class="test-btn" onclick="runTestPost('/create-all-policies')">Create All Required Policies</button>
                <p style="font-size: 12px; color: #666;">Business policies are required to publish offers. Check your opt-in status, then create all policies.</p>
            </div>

            <div class="section">
                <h2>Individual API Tests</h2>
                <button onclick="runTest('/test-fulfillment-policies')">Test Fulfillment Policies</button>
                <button onclick="runTest('/test-payment-policies')">Test Payment Policies</button>
                <button onclick="runTest('/test-return-policies')">Test Return Policies</button>
            </div>

            <div class="section">
                <h2>📦 View Published Listings</h2>
                <button class="test-btn" onclick="runTest('/get-all-published-listings')">Get All Published Listings</button>
                <button onclick="window.open('https://www.sandbox.ebay.com/sh/ovw', '_blank')">Open Seller Hub</button>
                <button onclick="window.open('https://www.sandbox.ebay.com/mye/myebay/selling', '_blank')">Open My eBay</button>
            </div>

            <div id="result" class="result" style="display:none;">
                <h3>Test Results:</h3>
                <pre id="result-content"></pre>
            </div>
        </div>

        <script>
            async function checkToken() {
                try {
                    const response = await fetch('/token/status');
                    const data = await response.json();
                    alert(data.has_token ? '✓ Token is active!' : '✗ No token. Please authorize first.');
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function runTest(endpoint) {
                const resultDiv = document.getElementById('result');
                const resultContent = document.getElementById('result-content');

                resultDiv.style.display = 'block';
                resultContent.textContent = 'Running test...';

                try {
                    const response = await fetch(endpoint);
                    const data = await response.json();
                    resultContent.textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    resultContent.textContent = 'Error: ' + error.message;
                }
            }

            async function runTestPost(endpoint) {
                const resultDiv = document.getElementById('result');
                const resultContent = document.getElementById('result-content');

                resultDiv.style.display = 'block';
                resultContent.textContent = 'Running test...';

                try {
                    const response = await fetch(endpoint, { method: 'POST' });
                    const data = await response.json();
                    resultContent.textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    resultContent.textContent = 'Error: ' + error.message;
                }
            }
        </script>
    </body>
    </html>
    """)


@app.get("/start-auth")
async def start_auth():
    """Start OAuth authorization flow"""
    from fastapi.responses import RedirectResponse

    state = secrets.token_urlsafe(32)
    scope_string = " ".join(REQUIRED_SCOPES)

    oauth_sessions[state] = {"scopes": scope_string}

    auth_params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": scope_string,
        "state": state
    }

    from urllib.parse import urlencode
    query_string = urlencode(auth_params)
    full_auth_url = f"{SANDBOX_AUTH_URL}?{query_string}"

    return RedirectResponse(url=full_auth_url)


@app.get("/oauth/callback", response_class=HTMLResponse)
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...)
):
    """OAuth callback endpoint"""
    if state not in oauth_sessions:
        return HTMLResponse(content="<h1>❌ Invalid state parameter</h1>", status_code=400)

    try:
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }

        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }

        response = requests.post(SANDBOX_TOKEN_URL, headers=headers, data=body)

        if response.status_code != 200:
            return HTMLResponse(content=f"<h1>❌ Token exchange failed</h1><p>{response.text}</p>", status_code=500)

        token_data = response.json()
        print(f"[OAuth] Generated access token: {token_data.get('access_token')}")
        token_storage["current_token"] = token_data

        del oauth_sessions[state]

        return HTMLResponse(content=f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; text-align: center; }}
                    .success {{ background-color: #d4edda; padding: 30px; border-radius: 8px; }}
                    button {{ background-color: #0064d2; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; margin: 10px; }}
                </style>
            </head>
            <body>
                <div class="success">
                    <h1 style="color: #28a745;">✅ Authorization Successful!</h1>
                    <p>Your eBay OAuth token has been generated.</p>
                    <p><strong>Expires in:</strong> {token_data.get('expires_in')} seconds</p>
                    <button onclick="window.location.href='/'">Go to Test Suite</button>
                </div>
            </body>
        </html>
        """)

    except Exception as e:
        return HTMLResponse(content=f"<h1>❌ Error: {str(e)}</h1>", status_code=500)


@app.get("/token/status")
async def get_token_status():
    """Check current token status"""
    if token_storage["current_token"]:
        token_data = token_storage["current_token"]
        return {
            "has_token": True,
            "access_token": token_data.get("access_token")[:50] + "...",
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in"),
            "has_refresh_token": bool(token_data.get("refresh_token"))
        }
    return {"has_token": False, "message": "No token available"}


# ============================================================================
# TEST ENDPOINTS - COMPREHENSIVE API TESTING
# ============================================================================

@app.get("/test-all")
async def test_all_endpoints():
    """
    Master test endpoint - runs comprehensive tests of all eBay API endpoints
    This will test the complete flow: OAuth -> Location -> Item -> Offer -> Listing -> Get Details
    """
    results = {
        "test_name": "Comprehensive eBay API Test Suite",
        "timestamp": time.time(),
        "tests": []
    }

    # Use alphanumeric-only SKU (no hyphens allowed per eBay API requirements)
    test_sku = f"TESTSKU{int(time.time())}"

    try:
        # Test 1: Token verification
        log_test("1", "Verifying OAuth token")
        token = get_access_token()
        results["tests"].append({
            "name": "Token Verification",
            "status": "PASSED",
            "details": f"Token available (length: {len(token)})"
        })

        # Test 2: Check and enable Business Policies opt-in
        log_test("2", "Checking Business Policies opt-in status")
        opted_in_programs = check_opted_in_programs()
        is_opted_in = opted_in_programs and "SELLING_POLICY_MANAGEMENT" in opted_in_programs

        if not is_opted_in:
            log_test("2", "Not opted in to SELLING_POLICY_MANAGEMENT, attempting to opt-in", False)
            opt_in_result = opt_in_to_selling_policies()
            results["tests"].append({
                "name": "Opt-in to Business Policies",
                "status": "PASSED" if opt_in_result.get("success") else "WARNING",
                "details": opt_in_result
            })

            if not opt_in_result.get("success"):
                # Provide manual opt-in instructions
                results["tests"].append({
                    "name": "Manual Opt-in Required",
                    "status": "WARNING",
                    "details": {
                        "message": "Please manually opt-in to Business Policies via the sandbox web page",
                        "url": "http://www.bizpolicy.sandbox.ebay.com/businesspolicy/policyoptin",
                        "instructions": "Visit the URL above, sign in with your sandbox account, and enable Business Policies. Then re-run this test."
                    }
                })
        else:
            log_test("2", "Already opted in to SELLING_POLICY_MANAGEMENT", True)
            results["tests"].append({
                "name": "Business Policies Opt-in Status",
                "status": "PASSED",
                "details": {"opted_in": True, "programs": opted_in_programs}
            })

        # Test 3: Create inventory location
        log_test("3", "Creating inventory location")
        location_result = await test_inventory_location()
        results["tests"].append({
            "name": "Create Inventory Location",
            "status": "PASSED" if location_result.get("success") else "FAILED",
            "details": location_result
        })

        # Get headers for subsequent API calls
        headers = get_headers()

        # Test 4: Create fulfillment policy (required for publishing offers)
        log_test("4", "Creating fulfillment policy with shipping services")
        fulfillment_policy_id = None
        try:
            fulfillment_payload = {
                "name": "Test Shipping Policy",
                "description": "Standard domestic shipping for test listings",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "handlingTime": {
                    "unit": "DAY",
                    "value": 1
                },
                "localPickup": False,
                "freightShipping": False,
                "shippingOptions": [{
                    "optionType": "DOMESTIC",
                    "costType": "FLAT_RATE",
                    "shippingServices": [{
                        "shippingServiceCode": "USPSPriority",
                        "freeShipping": True,
                        "shippingCost": {
                            "currency": "USD",
                            "value": "0.00"
                        }
                    }]
                }]
            }

            fulfillment_url = f"{SANDBOX_ACCOUNT_BASE}/fulfillment_policy"
            fulfillment_response = requests.post(fulfillment_url, headers=headers, json=fulfillment_payload)

            if fulfillment_response.status_code in [200, 201]:
                fulfillment_data = fulfillment_response.json()
                fulfillment_policy_id = fulfillment_data.get("fulfillmentPolicyId")
                log_test("4", f"Fulfillment policy created: {fulfillment_policy_id}", True)
                results["tests"].append({
                    "name": "Create Fulfillment Policy",
                    "status": "PASSED",
                    "details": {"policyId": fulfillment_policy_id}
                })
            else:
                # Try to get existing policy (error 20400 means it already exists)
                get_policies_url = f"{SANDBOX_ACCOUNT_BASE}/fulfillment_policy?marketplace_id=EBAY_US"
                get_response = requests.get(get_policies_url, headers=headers)
                if get_response.status_code == 200:
                    policies_data = get_response.json()
                    if policies_data.get("total", 0) > 0:
                        # Use the first policy that has shipping services
                        for policy in policies_data.get("fulfillmentPolicies", []):
                            if policy.get("shippingOptions") and len(policy["shippingOptions"]) > 0:
                                fulfillment_policy_id = policy["fulfillmentPolicyId"]
                                log_test("4", f"Using existing fulfillment policy with shipping services: {fulfillment_policy_id}", True)
                                results["tests"].append({
                                    "name": "Create Fulfillment Policy",
                                    "status": "PASSED",
                                    "details": {
                                        "policyId": fulfillment_policy_id,
                                        "note": "Using existing policy",
                                        "policy_name": policy.get("name")
                                    }
                                })
                                break

                if not fulfillment_policy_id:
                    log_test("4", f"Failed to create/get fulfillment policy: {fulfillment_response.text}", False)
                    results["tests"].append({
                        "name": "Create Fulfillment Policy",
                        "status": "WARNING",
                        "details": {
                            "error": fulfillment_response.text,
                            "note": "Make sure you are opted in to Business Policies"
                        }
                    })
        except Exception as e:
            log_test("4", f"Fulfillment policy error: {str(e)}", False)
            results["tests"].append({
                "name": "Create Fulfillment Policy",
                "status": "WARNING",
                "details": {"error": str(e)}
            })

        # Test 5: Create payment policy (required for publishing offers)
        log_test("5", "Creating payment policy")
        payment_policy_id = None
        try:
            # For eBay Managed Payments, don't specify payment methods
            payment_payload = {
                "name": "Test Payment Policy",
                "description": "Standard payment policy for managed payments",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "immediatePay": False
            }

            payment_url = f"{SANDBOX_ACCOUNT_BASE}/payment_policy"
            payment_response = requests.post(payment_url, headers=headers, json=payment_payload)

            if payment_response.status_code in [200, 201]:
                payment_data = payment_response.json()
                payment_policy_id = payment_data.get("paymentPolicyId")
                log_test("5", f"Payment policy created: {payment_policy_id}", True)
                results["tests"].append({
                    "name": "Create Payment Policy",
                    "status": "PASSED",
                    "details": {"policyId": payment_policy_id}
                })
            else:
                # Try to get existing
                get_payment_url = f"{SANDBOX_ACCOUNT_BASE}/payment_policy?marketplace_id=EBAY_US"
                get_response = requests.get(get_payment_url, headers=headers)
                if get_response.status_code == 200:
                    payment_data = get_response.json()
                    if payment_data.get("total", 0) > 0:
                        payment_policy_id = payment_data["paymentPolicies"][0]["paymentPolicyId"]
                        log_test("5", f"Using existing payment policy: {payment_policy_id}", True)
                        results["tests"].append({
                            "name": "Create Payment Policy",
                            "status": "PASSED",
                            "details": {"policyId": payment_policy_id, "note": "Using existing"}
                        })
                if not payment_policy_id:
                    results["tests"].append({
                        "name": "Create Payment Policy",
                        "status": "WARNING",
                        "details": {
                            "error": payment_response.text,
                            "note": "Make sure you are opted in to Business Policies"
                        }
                    })
        except Exception as e:
            results["tests"].append({
                "name": "Create Payment Policy",
                "status": "WARNING",
                "details": {"error": str(e)}
            })

        # Test 6: Create return policy (required for publishing offers)
        log_test("6", "Creating return policy")
        return_policy_id = None
        try:
            return_payload = {
                "name": "Test Return Policy",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "returnsAccepted": True,
                "returnPeriod": {"unit": "DAY", "value": 30},
                "refundMethod": "MONEY_BACK",
                "returnShippingCostPayer": "BUYER"
            }

            return_url = f"{SANDBOX_ACCOUNT_BASE}/return_policy"
            return_response = requests.post(return_url, headers=headers, json=return_payload)

            if return_response.status_code in [200, 201]:
                return_data = return_response.json()
                return_policy_id = return_data.get("returnPolicyId")
                log_test("6", f"Return policy created: {return_policy_id}", True)
                results["tests"].append({
                    "name": "Create Return Policy",
                    "status": "PASSED",
                    "details": {"policyId": return_policy_id}
                })
            else:
                # Try to get existing
                get_return_url = f"{SANDBOX_ACCOUNT_BASE}/return_policy?marketplace_id=EBAY_US"
                get_response = requests.get(get_return_url, headers=headers)
                if get_response.status_code == 200:
                    return_data = get_response.json()
                    if return_data.get("total", 0) > 0:
                        return_policy_id = return_data["returnPolicies"][0]["returnPolicyId"]
                        log_test("6", f"Using existing return policy: {return_policy_id}", True)
                        results["tests"].append({
                            "name": "Create Return Policy",
                            "status": "PASSED",
                            "details": {"policyId": return_policy_id, "note": "Using existing"}
                        })
                if not return_policy_id:
                    results["tests"].append({
                        "name": "Create Return Policy",
                        "status": "WARNING",
                        "details": {
                            "error": return_response.text,
                            "note": "Make sure you are opted in to Business Policies"
                        }
                    })
        except Exception as e:
            results["tests"].append({
                "name": "Create Return Policy",
                "status": "WARNING",
                "details": {"error": str(e)}
            })

        # Test 7: Create inventory item
        log_test("7", f"Creating inventory item with SKU: {test_sku}")
        inventory_payload = {
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": 10
                }
            },
            "condition": "NEW",
            "product": {
                "title": "Test Product - GoPro Hero Camera",
                "description": "This is a test listing created via API for comprehensive testing purposes.",
                "imageUrls": [
                    "https://i.ebayimg.com/images/g/T~0AAOSwf6RkP3aI/s-l1600.jpg"
                ],
                "brand": "GoPro",
                "mpn": "HERO4BLACK",  # Required: Manufacturer Part Number paired with brand
                "aspects": {
                    "Brand": ["GoPro"],  # Required: Brand as item specific
                    "Model": ["Hero 4 Black"],  # Required for category 31388 (Cameras & Photo)
                    "Type": ["Digital Camera"]  # Required: Camera type
                }
            }
        }

        inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item/{test_sku}"
        inventory_response = requests.put(inventory_url, headers=headers, json=inventory_payload)

        if inventory_response.status_code in [200, 201, 204]:
            log_test("7", "Inventory item created successfully", True)
            results["tests"].append({
                "name": "Create Inventory Item",
                "status": "PASSED",
                "details": {"sku": test_sku, "status_code": inventory_response.status_code}
            })
        else:
            log_test("7", f"Failed to create inventory item: {inventory_response.text}", False)
            results["tests"].append({
                "name": "Create Inventory Item",
                "status": "FAILED",
                "details": {"error": inventory_response.text}
            })

        # Test 8: Get inventory item
        log_test("8", f"Getting inventory item details for SKU: {test_sku}")
        get_inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item/{test_sku}"
        get_inventory_response = requests.get(get_inventory_url, headers=headers)

        if get_inventory_response.status_code == 200:
            item_data = get_inventory_response.json()
            log_test("8", "Retrieved inventory item successfully", True)
            results["tests"].append({
                "name": "Get Inventory Item",
                "status": "PASSED",
                "details": item_data
            })
        else:
            log_test("8", f"Failed to get inventory item: {get_inventory_response.text}", False)
            results["tests"].append({
                "name": "Get Inventory Item",
                "status": "FAILED",
                "details": {"error": get_inventory_response.text}
            })

        # Test 9: Create offer
        log_test("9", "Creating offer for inventory item")
        offer_payload = {
            "sku": test_sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingDescription": "Test listing for API comprehensive testing",
            "categoryId": "31388",  # Cameras & Photo category
            "merchantLocationKey": "default_location",
            "listingDuration": "GTC",
            "pricingSummary": {
                "price": {
                    "value": "299.99",
                    "currency": "USD"
                }
            }
        }

        # Add policies - ALL THREE ARE REQUIRED to publish offers via Inventory API
        if fulfillment_policy_id and payment_policy_id and return_policy_id:
            offer_payload["listingPolicies"] = {
                "fulfillmentPolicyId": fulfillment_policy_id,
                "paymentPolicyId": payment_policy_id,
                "returnPolicyId": return_policy_id
            }
            log_test("9", "Adding business policies to offer", True)
        else:
            # Business policies are REQUIRED for publishing offers via Inventory API
            # Inline shipping options alone will NOT work for publishing
            missing_policies = []
            if not fulfillment_policy_id:
                missing_policies.append("fulfillment")
            if not payment_policy_id:
                missing_policies.append("payment")
            if not return_policy_id:
                missing_policies.append("return")

            log_test("9", f"WARNING: Missing required policies: {', '.join(missing_policies)}", False)
            results["tests"].append({
                "name": "Policy Validation",
                "status": "WARNING",
                "details": {
                    "missing_policies": missing_policies,
                    "message": "All three business policies (fulfillment, payment, return) are REQUIRED to publish offers",
                    "solution": "Ensure you are opted in to Business Policies and all three policies are created successfully"
                }
            })

        offer_url = f"{SANDBOX_INVENTORY_BASE}/offer"
        offer_response = requests.post(offer_url, headers=headers, json=offer_payload)

        offer_id = None
        if offer_response.status_code in [200, 201]:
            offer_data = offer_response.json()
            offer_id = offer_data.get("offerId")
            log_test("9", f"Offer created successfully: {offer_id}", True)
            results["tests"].append({
                "name": "Create Offer",
                "status": "PASSED",
                "details": offer_data
            })
        else:
            log_test("9", f"Failed to create offer: {offer_response.text}", False)
            results["tests"].append({
                "name": "Create Offer",
                "status": "FAILED",
                "details": {"error": offer_response.text}
            })

        # Test 10: Get offer details
        if offer_id:
            log_test("10", f"Getting offer details for offer ID: {offer_id}")
            get_offer_url = f"{SANDBOX_INVENTORY_BASE}/offer/{offer_id}"
            get_offer_response = requests.get(get_offer_url, headers=headers)

            if get_offer_response.status_code == 200:
                offer_details = get_offer_response.json()
                log_test("10", "Retrieved offer details successfully", True)
                results["tests"].append({
                    "name": "Get Offer Details",
                    "status": "PASSED",
                    "details": offer_details
                })
            else:
                log_test("10", f"Failed to get offer details: {get_offer_response.text}", False)
                results["tests"].append({
                    "name": "Get Offer Details",
                    "status": "FAILED",
                    "details": {"error": get_offer_response.text}
                })

        # Test 11: Publish offer
        if offer_id:
            log_test("11", f"Publishing offer: {offer_id}")
            publish_url = f"{SANDBOX_INVENTORY_BASE}/offer/{offer_id}/publish"
            publish_response = requests.post(publish_url, headers=headers)

            listing_id = None
            if publish_response.status_code == 200:
                listing_data = publish_response.json()
                listing_id = listing_data.get("listingId")
                log_test("11", f"Offer published successfully. Listing ID: {listing_id}", True)
                results["tests"].append({
                    "name": "Publish Offer",
                    "status": "PASSED",
                    "details": {
                        "listingId": listing_id,
                        "sandbox_url": f"https://www.sandbox.ebay.com/itm/{listing_id}",
                        "warnings": listing_data.get("warnings", [])
                    }
                })
            else:
                log_test("11", f"Failed to publish offer: {publish_response.text}", False)
                results["tests"].append({
                    "name": "Publish Offer",
                    "status": "FAILED",
                    "details": {
                        "error": publish_response.text,
                        "hint": "Ensure all three business policies are properly configured and the account is opted in to Business Policies"
                    }
                })

        # Test 12: Get all inventory items
        log_test("12", "Getting all inventory items")
        all_inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item"
        all_inventory_response = requests.get(all_inventory_url, headers=headers)

        if all_inventory_response.status_code == 200:
            all_items = all_inventory_response.json()
            log_test("12", f"Retrieved {all_items.get('total', 0)} inventory items", True)
            results["tests"].append({
                "name": "Get All Inventory Items",
                "status": "PASSED",
                "details": {"total": all_items.get("total", 0), "items": all_items.get("inventoryItems", [])}
            })
        else:
            log_test("12", f"Failed to get inventory items: {all_inventory_response.text}", False)
            results["tests"].append({
                "name": "Get All Inventory Items",
                "status": "FAILED",
                "details": {"error": all_inventory_response.text}
            })

        # Test 13: Get offers for specific SKU
        # Note: We query by SKU to avoid error 25707 from old inventory items with invalid SKU formats
        log_test("13", f"Getting offers for SKU: {test_sku}")
        sku_offers_url = f"{SANDBOX_INVENTORY_BASE}/offer?sku={test_sku}"
        sku_offers_response = requests.get(sku_offers_url, headers=headers)

        if sku_offers_response.status_code == 200:
            sku_offers = sku_offers_response.json()
            log_test("13", f"Retrieved {sku_offers.get('total', 0)} offers for SKU", True)
            results["tests"].append({
                "name": "Get Offers by SKU",
                "status": "PASSED",
                "details": {
                    "sku": test_sku,
                    "total": sku_offers.get("total", 0),
                    "offers": sku_offers.get("offers", []),
                    "note": "Querying by SKU to avoid old items with invalid SKU formats"
                }
            })
        else:
            log_test("13", f"Failed to get offers: {sku_offers_response.text}", False)
            results["tests"].append({
                "name": "Get Offers by SKU",
                "status": "FAILED",
                "details": {"error": sku_offers_response.text}
            })

        # Summary
        passed = sum(1 for t in results["tests"] if t["status"] == "PASSED")
        failed = sum(1 for t in results["tests"] if t["status"] == "FAILED")
        warning = sum(1 for t in results["tests"] if t["status"] == "WARNING")

        results["summary"] = {
            "total_tests": len(results["tests"]),
            "passed": passed,
            "failed": failed,
            "warnings": warning,
            "success_rate": f"{(passed / len(results['tests']) * 100):.1f}%"
        }

        log_test("COMPLETE", f"Test suite finished: {passed} passed, {failed} failed, {warning} warnings", True)

        return JSONResponse(content=results)

    except HTTPException as e:
        return JSONResponse(content={
            "error": "Authentication required",
            "message": str(e.detail),
            "hint": "Please visit /start-auth to authorize first"
        }, status_code=401)
    except Exception as e:
        log_test("ERROR", f"Test suite failed: {str(e)}", False)
        return JSONResponse(content={
            "error": "Test suite failed",
            "message": str(e),
            "partial_results": results
        }, status_code=500)


@app.get("/test-inventory-location")
async def test_inventory_location():
    """Test creating and getting inventory location"""
    try:
        headers = get_headers()

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
            "name": "Default Test Location",
            "merchantLocationStatus": "ENABLED",
            "locationTypes": ["WAREHOUSE"]
        }

        location_url = f"{SANDBOX_INVENTORY_BASE}/location/default_location"
        response = requests.post(location_url, headers=headers, json=location_payload)

        # Get location
        get_response = requests.get(location_url, headers=headers)

        return {
            "success": True,
            "create_status": response.status_code,
            "get_status": get_response.status_code,
            "location_data": get_response.json() if get_response.status_code == 200 else None,
            "message": "Location already exists" if response.status_code == 409 else "Location created"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/test-fulfillment-policies")
async def test_fulfillment_policies():
    """
    Test getting fulfillment policies.
    Note: 400 errors are common in sandbox environments if policies haven't been created yet.
    This is expected behavior and not necessarily an error.
    """
    try:
        headers = get_headers()

        # Get existing policies
        url = f"{SANDBOX_ACCOUNT_BASE}/fulfillment_policy?marketplace_id=EBAY_US"
        response = requests.get(url, headers=headers)

        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "total_policies": 0,
            "policies": [],
            "note": "400 errors are common in sandbox if no policies exist yet"
        }

        if response.status_code == 200:
            data = response.json()
            result["total_policies"] = data.get("total", 0)
            result["policies"] = data.get("fulfillmentPolicies", [])
        elif response.status_code == 400:
            result["message"] = "No policies found (common in sandbox)"

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/test-payment-policies")
async def test_payment_policies():
    """
    Test getting payment policies.
    Note: 400 errors are common in sandbox environments if policies haven't been created yet.
    """
    try:
        headers = get_headers()

        url = f"{SANDBOX_ACCOUNT_BASE}/payment_policy?marketplace_id=EBAY_US"
        response = requests.get(url, headers=headers)

        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "total_policies": 0,
            "policies": [],
            "note": "400 errors are common in sandbox if no policies exist yet"
        }

        if response.status_code == 200:
            data = response.json()
            result["total_policies"] = data.get("total", 0)
            result["policies"] = data.get("paymentPolicies", [])
        elif response.status_code == 400:
            result["message"] = "No policies found (common in sandbox)"

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/test-return-policies")
async def test_return_policies():
    """
    Test getting return policies.
    Note: 400 errors are common in sandbox environments if policies haven't been created yet.
    """
    try:
        headers = get_headers()

        url = f"{SANDBOX_ACCOUNT_BASE}/return_policy?marketplace_id=EBAY_US"
        response = requests.get(url, headers=headers)

        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "total_policies": 0,
            "policies": [],
            "note": "400 errors are common in sandbox if no policies exist yet"
        }

        if response.status_code == 200:
            data = response.json()
            result["total_policies"] = data.get("total", 0)
            result["policies"] = data.get("returnPolicies", [])
        elif response.status_code == 400:
            result["message"] = "No policies found (common in sandbox)"

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/check-optin-status")
async def check_optin_status_endpoint():
    """
    Check if the account is opted in to SELLING_POLICY_MANAGEMENT.
    This is required to create and use business policies.
    """
    try:
        programs = check_opted_in_programs()

        if programs is None:
            return {
                "success": False,
                "message": "Failed to check opt-in status",
                "error": "Unable to retrieve opted-in programs from eBay API"
            }

        is_opted_in = "SELLING_POLICY_MANAGEMENT" in programs

        return {
            "success": True,
            "opted_in_to_business_policies": is_opted_in,
            "all_programs": programs,
            "message": "Opted in to Business Policies" if is_opted_in else "NOT opted in to Business Policies",
            "manual_optin_url": "http://www.bizpolicy.sandbox.ebay.com/businesspolicy/policyoptin" if not is_opted_in else None
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/optin-to-business-policies")
async def optin_to_business_policies_endpoint():
    """
    Opt-in to SELLING_POLICY_MANAGEMENT program.
    This is required to create and use business policies (fulfillment, payment, return).
    """
    try:
        # First check if already opted in
        programs = check_opted_in_programs()
        if programs and "SELLING_POLICY_MANAGEMENT" in programs:
            return {
                "success": True,
                "already_opted_in": True,
                "message": "Already opted in to SELLING_POLICY_MANAGEMENT"
            }

        # Attempt to opt-in
        result = opt_in_to_selling_policies()
        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "manual_optin_url": "http://www.bizpolicy.sandbox.ebay.com/businesspolicy/policyoptin"
        }


@app.post("/create-all-policies")
async def create_all_policies_endpoint():
    """
    Create all three required business policies: Fulfillment, Payment, and Return.
    This will check existing policies and only create the ones that are missing.
    """
    try:
        headers = get_headers()
        results = {
            "fulfillment": {"exists": False, "policy_id": None},
            "payment": {"exists": False, "policy_id": None},
            "return": {"exists": False, "policy_id": None}
        }

        # Check and create Fulfillment Policy
        get_fulfillment_url = f"{SANDBOX_ACCOUNT_BASE}/fulfillment_policy?marketplace_id=EBAY_US"
        fulfillment_response = requests.get(get_fulfillment_url, headers=headers)

        if fulfillment_response.status_code == 200:
            fulfillment_data = fulfillment_response.json()
            if fulfillment_data.get("total", 0) > 0:
                # Use existing policy with shipping services
                for policy in fulfillment_data.get("fulfillmentPolicies", []):
                    if policy.get("shippingOptions") and len(policy["shippingOptions"]) > 0:
                        results["fulfillment"]["exists"] = True
                        results["fulfillment"]["policy_id"] = policy["fulfillmentPolicyId"]
                        results["fulfillment"]["name"] = policy.get("name")
                        break

        if not results["fulfillment"]["exists"]:
            # Create new fulfillment policy
            fulfillment_payload = {
                "name": "Standard Shipping Policy",
                "description": "Standard domestic shipping",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "handlingTime": {"unit": "DAY", "value": 1},
                "localPickup": False,
                "freightShipping": False,
                "shippingOptions": [{
                    "optionType": "DOMESTIC",
                    "costType": "FLAT_RATE",
                    "shippingServices": [{
                        "shippingServiceCode": "USPSPriority",
                        "freeShipping": True,
                        "shippingCost": {"currency": "USD", "value": "0.00"}
                    }]
                }]
            }
            create_response = requests.post(f"{SANDBOX_ACCOUNT_BASE}/fulfillment_policy", headers=headers, json=fulfillment_payload)
            if create_response.status_code in [200, 201]:
                data = create_response.json()
                results["fulfillment"]["created"] = True
                results["fulfillment"]["policy_id"] = data.get("fulfillmentPolicyId")

        # Check and create Payment Policy
        get_payment_url = f"{SANDBOX_ACCOUNT_BASE}/payment_policy?marketplace_id=EBAY_US"
        payment_response = requests.get(get_payment_url, headers=headers)

        if payment_response.status_code == 200:
            payment_data = payment_response.json()
            if payment_data.get("total", 0) > 0:
                results["payment"]["exists"] = True
                results["payment"]["policy_id"] = payment_data["paymentPolicies"][0]["paymentPolicyId"]
                results["payment"]["name"] = payment_data["paymentPolicies"][0].get("name")

        if not results["payment"]["exists"]:
            # Create new payment policy for Managed Payments
            # Note: eBay Managed Payments accounts don't require specifying payment methods
            payment_payload = {
                "name": "Standard Payment Policy",
                "description": "Standard payment policy for managed payments",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "immediatePay": False
            }
            create_response = requests.post(f"{SANDBOX_ACCOUNT_BASE}/payment_policy", headers=headers, json=payment_payload)
            if create_response.status_code in [200, 201]:
                data = create_response.json()
                results["payment"]["created"] = True
                results["payment"]["policy_id"] = data.get("paymentPolicyId")
            else:
                results["payment"]["error"] = create_response.text

        # Check and create Return Policy
        get_return_url = f"{SANDBOX_ACCOUNT_BASE}/return_policy?marketplace_id=EBAY_US"
        return_response = requests.get(get_return_url, headers=headers)

        if return_response.status_code == 200:
            return_data = return_response.json()
            if return_data.get("total", 0) > 0:
                results["return"]["exists"] = True
                results["return"]["policy_id"] = return_data["returnPolicies"][0]["returnPolicyId"]
                results["return"]["name"] = return_data["returnPolicies"][0].get("name")

        if not results["return"]["exists"]:
            # Create new return policy
            return_payload = {
                "name": "Standard Return Policy",
                "description": "Standard return policy",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "returnsAccepted": True,
                "returnPeriod": {"unit": "DAY", "value": 30},
                "refundMethod": "MONEY_BACK",
                "returnShippingCostPayer": "BUYER"
            }
            create_response = requests.post(f"{SANDBOX_ACCOUNT_BASE}/return_policy", headers=headers, json=return_payload)
            if create_response.status_code in [200, 201]:
                data = create_response.json()
                results["return"]["created"] = True
                results["return"]["policy_id"] = data.get("returnPolicyId")
            else:
                results["return"]["error"] = create_response.text

        # Check if all policies are available
        all_ready = (results["fulfillment"]["policy_id"] and
                     results["payment"]["policy_id"] and
                     results["return"]["policy_id"])

        return {
            "success": all_ready,
            "message": "All policies ready" if all_ready else "Some policies are missing",
            "policies": results,
            "ready_to_publish": all_ready
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/test-policies")
async def test_policies():
    """Test all policy endpoints together"""
    return {
        "fulfillment": await test_fulfillment_policies(),
        "payment": await test_payment_policies(),
        "return": await test_return_policies()
    }


@app.get("/test-inventory-operations")
async def test_inventory_operations():
    """Test various inventory operations"""
    try:
        headers = get_headers()
        # Use alphanumeric-only SKU (no hyphens)
        test_sku = f"INVTEST{int(time.time())}"

        results = {
            "test_sku": test_sku,
            "operations": []
        }

        # Create item
        create_payload = {
            "availability": {"shipToLocationAvailability": {"quantity": 5}},
            "condition": "NEW",
            "product": {
                "title": "Test Inventory Operations Item",
                "description": "Testing inventory operations",
                "imageUrls": ["https://i.ebayimg.com/images/g/T~0AAOSwf6RkP3aI/s-l1600.jpg"],
                "brand": "Generic",
                "mpn": "TESTMPN001",
                "aspects": {
                    "Brand": ["Generic"],
                    "Model": ["Test Model"],
                    "Type": ["Digital Camera"]
                }
            }
        }

        create_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item/{test_sku}"
        create_response = requests.put(create_url, headers=headers, json=create_payload)
        results["operations"].append({
            "operation": "create",
            "status": create_response.status_code,
            "success": create_response.status_code in [200, 201, 204]
        })

        # Get item
        get_response = requests.get(create_url, headers=headers)
        results["operations"].append({
            "operation": "get",
            "status": get_response.status_code,
            "success": get_response.status_code == 200,
            "data": get_response.json() if get_response.status_code == 200 else None
        })

        # Update quantity
        update_payload = create_payload.copy()
        update_payload["availability"]["shipToLocationAvailability"]["quantity"] = 15
        update_response = requests.put(create_url, headers=headers, json=update_payload)
        results["operations"].append({
            "operation": "update",
            "status": update_response.status_code,
            "success": update_response.status_code in [200, 201, 204]
        })

        # Get updated item
        get_updated_response = requests.get(create_url, headers=headers)
        results["operations"].append({
            "operation": "get_updated",
            "status": get_updated_response.status_code,
            "success": get_updated_response.status_code == 200,
            "data": get_updated_response.json() if get_updated_response.status_code == 200 else None
        })

        return {"success": True, "results": results}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/test-create-listing")
async def test_create_listing():
    """Quick test to create a complete listing"""
    # Use alphanumeric-only SKU (no hyphens)
    test_sku = f"QUICKTEST{int(time.time())}"

    try:
        headers = get_headers()

        # Ensure location
        await test_inventory_location()

        # Create item
        inventory_payload = {
            "availability": {"shipToLocationAvailability": {"quantity": 10}},
            "condition": "NEW",
            "product": {
                "title": "Quick Test Product",
                "description": "Quick test listing",
                "imageUrls": ["https://i.ebayimg.com/images/g/T~0AAOSwf6RkP3aI/s-l1600.jpg"],
                "brand": "TestBrand",
                "mpn": "QT12345",
                "aspects": {
                    "Brand": ["TestBrand"],
                    "Model": ["Quick Test Model"],
                    "Type": ["Digital Camera"]
                }
            }
        }

        inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item/{test_sku}"
        requests.put(inventory_url, headers=headers, json=inventory_payload)

        # Create offer
        offer_payload = {
            "sku": test_sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingDescription": "Quick test listing",
            "categoryId": "31388",
            "merchantLocationKey": "default_location",
            "listingDuration": "GTC",
            "pricingSummary": {"price": {"value": "99.99", "currency": "USD"}}
        }

        offer_url = f"{SANDBOX_INVENTORY_BASE}/offer"
        offer_response = requests.post(offer_url, headers=headers, json=offer_payload)

        if offer_response.status_code in [200, 201]:
            offer_data = offer_response.json()
            offer_id = offer_data.get("offerId")

            # Publish
            publish_url = f"{SANDBOX_INVENTORY_BASE}/offer/{offer_id}/publish"
            publish_response = requests.post(publish_url, headers=headers)

            if publish_response.status_code == 200:
                listing_data = publish_response.json()
                return {
                    "success": True,
                    "sku": test_sku,
                    "offer_id": offer_id,
                    "listing_id": listing_data.get("listingId"),
                    "sandbox_url": f"https://www.sandbox.ebay.com/itm/{listing_data.get('listingId')}"
                }

        return {"success": False, "error": "Failed to create listing"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/test-get-listing")
async def test_get_listing():
    """Test getting listing details"""
    try:
        headers = get_headers()

        # Get all inventory items first
        inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item"
        inventory_response = requests.get(inventory_url, headers=headers)

        if inventory_response.status_code == 200:
            inventory_data = inventory_response.json()
            items = inventory_data.get("inventoryItems", [])

            if items:
                # Get offers for the first valid SKU (alphanumeric only)
                valid_items = [item for item in items if item.get("sku", "").replace("_", "").replace("-", "").isalnum()]

                if valid_items:
                    first_item = valid_items[0]
                    sku = first_item.get("sku")

                    # Get offers for this SKU
                    offers_url = f"{SANDBOX_INVENTORY_BASE}/offer?sku={sku}"
                    offers_response = requests.get(offers_url, headers=headers)

                    if offers_response.status_code == 200:
                        offers_data = offers_response.json()
                        offers = offers_data.get("offers", [])

                        if offers:
                            first_offer = offers[0]
                            offer_id = first_offer.get("offerId")
                            listing_id = first_offer.get("listingId")

                            return {
                                "success": True,
                                "sku": sku,
                                "offer_id": offer_id,
                                "listing_id": listing_id,
                                "sandbox_url": f"https://www.sandbox.ebay.com/itm/{listing_id}" if listing_id else None,
                                "status": first_offer.get("status"),
                                "offer_details": first_offer
                            }

            return {"success": True, "message": "No valid items/offers found", "total_items": len(items)}

        return {"success": False, "error": "Failed to get inventory items"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/test-publish-flow")
async def test_publish_flow():
    """
    Test the complete publish endpoint flow:
    1. Create inventory item
    2. Create offer with business policies
    3. Publish offer
    4. Return listing details and sandbox URL
    """
    test_sku = f"PUBTEST{int(time.time())}"

    try:
        headers = get_headers()
        results = {
            "test_name": "Publish Endpoint Flow Test",
            "sku": test_sku,
            "steps": []
        }

        # Step 1: Ensure inventory location exists
        log_test("PUBLISH-1", "Ensuring inventory location exists")
        location_result = await test_inventory_location()
        results["steps"].append({
            "step": 1,
            "name": "Inventory Location",
            "success": location_result.get("success", False),
            "details": location_result
        })

        # Step 2: Get or create business policies
        log_test("PUBLISH-2", "Getting/creating business policies")
        fulfillment_policy_id = None
        payment_policy_id = None
        return_policy_id = None

        # Get fulfillment policy
        get_fulfillment_url = f"{SANDBOX_ACCOUNT_BASE}/fulfillment_policy?marketplace_id=EBAY_US"
        fulfillment_response = requests.get(get_fulfillment_url, headers=headers)
        if fulfillment_response.status_code == 200:
            fulfillment_data = fulfillment_response.json()
            if fulfillment_data.get("total", 0) > 0:
                for policy in fulfillment_data.get("fulfillmentPolicies", []):
                    if policy.get("shippingOptions") and len(policy["shippingOptions"]) > 0:
                        fulfillment_policy_id = policy["fulfillmentPolicyId"]
                        break

        # Get payment policy
        get_payment_url = f"{SANDBOX_ACCOUNT_BASE}/payment_policy?marketplace_id=EBAY_US"
        payment_response = requests.get(get_payment_url, headers=headers)
        if payment_response.status_code == 200:
            payment_data = payment_response.json()
            if payment_data.get("total", 0) > 0:
                payment_policy_id = payment_data["paymentPolicies"][0]["paymentPolicyId"]

        # Get return policy
        get_return_url = f"{SANDBOX_ACCOUNT_BASE}/return_policy?marketplace_id=EBAY_US"
        return_response = requests.get(get_return_url, headers=headers)
        if return_response.status_code == 200:
            return_data = return_response.json()
            if return_data.get("total", 0) > 0:
                return_policy_id = return_data["returnPolicies"][0]["returnPolicyId"]

        policies_ready = fulfillment_policy_id and payment_policy_id and return_policy_id
        results["steps"].append({
            "step": 2,
            "name": "Business Policies",
            "success": policies_ready,
            "details": {
                "fulfillment_policy_id": fulfillment_policy_id,
                "payment_policy_id": payment_policy_id,
                "return_policy_id": return_policy_id,
                "all_ready": policies_ready
            }
        })

        if not policies_ready:
            return {
                "success": False,
                "message": "Business policies are not ready. Please create them first.",
                "hint": "Use the 'Create All Required Policies' button to set up business policies",
                "results": results
            }

        # Step 3: Create inventory item
        log_test("PUBLISH-3", f"Creating inventory item with SKU: {test_sku}")
        inventory_payload = {
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": 10
                }
            },
            "condition": "NEW",
            "product": {
                "title": "Publish Flow Test - GoPro Hero Camera",
                "description": "Test listing for publish endpoint flow validation",
                "imageUrls": [
                    "https://i.ebayimg.com/images/g/T~0AAOSwf6RkP3aI/s-l1600.jpg"
                ],
                "brand": "GoPro",
                "mpn": "PUBTEST001",
                "aspects": {
                    "Brand": ["GoPro"],
                    "Model": ["Hero 4 Black"],
                    "Type": ["Digital Camera"]
                }
            }
        }

        inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item/{test_sku}"
        inventory_response = requests.put(inventory_url, headers=headers, json=inventory_payload)

        inventory_success = inventory_response.status_code in [200, 201, 204]
        results["steps"].append({
            "step": 3,
            "name": "Create Inventory Item",
            "success": inventory_success,
            "details": {
                "status_code": inventory_response.status_code,
                "error": inventory_response.text if not inventory_success else None
            }
        })

        if not inventory_success:
            return {
                "success": False,
                "message": "Failed to create inventory item",
                "results": results
            }

        # Step 4: Create offer with business policies
        log_test("PUBLISH-4", "Creating offer with business policies")
        offer_payload = {
            "sku": test_sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingDescription": "Test listing for publish endpoint flow",
            "categoryId": "31388",  # Cameras & Photo
            "merchantLocationKey": "default_location",
            "listingDuration": "GTC",
            "pricingSummary": {
                "price": {
                    "value": "349.99",
                    "currency": "USD"
                }
            },
            "listingPolicies": {
                "fulfillmentPolicyId": fulfillment_policy_id,
                "paymentPolicyId": payment_policy_id,
                "returnPolicyId": return_policy_id
            }
        }

        offer_url = f"{SANDBOX_INVENTORY_BASE}/offer"
        offer_response = requests.post(offer_url, headers=headers, json=offer_payload)

        offer_id = None
        offer_success = offer_response.status_code in [200, 201]
        if offer_success:
            offer_data = offer_response.json()
            offer_id = offer_data.get("offerId")

        results["steps"].append({
            "step": 4,
            "name": "Create Offer",
            "success": offer_success,
            "details": {
                "status_code": offer_response.status_code,
                "offer_id": offer_id,
                "error": offer_response.text if not offer_success else None
            }
        })

        if not offer_success:
            return {
                "success": False,
                "message": "Failed to create offer",
                "results": results
            }

        # Step 5: Publish the offer
        log_test("PUBLISH-5", f"Publishing offer: {offer_id}")
        publish_url = f"{SANDBOX_INVENTORY_BASE}/offer/{offer_id}/publish"
        publish_response = requests.post(publish_url, headers=headers)

        listing_id = None
        publish_success = publish_response.status_code == 200
        if publish_success:
            listing_data = publish_response.json()
            listing_id = listing_data.get("listingId")

            log_test("PUBLISH-5", f"Successfully published! Listing ID: {listing_id}", True)

            results["steps"].append({
                "step": 5,
                "name": "Publish Offer",
                "success": True,
                "details": {
                    "listing_id": listing_id,
                    "sandbox_url": f"https://www.sandbox.ebay.com/itm/{listing_id}",
                    "warnings": listing_data.get("warnings", [])
                }
            })
        else:
            log_test("PUBLISH-5", f"Failed to publish: {publish_response.text}", False)
            results["steps"].append({
                "step": 5,
                "name": "Publish Offer",
                "success": False,
                "details": {
                    "status_code": publish_response.status_code,
                    "error": publish_response.text
                }
            })

        # Final summary
        all_success = all(step["success"] for step in results["steps"])
        results["summary"] = {
            "overall_success": all_success,
            "total_steps": len(results["steps"]),
            "successful_steps": sum(1 for step in results["steps"] if step["success"]),
            "listing_id": listing_id,
            "sandbox_url": f"https://www.sandbox.ebay.com/itm/{listing_id}" if listing_id else None,
            "message": "Successfully published listing!" if all_success else "Publish flow failed"
        }

        return {
            "success": all_success,
            "results": results
        }

    except HTTPException as e:
        return {
            "success": False,
            "error": "Authentication required",
            "message": str(e.detail),
            "hint": "Please visit /start-auth to authorize first"
        }
    except Exception as e:
        log_test("PUBLISH-ERROR", f"Publish flow test failed: {str(e)}", False)
        return {
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred during the publish flow test"
        }


@app.get("/get-all-published-listings")
async def get_all_published_listings():
    """
    Get all published listings with their sandbox URLs.
    This endpoint returns all items that have been successfully published to eBay sandbox.
    """
    try:
        headers = get_headers()
        published_listings = []

        # Get all inventory items
        inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item"
        inventory_response = requests.get(inventory_url, headers=headers)

        if inventory_response.status_code != 200:
            return {"success": False, "error": "Failed to get inventory items"}

        inventory_data = inventory_response.json()
        items = inventory_data.get("inventoryItems", [])

        # For each item, try to get its offers
        for item in items:
            sku = item.get("sku", "")

            # Skip items with invalid SKU formats
            if not sku or not sku.replace("_", "").replace("-", "").isalnum():
                continue

            try:
                # Get offers for this SKU
                offers_url = f"{SANDBOX_INVENTORY_BASE}/offer?sku={sku}"
                offers_response = requests.get(offers_url, headers=headers)

                if offers_response.status_code == 200:
                    offers_data = offers_response.json()
                    offers = offers_data.get("offers", [])

                    for offer in offers:
                        listing_id = offer.get("listingId")
                        status = offer.get("status")

                        # Only include published listings
                        if listing_id and status == "PUBLISHED":
                            published_listings.append({
                                "sku": sku,
                                "title": item.get("product", {}).get("title", "N/A"),
                                "offer_id": offer.get("offerId"),
                                "listing_id": listing_id,
                                "sandbox_url": f"https://www.sandbox.ebay.com/itm/{listing_id}",
                                "price": offer.get("pricingSummary", {}).get("price", {}).get("value"),
                                "currency": offer.get("pricingSummary", {}).get("price", {}).get("currency"),
                                "quantity": item.get("availability", {}).get("shipToLocationAvailability", {}).get("quantity"),
                                "status": status
                            })
            except Exception as e:
                # Skip items that cause errors
                continue

        return {
            "success": True,
            "total_published": len(published_listings),
            "listings": published_listings,
            "seller_hub_url": "https://www.sandbox.ebay.com/sh/ovw",
            "my_ebay_url": "https://www.sandbox.ebay.com/mye/myebay/selling"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/publish")
async def publish_listing(
    name: str = Query(..., description="Product name/title"),
    description: str = Query(..., description="Product description"),
    price: float = Query(..., description="Price in USD"),
    quantity: int = Query(default=1, description="Available quantity"),
    brand: str = Query(default="Generic", description="Product brand"),
    category_id: str = Query(default="31388", description="eBay category ID (default: Cameras & Photo)"),
    image_url: str = Query(default="https://i.ytimg.com/vi/Y13DcudSY8c/hq720.jpg?sqp=-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD&rs=AOn4CLCciXbZTi3Nr0oHVpz7sq7fVdFHxQ", description="Product image URL (must use HTTPS)")
):
    """
    Simplified endpoint to publish a listing to eBay.
    This endpoint handles the complete flow: create inventory item, create offer, and publish.
    """
    test_sku = f"AGENT{int(time.time())}"

    try:
        headers = get_headers()

        # Step 1: Ensure inventory location exists
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
        requests.post(location_url, headers=headers, json=location_payload)

        # Step 2: Get business policies (required for publishing)
        fulfillment_policy_id = None
        payment_policy_id = None
        return_policy_id = None

        # Get fulfillment policy
        get_fulfillment_url = f"{SANDBOX_ACCOUNT_BASE}/fulfillment_policy?marketplace_id=EBAY_US"
        fulfillment_response = requests.get(get_fulfillment_url, headers=headers)
        if fulfillment_response.status_code == 200:
            fulfillment_data = fulfillment_response.json()
            if fulfillment_data.get("total", 0) > 0:
                for policy in fulfillment_data.get("fulfillmentPolicies", []):
                    if policy.get("shippingOptions") and len(policy["shippingOptions"]) > 0:
                        fulfillment_policy_id = policy["fulfillmentPolicyId"]
                        break

        # Get payment policy
        get_payment_url = f"{SANDBOX_ACCOUNT_BASE}/payment_policy?marketplace_id=EBAY_US"
        payment_response = requests.get(get_payment_url, headers=headers)
        if payment_response.status_code == 200:
            payment_data = payment_response.json()
            if payment_data.get("total", 0) > 0:
                payment_policy_id = payment_data["paymentPolicies"][0]["paymentPolicyId"]

        # Get return policy
        get_return_url = f"{SANDBOX_ACCOUNT_BASE}/return_policy?marketplace_id=EBAY_US"
        return_response = requests.get(get_return_url, headers=headers)
        if return_response.status_code == 200:
            return_data = return_response.json()
            if return_data.get("total", 0) > 0:
                return_policy_id = return_data["returnPolicies"][0]["returnPolicyId"]

        if not (fulfillment_policy_id and payment_policy_id and return_policy_id):
            return {
                "success": False,
                "error": "Business policies not configured",
                "message": "Please run /create-all-policies endpoint first to set up required business policies"
            }

        # Step 3: Create inventory item
        # Validate image URL uses HTTPS
        if not image_url.startswith("https://"):
            return {
                "success": False,
                "error": "Invalid image URL",
                "message": "Image URL must use HTTPS protocol. Self-hosted images must be served over HTTPS."
            }

        inventory_payload = {
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": quantity
                }
            },
            "condition": "NEW",
            "product": {
                "title": name,
                "description": description,
                "imageUrls": [
                    image_url
                ],
                "brand": brand,
                "mpn": test_sku,
                "aspects": {
                    "Brand": [brand],
                    "Model": [name],
                    "Type": ["Product"]
                }
            }
        }

        inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item/{test_sku}"
        inventory_response = requests.put(inventory_url, headers=headers, json=inventory_payload)

        if inventory_response.status_code not in [200, 201, 204]:
            return {
                "success": False,
                "error": "Failed to create inventory item",
                "details": inventory_response.text
            }

        # Step 4: Create offer with business policies
        offer_payload = {
            "sku": test_sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingDescription": description,
            "categoryId": category_id,
            "merchantLocationKey": "default_location",
            "listingDuration": "GTC",
            "pricingSummary": {
                "price": {
                    "value": str(price),
                    "currency": "USD"
                }
            },
            "listingPolicies": {
                "fulfillmentPolicyId": fulfillment_policy_id,
                "paymentPolicyId": payment_policy_id,
                "returnPolicyId": return_policy_id
            }
        }

        offer_url = f"{SANDBOX_INVENTORY_BASE}/offer"
        offer_response = requests.post(offer_url, headers=headers, json=offer_payload)

        if offer_response.status_code not in [200, 201]:
            return {
                "success": False,
                "error": "Failed to create offer",
                "details": offer_response.text
            }

        offer_data = offer_response.json()
        offer_id = offer_data.get("offerId")

        # Step 5: Publish the offer
        publish_url = f"{SANDBOX_INVENTORY_BASE}/offer/{offer_id}/publish"
        publish_response = requests.post(publish_url, headers=headers)

        if publish_response.status_code != 200:
            return {
                "success": False,
                "error": "Failed to publish offer",
                "details": publish_response.text
            }

        listing_data = publish_response.json()
        listing_id = listing_data.get("listingId")
        sandbox_url = f"https://www.sandbox.ebay.com/itm/{listing_id}"

        # Log the successful publish with clickable URL
        log_test("PUBLISH", f"✅ Successfully published: {name}", True)
        log_test("PUBLISH", f"📦 Listing ID: {listing_id}", True)
        log_test("PUBLISH", f"🔗 Sandbox URL: {sandbox_url}", True)
        print(f"\n{'='*70}")
        print(f"✅ LISTING PUBLISHED SUCCESSFULLY!")
        print(f"{'='*70}")
        print(f"Title:       {name}")
        print(f"Price:       ${price}")
        print(f"Quantity:    {quantity}")
        print(f"Brand:       {brand}")
        print(f"SKU:         {test_sku}")
        print(f"Listing ID:  {listing_id}")
        print(f"Image:       {image_url}")
        print(f"Sandbox URL: {sandbox_url}")
        print(f"{'='*70}\n")

        return {
            "success": True,
            "message": f"Successfully published listing: {name}",
            "sku": test_sku,
            "offer_id": offer_id,
            "listing_id": listing_id,
            "sandbox_url": sandbox_url,
            "price": price,
            "quantity": quantity
        }

    except HTTPException as e:
        return {
            "success": False,
            "error": "Authentication required",
            "message": str(e.detail),
            "hint": "Please visit /start-auth to authorize first"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred while publishing the listing"
        }


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🚀 eBay Comprehensive API Test Suite")
    print("="*70)
    print("\n📋 Quick Start:")
    print(f"   1. Open browser: {PUBLIC_URL}")
    print("   2. Click 'Start OAuth Authorization'")
    print("   3. Sign in with eBay Sandbox account")
    print("   4. Check Business Policies opt-in status")
    print("   5. Opt-in to Business Policies if needed")
    print("   6. Run comprehensive tests!")
    print("\n🧪 Test Endpoints:")
    print("   POST /publish                     - Publish a listing (for agents)")
    print("   GET  /test-all                    - Run all tests")
    print("   GET  /check-optin-status          - Check Business Policies opt-in")
    print("   POST /optin-to-business-policies  - Opt-in to Business Policies")
    print("   POST /create-all-policies         - Create all required policies")
    print("   GET  /test-inventory-location     - Test location APIs")
    print("   GET  /test-create-listing         - Test listing creation")
    print("   GET  /test-publish-flow           - Test publish endpoint flow")
    print("   GET  /test-get-listing            - Test listing retrieval")
    print("   GET  /test-policies               - Test policy APIs")
    print("   GET  /test-inventory-operations   - Test inventory CRUD")
    print("\n⚠️  IMPORTANT:")
    print("   Business Policies opt-in is REQUIRED to publish offers!")
    print("   Use /create-all-policies to create missing Payment Policy")
    print("\n" + "="*70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)
