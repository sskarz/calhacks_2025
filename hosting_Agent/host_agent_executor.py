"""
Host Agent Executor - A2A to Google ADK Bridge

This module serves as the critical bridge between:
- A2A Protocol (Agent-to-Agent standard communication)
- Google ADK (Agent Development Kit - the actual agent runtime)

Think of it as a translator that:
1. Receives A2A-formatted requests from external agents
2. Converts them to Google ADK format
3. Executes the ADK agent
4. Converts responses back to A2A format
5. Returns results to the requesting agent
"""

import json
import logging

from typing import TYPE_CHECKING

# ============================================================================
# A2A SERVER IMPORTS - Protocol and task management
# ============================================================================
from a2a.server.agent_execution import AgentExecutor  # Base class for agent executors
from a2a.server.agent_execution.context import RequestContext  # Request metadata wrapper
from a2a.server.events.event_queue import EventQueue  # Async event notification system
from a2a.server.tasks import TaskUpdater  # Updates task status/results

# A2A Protocol types - Standardized data structures for agent communication
from a2a.types import (
    AgentCard,                      # Agent metadata/"business card"
    FilePart,                       # File content in messages
    FileWithBytes,                  # File with raw bytes
    FileWithUri,                    # File with URI reference
    Part,                           # Base message part type
    TaskState,                      # Task status enum (submitted, working, completed, etc.)
    TextPart,                       # Text content in messages
    UnsupportedOperationError,      # Error for unsupported operations
)
from a2a.utils.errors import ServerError  # Server error wrapper

# ============================================================================
# GOOGLE ADK IMPORTS - Agent runtime and AI model interaction
# ============================================================================
from google.adk import Runner  # Executes ADK-based agents with memory/session support
from google.genai import types  # Google's Generative AI type definitions

# ============================================================================
# TRACEABILITY EXTENSION - Debug/monitoring capabilities
# ============================================================================
from traceability_ext import (
    TRACEABILITY_EXTENSION_URI,  # Unique ID for traceability extension
    CallTypeEnum,                # Types of calls (HOST, AGENT, TOOL)
    ResponseTrace,               # Trace container for entire request
    TraceStep,                   # Individual step in the trace
)

# TYPE_CHECKING is only True during static type checking (mypy, etc.)
# This import is only for type hints, not runtime
if TYPE_CHECKING:
    from google.adk.sessions.session import Session

# ============================================================================
# LOGGING SETUP
# ============================================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Verbose logging for development/debugging

# ============================================================================
# CONSTANTS
# ============================================================================
DEFAULT_USER_ID = 'self'  # Default user ID for ADK sessions
                          # (ADK requires a user_id for session management)


