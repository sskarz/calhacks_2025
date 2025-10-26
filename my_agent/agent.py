from google.adk.agents.llm_agent import Agent
from google.adk.agents.llm_agent import LlmAgent

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

tetsy_agent = Agent(
    name="tetsy_agent",
    model='gemini-2.5-flash', # Can be a string for Gemini or a LiteLlm object
    description="Provides ecommerence tasks for the ecommerence site Tetsy.",
    instruction=
    """
    You are a helpful emcommernce assistant. ",
    When the user ask to do postings, the do the post_Listing_test function
    When the user ask to get price, then to the get_Price_test function
    tools=[post_Listing_test], # Pass the function directly
    """,
    tools = [get_Price_test, post_Listing_test],
)

#=============================

root_agent = LlmAgent(
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




