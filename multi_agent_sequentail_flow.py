from pg_utils import PostgresChain
import warnings
warnings.filterwarnings("ignore")
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
from autogen_agentchat.messages import AgentEvent, ChatMessage
from autogen_agentchat.teams import SelectorGroupChat
from typing import Sequence

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

# Method to add a new customer to the CRM database
def add_customer(procedure_name, parameters):
    from sqlalchemy import text
    with crm_db._engine.connect() as connection:
        trans = connection.begin()  # Begin a transaction
        try:
            # Prepare the parameter placeholders
            param_placeholders = ', '.join([f":{k}" for k in parameters.keys()])
            # Construct the SQL command to execute the stored procedure
            sql_command = text(f"CALL {procedure_name}({param_placeholders})")
            # Pass parameters as a dictionary
            result = connection.execute(sql_command, parameters)
            # Commit the transaction
            trans.commit()
            # Return a success message
            return "Customer added successfully."
        except Exception as e:
            trans.rollback()
            return f"An error occurred while executing the stored procedure: {e}"
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

    #user_proxy = UserProxyAgent("user_proxy", description="Provide results to user in a consice and clear manner.") 

    shipment_agent = AssistantAgent(name="shipment_agent",
                                    model_client=client,
                                    description="Retrieves information from the shipment database.",
                                    tools=[FunctionTool(name="shipment_query", func= shipment_chain.execute_query, description= "runs postgres query on shipment database")],
                                    system_message=(
                                "Your role is to query the database using 'shipment_query'."
                                # "Use 'get_shared_schema_info' from schema_agent to retrieve schema information."
                                "PostgreSQL query should adhere to the schema iformation"
                                "Focus on the shipments tables and ensure that all shipments are tracked correctly."
                                "Conditions in query should not be case sensitive."
                                )
                                )
                                        
    schema_agent = AssistantAgent(name="schema_agent",
                                  model_client=client,
                                  description="Understands and shares database schema information.",
                                  tools=[FunctionTool(name="get_schema", func = shipment_chain.get_schema_info, description="Retrieves the database schema and shares it"),
                                         FunctionTool(name="get_shared_schema_info", func = get_shared_schema_info, description="Retrieves the shared schema information")],
                                    system_message=(
                                            "Your role is to retrieve and understand the database schema and referential integrity constraints."
                                            "Only use 'get_schema' to retrieve schema information and share schema with the next agent."
                                        ),
          )
    concierge_agent = AssistantAgent(name="concierge_agent",
                                    model_client=client,
                                    description="Provides final answer to user",
                                    system_message=(
                                        "Your role is to simplify the results for the user and provide the final answer. Only provide results after shipment_agent has completed its task."
                                    ),
                                )
           
    def get_user_input(dummy_var):
        return input("Ask a question or type 'bye' to end the conversation:")
    user_proxy = UserProxyAgent("user_proxy", 
                                description="Interact with user",
                                input_func = get_user_input)

    def selector_func(messages: Sequence[AgentEvent | ChatMessage]) -> str | None:
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

    res = asyncio.run(init_agent_chats(q))
    # print(res)