# ============================================================================
# MAIN EXECUTOR CLASS
# ============================================================================
class HostAgentExecutor(AgentExecutor):
    """
    An AgentExecutor that runs an ADK-based Agent for host_agent.
    
    This class is the bridge between two worlds:
    - A2A Protocol: Standard agent-to-agent communication
    - Google ADK: Google's agent runtime framework
    
    RESPONSIBILITIES:
    1. Convert A2A requests → ADK format
    2. Execute the ADK agent (your actual AI agent logic)
    3. Stream events back to the client
    4. Convert ADK responses → A2A format
    5. Manage sessions and state
    6. Handle traceability/debugging
    
    ARCHITECTURE POSITION:
    DefaultRequestHandler → HostAgentExecutor → ADK Runner → Your Agent
    """

    def __init__(self, runner: Runner, card: AgentCard):
        """
        Initialize the executor.
        
        Args:
            runner: The ADK Runner that executes your agent
                   (configured with memory, sessions, artifacts)
            card: The AgentCard describing your agent's capabilities
                 (used for metadata and discovery)
        """
        self.runner = runner  # Executes the actual agent logic
        self._card = card     # Agent's "business card"
        
        # Track active sessions for potential cancellation
        # Set of session IDs that are currently processing
        self._active_sessions: set[str] = set()

    async def _process_request(
        self,
        new_message: types.Content,      # User's message in Google ADK format
        session_id: str,                 # Conversation session ID
        task_updater: TaskUpdater,       # Updates task status/results
        response_trace: ResponseTrace = None,  # Optional tracing for debugging
    ) -> None:
        """
        Core method that processes an agent request through the ADK runtime.
        
        This method:
        1. Gets or creates a session for this conversation
        2. Runs the ADK agent (which may call tools, other agents, etc.)
        3. Streams events back as they occur
        4. Handles function calls (like delegating to other agents)
        5. Updates task status as work progresses
        6. Adds tracing information if enabled
        
        Args:
            new_message: The user's message in Google GenAI format
            session_id: Unique ID for this conversation
            task_updater: Interface to update the task in the TaskStore
            response_trace: Optional trace for debugging/monitoring
        """
        # ====================================================================
        # STEP 1: SESSION MANAGEMENT
        # ====================================================================
        # Get existing session or create new one
        # Sessions store conversation history and context
        session_obj = await self._upsert_session(session_id)
        
        # Update session_id with the ID from the resolved session object.
        # (it may be the same as the one passed in if it already exists)
        session_id = session_obj.id

        # Track this session as active (for potential cancellation)
        self._active_sessions.add(session_id)

        try:
            # ================================================================
            # STEP 2: RUN THE ADK AGENT
            # ================================================================
            # run_async() is a generator that yields events as they occur
            # Events include:
            # - Text responses (partial or final)
            # - Function calls (tool usage, agent delegation)
            # - Usage metadata (token counts)
            async for event in self.runner.run_async(
                user_id=DEFAULT_USER_ID,      # User identifier for session
                session_id=session_id,        # Conversation context
                new_message=new_message,      # The actual query/request
            ):
                # Log each event for debugging
                logger.debug(
                    '### Event received: %s',
                    event.model_dump_json(exclude_none=True, indent=2),
                )

                # ============================================================
                # CASE 1: FINAL RESPONSE (Agent is done)
                # ============================================================
                if event.is_final_response():
                    # Convert all parts from Google ADK format → A2A format
                    # Filter out empty parts (no text, file, or inline data)
                    parts = [
                        convert_genai_part_to_a2a(part)
                        for part in event.content.parts
                        if (part.text or part.file_data or part.inline_data)
                    ]

                    # If traceability is enabled, add the trace as final step
                    if response_trace:
                        # Create an "ending" step in the trace
                        with TraceStep(
                            response_trace,
                            CallTypeEnum.HOST,        # This is the host agent
                            name='host_agent',        # Name of this agent
                            parameters={},            # No parameters for ending step
                            requests='',              # No request at this point
                            step_type='ending',       # Type: ending the request
                        ) as ending_step:
                            logger.debug('### Finishing call with ending step')
                            # Record token usage for this step
                            ending_step.end_step(
                                total_tokens=event.usage_metadata.total_token_count,
                            )

                        # Convert trace to dictionary and add as artifact
                        trace_artifact = response_trace.as_dict()
                        logger.debug(
                            '### Exporting trace artifact to response: %s',
                            json.dumps(trace_artifact, indent=2),
                        )

                        # Add trace as a text part in the response
                        # Client can parse this to see the execution trace
                        parts.append(TextPart(text=json.dumps(trace_artifact)))

                    logger.debug('#### Yielding final response: %s', parts)
                    
                    # Send the final response parts to the client
                    await task_updater.add_artifact(parts)

                    # Mark task as completed (final=True means no more updates)
                    await task_updater.update_status(
                        TaskState.completed, final=True
                    )

                    break  # Exit the event loop - we're done
                
                # ============================================================
                # CASE 2: INTERMEDIATE RESPONSE (Agent still thinking/working)
                # ============================================================
                # Check if this event contains function calls
                # If not, it's just a text update we should show to the user
                if not event.get_function_calls():
                    # Convert parts to A2A format
                    parts = [
                        convert_genai_part_to_a2a(part)
                        for part in event.content.parts
                        if (part.text or part.file_data or part.inline_data)
                    ]

                    logger.debug('#### Yielding update response: %s', parts)
                    
                    # Update task status to "working" with the intermediate message
                    # This allows streaming responses to the client
                    await task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            [
                                convert_genai_part_to_a2a(part)
                                for part in event.content.parts
                                if (
                                    part.text
                                    or part.file_data
                                    or part.inline_data
                                )
                            ],
                        ),
                    )
                
                # ============================================================
                # CASE 3: FUNCTION CALLS (Agent calling tools/other agents)
                # ============================================================
                else:
                    logger.debug('#### Event - Function Calls')
                    
                    # Extract information about agent calls
                    # (when this agent delegates to other agents)
                    agent_name = ''
                    agent_query = ''
                    calls = event.get_function_calls()
                    
                    if calls:
                        for call in calls:
                            # Check if this is a delegation to another agent
                            if call.name == 'send_message':
                                agent_name = call.args.get('agent_name')
                                agent_query = call.args.get('task')

                    # If traceability is enabled, record this delegation
                    if response_trace and agent_name:
                        # First, record the "thinking" step where we decided
                        # to call another agent
                        with TraceStep(
                            response_trace,
                            CallTypeEnum.HOST,           # This is the host thinking
                            name='host_agent',           # Host agent name
                            parameters={},               # No special parameters
                            requests=agent_query,        # What we're asking
                            step_type='thinking',        # Type: thinking/reasoning
                        ) as thinking_step:
                            logger.debug(
                                '### Tracing agent call with token: %s',
                                event.usage_metadata.total_token_count,
                            )
                            # Record token usage for the thinking step
                            thinking_step.end_step(
                                total_tokens=event.usage_metadata.total_token_count,
                            )

                        # Then, record the actual agent call
                        with TraceStep(
                            response_trace,
                            CallTypeEnum.AGENT,          # This is an agent call
                            name=agent_name,             # Name of called agent
                            parameters={},               # Parameters for the call
                            requests=agent_query,        # What we're asking
                            step_type='agent_call',      # Type: calling another agent
                        ):
                            logger.debug(
                                '### Tracing agent call for agent: %s',
                                agent_name,
                            )

        finally:
            # ================================================================
            # CLEANUP: Remove from active sessions when done
            # ================================================================
            # This happens whether we completed successfully or encountered an error
            self._active_sessions.discard(session_id)

    async def execute(
        self,
        context: RequestContext,    # Full request context (task_id, message, etc.)
        event_queue: EventQueue,    # Queue for publishing task updates
        response_trace: ResponseTrace = None,  # Optional tracing
    ):
        """
        Main entry point for executing an agent request.
        
        This is called by the DefaultRequestHandler when a new task arrives.
        
        Flow:
        1. Check if traceability extension is requested
        2. Update task status to "working"
        3. Convert A2A message → ADK format
        4. Process the request through the ADK agent
        5. Stream results back to the client
        
        Args:
            context: Full request context including:
                    - task_id: Unique task identifier
                    - context_id: Conversation context ID
                    - message: The user's message (A2A format)
                    - requested_extensions: Extensions the client wants
            event_queue: Queue for publishing task status updates
            response_trace: Optional trace for debugging
        """
        logger.debug('[host_agent] execute called with context: %s', context)
        logger.debug(
            '[host_agent] execute called with context.requested_extensions: %s',
            context.requested_extensions,
        )

        # ====================================================================
        # STEP 1: HANDLE TRACEABILITY EXTENSION
        # ====================================================================
        # Check if the client requested the traceability extension
        # This provides detailed execution traces for debugging
        if TRACEABILITY_EXTENSION_URI in context.requested_extensions:
            # Activate the extension in the response
            context.add_activated_extension(TRACEABILITY_EXTENSION_URI)
            logger.debug(
                '[host_agent] Activated extensions: %s',
                TRACEABILITY_EXTENSION_URI,
            )
            # Initialize the trace object
            response_trace = ResponseTrace()
            logger.debug(
                '[host_agent] Traceability extension activated, initializing trace.'
            )

        # ====================================================================
        # STEP 2: INITIALIZE TASK UPDATER
        # ====================================================================
        # TaskUpdater is our interface to update task status in the TaskStore
        # Run the agent until either complete or the task is suspended.
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        
        # Immediately notify that the task is submitted (if it's a new task)
        if not context.current_task:
            await updater.update_status(TaskState.submitted)
        
        # Update status to "working" - agent is now processing
        await updater.update_status(TaskState.working)
        
        # ====================================================================
        # STEP 3: CONVERT MESSAGE AND PROCESS REQUEST
        # ====================================================================
        # Convert the A2A message format → Google ADK format
        # Then process through the ADK agent
        await self._process_request(
            # Wrap parts in UserContent (ADK's message format)
            types.UserContent(
                parts=[
                    convert_a2a_part_to_genai(part)
                    for part in context.message.parts
                ],
            ),
            context.context_id,  # Session ID for conversation context
            updater,             # Task updater for status updates
            response_trace=response_trace,  # Optional trace
        )
        
        logger.debug('[host_agent] execute exiting')

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        """
        Cancel the execution for the given context.

        NOTE: Currently logs the cancellation attempt as the underlying ADK runner
        doesn't support direct cancellation of ongoing tasks.
        
        In the future, this could:
        - Stop the ADK runner mid-execution
        - Clean up resources
        - Cancel any pending tool/agent calls
        
        Args:
            context: Request context containing the session to cancel
            event_queue: Event queue (unused currently)
            
        Raises:
            ServerError: Always raises UnsupportedOperationError
        """
        session_id = context.context_id
        
        # Check if this session is actually running
        if session_id in self._active_sessions:
            logger.info(
                f'Cancellation requested for active host_agent session: {session_id}'
            )
            # TODO: Implement proper cancellation when ADK supports it
            # For now, just remove from tracking
            self._active_sessions.discard(session_id)
        else:
            logger.debug(
                f'Cancellation requested for inactive host_agent session: {session_id}'
            )

        # Always raise error - cancellation not yet supported
        raise ServerError(error=UnsupportedOperationError())

    async def _upsert_session(self, session_id: str) -> 'Session':
        """
        Retrieves a session if it exists, otherwise creates a new one.

        This is a "get or create" pattern - commonly called "upsert"
        (update or insert).
        
        Sessions store:
        - Conversation history
        - Context/memory
        - Previous turns
        
        This allows multi-turn conversations where the agent remembers
        previous interactions.
        
        Args:
            session_id: Unique identifier for this conversation
            
        Returns:
            Session object (either existing or newly created)
        """
        # Try to get existing session
        session = await self.runner.session_service.get_session(
            app_name=self.runner.app_name,  # App namespace
            user_id=DEFAULT_USER_ID,        # User identifier
            session_id=session_id,          # Session identifier
        )
        
        # If session doesn't exist, create a new one
        if session is None:
            session = await self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                user_id=DEFAULT_USER_ID,
                session_id=session_id,
            )
        
        return session


