import asyncio
import os
import uuid
import json
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
TETSY_AGENT_URL = os.getenv("TETSY_AGENT_URL", "http://localhost:10001")


async def simple_json_rpc_test():
    """
    Simple test using raw JSON-RPC to see if server responds
    """
    import httpx
    
    user_input = "Please post a listing on Tetsy for a 'Handmade Scarf', description 'Warm and cozy wool scarf', price 35.50"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "execute",
        "params": {"message": user_input},
        "id": str(uuid.uuid4())
    }
    
    print(f"Sending JSON-RPC request to {TETSY_AGENT_URL}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{TETSY_AGENT_URL}/", json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(simple_json_rpc_test())


if __name__ == "__main__":
    asyncio.run(simple_json_rpc_test())