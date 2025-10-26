
# CalHacks 2025 

## ASAP: A2A Powered Multi-Platform E-Commerce  System

- Sanskar Thapa
- Damarrion (DIIZZY) Morgan-Harper
- Joshua Soteras 

An intelligent e-commerce orchestration platform that uses Google ADK (Anthropic Developers Kit) agents to automatically create, manage, and negotiate product listings across multiple marketplaces (eBay and Tetsy).

## Features

### Skillfully using Google's Agent 2 Agent (A2A) Protocol

- **Intelligent Agent Orchestration**: Multi-agent system with specialized agents for each platform
- **AI-Powered Product Analysis**: Upload product images and automatically extract details using Google Gemini AI
- **Multi-Platform Listing**: Seamlessly create listings on eBay and Tetsy from a single interface
- **Automated Price Negotiation**: AI agents handle buyer-seller negotiations on Tetsy with intelligent pricing strategies
- **Real-Time Dashboard**: WebSocket-powered live updates of all listings
- **Unified Management**: Track and manage inventory across all platforms in one place

## Architecture Overview

This project uses a multi-tier architecture with:
- **React Frontend** (TypeScript, Tailwind CSS, Shadcn UI)
- **FastAPI Backends** (Python, WebSocket support)
- **Google ADK Multi-Agent System** (Gemini 2.5-Flash)
- **SQLite Databases** (Listings and negotiations)
- **Platform Integrations** (eBay Sandbox API, Tetsy API)

## Project Structure

```
calhacks_2025/
├── backend/                    # Main API server (Port 8000)
│   ├── apis.py                # Primary API routes and WebSocket
│   ├── db.py                  # SQLite database helpers
│   ├── ebay_api.py            # eBay sandbox integration (Port 8001)
│   ├── requirements.txt       # Python dependencies
│   └── offersb.db            # SQLite database
│
├── front/                      # React frontend (Port 5173)
│   ├── src/
│   │   ├── pages/            # Dashboard and CreateListing pages
│   │   ├── components/       # Reusable UI components
│   │   ├── lib/              # API client and utilities
│   │   └── types/            # TypeScript type definitions
│   └── package.json
│
├── specialty_agents/           # Google ADK agent system
│   ├── my_agent/              # Root orchestrator (Port 10000)
│   ├── ebay_agent/            # eBay specialist (Port 10002)
│   └── tetsy_agent/           # Tetsy specialist (Port 10001)
│
└── Tetsy/                      # Tetsy platform implementation
    ├── backend/               # Negotiation API (Port 8050)
    └── frontend/              # Buyer-seller interface
```

## Prerequisites

- **Python** 3.8+
- **Node.js** 18+
- **Google API Key** (for Gemini AI)
- **eBay Developer Account** (for eBay integration)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd calhacks_2025
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
GOOGLE_API_KEY=your_google_api_key_here
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
EBAY_REDIRECT_URI=http://localhost:8001/oauth/callback
```

### 3. Frontend Setup

```bash
cd front
npm install
```

### 4. Agent Setup

The agents use Google ADK and share the same `requirements.txt` from the backend:

```bash
cd specialty_agents/my_agent
pip install -r ../../backend/requirements.txt
```

## Running the Application

You need to start multiple services in separate terminal windows:

### Terminal 1: Main Backend API

```bash
cd backend
python apis.py
# Runs on http://localhost:8000
```

### Terminal 2: eBay Integration Backend

```bash
cd backend
uvicorn ebay_api:app --reload --port 8001
# Runs on http://localhost:8001
```

### Terminal 3: Tetsy Negotiation Backend

```bash
cd Tetsy/backend
python main.py
# Runs on http://localhost:8050
```

### Terminal 4: Root Orchestrator Agent

```bash
cd specialty_agents/my_agent
python -m __main__
# Runs on http://localhost:10000
```

### Terminal 5: Tetsy Agent

```bash
cd specialty_agents/tetsy_agent
python -m __main__
# Runs on http://localhost:10001
```

### Terminal 6: eBay Agent

```bash
cd specialty_agents/ebay_agent
python -m __main__
# Runs on http://localhost:10002
```

### Terminal 7: Frontend

```bash
cd front
npm run dev
# Runs on http://localhost:5173
```

## Usage

### Creating a Listing

1. Navigate to **Create Listing** page
2. **Upload Product Image**: Drag & drop or click to upload
3. **AI Analysis**: Gemini automatically extracts product details (name, price, description, brand)
4. **Review & Edit**: Confirm or modify the extracted details
5. **Select Platform**: Choose eBay or Tetsy
6. **Submit**: The orchestrator agent routes to the appropriate platform agent
7. **View Dashboard**: See your listing appear in real-time

### Managing Listings

- **Dashboard**: View all listings across platforms with live updates
- **Status Tracking**: Monitor listing status (Draft, Pending, Live, Sold)
- **Platform Filtering**: See which platform each listing is on (color-coded)

### Handling Negotiations (Tetsy Only)

The Tetsy agent automatically handles buyer offers with intelligent pricing:
- **Accepts offers** >= 85% of asking price
- **Counters at 90%** for offers below 85%
- **Rejects** very low offers
- All negotiations are tracked in the Tetsy backend database

## API Endpoints

### Main Backend (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/api/analyze-product-image` | POST | AI image analysis (Gemini) |
| `/api/stream` | WebSocket | Real-time listing updates |
| `/api/create-listing-with-agent` | POST | Create listing via agent system |
| `/api/add_item` | POST | Direct database insertion |