# ============================================================================
# CONVERSION FUNCTIONS - A2A ↔ Google ADK Format
# ============================================================================
# These functions translate between two different message formats:
# - A2A: Standard agent-to-agent protocol
# - Google ADK (GenAI): Google's internal AI format
# ============================================================================

def convert_a2a_part_to_genai(part: Part) -> types.Part:
    """
    Convert a single A2A Part type into a Google Gen AI Part type.
    
    A2A uses its own Part types (TextPart, FilePart, etc.)
    Google ADK uses types.Part with different internal structure
    
    This function translates from A2A → Google format so the ADK agent
    can understand the message.
    
    Args:
        part: The A2A Part to convert
            Can be: TextPart, FilePart (with URI or bytes)

    Returns:
        The equivalent Google Gen AI Part
        
    Examples:
        TextPart("Hello") → types.Part(text="Hello")
        FilePart(uri="gs://...") → types.Part(file_data=FileData(...))

    Raises:
        ValueError: If the part type is not supported
    """
    # Access the actual part content (A2A wraps parts in a root)
    part = part.root
    
    # ========================================================================
    # CASE 1: TEXT PART
    # ========================================================================
    if isinstance(part, TextPart):
        return types.Part(text=part.text)
    
    # ========================================================================
    # CASE 2: FILE PART
    # ========================================================================
    if isinstance(part, FilePart):
        # Sub-case 2a: File referenced by URI (e.g., gs://bucket/file.jpg)
        if isinstance(part.file, FileWithUri):
            return types.Part(
                file_data=types.FileData(
                    file_uri=part.file.uri,           # Where the file is located
                    mime_type=part.file.mime_type     # File type (image/png, etc.)
                )
            )
        
        # Sub-case 2b: File with raw bytes (embedded in message)
        if isinstance(part.file, FileWithBytes):
            return types.Part(
                inline_data=types.Blob(
                    data=part.file.bytes,             # Raw file data
                    mime_type=part.file.mime_type     # File type
                )
            )
        
        # Unknown file type
        raise ValueError(f'Unsupported file type: {type(part.file)}')
    
    # Unknown part type
    raise ValueError(f'Unsupported part type: {type(part)}')


