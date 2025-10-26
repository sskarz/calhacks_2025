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

ebay_agent = RemoteA2aAgent(
    name='ebay_agent',
    agent_card='http://localhost:10002/.well-known/agent-card.json',
)

#=============================


#=============================

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="Tells the current time in a specified city and ecommerce agent",
    instruction=
    """
    You are a helpful assistant that checks time in specific cities and does ecommerce tasks and actions for Tetsy and nothing else.
      You are a helpful assistant that tells the current time in cities. Use the 'get_current_time' tool for this purpose.
      Follow these steps:

      1. When you receive an image description and product details, format the given information in json format.
      If the user wants to do posting, first check which store/website they are referencing.
      If they are referencing Tetsy, delegate the task to tetsy_agent.
      If they are referencing Ebay, delegate the task to ebay_agent.
      If they want to do both then delegate the task to tetsy_agent and ebay_agent.
      Make sure to give the agents the json file.
      Write back to the user to show the results of the json you generated + what you chose.

      2. If the user states any other website other than Tetsy or Ebay, then tell them you cannot do that.

      3. If the user asks for the time, use the get_current_time function.
      4. If the user asks anything other than the above please state what you do.
      Always clarify the results before proceeding.

    """,

    sub_agents=[tetsy_agent, ebay_agent],
    tools=[get_current_time],
)