### eBay Backend (Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/start-auth` | GET | Initiate eBay OAuth |
| `/oauth/callback` | GET | OAuth redirect handler |
| `/publish` | POST | Publish listing to eBay |
| `/create-all-policies` | POST | Create business policies |

### Tetsy Backend (Port 8050)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/negotiations` | GET | Get all negotiations |
| `/api/negotiations/{id}` | GET | Get negotiation details |
| `/api/negotiations` | POST | Start new negotiation |
| `/api/negotiations/{id}/messages` | POST | Send message/offer |

## Database Schema

### Main Database (`offersb.db`)

**Table: `users` (Listings)**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    platform TEXT NOT NULL,
    price REAL NOT NULL,
    high_price REAL,              -- Highest offer received
    status TEXT,                   -- 'listed', 'sold', 'pending'
    quantity INTEGER,
    imageSrc BLOB,                -- Product image bytes
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP
)
```

### Tetsy Database (`negotiations.db`)

**Table: `negotiations`**
```sql
CREATE TABLE negotiations (
    id TEXT PRIMARY KEY,
    product_id TEXT,
    buyer_id TEXT,
    seller_id TEXT,
    status TEXT,                   -- 'pending', 'accepted', 'rejected', 'counter'
    last_offer_amount REAL,
    created_at TIMESTAMP,
    ...
)
```

**Table: `messages`**
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    negotiation_id TEXT,
    sender_id TEXT,
    sender_type TEXT,              -- 'buyer', 'seller'
    type TEXT,                     -- 'message', 'offer', 'counter_offer'
    offer_amount REAL,
    ...
)
```

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **SQLite** - Embedded database
- **WebSockets** - Real-time communication
- **Google Generative AI** - Gemini 2.0-flash for image analysis
- **Google ADK** - Multi-agent orchestration framework
- **Httpx** - Async HTTP client
- **Pydantic** - Data validation

### Frontend
- **React 19** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS
- **Shadcn UI** - Component library (Radix UI + Tailwind)
- **React Router** - Client-side routing
- **React Hook Form** - Form management
- **Zod** - Schema validation
- **Axios** - HTTP client
- **Sonner** - Toast notifications

### AI/Agents
- **Google ADK** - Agent development kit
- **Gemini 2.5-Flash** - LLM for agent intelligence
- **RemoteA2aAgent** - Agent-to-agent communication pattern

## Multi-Agent System

### Root Orchestrator Agent (Port 10000)
- **Purpose**: Routes listing requests to appropriate platform agents
- **Model**: Gemini 2.5-Flash
- **Sub-agents**: tetsy_agent, ebay_agent

### eBay Agent (Port 10002)
- **Purpose**: Publishes listings to eBay Sandbox
- **Tools**:
  - `publish_to_ebay()` - Creates inventory items and offers
  - Database integration for tracking

### Tetsy Agent (Port 10001)
- **Purpose**: Manages Tetsy listings and handles negotiations
- **Tools**:
  - `post_listing_to_tetsy()` - Creates listings
  - `check_tetsy_notifications()` - Monitors offers
  - `respond_to_negotiation()` - Intelligent offer handling
- **Strategy**:
  - Accept offers >= 85% of asking price
  - Counter at 90% for lower offers
  - Professional communication with buyers

## Data Flow