def convert_genai_part_to_a2a(part: types.Part) -> Part:
    """
    Convert a single Google Gen AI Part type into an A2A Part type.
    
    This is the reverse of convert_a2a_part_to_genai.
    Translates from Google ADK format → A2A format so we can send
    responses back in the standard A2A protocol.
    
    Args:
        part: The Google Gen AI Part to convert
            Can have: text, file_data, inline_data

    Returns:
        The equivalent A2A Part
        
    Examples:
        types.Part(text="Hello") → TextPart(text="Hello")
        types.Part(file_data=...) → FilePart(file=FileWithUri(...))

    Raises:
        ValueError: If the part type is not supported
    """
    # ========================================================================
    # CASE 1: TEXT CONTENT
    # ========================================================================
    if part.text:
        return TextPart(text=part.text)
    
    # ========================================================================
    # CASE 2: FILE REFERENCED BY URI
    # ========================================================================
    if part.file_data:
        return FilePart(
            file=FileWithUri(
                uri=part.file_data.file_uri,        # File location (URI)
                mime_type=part.file_data.mime_type,  # File type
            )
        )
    
    # ========================================================================
    # CASE 3: INLINE FILE DATA (raw bytes)
    # ========================================================================
    if part.inline_data:
        return Part(
            root=FilePart(
                file=FileWithBytes(
                    bytes=part.inline_data.data,           # Raw bytes
                    mime_type=part.inline_data.mime_type,  # File type
                )
            )
        )
    
    # Unknown part type
    raise ValueError(f'Unsupported part type: {part}')


