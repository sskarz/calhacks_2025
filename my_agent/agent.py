from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.llm_agent import Agent

# Mock tool implementation
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}



#===================================

def get_Price_test():
        
    print("The price is over 90000")


def post_Listing_test() :

    print('listing posted')

#==========================================

tetsy_agent = RemoteA2aAgent(
    name='tetsy_agent',
    agent_card='http://localhost:10001/.well-known/agent-card.json',
)

#=============================

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="Tells the current time in a specified city and emcommerence agent",
    instruction=
    """
    You are a helpful assistant that check time in specific citues  and do ecommerence tasks and actions for Testy and nothing else.
      You are a helpful assistant that tells the current time in cities. Use the 'get_current_time' tool for this purpose." t
      Follow these steps:
      1. If the user wants to do posting and check price to Tetsy, then delegate that to the tetsy_agent. Only if they say from Tetsy
      2. If the user states any other website other than Tetsy, then tell them you cannot do that.
      3. If the user ask for the time, use the get_current_time function.
      4. If the user ask anything other than the above please state what you do.
      Always clarify the results before proceeding.
     
    """,
    sub_agents=[tetsy_agent],
    tools=[get_current_time],
)