```
User uploads image → Gemini AI analysis → Frontend form
    ↓
User confirms details + selects platform → API call
    ↓
Main Backend /api/create-listing-with-agent
    ↓
Root Agent (Gemini 2.5-Flash) decides routing
    ↓
    ├─→ eBay Agent → eBay API → eBay Sandbox
    │   └─→ Database save
    │
    └─→ Tetsy Agent → Tetsy Backend → Tetsy Database
        └─→ Database save
            ↓
WebSocket broadcasts update → All connected dashboards refresh
```

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd front
npm test
```

### Code Style

```bash
# Frontend linting
cd front
npm run lint
```

## eBay Integration Notes

- Uses **eBay Sandbox** environment for testing
- Requires **OAuth 2.0** authentication flow
- **Business policies** (fulfillment, payment, return) are mandatory
- SKU format: alphanumeric only (no special characters)
- Category-specific product attributes required

### eBay Setup Steps

1. Visit `/start-auth` to initiate OAuth
2. Complete authorization on eBay
3. Run `/optin-to-business-policies`
4. Create policies via `/create-all-policies`
5. Now ready to publish listings

## Troubleshooting

### Agents not connecting
- Ensure all backend services are running first
- Check that ports 8000, 8001, 8050, 10000-10002 are available
- Verify `GOOGLE_API_KEY` is set in `.env`

### eBay authentication fails
- Check eBay credentials in `.env`
- Ensure redirect URI matches eBay app settings
- Verify you're using sandbox credentials for sandbox environment

### WebSocket disconnects
- Check browser console for errors
- Ensure main backend (port 8000) is running
- Frontend auto-reconnects every 3 seconds

### Image analysis fails
- Verify `GOOGLE_API_KEY` is valid
- Check image format is supported (JPEG, PNG)
- Ensure image file size is reasonable (< 10MB)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project was developed for CalHacks 2025.

## Acknowledgments

- Built with Google ADK and Gemini AI
- eBay Developers Program for sandbox access
- Shadcn UI for beautiful components
- FastAPI and React communities


# System Architecture Flowchart

## Complete System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE LAYER                            │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              React Frontend (Port 5173)                               │  │
│  │  ┌─────────────────────┐      ┌──────────────────────────────────┐  │  │
│  │  │  CreateListing Page │      │      Dashboard Page              │  │  │
│  │  │  - Image Upload     │      │  - Real-time listing view        │  │  │
│  │  │  - AI Analysis      │      │  - Status tracking               │  │  │
│  │  │  - Platform Select  │      │  - Platform filtering            │  │  │
│  │  └─────────────────────┘      └──────────────────────────────────┘  │  │
│  │               │                            ▲                          │  │
│  │               │ HTTP POST                  │ WebSocket                │  │
│  │               │ (FormData)                 │ (real-time)              │  │
│  └───────────────┼────────────────────────────┼──────────────────────────┘  │
└─────────────────┼────────────────────────────┼─────────────────────────────┘
                  │                            │
                  ▼                            │
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MAIN BACKEND LAYER (Port 8000)                      │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     FastAPI Application (apis.py)                      │  │
│  │                                                                         │  │
│  │  POST /api/analyze-product-image                                       │  │
│  │  ┌────────────────────────────────────────────────────────┐           │  │
│  │  │ 1. Receive image upload (multipart/form-data)          │           │  │
│  │  │ 2. Encode to base64                                    │           │  │
│  │  │ 3. Send to Gemini 2.0-flash-exp ──────────────┐       │           │  │
│  │  │ 4. Parse JSON response                         │       │           │  │
│  │  │ 5. Extract: name, description, price, brand    │       │           │  │
│  │  │ 6. Return product details to frontend          │       │           │  │
│  │  └────────────────────────────────────────────────┼───────┘           │  │
│  │                                                    │                   │  │
│  │  POST /api/create-listing-with-agent              │                   │  │
│  │  ┌────────────────────────────────────────────────┼───────┐           │  │
│  │  │ 1. Receive: name, description, price,          │       │           │  │
│  │  │             quantity, brand, platform           │       │           │  │
│  │  │ 2. Create Runner with root_agent ──────────────┼───┐   │           │  │
│  │  │ 3. Invoke agent with prompt                    │   │   │           │  │
│  │  │ 4. Collect agent response                      │   │   │           │  │
│  │  │ 5. Return response to frontend                 │   │   │           │  │
│  │  └────────────────────────────────────────────────┘   │   │           │  │
│  │                                                        │   │           │  │
│  │  WebSocket /api/stream ◄───────────────────────────────┘   │           │  │
│  │  ┌─────────────────────────────────────────┐              │           │  │
│  │  │ 1. Accept WebSocket connection          │              │           │  │
│  │  │ 2. Every 2 seconds:                     │              │           │  │
│  │  │    - Query all items from database      │              │           │  │
│  │  │    - Convert BLOB images to base64      │              │           │  │
│  │  │    - Send JSON array to all clients     │              │           │  │
│  │  └─────────────────────────────────────────┘              │           │  │
│  │                                                            │           │  │
│  │  POST /api/add_item                                       │           │  │
│  │  ┌─────────────────────────────────────────┐              │           │  │
│  │  │ Direct database insertion               │              │           │  │
│  │  │ (used by agents after platform publish) │              │           │  │
│  │  └─────────────────────────────────────────┘              │           │  │
│  └────────────────────────────────┬───────────────────────────┼───────────┘  │
│                                   │                           │              │
│                  ┌────────────────┼───────────────────────────┘              │
│                  │                │                                          │
│         ┌────────▼──────┐    ┌───▼─────────┐                                │
│         │  SQLite DB    │    │  Gemini AI  │                                │
│         │ (offersb.db)  │    │  (Google)   │                                │
│         │               │    │             │                                │
│         │  Table: users │    │ Model:      │                                │
│         │  - id         │    │ gemini-2.0- │                                │
│         │  - title      │    │ flash-exp   │                                │
│         │  - platform   │    └─────────────┘                                │
│         │  - price      │                                                   │
│         │  - status     │                                                   │
│         │  - imageSrc   │                                                   │
│         └───────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Invokes via Runner
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MULTI-AGENT ORCHESTRATION LAYER                        │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              Root Orchestrator Agent (Port 10000)                      │  │
│  │              Model: Gemini 2.5-Flash (Google ADK)                      │  │
│  │                                                                         │  │
│  │  Instructions:                                                          │  │
│  │  1. Receive product data in JSON format                                │  │
│  │  2. Parse platform preference (Tetsy or eBay)                          │  │
│  │  3. Route to appropriate sub-agent:                                    │  │
│  │     - If platform = "Tetsy" → delegate to tetsy_agent                 │  │
│  │     - If platform = "eBay" → delegate to ebay_agent                   │  │
│  │  4. Return results to caller                                           │  │
│  │                                                                         │  │
│  │  Sub-agents:                                                            │  │
│  │  - tetsy_agent (RemoteA2aAgent, localhost:10001)                       │  │
│  │  - ebay_agent (RemoteA2aAgent, localhost:10002)                        │  │
│  └───────────────────────────┬──────────────────┬──────────────────────────┘  │
│                              │                  │                            │
└──────────────────────────────┼──────────────────┼────────────────────────────┘
                               │                  │
              ┌────────────────┘                  └────────────────┐
              │                                                    │
              ▼                                                    ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────────┐
│    Tetsy Agent (Port 10001)          │    │    eBay Agent (Port 10002)       │
│    Model: Gemini 2.5-Flash           │    │    Model: Gemini 2.5-Flash       │
│                                      │    │                                  │
│  Tools:                              │    │  Tools:                          │
│  ┌───────────────────────────────┐  │    │  ┌────────────────────────────┐  │
│  │ post_listing_to_tetsy()       │  │    │  │ publish_to_ebay()          │  │
│  │ - name, description, price    │  │    │  │ - name, description, price │  │
│  │ - image_url, seller_id        │  │    │  │ - quantity, brand          │  │
│  │ - POST to localhost:8050      │  │    │  │ - POST to localhost:8001   │  │
│  │ - Saves to database           │  │    │  │ - Creates placeholder img  │  │
│  └───────────────────────────────┘  │    │  │ - Saves to database        │  │
│                                      │    │  └────────────────────────────┘  │
│  ┌───────────────────────────────┐  │    │                                  │
│  │ check_tetsy_notifications()   │  │    │  Instructions:                   │
│  │ - listing_id                  │  │    │  1. Extract product fields      │
│  │ - Check for buyer offers      │  │    │  2. Infer market pricing        │
│  └───────────────────────────────┘  │    │  3. Call publish_to_ebay()      │
│                                      │    │  4. Return listing URL          │
│  ┌───────────────────────────────┐  │    │                                  │
│  │ respond_to_negotiation()      │  │    └──────────────┬───────────────────┘
│  │ - negotiation_id              │  │                   │
│  │ - response_type (accept/      │  │                   │
│  │   reject/counter)             │  │                   ▼
│  │ - counter_offer amount        │  │    ┌──────────────────────────────────┐
│  │                               │  │    │  eBay Backend (Port 8001)        │
│  │ Strategy:                     │  │    │  File: ebay_api.py               │
│  │ - Accept if offer >= 85%      │  │    │                                  │
│  │ - Counter at 90% if < 85%     │  │    │  POST /publish                   │
│  │ - Reject very low offers      │  │    │  ┌────────────────────────────┐  │
│  └───────────────────────────────┘  │    │  │ 1. Validate OAuth token    │  │
│                                      │    │  │ 2. Create inventory item   │  │
│  Instructions:                       │    │  │ 3. Create offer with       │  │
│  1. Post listings to Tetsy           │    │  │    business policies       │  │
│  2. Handle buyer negotiations        │    │  │ 4. Publish to eBay sandbox │  │
│  3. Respond professionally           │    │  │ 5. Return listing URL      │  │
│  4. Maximize sales with fair         │    │  │ 6. Save to main DB         │  │
│     pricing                          │    │  └────────────────────────────┘  │
└──────────────┬───────────────────────┘    │                                  │
               │                            │  Other Endpoints:                │
               │                            │  - GET /start-auth (OAuth)       │
               │                            │  - GET /oauth/callback           │
               │                            │  - POST /create-all-policies     │
               ▼                            │  - POST /optin-to-business-...   │
┌──────────────────────────────────────┐    └──────────────┬───────────────────┘
│ Tetsy Backend (Port 8050)            │                   │
│ File: Tetsy/backend/main.py          │                   ▼
│                                      │    ┌──────────────────────────────────┐
│ Database: negotiations.db            │    │      eBay Sandbox API            │
│ ┌─────────────────┐                  │    │      (External Service)          │
│ │ negotiations    │                  │    │                                  │
│ │ messages        │                  │    │  - OAuth 2.0 authentication      │
│ │ listings        │                  │    │  - Inventory API                 │
│ └─────────────────┘                  │    │  - Business Policy API           │
│                                      │    │  - Trading API                   │
│ POST /api/listings                   │    │  - Returns listing URLs          │
│ ┌────────────────────────────────┐   │    └──────────────────────────────────┘
│ │ 1. Create listing record       │   │
│ │ 2. Store in listings table     │   │
│ │ 3. Return listing_id           │   │
│ └────────────────────────────────┘   │
│                                      │
│ POST /api/negotiations               │
│ ┌────────────────────────────────┐   │
│ │ 1. Create negotiation record   │   │
│ │ 2. Create initial offer msg    │   │
│ │ 3. Webhook to tetsy_agent:     │   │
│ │    POST localhost:10001/       │   │
│ │         webhook/message        │   │
│ │ 4. Agent decides response      │   │
│ └────────────────────────────────┘   │
│                                      │
│ POST /api/seller/{id}/negotiations/  │
│      {neg_id}/accept                 │
│ ┌────────────────────────────────┐   │
│ │ 1. Update status to 'accepted' │   │
│ │ 2. Add acceptance message      │   │
│ │ 3. Mark as sold                │   │
│ └────────────────────────────────┘   │
│                                      │
│ POST /api/seller/{id}/negotiations/  │
│      {neg_id}/counter                │
│ ┌────────────────────────────────┐   │
│ │ 1. Update status to 'counter'  │   │
│ │ 2. Set last_offer_amount       │   │
│ │ 3. Add counter-offer message   │   │
│ └────────────────────────────────┘   │
│                                      │
│ GET /api/negotiations                │
│ ┌────────────────────────────────┐   │
│ │ Return all negotiations for    │   │
│ │ buyer with messages            │   │
│ └────────────────────────────────┘   │
└──────────────────────────────────────┘
```

