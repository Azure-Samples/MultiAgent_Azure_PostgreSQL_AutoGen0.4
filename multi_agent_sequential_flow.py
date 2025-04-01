from pg_utils import PostgresChain
import warnings
warnings.filterwarnings("ignore")
from agent_tools import create_user_proxy, create_schema_agent, create_shipment_agent, init_client, initiate_planner_agent, create_customer_agent
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
    return None

async def init_sequential_group_chat(init_task, connection_pool):
    # Initialize connection pool

    shipment_chain = PostgresChain(connection_pool)
    customer_chain = PostgresChain(connection_pool)

    client = init_client()
    
    plannning_agent = initiate_planner_agent(client)
    schema_agent = create_schema_agent(client, shipment_chain)
    shipment_agent = create_shipment_agent(client, shipment_chain)
    customer_agent = create_customer_agent(client, customer_chain)
    user_proxy = create_user_proxy()


    termination = TextMentionTermination("bye")
    team = SelectorGroupChat(
        [plannning_agent,schema_agent, customer_agent, shipment_agent, user_proxy],
        model_client=client,
        selector_func= selector_func,
        termination_condition=termination,
    )

    await Console(team.run_stream(task=init_task))

    shipment_chain.__close__()
    customer_chain.__close__(pool=True)
    print("connections closed succssfully")

    return True

    