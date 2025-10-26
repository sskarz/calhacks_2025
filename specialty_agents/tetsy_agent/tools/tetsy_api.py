'''
Implementation of Tetsy API tool for the Tetsy agent.

'''
import os
import logging
import httpx # Library to make HTTP requests
from dotenv import load_dotenv

load_dotenv() # Load .env file from the tetsy_agent directory
logger = logging.getLogger(__name__)

TETSY_BACKEND_URL = os.getenv("TETSY_BACKEND_API_URL", "http://localhost:8050/api") # Default if not set in .env

# --- Tool to post a listing ---
async def post_listing_to_tetsy(name: str, description: str, price: float) -> dict:
    """
    Posts a new product listing to the Tetsy platform backend.

    Args:
        name: The name of the product.
        description: A description of the product.
        price: The price of the product.

    Returns:
        A dictionary containing the result (e.g., listing ID) or an error.
    """
    logger.info(f"Posting to Tetsy: {name}, Price: {price}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TETSY_BACKEND_URL}/listings", # Your Tetsy backend endpoint
                json={"name": name, "description": description, "price": price}
            )
            response.raise_for_status() # Raise error for bad status codes (4xx, 5xx)
            result = response.json()
            logger.info(f"Tetsy posting successful: {result}")
            return {"status": "success", "listing_id": result.get("id"), "details": result}
        except httpx.RequestError as e:
            logger.error(f"HTTP error posting to Tetsy: {e}")
            return {"status": "error", "message": f"Network error connecting to Tetsy backend: {e}"}
        except httpx.HTTPStatusError as e:
            logger.error(f"Tetsy backend returned error: {e.response.status_code} - {e.response.text}")
            return {"status": "error", "message": f"Tetsy backend error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            logger.error(f"Unexpected error during Tetsy post: {e}", exc_info=True)
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}

# --- Tool to check notifications ---
async def check_tetsy_notifications(listing_id: str) -> dict:
    """
    Checks for notifications for a specific listing on Tetsy.

    Args:
        listing_id: The ID of the listing to check.

    Returns:
        A dictionary containing notification details or an error.
    """
    logger.info(f"Checking Tetsy notifications for listing: {listing_id}")
    async with httpx.AsyncClient() as client:
        try:
            # Assume your Tetsy backend has an endpoint like this
            response = await client.get(f"{TETSY_BACKEND_URL}/listings/{listing_id}/notifications")
            response.raise_for_status()
            notifications = response.json()
            logger.info(f"Tetsy notifications retrieved: {notifications}")
            return {"status": "success", "notifications": notifications}
        except httpx.RequestError as e:
            logger.error(f"HTTP error checking Tetsy notifications: {e}")
            return {"status": "error", "message": f"Network error connecting to Tetsy backend: {e}"}
        except httpx.HTTPStatusError as e:
             logger.error(f"Tetsy backend returned error on notification check: {e.response.status_code} - {e.response.text}")
             return {"status": "error", "message": f"Tetsy backend error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            logger.error(f"Unexpected error checking Tetsy notifications: {e}", exc_info=True)
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}