## Detailed Flow Sequences

### Flow 1: Create Listing via AI Analysis

```
┌──────────┐
│   User   │
└─────┬────┘
      │
      │ 1. Upload product image
      ▼
┌───────────────────────┐
│  CreateListing Page   │
│  (React Frontend)     │
└──────────┬────────────┘
           │
           │ 2. POST /api/analyze-product-image
           │    (multipart/form-data: image file)
           ▼
┌───────────────────────────────────────┐
│  Main Backend API (Port 8000)         │
│  apis.py                              │
│                                       │
│  analyze_product_image()              │
│  ┌─────────────────────────────────┐  │
│  │ • Read image bytes              │  │
│  │ • Encode to base64              │  │
│  └──────────┬──────────────────────┘  │
└─────────────┼─────────────────────────┘
              │
              │ 3. Send image + prompt
              ▼
┌─────────────────────────────────────┐
│   Google Generative AI              │
│   Model: gemini-2.0-flash-exp       │
│                                     │
│   Prompt: "Extract product details │
│   in JSON format..."                │
│                                     │
│   Returns:                          │
│   {                                 │
│     "name": "...",                  │
│     "description": "...",           │
│     "price": "...",                 │
│     "brand": "...",                 │
│     "quantity": "1"                 │
│   }                                 │
└──────────────┬──────────────────────┘
               │
               │ 4. JSON response
               ▼
┌───────────────────────────────────────┐
│  Main Backend API                     │
│  ┌─────────────────────────────────┐  │
│  │ • Parse JSON                    │  │
│  │ • Remove markdown if present    │  │
│  │ • Return product_details        │  │
│  └──────────┬──────────────────────┘  │
└─────────────┼─────────────────────────┘
              │
              │ 5. Return JSON to frontend
              ▼
┌───────────────────────┐
│  CreateListing Page   │
│  ┌─────────────────┐  │
│  │ • Pre-fill form │  │
│  │ • User reviews  │  │
│  │ • User selects  │  │
│  │   platform      │  │
│  │ • User submits  │  │
│  └────────┬────────┘  │
└───────────┼───────────┘
            │
            │ 6. Submit form
            ▼
      [Continue to Flow 2]
```

