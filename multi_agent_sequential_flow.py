from pg_utils import PostgresChain
import warnings
warnings.filterwarnings("ignore")
import asyncio
from agent_tools import create_user_proxy, create_concierge_agent, create_schema_agent, create_shipment_agent, init_client
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage
from autogen_agentchat.teams import SelectorGroupChat
from typing import Sequence


def selector_func(messages: Sequence[AgentEvent | ChatMessage]) -> str | None:
    # defines the sequential communication flow between agents
    if messages[-1].source == "user":
        print("Calling schema agent")
        return "schema_agent"
    if messages[-1].source == "schema_agent":
        print("Calling shipment agent")
        return "shipment_agent"
    if messages[-1].source == "shipment_agent":
        return "concierge_agent"
    if messages[-1].source == "concierge_agent":
        print(messages[-1].content)
        print("Calling user proxy")
        return "user_proxy"
    return None
async def init_sequential_group_chat(init_task):

    shipment_chain = PostgresChain()

    client = init_client()

    schema_agent = create_schema_agent(client, shipment_chain)
    shipment_agent = create_shipment_agent(client, shipment_chain)
    concierge_agent = create_concierge_agent(client)
    user_proxy = create_user_proxy()

    termination = TextMentionTermination("bye")
    # text_termination = TextMentionTermination("bye")
    team = SelectorGroupChat(
        [schema_agent, shipment_agent, concierge_agent, user_proxy],
        model_client=client,
        selector_func=selector_func,
        termination_condition=termination,
    )

    stream = team.run_stream(task=init_task)
    message_l = [] 
    async for messages in stream:
        message_l.append(messages)

    shipment_chain.__close__()
    print("connections closed succssfully")

    return message_l

if __name__ == "__main__":
    q = "Is Alice Johnson a customer?"

    final_res = asyncio.run(init_sequential_group_chat(q))
    print(final_res)
    
