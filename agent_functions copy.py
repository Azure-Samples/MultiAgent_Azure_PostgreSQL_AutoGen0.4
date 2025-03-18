from pg_utils import PostgresChain

import asyncio
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool, BaseTool
from pydantic import BaseModel
from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.conditions import ExternalTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.teams import Swarm


from dotenv import load_dotenv
# Load environment variables from the .env file from the same directory as notebook 
load_dotenv()
import os

AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')


# def retrieve_schema(db_chain: PostgresChain) -> str:
#     schema_info = db_chain.schema
#     return schema_info
# async def query_shipment(db_chain: PostgresChain, query: str) -> list:
#     #sql_query = db_chain.nl2query(query)
#     return await db_chain.execute_query(query)
# def get_schema_from_agent(agent) -> str:
#     schema_info = get_schema_info(db_chain)
#     agent.schema_info = schema_info
#     return "Schema information retrieved and stored."

def get_shared_schema_info():
    if schema_agent.schema_info is None:
        schema_agent.get_schema()
    return schema_agent.schema_info


llm_config = {
    "provider": "AzureOpenAIChatCompletionClient",
    "config": {
        "model": "gpt-4",
        "azure_endpoint": AZURE_OPENAI_ENDPOINT,
        "azure_deployment": AZURE_OPENAI_DEPLOYMENT,
        "api_version" : "2024-12-01-preview",
        "api_key": AZURE_OPENAI_KEY,
        "seed": 42}
    
    # "functions": [
    #     {
    #         "name": "query_shipment",
    #         "description": "Queries the Shipment database based on the provided query",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "query": {"type": "string", "description": "The SQL query to execute on the shipment database"},
    #                 "db_chain": {"type": "object", "description": "The PostgresChain object to run the query on"}
    #             },
    #             "required": ["query", "db_chain"]
    #         }
    #     },

    #     {
    #         "name": "retrieve_schema",
    #         "description": "Retrieves the database schema and referential integrity information. Only use 'retrieve_schema' to retrieve schema information and store it. Do not do anything else",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "db_chain": {"type": "object", "description": "The PostgresChain object to retrieve the schema from"}
    #             },
    #             "required": ["db_chain"]
    #         }
    #     },

    # ]
}

client = ChatCompletionClient.load_component(llm_config)

async def init_agent_chats(init_task):
    # customer_chain = PostgresChain()
    # product_chain = PostgresChain()
    shipment_chain = PostgresChain()

    user_proxy = UserProxyAgent("user_proxy", description="Provide results to user in a consice and clear manner.") 

    shipment_agent = AssistantAgent(name="shipment_agent",
                                    model_client=client,
                                    description="Retrieves information from the shipment database.",
                                    tools=[FunctionTool(name="shipment_query", func= shipment_chain.execute_query, description= "runs postgres query on shipment database")],
                                    system_message=(
                                "Your role is to query the database using 'shipment_query'."
                                "Use 'get_shared_schema_info' from schema_agent to retrieve schema information."
                                "PostgreSQL query should adhere to the schema iformation"
                                "Focus on the shipments tables and ensure that all shipments are tracked correctly."
                                "Conditions in query should not be case sensitive.")
                                )
                                        
    schema_agent = AssistantAgent(name="schema_agent",
                                  model_client=client,
                                  description="Understands and shares database schema information.",
                                  tools=[FunctionTool(name="get_schema", func = shipment_chain.get_schema_info, description="Retrieves the database schema and shares it"),
                                         FunctionTool(name="get_shared_schema_info", func = get_shared_schema_info, description="Retrieves the shared schema information")],
                                    system_message=(
                                            "Your role is to retrieve and understand the database schema and referential integrity constraints."
                                            "Only use 'get_schema' to retrieve schema information and store it. Share schema information with other agents."
                                        ),
          )       

    # modify_agent = AssistantAgent(name="modify_chain",
    #                            model_client=modify_chain.llm,
    #                            description="Adds a customer to the CRM database by executing the 'add_customer' stored procedure with the provided parameters.",
    #                            tools=[FunctionTool(modify_chain.add_customer, description="Adds a customer to database by executing the 'add_customer' stored procedure")],
    #                            system_message=(
    #                               "Your role is to add new records to customers table. Use the 'add_customer' function to call the appropriate stored procedure for adding new customers."
    #                               "Do nothing if the ask is not to insert a new record."
    #                               "take schema info of database into account."
    #                               "have human to validate the operation before making it."),
    #                     )

    


    text_termination = TextMentionTermination("bye")
    team = MagenticOneGroupChat([user_proxy, schema_agent,shipment_agent],
                            model_client=client,
                            max_turns=1,
                            termination_condition=text_termination,
                            final_answer_prompt="simplify the results for the user and provide the final answer.")

    await Console(team.run_stream(task=init_task))

    shipment_chain.__close__()
    # modify_chain.__close__()
    print("connections closed succssfully")


if __name__ == "__main__":
    #start_task = input("enter your question: ")

    asyncio.run(init_agent_chats("Which products with names are currently tracking in transit?"))

    # a= asyncio.run(pg.ask_question(q))
    # print(a)