### Flow 2: Agent-Based Listing Creation

```
┌───────────────────────┐
│  CreateListing Page   │
└──────────┬────────────┘
           │
           │ 1. POST /api/create-listing-with-agent
           │    Form data: name, description, price,
           │               quantity, brand, platform
           ▼
┌───────────────────────────────────────────┐
│  Main Backend API (Port 8000)             │
│  apis.py                                  │
│                                           │
│  create_listing_with_agent()              │
│  ┌──────────────────────────────────────┐ │
│  │ • Prepare product_data JSON          │ │
│  │ • Create prompt for agent:           │ │
│  │   "Please post this product to       │ │
│  │    [Tetsy/eBay]: {product_data}"     │ │
│  │ • Import root_agent                  │ │
│  │ • Create Runner with:                │ │
│  │   - InMemorySessionService           │ │
│  │   - InMemoryMemoryService            │ │
│  │ • Create session                     │ │
│  │ • Create Content with prompt         │ │
│  │ • Call runner.run_async()            │ │
│  └─────────────┬────────────────────────┘ │
└────────────────┼──────────────────────────┘
                 │
                 │ 2. Invoke agent via ADK Runner
                 ▼
┌──────────────────────────────────────────────────┐
│  Root Orchestrator Agent (Port 10000)            │
│  specialty_agents/my_agent/agent.py              │
│  Model: Gemini 2.5-Flash                         │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ System Instructions:                       │  │
│  │ "You are a listing orchestrator that       │  │
│  │  routes product listings to appropriate    │  │
│  │  platform agents (Tetsy or eBay)"          │  │
│  │                                            │  │
│  │ Process:                                   │  │
│  │ 1. Parse incoming product data             │  │
│  │ 2. Identify target platform from prompt    │  │
│  │ 3. Select appropriate sub-agent            │  │
│  └──────────────┬─────────────────────────────┘  │
│                 │                                │
│  Sub-agents:    │                                │
│  ┌──────────────┼──────────────┐                 │
│  │ tetsy_agent  │ ebay_agent   │                 │
│  │ (Port 10001) │ (Port 10002) │                 │
│  └──────────────┴──────────────┘                 │
└──────────────────┼───────────────┼────────────────┘
                   │               │
        [Tetsy]    │               │    [eBay]
                   ▼               ▼
         ┌─────────────────┐  ┌──────────────────┐
         │  Continue to    │  │  Continue to     │
         │  Flow 3         │  │  Flow 4          │
         └─────────────────┘  └──────────────────┘
```

### Flow 3: Tetsy Platform Listing

