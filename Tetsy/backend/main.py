import sys
from fastapi import FastAPI, HTTPException, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import sqlite3
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tetsy - Negotiation Backend")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Log validation errors in detail."""
    logger.error(f"Validation Error: {exc}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request Query: {request.query_params}")
    logger.error(f"Errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"status": "error", "detail": exc.errors()}
    )

# Mock buyer ID (single user)
BUYER_ID = "buyer-001"

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
DB_PATH = "negotiations.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS negotiations (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            buyer_id TEXT NOT NULL,
            seller_id TEXT NOT NULL,
            product_title TEXT,
            product_image TEXT,
            status TEXT CHECK (status IN ('pending', 'accepted', 'rejected', 'counter')) DEFAULT 'pending',
            last_offer_amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archived BOOLEAN DEFAULT FALSE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            negotiation_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            sender_type TEXT CHECK (sender_type IN ('buyer', 'seller')),
            content TEXT,
            type TEXT CHECK (type IN ('message', 'offer', 'counter_offer')) DEFAULT 'message',
            offer_amount REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_by_seller BOOLEAN DEFAULT FALSE,
            read_by_buyer BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (negotiation_id) REFERENCES negotiations(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            seller_id TEXT NOT NULL,
            image BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    
    conn.commit()
    conn.close()

init_db()

# ============ MODELS ============

class SellerMessageRequest(BaseModel):
    negotiation_id: str
    seller_id: str
    content: str
    type: str  # "message" | "counter_offer"
    counter_offer_amount: Optional[float] = None

class SellerOfferResponse(BaseModel):
    negotiation_id: str
    seller_id: str
    action: str  # "accept" | "reject" | "counter"
    counter_amount: Optional[float] = None
    message: Optional[str] = None

class StartNegotiationRequest(BaseModel):
    product_id: str = Field(..., alias="productId")
    product_title: str = Field(..., alias="productTitle")
    product_image: Optional[str] = Field(None, alias="productImage")  # Make it optional
    seller_id: str = Field(..., alias="sellerId")
    offer_amount: float = Field(..., alias="offerAmount")
    message: Optional[str] = None
    
    @field_validator('product_id', mode='before')
    @classmethod
    def convert_product_id(cls, v):
        """Convert product_id to string if it's a number."""
        return str(v)
    
    class Config:
        populate_by_name = True

class SendMessageRequest(BaseModel):
    negotiation_id: str = Field(..., alias="negotiationId")
    content: str
    type: str = "message"
    offer_amount: Optional[float] = Field(None, alias="offerAmount")
    
    class Config:
        populate_by_name = True

# ============ BUYER ENDPOINTS ============

@app.get("/api/negotiations")
async def get_negotiations():
    """Get all negotiations for the buyer."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM negotiations 
            WHERE buyer_id = ? AND archived = FALSE
            ORDER BY updated_at DESC
        ''', (BUYER_ID,))
        
        negotiations = cursor.fetchall()
        conn.close()
        
        return [dict(n) for n in negotiations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/negotiations/{negotiation_id}")
async def get_negotiation(negotiation_id: str):
    """Get full negotiation details with all messages."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM negotiations 
            WHERE id = ? AND buyer_id = ?
        ''', (negotiation_id, BUYER_ID))
        
        negotiation = cursor.fetchone()
        if not negotiation:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        cursor.execute('''
            SELECT * FROM messages 
            WHERE negotiation_id = ? 
            ORDER BY timestamp ASC
        ''', (negotiation_id,))
        
        messages = cursor.fetchall()
        conn.close()
        
        result = dict(negotiation)
        result['messages'] = [dict(m) for m in messages]
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/negotiations")
async def start_negotiation(request: StartNegotiationRequest):
    """Start a new negotiation for a product."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        negotiation_id = f"neg-{int(datetime.now().timestamp() * 1000)}"
        
        cursor.execute('''
            INSERT INTO negotiations 
            (id, product_id, buyer_id, seller_id, product_title, product_image, status, last_offer_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            negotiation_id,
            request.product_id,
            BUYER_ID,
            request.seller_id,
            request.product_title,
            request.product_image,
            "pending",
            request.offer_amount
        ))
        
        # Add initial message with offer
        cursor.execute('''
            INSERT INTO messages 
            (id, negotiation_id, sender_id, sender_type, content, type, offer_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"msg-{int(datetime.now().timestamp() * 1000)}",
            negotiation_id,
            BUYER_ID,
            "buyer",
            request.message or f"I'd like to offer ${request.offer_amount:.2f} for this item.",
            "offer",
            request.offer_amount
        ))
        
        conn.commit()
        conn.close()

        #call agent webhook
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:10001/webhook/message",
                json={
                    "negotiation_id": negotiation_id,
                    "sender_id": BUYER_ID,
                    "content": request.message or f"I'd like to offer ${request.offer_amount:.2f} for this item.",
                    "offer_amount": request.offer_amount
                }
            )
        
        return {"status": "success", "negotiation_id": negotiation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/negotiations/{negotiation_id}/messages")
async def send_message(negotiation_id: str, request: SendMessageRequest):
    """Send a message or offer in an existing negotiation."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify negotiation exists and buyer owns it
        cursor.execute(
            "SELECT * FROM negotiations WHERE id = ? AND buyer_id = ?",
            (negotiation_id, BUYER_ID)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Not authorized")
        
        cursor.execute('''
            INSERT INTO messages 
            (id, negotiation_id, sender_id, sender_type, content, type, offer_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"msg-{int(datetime.now().timestamp() * 1000)}",
            negotiation_id,
            BUYER_ID,
            "buyer",
            request.content,
            request.type,
            request.offer_amount
        ))
        
        if request.type == "offer":
            cursor.execute(
                "UPDATE negotiations SET last_offer_amount = ?, status = 'pending' WHERE id = ?",
                (request.offer_amount, negotiation_id)
            )
        
        conn.commit()
        conn.close()

        #call agent webhook
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:10001/webhook/message",
                json={
                    "negotiation_id": negotiation_id,
                    "sender_id": BUYER_ID,
                    "content": request.content,
                    "offer_amount": request.offer_amount
                }
            )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/negotiations/{negotiation_id}/accept")
