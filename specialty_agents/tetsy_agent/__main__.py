from google.adk.a2a.utils.agent_to_a2a import to_a2a
from .agent import root_agent

a2a_app = to_a2a(root_agent, port=10001)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(a2a_app, host='0.0.0.0', port=10001)