```
┌────────────────────────────────────────┐
│  Root Orchestrator Agent               │
└─────────────────┬──────────────────────┘
                  │
                  │ Delegate to tetsy_agent
                  ▼
┌──────────────────────────────────────────────────┐
│  Tetsy Agent (Port 10001)                        │
│  specialty_agents/tetsy_agent/agent.py           │
│  Model: Gemini 2.5-Flash                         │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ Instructions:                              │  │
│  │ "Post listings to Tetsy and handle buyer  │  │
│  │  negotiations professionally"              │  │
│  │                                            │  │
│  │ Decision:                                  │  │
│  │ • Extract: name, description, price,       │  │
│  │           image_url, seller_id             │  │
│  │ • Call tool: post_listing_to_tetsy()       │  │
│  └──────────────┬─────────────────────────────┘  │
└─────────────────┼────────────────────────────────┘
                  │
                  │ Execute tool
                  ▼
┌──────────────────────────────────────────────────┐
│  Tool: post_listing_to_tetsy()                   │
│  (Python function in tetsy_agent)                │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ def post_listing_to_tetsy(                 │  │
│  │     name, description, price,              │  │
│  │     image_url, seller_id                   │  │
│  │ ):                                         │  │
│  │   # 1. POST to Tetsy backend               │  │
│  │   httpx.post(                              │  │
│  │     "http://localhost:8050/api/listings",  │  │
│  │     json={...}                             │  │
│  │   )                                        │  │
│  │                                            │  │
│  │   # 2. Save to main database               │  │
│  │   httpx.post(                              │  │
│  │     "http://localhost:8000/api/add_item",  │  │
│  │     data={...}                             │  │
│  │   )                                        │  │
│  └──────────────┬─────────────────────────────┘  │
└─────────────────┼────────────────────────────────┘
                  │
         ┌────────┴─────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌──────────────────┐
│ Tetsy Backend   │  │  Main Backend    │
│ (Port 8050)     │  │  (Port 8000)     │
│                 │  │                  │
│ POST /api/      │  │  POST /api/      │
│   listings      │  │    add_item      │
│                 │  │                  │
│ ┌────────────┐  │  │  ┌────────────┐  │
│ │ Insert into│  │  │  │ Insert into│  │
│ │ listings   │  │  │  │ users table│  │
│ │ table      │  │  │  │            │  │
│ └────────────┘  │  │  │ - title    │  │
│                 │  │  │ - platform │  │
│ Database:       │  │  │   "Tetsy"  │  │
│ negotiations.db │  │  │ - price    │  │
│                 │  │  │ - status   │  │
│                 │  │  │   "listed" │  │
│                 │  │  │ - imageSrc │  │
└─────────────────┘  │  └────────────┘  │
                     │                  │
                     │  Database:       │
                     │  offersb.db      │
                     └──────┬───────────┘
                            │
                            │ WebSocket broadcasts
                            │ new listing every 2s
                            ▼
                     ┌─────────────────┐
                     │  All Dashboard  │
                     │  clients update │
                     └─────────────────┘
```

### Flow 4: eBay Platform Listing

```
┌────────────────────────────────────────┐
│  Root Orchestrator Agent               │
└─────────────────┬──────────────────────┘
                  │
                  │ Delegate to ebay_agent
                  ▼
┌──────────────────────────────────────────────────┐
│  eBay Agent (Port 10002)                         │
│  specialty_agents/ebay_agent/agent.py            │
│  Model: Gemini 2.5-Flash                         │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ Instructions:                              │  │
│  │ "Publish product listings to eBay with    │  │
│  │  appropriate pricing and categorization"   │  │
│  │                                            │  │
│  │ Decision:                                  │  │
│  │ • Extract: name, description, price,       │  │
│  │           quantity, brand                  │  │
│  │ • Infer market-competitive pricing         │  │
│  │ • Call tool: publish_to_ebay()             │  │
│  └──────────────┬─────────────────────────────┘  │
└─────────────────┼────────────────────────────────┘
                  │
                  │ Execute tool
                  ▼
┌──────────────────────────────────────────────────┐
│  Tool: publish_to_ebay()                         │
│  (Python function in ebay_agent)                 │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ def publish_to_ebay(                       │  │
│  │     name, description, price,              │  │
│  │     quantity, brand                        │  │
│  │ ):                                         │  │
│  │   # 1. Create placeholder image            │  │
│  │   image = create_placeholder()             │  │
│  │                                            │  │
│  │   # 2. POST to eBay backend                │  │
│  │   response = httpx.post(                   │  │
│  │     "http://localhost:8001/publish",       │  │
│  │     data={...}                             │  │
│  │   )                                        │  │
│  │                                            │  │
│  │   # 3. Save to main database               │  │
│  │   httpx.post(                              │  │
│  │     "http://localhost:8000/api/add_item",  │  │
│  │     data={...}                             │  │
│  │   )                                        │  │
│  └──────────────┬─────────────────────────────┘  │
└─────────────────┼────────────────────────────────┘
                  │
         ┌────────┴─────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌──────────────────┐
│ eBay Backend    │  │  Main Backend    │
│ (Port 8001)     │  │  (Port 8000)     │
│ ebay_api.py     │  │  apis.py         │
│                 │  │                  │
│ POST /publish   │  │  POST /api/      │
│                 │  │    add_item      │
│ ┌────────────┐  │  │                  │
│ │ 1. Validate│  │  │  Same as Flow 3  │
│ │    OAuth   │  │  └──────────────────┘
│ │    token   │  │
│ │            │  │
│ │ 2. Create  │  │
│ │    inventory│  │
│ │    item    │  │
│ │    POST    │  │
│ │    /sell/  │  │
│ │    inventory│
│ │    /v1/    │  │
│ │    inventory│
│ │    _item/{sku}│
│ │            │  │
│ │ 3. Create  │  │
│ │    offer   │  │
│ │    POST    │  │
│ │    /sell/  │  │
│ │    inventory│
│ │    /v1/    │  │
│ │    offer   │  │
│ │            │  │
│ │ 4. Publish │  │
│ │    offer   │  │
│ │    POST    │  │
│ │    /sell/  │  │
│ │    inventory│
│ │    /v1/    │  │
│ │    offer/  │  │
│ │    {id}/   │  │
│ │    publish │  │
│ └─────┬──────┘  │
└───────┼─────────┘
        │
        │ 5. eBay API calls
        ▼
┌─────────────────────┐
│  eBay Sandbox API   │
│  (External)         │
│                     │
│  • OAuth 2.0 auth   │
│  • Inventory API    │
│  • Business Policy  │
│  • Trading API      │
│                     │
│  Returns:           │
│  - listing_id       │
│  - sandbox_url      │
└──────┬──────────────┘
       │
       │ 6. Return listing URL
       ▼
  [Listing created]
```

### Flow 5: Tetsy Buyer Negotiation

