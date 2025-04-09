from pg_utils import PostgresChain
import warnings
warnings.filterwarnings("ignore")
from agent_tools import create_user_proxy, create_schema_agent, create_shipment_agent, init_client, create_customer_agent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console




async def init_magentic_group_chat(init_task, connection_pool, close_pool):

    shipment_chain = PostgresChain(connection_pool)
    customer_chain = PostgresChain(connection_pool)

    client = init_client()
    
    #plannning_agent = initiate_planner_agent(client)
    schema_agent = create_schema_agent(client, shipment_chain)
    shipment_agent = create_shipment_agent(client, shipment_chain)
    customer_agent = create_customer_agent(client, customer_chain)
    user_proxy = create_user_proxy()
                                  


    termination = TextMentionTermination("bye")
    team = MagenticOneGroupChat(
        [schema_agent, shipment_agent, 
         customer_agent, user_proxy],
         model_client=client,
        termination_condition=termination,
        final_answer_prompt="Simplify final answer.",
    )

    await Console(team.run_stream(task=init_task))

    shipment_chain.__close__()
    customer_chain.__close__(close_pool)
    print("connections closed succssfully")

    return True

    