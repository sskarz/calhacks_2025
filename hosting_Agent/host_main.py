from python_a2a import A2AServer, agent, skill
from python_a2a.langchain import to_langchain_agent




@agent(

    name = "Seller Agent", 
    description = " Give information to following agents: "
)
class Orchestrator(A2AServer):

    @skill(
        name = "Post to All Platforms",
        desci

    )