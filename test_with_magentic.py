import asyncio
from pg_utils import init_pool   
from multi_agent_chats import GroupChat
import pwinput


if __name__ == "__main__":

    pw = pwinput.pwinput(prompt='Enter your Azure postgreSQL db password: ', mask='*')
    connection_pool = init_pool(pw)
    groupchat = GroupChat(connection_pool)
    q = input("Ask a question: ")  # Get user input for the query

    asyncio.run(groupchat.init_magentic(q))
    asyncio.run(groupchat.close_connection())