```
┌──────────────────────┐
│  Buyer               │
│  (Tetsy Frontend)    │
└──────────┬───────────┘
           │
           │ 1. Make offer on product
           │    "I'll pay $40 for this $50 item"
           ▼
┌──────────────────────────────────────┐
│  Tetsy Backend (Port 8050)           │
│  main.py                             │
│                                      │
│  POST /api/negotiations              │
│  ┌──────────────────────────────┐    │
│  │ Body:                        │    │
│  │ {                            │    │
│  │   "productId": "123",        │    │
│  │   "productTitle": "...",     │    │
│  │   "sellerId": "Tetsy",       │    │
│  │   "offerAmount": 40.00,      │    │
│  │   "message": "..."           │    │
│  │ }                            │    │
│  │                              │    │
│  │ Process:                     │    │
│  │ 1. Create negotiation record │    │
│  │    - id: "neg-{timestamp}"   │    │
│  │    - status: "pending"       │    │
│  │    - last_offer_amount: 40   │    │
│  │                              │    │
│  │ 2. Create initial message    │    │
│  │    - type: "offer"           │    │
│  │    - offer_amount: 40        │    │
│  │                              │    │
│  │ 3. Save to database          │    │
│  └──────────┬───────────────────┘    │
└─────────────┼────────────────────────┘
              │
              │ 4. Webhook to agent
              │    POST http://localhost:10001/
              │         webhook/message
              ▼
┌────────────────────────────────────────────────┐
│  Tetsy Agent (Port 10001)                      │
│                                                │
│  Webhook handler receives:                     │
│  {                                             │
│    "negotiation_id": "neg-123",                │
│    "product_id": "123",                        │
│    "offer_amount": 40.00,                      │
│    "asking_price": 50.00,                      │
│    "message": "..."                            │
│  }                                             │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │ Agent Decision Logic (Gemini 2.5-Flash): │  │
│  │                                          │  │
│  │ offer_percentage = 40 / 50 = 80%         │  │
│  │                                          │  │
│  │ IF offer >= 85% of asking_price:         │  │
│  │    → Accept the offer                    │  │
│  │                                          │  │
│  │ ELSE IF offer < 85%:                     │  │
│  │    → Counter at 90% of asking_price      │  │
│  │    → counter_amount = 50 * 0.9 = $45     │  │
│  │                                          │  │
│  │ ELSE (very low offer):                   │  │
│  │    → Reject politely                     │  │
│  │                                          │  │
│  │ In this case: 80% < 85%                  │  │
│  │ → Call respond_to_negotiation()          │  │
│  │   with counter_offer                     │  │
│  └──────────────┬───────────────────────────┘  │
└─────────────────┼──────────────────────────────┘
                  │
                  │ 5. Execute tool
                  ▼
┌──────────────────────────────────────────────────┐
│  Tool: respond_to_negotiation()                  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ def respond_to_negotiation(               │  │
│  │     negotiation_id="neg-123",             │  │
│  │     response_type="counter",              │  │
│  │     counter_offer=45.00                   │  │
│  │ ):                                        │  │
│  │   httpx.post(                             │  │
│  │     "http://localhost:8050/api/seller/"   │  │
│  │     "Tetsy/negotiations/neg-123/counter", │  │
│  │     json={                                │  │
│  │       "counter_offer_amount": 45.00,      │  │
│  │       "message": "Thanks for your offer!  │  │
│  │                   How about $45?"         │  │
│  │     }                                     │  │
│  │   )                                       │  │
│  └──────────────┬─────────────────────────────┘  │
└─────────────────┼────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────┐
│  Tetsy Backend (Port 8050)                       │
│                                                  │
│  POST /api/seller/Tetsy/negotiations/            │
│       neg-123/counter                            │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ 1. Update negotiation:                     │  │
│  │    - status = "counter"                    │  │
│  │    - last_offer_amount = 45.00             │  │
│  │                                            │  │
│  │ 2. Create message:                         │  │
│  │    - type = "counter_offer"                │  │
│  │    - offer_amount = 45.00                  │  │
│  │    - content = "Thanks for your offer!..." │  │
│  │    - sender_type = "seller"                │  │
│  │                                            │  │
│  │ 3. Save to database                        │  │
│  └──────────────┬─────────────────────────────┘  │
└─────────────────┼────────────────────────────────┘
                  │
                  │ 6. Counter-offer saved
                  ▼
┌──────────────────────────────────────┐
│  Buyer sees counter-offer            │
│  in Tetsy Frontend                   │
│                                      │
│  Options:                            │
│  ┌────────────────────────────────┐  │
│  │ • Accept $45 counter-offer     │  │
│  │   → POST /api/negotiations/    │  │
│  │     neg-123/accept             │  │
│  │                                │  │
│  │ • Make new offer ($42?)        │  │
│  │   → POST /api/negotiations/    │  │
│  │     neg-123/messages           │  │
│  │     (triggers agent again)     │  │
│  │                                │  │
│  │ • Walk away                    │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### Flow 6: WebSocket Real-Time Updates

```
┌──────────────────────────────────────┐
│  Multiple Dashboard Users            │
│  (Browser clients)                   │
│                                      │
│  User A   User B   User C            │
└────┬──────┬────────┬──────────────────┘
     │      │        │
     │      │        │ 1. WebSocket connect
     │      │        │    ws://localhost:8000/api/stream
     │      │        │
     ▼      ▼        ▼
