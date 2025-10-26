from google.adk.tools import FunctionTool
from google.adk.agents.llm_agent import Agent
import httpx
from typing import Optional

async def post_listing_to_tetsy(name: str, description: str, price: float, image_url: Optional[str] = None, seller_id: str = "Tetsy") -> str:
    """Post a new listing to Tetsy.
        When the user asks to post something, you MUST call this tool with:
        - name: the item name
        - description: the item description  
        - price: the price as a float
        - seller_id: Tetsy seller (defaults to 'Tetsy')
        - image_url: URL or file path to the product image (optional)
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Posting listing: name={name}, description={description}, price={price}, seller_id={seller_id}, image_url={image_url}")

    async with httpx.AsyncClient() as client:
        try:
            # Build params dict
            params = {"name": name, "description": description, "price": str(price), "seller_id": seller_id}
            if image_url:
                params["image_url"] = image_url
            
            response = await client.post(
                "http://localhost:8050/api/listings",
                params=params
            )
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response text: {response.text}")
            response.raise_for_status()
            return f"Successfully posted listing: {response.json()}"
        except Exception as e:
            logger.error(f"Error posting listing: {e}")
            raise

async def check_tetsy_notifications(listing_id: str) -> str:
    """Check notifications for a listing."""
    return f"Checked listing {listing_id}"

async def respond_to_negotiation(negotiation_id: str, response_type: str, seller_id: str = "Tetsy", counter_offer: Optional[float] = None) -> str:
    """Respond to a buyer's negotiation offer.
    
    Args:
        negotiation_id: The negotiation ID to respond to
        response_type: One of 'accept', 'reject', or 'counter'
        seller_id: The seller ID (defaults to 'Tetsy')
        counter_offer: If response_type is 'counter', provide the counter-offer amount
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Responding to negotiation: {negotiation_id} with {response_type}")
    
    async with httpx.AsyncClient() as client:
        try:
            if response_type == "accept":
                endpoint = f"http://localhost:8050/api/seller/{seller_id}/negotiations/{negotiation_id}/accept"
                response = await client.post(endpoint)
            elif response_type == "reject":
                endpoint = f"http://localhost:8050/api/seller/{seller_id}/negotiations/{negotiation_id}/reject"
                response = await client.post(endpoint)
            elif response_type == "counter":
                if counter_offer is None:
                    raise ValueError("counter_offer amount required for counter response")
                endpoint = f"http://localhost:8050/api/seller/{seller_id}/negotiations/{negotiation_id}/counter"
                response = await client.post(
                    endpoint,
                    json={"counter_offer_amount": counter_offer}
                )
            else:
                raise ValueError(f"Invalid response_type: {response_type}")
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response text: {response.text}")
            response.raise_for_status()
            return f"Successfully {response_type} negotiation {negotiation_id}"
        except Exception as e:
            logger.error(f"Error responding to negotiation: {e}")
            raise

root_agent = Agent(
    model='gemini-2.5-flash',
    name='tetsy_agent',
    description='Manages Tetsy listings and negotiations',
    instruction='''You are a Tetsy seller agent representing "Tetsy" seller. Your job is to:
1. Post new listings using the post_listing_to_tetsy tool
2. Respond to buyer negotiations using the respond_to_negotiation tool

When responding to negotiations:
- If the offer is reasonable (85%+ of asking price), ACCEPT it
- If the offer is low (below 85% of asking price), send a COUNTER offer at 90% of asking price
- If you need to reject, explain why

Always be professional and try to make the sale.

Use the tools appropriately based on what the buyer is asking for.''',
    tools=[
        FunctionTool(post_listing_to_tetsy),
        FunctionTool(check_tetsy_notifications),
        FunctionTool(respond_to_negotiation),
    ],
)
