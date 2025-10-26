from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import httpx

# Load environment variables from .env file
load_dotenv()

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from .agent import root_agent

# Create A2A app (this becomes the main app)
a2a_app = to_a2a(root_agent, port=10001)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(a2a_app, host='0.0.0.0', port=10001)