# ============================================================================
# ARCHITECTURE SUMMARY
# ============================================================================
"""
This module is the critical bridge in the A2A architecture:

REQUEST FLOW:
1. External Agent → HTTP Request → DefaultRequestHandler
2. DefaultRequestHandler → HostAgentExecutor.execute()
3. HostAgentExecutor → Converts A2A → Google ADK format
4. HostAgentExecutor → Calls ADK Runner (your agent logic)
5. ADK Runner → Executes agent, may call tools/other agents
6. ADK Runner → Returns events (text, function calls, etc.)
7. HostAgentExecutor → Converts Google ADK → A2A format
8. HostAgentExecutor → Updates TaskStore via TaskUpdater
9. TaskUpdater → Publishes to EventQueue
10. DefaultRequestHandler → Returns HTTP response

KEY RESPONSIBILITIES:
- Format conversion (A2A ↔ ADK)
- Session management (conversation context)
- Event streaming (partial results)
- Traceability (debugging/monitoring)
- Status updates (submitted → working → completed)

WHY THIS EXISTS:
- A2A is a standardized protocol for agent communication
- Google ADK is a specific agent framework
- We need to bridge these two worlds
- This allows A2A agents to use Google's powerful ADK runtime
- Other agents don't need to know we're using ADK internally
"""