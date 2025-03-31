from pg_utils import PostgresChain
import warnings
warnings.filterwarnings("ignore")
import asyncio
from agent_tools import create_user_proxy, create_schema_agent, create_shipment_agent, init_client, initiate_planner_agent, create_customer_agent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from typing import Sequence



async def init_roundrobin_group_chat(init_task):

    shipment_chain = PostgresChain()
    customer_chain = PostgresChain()

    client = init_client()
    
    #plannning_agent = initiate_planner_agent(client)
    schema_agent = create_schema_agent(client, shipment_chain)
    shipment_agent = create_shipment_agent(client, shipment_chain)
    customer_agent = create_customer_agent(client, customer_chain)
    user_proxy = create_user_proxy()
                                  


    termination = TextMentionTermination("bye")
    team = RoundRobinGroupChat(
        [schema_agent, shipment_agent, 
         customer_agent, user_proxy],
        termination_condition=termination
    )

    await Console(team.run_stream(task=init_task))

    shipment_chain.__close__()
    customer_chain.__close__(pool=True)
    print("connections closed succssfully")

    return True

if __name__ == "__main__":
    q = "how many items are in transit?"

    final_res = asyncio.run(init_roundrobin_group_chat(q))

    