┌──────────────────────────────────────────────────┐
│  Main Backend API (Port 8000)                    │
│  apis.py                                         │
│                                                  │
│  @app.websocket("/api/stream")                   │
│  async def websocket_endpoint(websocket)         │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ 1. Accept WebSocket connection             │  │
│  │    await websocket.accept()                │  │
│  │                                            │  │
│  │ 2. Enter infinite loop:                    │  │
│  │    while True:                             │  │
│  │                                            │  │
│  │      a. Get fresh DB connection            │  │
│  │         conn = db.get_db_connection()      │  │
│  │                                            │  │
│  │      b. Fetch all items                    │  │
│  │         items = db.get_all_items(conn)     │  │
│  │                                            │  │
│  │      c. Convert to JSON-serializable:      │  │
│  │         - Convert Row to dict              │  │
│  │         - Convert BLOB to base64           │  │
│  │                                            │  │
│  │      d. Broadcast to this client           │  │
│  │         await websocket.send_json(items)   │  │
│  │                                            │  │
│  │      e. Wait 2 seconds                     │  │
│  │         await asyncio.sleep(2)             │  │
│  │                                            │  │
│  │      f. Repeat                             │  │
│  └──────────────┬─────────────────────────────┘  │
└─────────────────┼────────────────────────────────┘
                  │
                  │ Query every 2 seconds
                  ▼
┌──────────────────────────────────────┐
│  SQLite Database (offersb.db)        │
│                                      │
│  SELECT * FROM users                 │
│  ORDER BY createdAt DESC             │
│                                      │
│  Returns array of listings:          │
│  [                                   │
│    {                                 │
│      id: 1,                          │
│      title: "iPhone 12",             │
│      platform: "eBay",               │
│      price: 599.99,                  │
│      status: "listed",               │
│      imageSrc: <base64 encoded>,     │
│      ...                             │
│    },                                │
│    ...                               │
│  ]                                   │
└──────────────┬───────────────────────┘
               │
               │ Return results
               ▼
┌──────────────────────────────────────────────────┐
│  Backend broadcasts to all connected clients     │
└─────┬────────┬────────┬──────────────────────────┘
      │        │        │
      │        │        │ 3. Receive JSON array
      │        │        │    every 2 seconds
      ▼        ▼        ▼
┌──────────────────────────────────────┐
│  Dashboard Pages (React)             │
│                                      │
│  useEffect(() => {                   │
│    const ws = new WebSocket(...)     │
│                                      │
│    ws.onmessage = (event) => {       │
│      const listings = JSON.parse(    │
│        event.data                    │
│      )                               │
│      setListings(listings)           │
│    }                                 │
│                                      │
│    ws.onclose = () => {              │
│      // Reconnect after 3 seconds    │
│      setTimeout(connect, 3000)       │
│    }                                 │
│  }, [])                              │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ Table re-renders with:         │  │
│  │ - Updated listings             │  │
│  │ - New status badges            │  │
│  │ - Platform indicators          │  │
│  │ - Real-time changes            │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

## System Integration Summary

### Port Allocation

| Port  | Service                    | Technology  | Purpose                          |
|-------|----------------------------|-------------|----------------------------------|
| 5173  | React Frontend             | Vite        | User interface                   |
| 8000  | Main Backend API           | FastAPI     | Core orchestration & WebSocket   |
| 8001  | eBay Integration Backend   | FastAPI     | eBay Sandbox API integration     |
| 8050  | Tetsy Backend              | FastAPI     | Negotiation & listing management |
| 10000 | Root Orchestrator Agent    | Google ADK  | Multi-agent routing              |
| 10001 | Tetsy Agent                | Google ADK  | Tetsy operations & negotiation   |
| 10002 | eBay Agent                 | Google ADK  | eBay listing publication         |

### Database Connections

```
┌────────────────────────┐
│  offersb.db            │
│  (Main Database)       │
├────────────────────────┤
│ Connected by:          │
│ • Main Backend (8000)  │
│ • eBay Agent (10002)   │
│ • Tetsy Agent (10001)  │
└────────────────────────┘

┌────────────────────────┐
│  negotiations.db       │
│  (Tetsy Database)      │
├────────────────────────┤
│ Connected by:          │
│ • Tetsy Backend (8050) │
└────────────────────────┘
```

### External API Integrations

```
┌─────────────────────────────┐
│  Google Generative AI       │
│  (Gemini)                   │
├─────────────────────────────┤
│ Used by:                    │
│ • Main Backend (8000)       │
│   - gemini-2.0-flash-exp    │
│     for image analysis      │
│                             │
│ • All Agents (10000-10002)  │
│   - gemini-2.5-flash        │
│     for agent intelligence  │
└─────────────────────────────┘

┌─────────────────────────────┐
│  eBay Sandbox API           │
├─────────────────────────────┤
│ Used by:                    │
│ • eBay Backend (8001)       │
│   - OAuth 2.0 auth          │
│   - Inventory API           │
│   - Business Policy API     │
│   - Trading API             │
└─────────────────────────────┘
```

## Component Dependencies

```
Frontend (React)
    ↓
    ├─→ Main Backend API ──→ SQLite DB (offersb.db)
    │       ↓
    │       ├─→ Google Gemini (image analysis)
    │       │
    │       └─→ Root Agent ──→ Google ADK
    │               ↓
    │               ├─→ Tetsy Agent
    │               │       ↓
    │               │       ├─→ Tetsy Backend ──→ SQLite DB (negotiations.db)
    │               │       └─→ Main Backend (save listing)
    │               │
    │               └─→ eBay Agent
    │                       ↓
    │                       ├─→ eBay Backend ──→ eBay Sandbox API
    │                       └─→ Main Backend (save listing)
    │
    └─→ Tetsy Backend (for buyer negotiations)
            ↓
            └─→ Tetsy Agent (webhook for auto-response)
```

