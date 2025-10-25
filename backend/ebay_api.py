import base64
from dotenv import load_dotenv
import os
import requests
import secrets
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
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
                <button class="test-btn" onclick="runTest('/test-policies')">Test Policies</button>
                <button class="test-btn" onclick="runTest('/test-inventory-operations')">Test Inventory Operations</button>
            </div>

            <div class="section">
                <h2>Individual API Tests</h2>
                <button onclick="runTest('/test-fulfillment-policies')">Test Fulfillment Policies</button>
                <button onclick="runTest('/test-payment-policies')">Test Payment Policies</button>
                <button onclick="runTest('/test-return-policies')">Test Return Policies</button>
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

    test_sku = f"TEST-SKU-{int(time.time())}"

    try:
        # Test 1: Token verification
        log_test("1", "Verifying OAuth token")
        token = get_access_token()
        results["tests"].append({
            "name": "Token Verification",
            "status": "PASSED",
            "details": f"Token available (length: {len(token)})"
        })

        # Test 2: Create inventory location
        log_test("2", "Creating inventory location")
        location_result = await test_inventory_location()
        results["tests"].append({
            "name": "Create Inventory Location",
            "status": "PASSED" if location_result.get("success") else "FAILED",
            "details": location_result
        })

        # Test 3: Get fulfillment policies
        log_test("3", "Testing fulfillment policies")
        fulfillment_result = await test_fulfillment_policies()
        results["tests"].append({
            "name": "Fulfillment Policies",
            "status": "PASSED" if fulfillment_result.get("success") else "WARNING",
            "details": fulfillment_result
        })

        # Test 4: Get payment policies
        log_test("4", "Testing payment policies")
        payment_result = await test_payment_policies()
        results["tests"].append({
            "name": "Payment Policies",
            "status": "PASSED" if payment_result.get("success") else "WARNING",
            "details": payment_result
        })

        # Test 5: Get return policies
        log_test("5", "Testing return policies")
        return_result = await test_return_policies()
        results["tests"].append({
            "name": "Return Policies",
            "status": "PASSED" if return_result.get("success") else "WARNING",
            "details": return_result
        })

        # Test 6: Create inventory item
        log_test("6", f"Creating inventory item with SKU: {test_sku}")
        headers = get_headers()
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
                "brand": "GoPro"
            }
        }

        inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item/{test_sku}"
        inventory_response = requests.put(inventory_url, headers=headers, json=inventory_payload)

        if inventory_response.status_code in [200, 201, 204]:
            log_test("6", "Inventory item created successfully", True)
            results["tests"].append({
                "name": "Create Inventory Item",
                "status": "PASSED",
                "details": {"sku": test_sku, "status_code": inventory_response.status_code}
            })
        else:
            log_test("6", f"Failed to create inventory item: {inventory_response.text}", False)
            results["tests"].append({
                "name": "Create Inventory Item",
                "status": "FAILED",
                "details": {"error": inventory_response.text}
            })

        # Test 7: Get inventory item
        log_test("7", f"Getting inventory item details for SKU: {test_sku}")
        get_inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item/{test_sku}"
        get_inventory_response = requests.get(get_inventory_url, headers=headers)

        if get_inventory_response.status_code == 200:
            item_data = get_inventory_response.json()
            log_test("7", "Retrieved inventory item successfully", True)
            results["tests"].append({
                "name": "Get Inventory Item",
                "status": "PASSED",
                "details": item_data
            })
        else:
            log_test("7", f"Failed to get inventory item: {get_inventory_response.text}", False)
            results["tests"].append({
                "name": "Get Inventory Item",
                "status": "FAILED",
                "details": {"error": get_inventory_response.text}
            })

        # Test 8: Create offer
        log_test("8", "Creating offer for inventory item")
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

        offer_url = f"{SANDBOX_INVENTORY_BASE}/offer"
        offer_response = requests.post(offer_url, headers=headers, json=offer_payload)

        offer_id = None
        if offer_response.status_code in [200, 201]:
            offer_data = offer_response.json()
            offer_id = offer_data.get("offerId")
            log_test("8", f"Offer created successfully: {offer_id}", True)
            results["tests"].append({
                "name": "Create Offer",
                "status": "PASSED",
                "details": offer_data
            })
        else:
            log_test("8", f"Failed to create offer: {offer_response.text}", False)
            results["tests"].append({
                "name": "Create Offer",
                "status": "FAILED",
                "details": {"error": offer_response.text}
            })

        # Test 9: Get offer details
        if offer_id:
            log_test("9", f"Getting offer details for offer ID: {offer_id}")
            get_offer_url = f"{SANDBOX_INVENTORY_BASE}/offer/{offer_id}"
            get_offer_response = requests.get(get_offer_url, headers=headers)

            if get_offer_response.status_code == 200:
                offer_details = get_offer_response.json()
                log_test("9", "Retrieved offer details successfully", True)
                results["tests"].append({
                    "name": "Get Offer Details",
                    "status": "PASSED",
                    "details": offer_details
                })
            else:
                log_test("9", f"Failed to get offer details: {get_offer_response.text}", False)
                results["tests"].append({
                    "name": "Get Offer Details",
                    "status": "FAILED",
                    "details": {"error": get_offer_response.text}
                })

        # Test 10: Publish offer
        if offer_id:
            log_test("10", f"Publishing offer: {offer_id}")
            publish_url = f"{SANDBOX_INVENTORY_BASE}/offer/{offer_id}/publish"
            publish_response = requests.post(publish_url, headers=headers)

            listing_id = None
            if publish_response.status_code == 200:
                listing_data = publish_response.json()
                listing_id = listing_data.get("listingId")
                log_test("10", f"Offer published successfully. Listing ID: {listing_id}", True)
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
                log_test("10", f"Failed to publish offer: {publish_response.text}", False)
                results["tests"].append({
                    "name": "Publish Offer",
                    "status": "FAILED",
                    "details": {"error": publish_response.text}
                })

        # Test 11: Get all inventory items
        log_test("11", "Getting all inventory items")
        all_inventory_url = f"{SANDBOX_INVENTORY_BASE}/inventory_item"
        all_inventory_response = requests.get(all_inventory_url, headers=headers)

        if all_inventory_response.status_code == 200:
            all_items = all_inventory_response.json()
            log_test("11", f"Retrieved {all_items.get('total', 0)} inventory items", True)
            results["tests"].append({
                "name": "Get All Inventory Items",
                "status": "PASSED",
                "details": {"total": all_items.get("total", 0), "items": all_items.get("inventoryItems", [])}
            })
        else:
            log_test("11", f"Failed to get inventory items: {all_inventory_response.text}", False)
            results["tests"].append({
                "name": "Get All Inventory Items",
                "status": "FAILED",
                "details": {"error": all_inventory_response.text}
            })

        # Test 12: Get all offers
        log_test("12", "Getting all offers")
        all_offers_url = f"{SANDBOX_INVENTORY_BASE}/offer"
        all_offers_response = requests.get(all_offers_url, headers=headers)

        if all_offers_response.status_code == 200:
            all_offers = all_offers_response.json()
            log_test("12", f"Retrieved {all_offers.get('total', 0)} offers", True)
            results["tests"].append({
                "name": "Get All Offers",
                "status": "PASSED",
                "details": {"total": all_offers.get("total", 0), "offers": all_offers.get("offers", [])}
            })
        else:
            log_test("12", f"Failed to get offers: {all_offers_response.text}", False)
            results["tests"].append({
                "name": "Get All Offers",
                "status": "FAILED",
                "details": {"error": all_offers_response.text}
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
    """Test getting and creating fulfillment policies"""
    try:
        headers = get_headers()

        # Get existing policies
        url = f"{SANDBOX_ACCOUNT_BASE}/fulfillment_policy?marketplace_id=EBAY_US"
        response = requests.get(url, headers=headers)

        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "total_policies": 0,
            "policies": []
        }

        if response.status_code == 200:
            data = response.json()
            result["total_policies"] = data.get("total", 0)
            result["policies"] = data.get("fulfillmentPolicies", [])

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/test-payment-policies")
async def test_payment_policies():
    """Test getting payment policies"""
    try:
        headers = get_headers()

        url = f"{SANDBOX_ACCOUNT_BASE}/payment_policy?marketplace_id=EBAY_US"
        response = requests.get(url, headers=headers)

        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "total_policies": 0,
            "policies": []
        }

        if response.status_code == 200:
            data = response.json()
            result["total_policies"] = data.get("total", 0)
            result["policies"] = data.get("paymentPolicies", [])

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/test-return-policies")
async def test_return_policies():
    """Test getting return policies"""
    try:
        headers = get_headers()

        url = f"{SANDBOX_ACCOUNT_BASE}/return_policy?marketplace_id=EBAY_US"
        response = requests.get(url, headers=headers)

        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "total_policies": 0,
            "policies": []
        }

        if response.status_code == 200:
            data = response.json()
            result["total_policies"] = data.get("total", 0)
            result["policies"] = data.get("returnPolicies", [])

        return result

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
        test_sku = f"INV-TEST-{int(time.time())}"

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
                "imageUrls": ["https://i.ebayimg.com/images/g/T~0AAOSwf6RkP3aI/s-l1600.jpg"]
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
    test_sku = f"QUICK-TEST-{int(time.time())}"

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
                "imageUrls": ["https://i.ebayimg.com/images/g/T~0AAOSwf6RkP3aI/s-l1600.jpg"]
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

        # Get all offers first
        offers_url = f"{SANDBOX_INVENTORY_BASE}/offer"
        offers_response = requests.get(offers_url, headers=headers)

        if offers_response.status_code == 200:
            offers_data = offers_response.json()
            offers = offers_data.get("offers", [])

            if offers:
                # Get details of first offer
                first_offer = offers[0]
                offer_id = first_offer.get("offerId")

                offer_details_url = f"{SANDBOX_INVENTORY_BASE}/offer/{offer_id}"
                details_response = requests.get(offer_details_url, headers=headers)

                return {
                    "success": True,
                    "total_offers": len(offers),
                    "tested_offer_id": offer_id,
                    "offer_details": details_response.json() if details_response.status_code == 200 else None
                }

            return {"success": True, "message": "No offers found", "total_offers": 0}

        return {"success": False, "error": "Failed to get offers"}

    except Exception as e:
        return {"success": False, "error": str(e)}


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
    print("   4. Run comprehensive tests!")
    print("\n🧪 Test Endpoints:")
    print("   GET  /test-all                    - Run all tests")
    print("   GET  /test-inventory-location     - Test location APIs")
    print("   GET  /test-create-listing         - Test listing creation")
    print("   GET  /test-get-listing            - Test listing retrieval")
    print("   GET  /test-policies               - Test policy APIs")
    print("   GET  /test-inventory-operations   - Test inventory CRUD")
    print("\n" + "="*70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
