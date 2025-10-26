'''
Define the Core and Capability of Tetsy specialty agent.
'''


import os
import logging
from google.adk.agents import Agent # Or LangGraph, etc.
from google.adk.models import Gemini # Or another model provider

# --- A2A SDK Imports ---
from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol

# --- Import the ACTUAL tool functions ---
from .tools.tetsy_api import post_listing_to_tetsy, check_tetsy_notifications

logger = logging.getLogger(__name__)


def create_tetsy_agent_card(host: str = "0.0.0.0", port: int = 10001) -> AgentCard:
    """
    Create the A2A AgentCard for the Tetsy Agent.
    
    Args:
        host: The host the agent server is running on
        port: The port the agent server is running on
    
    Returns:
        AgentCard: The card describing this agent to the A2A protocol
    """
    app_url = os.environ.get('APP_URL', f'http://{host}:{port}')
    
    skill = AgentSkill(
        id='tetsy_posting',
        name='Post to Tetsy',
        description='Creates product listings on the Tetsy platform.',
        tags=['tetsy', 'listing', 'e-commerce'],
        examples=['Post my blue scarf on Tetsy for $20'],
    )
    
    capabilities = AgentCapabilities(streaming=False)
    
    agent_card = AgentCard(
        name='Tetsy Agent',
        description='Handles posting listings and checking notifications specifically for Tetsy.',
        url=app_url,
        version='1.0.0',
        capabilities=capabilities,
        skills=[skill],
        defaultInputModes=[TransportProtocol.http_json],
        defaultOutputModes=[TransportProtocol.http_json],
    )
    
    return agent_card


# --- Function to create the Tetsy Agent instance ---
def create_tetsy_agent() -> Agent:
    """Constructs the ADK agent specifically for Tetsy tasks."""
    llm_model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

    # --- The System Prompt (Instructions) ---
    tetsy_instructions = """
    **Role:** You are a specialized agent for the Tetsy platform.
    **Goal:** Your ONLY job is to post new listings and check notifications on Tetsy using the provided tools.
    **Tools:**
    * `post_listing_to_tetsy`: Use this to create a new product listing. You need item name, description, and price.
    * `check_tetsy_notifications`: Use this to check for updates (like sales or offers) on a specific listing ID.
    **Rules:**
    * ONLY use the provided tools. Do not make up information or try to perform actions you don't have tools for.
    * If you need more information (e.g., missing price), ask the user clearly.
    * Confirm success or failure after using a tool.
    """

    return Agent(
        model=Gemini(model=llm_model_name), # Configure the LLM
        name='TetsyAgent',
        description='An agent that posts listings and checks notifications on the Tetsy platform.',
        instruction=tetsy_instructions, # Set the specific instructions
        # --- List the tools this agent can use ---
        tools=[
            post_listing_to_tetsy,
            check_tetsy_notifications,
        ],
    ) # Analogous to 