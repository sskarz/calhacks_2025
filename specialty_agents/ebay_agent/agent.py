from google.adk.tools import FunctionTool
from google.adk.agents.llm_agent import Agent
import httpx

async def publish_to_ebay(name: str, description: str, price: float, quantity: int = 1, brand: str = "Generic") -> str:
    """Publish a new listing to eBay. The product image is automatically set to a Pixel phone image."""
    import logging
    import io
    logger = logging.getLogger(__name__)

    logger.info(f"Publishing to eBay: name={name}, description={description}, price={price}, quantity={quantity}, brand={brand}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Step 1: Publish to eBay external service
            response = await client.post(
                "http://localhost:8001/publish",
                params={
                    "name": name,
                    "description": description,
                    "price": str(price),
                    "quantity": str(quantity),
                    "brand": brand
                    # image_url intentionally omitted - backend will use default Pixel image
                }
            )
            logger.info(f"eBay Response status: {response.status_code}")
            logger.info(f"eBay Response text: {response.text}")
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                # Step 2: Save to local database
                try:
                    # Create a placeholder image for database
                    placeholder_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

                    files = {
                        'image': ('placeholder.png', io.BytesIO(placeholder_image), 'image/png')
                    }
                    data = {
                        'title': name,
                        'description': description,
                        'platform': 'eBay',
                        'price': str(price),
                        'status': 'active',
                        'quantity': str(quantity)
                    }

                    db_response = await client.post(
                        "http://localhost:8000/api/add_item",
                        data=data,
                        files=files
                    )
                    logger.info(f"Database save status: {db_response.status_code}")
                    if db_response.status_code == 200:
                        logger.info("Successfully saved to database")
                    else:
                        logger.warning(f"Database save failed: {db_response.text}")
                except Exception as db_error:
                    logger.error(f"Error saving to database: {db_error}")
                    # Don't fail the whole operation if database save fails

                return f"Successfully published listing to eBay!\n\nDetails:\n- Title: {name}\n- Price: ${price}\n- Quantity: {quantity}\n- Brand: {brand}\n- Listing ID: {result.get('listing_id')}\n- Sandbox URL: {result.get('sandbox_url')}\n\nYou can view the listing at: {result.get('sandbox_url')}"
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

When the user asks to list or publish something to eBay, you MUST call this tool with:
- name: the product name/title (e.g., "Google Pixel 10 Pro 256GB Gray")
- description: a detailed product description based on the product specifications
- price: the price as a float in USD (use market research or reasonable pricing)
- quantity: the available quantity (default: 1)
- brand: the product brand (extract from user input, e.g., "Google")

For example, if the user says "List Pixel 10 pro 256 gb gray google", you should:
1. Extract: name="Google Pixel 10 Pro 256GB Gray", brand="Google", quantity=1
2. Create a compelling description highlighting the storage (256GB) and color (Gray)
3. Set a reasonable market price (e.g., $899.99 for a flagship phone)
4. Call publish_to_ebay with these parameters

The product image is automatically set by the system - you do NOT need to provide an image URL.

Always call the tool when asked to publish or list something.''',
    tools=[
        FunctionTool(publish_to_ebay),
    ],
)
