'''
Adapter between A2A protocol and Tetsy agent logic.
'''

#TODO: Implement AgentExecuter interface required by a2a-sdk
'''
It receives A2A requests (like send_message, get_task, stream_message) from the server (__main__.py) 
and translates them into calls to your agent's methods defined in agent.py (e.g., ainvoke, astream).
It then formats the agent's response back into the A2A protocol format.
'''