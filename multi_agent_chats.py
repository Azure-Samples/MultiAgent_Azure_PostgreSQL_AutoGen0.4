from pg_utils import PostgresChain
import warnings
warnings.filterwarnings("ignore")
from autogen_agentchat.conditions import TextMentionTermination
# from autogen_agentchat.ui import Console
from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat, MagenticOneGroupChat
from agent_tools import create_user_proxy, create_schema_agent, create_shipment_agent, init_client, initiate_planner_agent, create_customer_agent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage
from typing import Sequence

class GroupChat():
    def __init__(self, connection_pool):
        self.pool = connection_pool
        self.shipment_chain = PostgresChain(connection_pool)
        self.customer_chain = PostgresChain(connection_pool)
        self.client = init_client()
        self.schema_agent = create_schema_agent(self.client, self.shipment_chain)
        self.shipment_agent = create_shipment_agent(self.client, self.shipment_chain)
        self.customer_agent = create_customer_agent(self.client, self.customer_chain)
        self.plannning_agent = initiate_planner_agent(self.client)
        self.user_proxy = create_user_proxy()
        self.termination = TextMentionTermination("bye")

        print("Agents and required resources initialized successfully")

    async def init_magentic(self,init_task):
        team = MagenticOneGroupChat(
        [self.schema_agent, self.shipment_agent, 
         self.customer_agent, self.user_proxy],
         model_client=self.client,
        termination_condition=self.termination,
        final_answer_prompt="Do not end the chat until the human says so.",
        )
        fin_message = await self.run_group_chat(team, init_task)
        print(fin_message)
        
    async def init_roundrobin(self,init_task):
        team = RoundRobinGroupChat(
        [self.schema_agent, self.shipment_agent, 
         self.customer_agent, self.user_proxy],
        termination_condition=self.termination
        )
        fin_message = await self.run_group_chat(team, init_task)
        print(fin_message)

    async def init_selector(self,init_task):
        team = SelectorGroupChat(
            [self.plannning_agent,self.schema_agent, 
             self.customer_agent, self.shipment_agent,
             self.user_proxy],
             model_client=self.client,
             selector_func= self.selector_func,
             termination_condition=self.termination,
             allow_repeated_speaker = True
        )
        fin_message = await self.run_group_chat(team, init_task)
        print(fin_message)

    def selector_func(self, messages: Sequence[AgentEvent | ChatMessage]) -> str | None:
        # defines the sequential communication flow between agents
        if messages[-1].source == "user" or messages[-1].source == "user_proxy":
            # Planning agent should be the first to engage when given a new task, or check progress.
            return "planning_agent"
        return None

    async def run_group_chat(self, team, init_task):
        await team.reset() # remove this if you want agents to keep history
        message_count = 0
    
        async for message in team.run_stream(task=init_task):
            if not isinstance(message, TaskResult):
                print(f"\n-- {message_count+1}:{message.source} -- : {message.content}")
                message_count += 1

        print(f"Total messages exchanged: {message_count}")

        return "Conversation ended."
    async def close_connection(self):
        try:
            self.shipment_chain.__close__()
            self.customer_chain.__close__(pool=True)

            print("Connections pool closed successfully")
        except Exception as e:
            print(f"Error closing connections: {e}")
        
        print("You need to create a new instance of the class to use the service again!")
    

    