async def buyer_accept_negotiation(negotiation_id: str):
    """Buyer accepts the current seller counter offer."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE negotiations SET status = 'accepted', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND buyer_id = ?",
            (negotiation_id, BUYER_ID)
        )
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "action": "accepted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/listings")
async def create_listing(
    name: str = Query(...),
    description: str = Query(...),
    price: float = Query(...),
    seller_id: str = Query(...),
    image: bytes = None
):
    """Create a listing endpoint that accepts query parameters."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO listings (name, description, price, seller_id, image)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        name,
        description,
        price,
        seller_id,
        image
    ))

    conn.commit()
    listing_id = cursor.lastrowid
    conn.close()

    return {"status": "success", "id": f"listing-{listing_id}"}

@app.exception_handler(Exception)
async def exception_handler(request, exc):
    """Catch and log all exceptions."""
    import traceback
    print(f"Exception: {exc}", file=sys.stderr)
    traceback.print_exc()
    raise

# ============ SELLER ENDPOINTS ============

@app.get("/api/seller/{seller_id}/negotiations")
async def get_seller_negotiations(seller_id: str, status: str = "all"):
    """Get all negotiations for a seller."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = "SELECT * FROM negotiations WHERE seller_id = ?"
        params = [seller_id]
        
        if status != "all":
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY updated_at DESC"
        
        cursor.execute(query, params)
        negotiations = cursor.fetchall()
        conn.close()
        
        return [dict(n) for n in negotiations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seller/{seller_id}/negotiations/{negotiation_id}")
async def get_seller_negotiation(seller_id: str, negotiation_id: str):
    """Get full negotiation details for seller."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM negotiations 
            WHERE id = ? AND seller_id = ?
        ''', (negotiation_id, seller_id))
        
        negotiation = cursor.fetchone()
        if not negotiation:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        cursor.execute('''
            SELECT * FROM messages 
            WHERE negotiation_id = ? 
            ORDER BY timestamp ASC
        ''', (negotiation_id,))
        
        messages = cursor.fetchall()
        conn.close()
        
        result = dict(negotiation)
        result['messages'] = [dict(m) for m in messages]
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/seller/{seller_id}/negotiations/{negotiation_id}/respond")
async def seller_respond_to_offer(
    seller_id: str, 
    negotiation_id: str,
    response: SellerOfferResponse
):
    """Seller accepts, rejects, or counters an offer."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM negotiations WHERE id = ? AND seller_id = ?",
            (negotiation_id, seller_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Not authorized")
        
        status = response.action if response.action != "counter" else "counter"
        cursor.execute(
            "UPDATE negotiations SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, negotiation_id)
        )
        
        if response.action == "counter":
            cursor.execute('''
                INSERT INTO messages 
                (id, negotiation_id, sender_id, sender_type, content, type, offer_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"msg-{int(datetime.now().timestamp() * 1000)}",
                negotiation_id,
                seller_id,
                "seller",
                response.message or f"I can do ${response.counter_amount:.2f}",
                "counter_offer",
                response.counter_amount
            ))
            
            cursor.execute(
                "UPDATE negotiations SET last_offer_amount = ? WHERE id = ?",
                (response.counter_amount, negotiation_id)
            )
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "negotiation_id": negotiation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/seller/{seller_id}/negotiations/{negotiation_id}/message")
async def seller_send_message(
    seller_id: str,
    negotiation_id: str,
    request: SellerMessageRequest
):
    """Seller sends a regular message."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages 
            (id, negotiation_id, sender_id, sender_type, content, type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            f"msg-{int(datetime.now().timestamp() * 1000)}",
            negotiation_id,
            seller_id,
            "seller",
            request.content,
            request.type
        ))
        
        conn.commit()
        conn.close()
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/seller/{seller_id}/negotiations/{negotiation_id}/accept")
async def seller_accept_offer(seller_id: str, negotiation_id: str):
    """Seller accepts the current buyer offer."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE negotiations SET status = 'accepted', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND seller_id = ?",
            (negotiation_id, seller_id)
        )
        
        conn.commit()
        conn.close()
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/seller/{seller_id}/negotiations/{negotiation_id}/reject")
async def seller_reject_offer(seller_id: str, negotiation_id: str):
    """Seller rejects the current buyer offer."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE negotiations SET status = 'rejected', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND seller_id = ?",
            (negotiation_id, seller_id)
        )
        
        conn.commit()
        conn.close()
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seller/{seller_id}/unread-count")
async def get_unread_count(seller_id: str):
    """Get count of unread messages for seller."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM messages 
            WHERE negotiation_id IN (
                SELECT id FROM negotiations WHERE seller_id = ?
            ) AND read_by_seller = FALSE
        ''', (seller_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return {"unread_count": result['count'] if result else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/listing")
async def get_listing():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM listings")
        listings = cursor.fetchall()
        conn.close()

        return listings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8050)
