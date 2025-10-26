
# CalHacks 2025 - ASAP: A2A-Powered Multi-Platform E-Commerce  System

An intelligent e-commerce orchestration platform that uses Google ADK (Anthropic Developers Kit) agents to automatically create, manage, and negotiate product listings across multiple marketplaces (eBay and Tetsy).

## Features

- **AI-Powered Product Analysis**: Upload product images and automatically extract details using Google Gemini AI
- **Multi-Platform Listing**: Seamlessly create listings on eBay and Tetsy from a single interface
- **Intelligent Agent Orchestration**: Multi-agent system with specialized agents for each platform
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
