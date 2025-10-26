from google.adk.tools import FunctionTool
from google.adk.agents.llm_agent import Agent
import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def post_listing_to_tetsy(name: str, description: str, price: float, image_url: Optional[str] = None, seller_id: str = "Tetsy") -> str:
    """Post a new listing to Tetsy.
    
    Use this when asked to create or post a new product listing.
    
    Args:
        name: The product name/title
        description: Detailed product description
        price: The asking price as a float (e.g., 1000.00)
        image_url: URL or file path to product image (optional)
        seller_id: The seller ID (defaults to 'Tetsy')
    
    Returns:
        Success message with listing details
    """
    logger.info(f"Posting listing: name={name}, description={description}, price=${price}")

    async with httpx.AsyncClient() as client:
        try:
            # Call the agent-specific endpoint with JSON body
            response = await client.post(
                "http://localhost:8050/api/agent/listings",
                json={
                    "name": name,
                    "description": description,
                    "price": price,
                    "seller_id": seller_id,
                    "image_url": image_url
                }
            )
            logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            return f"Successfully posted listing '{name}' at ${price} to Tetsy"
        except Exception as e:
            logger.error(f"Error posting listing: {e}")
            raise

async def respond_to_negotiation(negotiation_id: str, response_type: str, seller_id: str = "Tetsy", counter_offer: Optional[float] = None, message: Optional[str] = None) -> str:
    """Respond to a buyer's negotiation offer.
    
    DECISION LOGIC:
    - ACCEPT if: buyer offer >= 85% of the asking price
    - COUNTER if: buyer offer < 85% of asking price, counter at 90% of asking price
    - REJECT if: buyer is not serious or offer is insulting
    
    Args:
        negotiation_id: The negotiation ID to respond to
        response_type: One of 'accept', 'reject', or 'counter'
        seller_id: The seller ID (defaults to 'Tetsy')
        counter_offer: Required if response_type is 'counter' - the counter-offer amount
        message: Optional message to include with the response
    
    Returns:
        Confirmation of the response sent
    """
    logger.info(f"Responding to negotiation {negotiation_id}: action={response_type}, counter=${counter_offer if counter_offer else 'N/A'}")
    
    async with httpx.AsyncClient() as client:
        try:
            if response_type == "accept":
                endpoint = f"http://localhost:8050/api/seller/{seller_id}/negotiations/{negotiation_id}/respond"
                response = await client.post(
                    endpoint,
                    json={
                        "action": "accept",
                        "message": message or "Great! I accept your offer. Let's complete the transaction."
                    }
                )
            elif response_type == "reject":
                endpoint = f"http://localhost:8050/api/seller/{seller_id}/negotiations/{negotiation_id}/respond"
                response = await client.post(
                    endpoint,
                    json={
                        "action": "reject",
                        "message": message or "Thank you for your interest, but I cannot accept this offer."
                    }
                )
            elif response_type == "counter":
                if counter_offer is None:
                    raise ValueError("counter_offer amount is required for counter response")
                endpoint = f"http://localhost:8050/api/seller/{seller_id}/negotiations/{negotiation_id}/respond"
                response = await client.post(
                    endpoint,
                    json={
                        "action": "counter",
                        "counter_amount": counter_offer,
                        "message": message or f"I appreciate your offer. I can do ${counter_offer:.2f}"
                    }
                )
            else:
                raise ValueError(f"Invalid response_type: {response_type}. Must be 'accept', 'reject', or 'counter'")
            
            logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            return f"Successfully {response_type} negotiation {negotiation_id}"
        except Exception as e:
            logger.error(f"Error responding to negotiation: {e}")
            raise

async def respond_to_message(negotiation_id: str, message: str, seller_id: str = "Tetsy") -> str:
    """Respond to a buyer's general message (not a price offer).
    
    Use this for answering questions about the item, shipping, condition, etc.
    Do NOT use this for price negotiations - use respond_to_negotiation instead.
    
    Args:
        negotiation_id: The negotiation ID to respond to
        message: Your response message to the buyer
        seller_id: The seller ID (defaults to 'Tetsy')
    
    Returns:
        Confirmation that message was sent
    """
    logger.info(f"Sending message to negotiation {negotiation_id}")
    
    async with httpx.AsyncClient() as client:
        try:
            endpoint = f"http://localhost:8050/api/seller/{seller_id}/negotiations/{negotiation_id}/respond"
            response = await client.post(
                endpoint,
                json={
                    "action": "message",
                    "message": message
                }
            )
            
            logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            return f"Successfully sent message to negotiation {negotiation_id}"
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

root_agent = Agent(
    model='gemini-2.5-flash',
    name='tetsy_agent',
    description='Tetsy seller agent that manages listings and negotiates with buyers',
    instruction='''You are a professional Tetsy seller agent representing the "Tetsy" seller account.

YOUR RESPONSIBILITIES:
1. Create new product listings when requested
2. Respond to buyer negotiations intelligently
3. ALWAYS use a tool to respond - do NOT just chat

CRITICAL: You MUST call a tool for EVERY buyer message:
- If buyer mentions a price/offer: use respond_to_negotiation tool
- If buyer asks questions/general message: use respond_to_message tool
- If creating a listing: use post_listing_to_tetsy tool

NEGOTIATION STRATEGY:
- Extract the asking price and buyer's offer from the context provided
- ACCEPT: If buyer offers 85% or more of the asking price
- COUNTER: If buyer offers less than 85%, counter at 90% of asking price
- REJECT: Only if the buyer is clearly unrealistic or disrespectful

GUIDELINES:
- ALWAYS use a tool - never just respond with text
- Always be professional and courteous
- Try to close the deal when possible
- Provide clear reasoning for counter-offers
- Don't negotiate below 80% of asking price
- Respond promptly to messages

TOOL USAGE (MANDATORY):
1. For price offers: respond_to_negotiation(negotiation_id, response_type, counter_offer, message) - if there is a price offer prioritize this tool
2. For questions: respond_to_message(negotiation_id, message)
3. For new listings: post_listing_to_tetsy(name, description, price)

You must call ONE of these tools with every buyer message - no exceptions.''',
    tools=[
        FunctionTool(post_listing_to_tetsy),
        FunctionTool(respond_to_negotiation),
        FunctionTool(respond_to_message),
    ],
)
