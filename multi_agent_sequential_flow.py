from pg_utils import PostgresChain
import warnings
warnings.filterwarnings("ignore")
import asyncio
from agent_tools import create_user_proxy, create_concierge_agent, create_schema_agent, create_shipment_agent, init_client, initiate_planner_agent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from typing import Sequence



def selector_func(messages: Sequence[AgentEvent | ChatMessage]) -> str | None:
    # defines the sequential communication flow between agents
    if messages[-1].source == "user" or messages[-1].source == "user_proxy":
        # Planning agent should be the first to engage when given a new task, or check progress.
        return "planning_agent"
    if messages[-1].source == "concierge_agent":
        # User proxy agent is the last to engage with the user.
        return "user_proxy"
    return None

async def init_sequential_group_chat(init_task):

    shipment_chain = PostgresChain()

    client = init_client()
    
    plannning_agent = initiate_planner_agent(client)
    schema_agent = create_schema_agent(client, shipment_chain)
    shipment_agent = create_shipment_agent(client, shipment_chain)
    concierge_agent = create_concierge_agent(client)
    user_proxy = create_user_proxy()

    selector_prompt = """Select an agent to perform task.

    {roles}

    Current conversation context:
    {history}

    Read the above conversation, then select an agent from {participants} to perform the next task.
    Make sure the 'planning_agent' has assigned tasks before other agents start working.
    Let each agent finish its task and return results before selecting the next agent.
    """

    termination = TextMentionTermination("bye")

    team = SelectorGroupChat(
        [plannning_agent,schema_agent, shipment_agent, concierge_agent, user_proxy],
        model_client=client,
        selector_func= selector_func,
        selector_prompt=selector_prompt,
        termination_condition=termination,
    )

    await Console(team.run_stream(task=init_task))

    shipment_chain.__close__()
    print("connections closed succssfully")

    return True

if __name__ == "__main__":
    q = "Is Alice Johnson a customer?"

    final_res = asyncio.run(init_sequential_group_chat(q))

    