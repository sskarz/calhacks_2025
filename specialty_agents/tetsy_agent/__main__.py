'''
Entry point for the Tetsy specialty agent.
'''


import logging
import os
import click
import uvicorn
from dotenv import load_dotenv

# --- A2A SDK Imports ---
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

# --- Local Imports ---
from .agent import create_tetsy_agent, create_tetsy_agent_card  # Import the agent creation functions
from .agent_executor import TetsyAgentExecutor  # Import the A2A adapter

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 10001  # Specific port for the Tetsy Agent


def main(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """
    Main entry point for the Tetsy Agent server.
    Sets up A2A components and runs the Starlette application.
    """
    try:
        # --- Create the Agent Card ---
        # This card describes the agent to the A2A protocol
        agent_card = create_tetsy_agent_card(host=host, port=port)
        logger.info(f"Agent card created: {agent_card.name}")

        # --- Create the ADK Agent Instance ---
        # This agent has its own LLM, tools, and instructions
        adk_agent = create_tetsy_agent()
        logger.info("ADK Agent created successfully")

        # --- Wire up A2A Components ---
        # Create the executor (handles A2A protocol execution)
        agent_executor = TetsyAgentExecutor()
        logger.info("TetsyAgentExecutor created")

        # Create the request handler (maps A2A requests to executor)
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor, task_store=InMemoryTaskStore()
        )
        logger.info("DefaultRequestHandler created")

        # Create the A2A Starlette application (HTTP server for A2A protocol)
        a2a_app = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )
        logger.info("A2AStarletteApplication created")

        # --- Run the Server ---
        logger.info(f"Starting Tetsy Agent server on {host}:{port}")
        uvicorn.run(a2a_app.build(), host=host, port=port)

    except Exception as e:
        logger.error(f"Failed to start Tetsy Agent server: {e}", exc_info=True)
        raise


# Command line interface setup (using click)
@click.command()
@click.option('--host', default=DEFAULT_HOST, help='Host to bind the server to')
@click.option('--port', default=DEFAULT_PORT, type=int, help='Port to bind the server to')
def cli(host: str, port: int):
    """Start the Tetsy Agent server."""
    main(host, port)


if __name__ == '__main__':
    cli()