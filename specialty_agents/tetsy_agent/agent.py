from google.adk.tools import FunctionTool
from google.adk.agents.llm_agent import Agent
import httpx

async def post_listing_to_tetsy(name: str, description: str, price: float) -> str:
    """Post a new listing to Tetsy."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Posting listing: name={name}, description={description}, price={price}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8050/api/listings",
                params={"name": name, "description": description, "price": str(price)}
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

root_agent = Agent(
    model='gemini-2.5-flash',
    name='tetsy_agent',
    description='Posts listings to Tetsy',
    instruction='''You are a Tetsy listing agent. Your job is to help users post listings on Tetsy.

You have ONE tool available: post_listing_to_tetsy(name, description, price)

When the user asks to post something, you MUST call this tool with:
- name: the item name
- description: the item description  
- price: the price as a float

Always call the tool when asked to post a listing. Extract the name, description, and price from the user's request and pass them to the tool.''',
    tools=[
        FunctionTool(post_listing_to_tetsy),
        FunctionTool(check_tetsy_notifications),
    ],
)
