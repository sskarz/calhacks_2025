from google.adk.tools import FunctionTool
from google.adk.agents.llm_agent import Agent
import httpx

async def publish_to_ebay(name: str, description: str, price: float, quantity: int = 1, brand: str = "Generic") -> str:
    """Publish a new listing to eBay."""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Publishing to eBay: name={name}, description={description}, price={price}, quantity={quantity}, brand={brand}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "http://localhost:8001/publish",
                params={
                    "name": name,
                    "description": description,
                    "price": str(price),
                    "quantity": str(quantity),
                    "brand": brand
                }
            )
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response text: {response.text}")
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                return f"Successfully published listing to eBay!\n\nDetails:\n- Title: {name}\n- Price: ${price}\n- Quantity: {quantity}\n- Listing ID: {result.get('listing_id')}\n- Sandbox URL: {result.get('sandbox_url')}\n\nYou can view the listing at: {result.get('sandbox_url')}"
            else:
                return f"Failed to publish listing: {result.get('error', 'Unknown error')}\n{result.get('message', '')}"
        except Exception as e:
            logger.error(f"Error publishing to eBay: {e}")
            raise

root_agent = Agent(
    model='gemini-2.5-flash',
    name='ebay_agent',
    description='Publishes listings to eBay',
    instruction='''You are an eBay listing agent. Your job is to help users publish listings on eBay.

You have ONE tool available: publish_to_ebay(name, description, price, quantity, brand)

When the user asks to publish something to eBay, you MUST call this tool with:
- name: the product name/title
- description: the product description
- price: the price as a float (in USD)
- quantity: the available quantity (default: 1)
- brand: the product brand (default: "Generic")

Always call the tool when asked to publish a listing. Extract the name, description, price, quantity, and brand from the user's request and pass them to the tool.''',
    tools=[
        FunctionTool(publish_to_ebay),
    ],
)
