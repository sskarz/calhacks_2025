'''
Adapter between A2A protocol and Tetsy agent logic using the A2A SDK.
This executor handles parsing user requests and calling Tetsy tools directly.
'''

# specialty_agents/tetsy_agent/agent_executor.py

import logging
import re

# --- A2A SDK Imports ---
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message

# --- Local imports ---
from .tools.tetsy_api import post_listing_to_tetsy

logger = logging.getLogger(__name__)


# --- Tetsy Agent Specific Executor ---
class TetsyAgentExecutor(AgentExecutor):
    """
    AgentExecutor implementation for the TetsyAgent.
    Directly calls Tetsy tools based on user requests.
    """

    def __init__(self):
        """
        Initializes the executor.
        """
        logger.info("TetsyAgentExecutor initialized.")

    async def _parse_listing_request(self, query: str) -> dict:
        """
        Parse a user's request to extract listing parameters.
        Looks for patterns like:
        - 'post a listing for "name", description "desc", price X'
        """
        # Try to extract name in quotes
        name_match = re.search(r"for\s+['\"]([^'\"]+)['\"]", query)
        name = name_match.group(1) if name_match else None
        
        # Try to extract description
        desc_match = re.search(r"description\s+['\"]([^'\"]+)['\"]", query)
        description = desc_match.group(1) if desc_match else None
        
        # Try to extract price (number)
        price_match = re.search(r"price\s+([0-9.]+)", query)
        price = float(price_match.group(1)) if price_match else None
        
        return {
            "name": name,
            "description": description,
            "price": price
        }

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """
        Handles A2A execute requests by parsing the message and calling tools.
        
        Args:
            context: Request context containing message and task information
            event_queue: Queue to emit status and result events
        """
        try:
            logger.info(f"TetsyAgentExecutor.execute called")
            
            # Get the task updater - KEY: Use context.task_id not a new task ID!
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            
            # Mark task as submitted if it's new
            if not context.current_task:
                await updater.update_status(TaskState.submitted)
            
            # Mark task as working
            await updater.update_status(TaskState.working)
            
            # Extract user input from context
            query = context.get_user_input()
            logger.info(f"Query: {query[:50]}...")

            # Check what the user is asking for
            response_text = ""
            
            if "post" in query.lower() and "listing" in query.lower():
                # Parse the listing request
                listing_params = await self._parse_listing_request(query)
                
                logger.info(f"Parsed listing params: {listing_params}")
                
                if listing_params["name"] and listing_params["price"] is not None:
                    logger.info(f"Posting listing: {listing_params}")
                    
                    try:
                        # Call the tool directly
                        result = await post_listing_to_tetsy(
                            name=listing_params["name"],
                            description=listing_params.get("description", ""),
                            price=listing_params["price"]
                        )
                        
                        logger.info(f"Tool result: {result}")
                        response_text = f"Successfully posted listing: {result}"
                    except Exception as tool_error:
                        logger.error(f"Error calling post_listing_to_tetsy: {tool_error}", exc_info=True)
                        response_text = f"Error posting listing: {str(tool_error)}"
                else:
                    missing = []
                    if not listing_params["name"]:
                        missing.append("item name")
                    if listing_params["price"] is None:
                        missing.append("price")
                    response_text = f"Could not parse listing details. Missing: {', '.join(missing)}. Please provide: 'item name', description, and price."
            else:
                response_text = f"I can help you post listings on Tetsy. Your request was: {query}"

            logger.info(f"Agent response: {response_text[:100]}...")

            # Add response as artifact
            await updater.add_artifact(
                [TextPart(text=response_text)],
                name="tetsy_response",
                description="Response from Tetsy agent",
            )

            # Complete the task with final=True
            await updater.update_status(TaskState.completed, final=True)

        except Exception as e:
            logger.error(f"Error in TetsyAgentExecutor.execute: {e}", exc_info=True)
            # Emit error status
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await updater.fail(f"Tetsy processing failed: {str(e)}")

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """
        Handles cancellation of a task.
        
        Args:
            context: Request context
            event_queue: Queue for events
        """
        logger.warning("Cancel requested but not implemented for TetsyAgentExecutor")
        raise UnsupportedOperationError(
            "Task cancellation is not supported by TetsyAgentExecutor"
        )