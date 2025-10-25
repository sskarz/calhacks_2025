# Etsy OAuth FastAPI Backend

A FastAPI backend that handles OAuth 2.0 authorization with Etsy's API using PKCE (Proof Key for Code Exchange).

## Features

- OAuth 2.0 authorization flow with PKCE
- Token exchange and refresh
- Etsy API integration
- Health check and ping endpoints
- User information retrieval

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

The `.env` file contains your Etsy API credentials:

```
ETSY_API_KEY="your_api_key_here"
ETSY_SHARED_SECRET="your_shared_secret_here"
REDIRECT_URI="http://localhost:8000/oauth/callback"
```

**Important:** You need to register this redirect URI in your Etsy App settings at https://www.etsy.com/developers/your-apps

### 3. Run the Server

```bash
python apis.py
```

Or using uvicorn directly:

```bash
uvicorn apis:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Root Endpoint
- **GET** `/` - API information and available endpoints

### Health Check
- **GET** `/health` - Health status

### OAuth Flow

#### 1. Start Authorization
- **GET** `/oauth/authorize?scopes=email_r listings_r`
  - Generates authorization URL
  - Returns URL to visit for granting access
  - Query Parameters:
    - `scopes` (optional): Space-separated scopes (default: "email_r listings_r")

**Common Scopes:**
- `email_r` - Read email address
- `listings_r` - Read shop listings
- `listings_w` - Write shop listings
- `transactions_r` - Read transactions
- `transactions_w` - Write transactions
- `shops_r` - Read shop information
- `shops_w` - Write shop information

#### 2. Callback (Automatic)
- **GET** `/oauth/callback?code=...&state=...`
  - Etsy redirects here after user authorization
  - Exchanges code for access token
  - Returns access token, refresh token, and user ID

#### 3. Refresh Token
- **POST** `/oauth/refresh?refresh_token=YOUR_REFRESH_TOKEN`
  - Refreshes an expired access token
  - Returns new access token and refresh token

### Etsy API Integration

#### Ping Etsy API
- **GET** `/ping`
  - Tests connection to Etsy API
  - Doesn't require OAuth

#### Get User Information
- **GET** `/user/{user_id}?access_token=YOUR_ACCESS_TOKEN`
  - Fetches user information from Etsy
  - Requires valid access token

## Usage Example

### Step 1: Initiate OAuth Flow

```bash
curl http://localhost:8000/oauth/authorize?scopes=email_r%20listings_r
```

Response:
```json
{
  "authorization_url": "https://www.etsy.com/oauth/connect?...",
  "state": "xyz123...",
  "message": "Visit the authorization_url to grant access"
}
```

### Step 2: Visit Authorization URL

Open the `authorization_url` in your browser and grant permissions.

### Step 3: Receive Tokens

After authorization, Etsy redirects to the callback URL and you receive:

```json
{
  "message": "Authorization successful",
  "user_id": "123456789",
  "access_token": "123456789.abc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "123456789.def..."
}
```

### Step 4: Use Access Token

```bash
curl "http://localhost:8000/user/123456789?access_token=YOUR_ACCESS_TOKEN"
```

### Step 5: Refresh Token When Expired

```bash
curl -X POST "http://localhost:8000/oauth/refresh?refresh_token=YOUR_REFRESH_TOKEN"
```

## Interactive Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Security Notes

1. **Production**: Replace in-memory storage with a secure database
2. **HTTPS**: Always use HTTPS in production
3. **Secrets**: Never commit `.env` file to version control
4. **State Parameter**: Used for CSRF protection
5. **PKCE**: Implemented for additional security

## Token Lifetimes

- **Access Token**: 1 hour (3600 seconds)
- **Refresh Token**: 90 days

## Troubleshooting

### "ETSY_API_KEY not configured"
- Check that `.env` file exists in the backend directory
- Ensure environment variables are properly loaded

### "Invalid state parameter"
- The OAuth session may have expired
- Start a new authorization flow

### "Token exchange failed"
- Verify your redirect URI matches the one registered in Etsy App settings
- Check that the authorization code hasn't expired (they're single-use)

### "Ping failed"
- Verify your API key is correct
- Check internet connection
- Ensure Etsy API is accessible

## Development

The backend uses:
- **FastAPI**: Modern Python web framework
- **httpx**: Async HTTP client
- **python-dotenv**: Environment variable management
- **Pydantic**: Data validation

## Next Steps

1. Add database integration for token storage
2. Implement token encryption
3. Add user session management
4. Create additional Etsy API endpoints (listings, transactions, etc.)
5. Add rate limiting
6. Implement webhook handlers
