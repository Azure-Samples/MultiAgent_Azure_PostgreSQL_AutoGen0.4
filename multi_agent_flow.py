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
}

client = ChatCompletionClient.load_component(llm_config)

async def init_agent_chats(init_task):
    # customer_chain = PostgresChain() #TBD
    # product_chain = PostgresChain() #TBD
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

    


    text_termination = TextMentionTermination("bye")
    team = MagenticOneGroupChat([user_proxy, schema_agent,shipment_agent],
                            model_client=client,
                            max_turns=1,
                            termination_condition=text_termination,
                            final_answer_prompt="simplify the results for the user and provide the final answer.")

    await Console(team.run_stream(task=init_task))

    shipment_chain.__close__()

    print("connections closed succssfully")


if __name__ == "__main__":

    asyncio.run(init_agent_chats("Which products with names are currently tracking in transit?"))
