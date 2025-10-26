from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.llm_agent import Agent

# In your backend server file (e.g., orchestrator.py or a dedicated API file)
from fastapi import FastAPI, UploadFile, File, Form
import base64
import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

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


app = FastAPI()

# Your API endpoint that React calls
@app.post("/process_image_upload")
async def handle_image_upload(
    file: UploadFile = File(...),
    # You might receive other form data too
    user_query: str = Form("Describe this image.")
):
    print(f"Received file: {file.filename}, type: {file.content_type}")

    # --- Read image bytes ---
    image_bytes = await file.read()

    # --- Encode image bytes to base64 ---
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # --- Get the MIME type ---
    mime_type = file.content_type
    if not mime_type:
        # Try to infer or default if not provided
        if file.filename.lower().endswith(".png"):
            mime_type = "image/png"
        elif file.filename.lower().endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
        else:
            mime_type = "application/octet-stream" # Fallback

    # --- Create multimodal input for ADK Agent ---
    user_prompt_with_image_data = Content(
        role="user",
        parts=[
            Part.from_text(user_query),
            # Use Part.from_data for bytes/base64
            Part.from_data(data=image_base64, mime_type=mime_type)
        ]
    )

    # --- Run the ADK Agent (similar to the previous example) ---
    runner = Runner(
        agent=root_agent, # Your defined ADK agent
        session_service=InMemorySessionService()
    )

    print("--- Sending image data prompt to agent ---")
    final_response_text = ""
    async for event in runner.run_async(
        "user_upload_test",
        "session_upload_test",
        content=user_prompt_with_image_data
    ):
        if event.type == "llm_response":
            print(f"Agent interim response: {event.data['text']}")
            final_response_text += event.data['text'] # Collect response chunks
        elif event.type == "tool_response":
             print(f"Tool Result: {event.data['output']}")
             # You might want to add tool results to the final response

    print(f"\nAgent Final Response: {final_response_text}")
    return {"description": final_response_text}


#if __name__ == "__main__":
#    uvicorn.run(app, host="localhost", port=8002)



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
      
      1. If the user submits an image, call handle_image_upload function. 
      Format the given information in json format.
      If the user wants to do posting, first check which store/website they are referencing.
      If they are referencing Tetsy, delegate the task to testy_agent. 
      If they are referencing Ebay, delegate the task to ebay_agent.
      If they want to do both then delegate the task to testy_agent and ebay_agent. 
      Make sure to give the agents the json file.
      Write back to the user to show the adresults of the json you generated + what you chose.
      
      2. If the user states any other website other than Tetsy or Ebay, then tell them you cannot do that.
      
      3. If the user ask for the time, use the get_current_time function.
      4. If the user ask anything other than the above please state what you do.
      Always clarify the results before proceeding.
     
    """,

    sub_agents=[tetsy_agent],
    tools=[get_current_time, handle_image_upload],
)

