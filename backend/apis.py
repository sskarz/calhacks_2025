import asyncio
import base64
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


@app.post("/api/process-image-upload")
async def process_image_upload(image: UploadFile = File(...)):
    """Process image upload from step 1"""
    print(f"Image uploaded: {image.filename}")
    print(f"Content type: {image.content_type}")
    return {"message": "Image received", "filename": image.filename}


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
