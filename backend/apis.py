import asyncio
import base64
import httpx
from fastapi import FastAPI, HTTPException, WebSocket, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
import db

# Load environment variables
load_dotenv()

conn = db.get_db_connection()
db.initialize_db(conn)

app = FastAPI(title="Dashboard Backend API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ListingItem(BaseModel):
    title: str
    description: str
    platform: str
    price: float
    status: str
    quantity: int
    imageSrc: str


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Dashboard Backend API",
        "endpoints": {
            "health": "/health",
            "stream": "/api/stream",
            "add_item": "/api/add_item"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/analyze-product-image")
async def analyze_product_image(image: UploadFile = File(...)):
    """Analyze product image and extract details using Gemini"""
    print(f"Image uploaded for analysis: {image.filename}")
    print(f"Content type: {image.content_type}")

    try:
        # Read the image data
        image_data = await image.read()

        # Encode image to base64 for Gemini
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Use Gemini directly to analyze the image
        import google.generativeai as genai
        import os
        import json

        # Configure Gemini
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Create prompt for product detail extraction
        prompt = """Analyze this product image and extract the following details in JSON format:
        {
            "name": "product name",
            "description": "detailed product description",
            "price": "estimated price in USD (just the number, no currency symbol)",
            "quantity": "1",
            "brand": "brand name if visible, otherwise 'Unknown'"
        }

        Important:
        - For price, provide a reasonable estimate based on the product type and condition
        - For quantity, default to "1" unless multiple items are clearly visible
        - For brand, look for logos, text, or distinctive features
        - Provide a detailed description including color, condition, and notable features

        Return ONLY valid JSON, no additional text."""

        # Send to Gemini
        response = model.generate_content([
            prompt,
            {"mime_type": f"image/{image.content_type.split('/')[-1]}", "data": image_base64}
        ])

        # Parse response
        response_text = response.text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        product_details = json.loads(response_text)
        print(f"Extracted product details: {product_details}")

        return product_details

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text: {response_text}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse product details from image analysis"
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing image: {str(e)}"
        )


# Frontend Endpoints

@app.websocket("/api/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.
    Sends database updates to connected clients.
    """
    await websocket.accept()
    try:
        while True:
            # Create a fresh connection for each iteration
            conn = db.get_db_connection()
            items = db.get_all_items(conn)
            # Convert Row objects to dictionaries and handle binary image data
            items_list = []
            if items:
                for item in items:
                    item_dict = dict(item)
                    # Convert BLOB image to base64 for JSON serialization
                    if item_dict.get('imageSrc') and isinstance(item_dict['imageSrc'], bytes):
                        import base64
                        item_dict['imageSrc'] = base64.b64encode(item_dict['imageSrc']).decode('utf-8')
                    items_list.append(item_dict)
            
            await websocket.send_json(items_list)
            await asyncio.sleep(2)  # Send updates every 2 seconds
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.post("/api/add_item")
async def add_item(
    title: str = Form(...),
    description: str = Form(...),
    platform: str = Form(...),
    price: float = Form(...),
    status: str = Form(...),
    quantity: int = Form(...),
    image: UploadFile = File(...)
):
    """Add a new listing with image upload."""
    try:
        # Read image as bytes
        image_data = await image.read()

        conn = db.get_db_connection()
        db.add_item(
            title=title,
            description=description,
            platform=platform,
            price=price,
            quantity=quantity,
            imageSrc=image_data,
            conn=conn
        )
        return {"message": "Item added successfully", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
