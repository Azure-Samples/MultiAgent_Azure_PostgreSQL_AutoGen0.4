# **Multi-Agent PostgreSQL Data Management System with AutoGen and Azure PostgreSQL**


<div align="center">
  <img src="https://github.com/mehrsa/MultiAgent_Azure_PostgreSQL_AutoGen0.4/blob/main/Drawing%203.png" alt="Architecture">
</div>

This repository demonstrates how to build a **multi-agent AI system** for managing shipment data stored on an Azure PostgreSQL database. Core technologies used are:

- **AutoGen** for coordinating AI agents in collaborative workflows.
- **Azure OpenAI GPT-4** for intelligent language understanding and generation of SQL queries in PostgreSQL.
- **Azure Database for PostgreSQL** for data storage and querying.

The application showcases a shipping company where agents manage shipments, customer and product information. The main goal of this repository is to illustrate how easy it is to have agents work together to not only answer questions regarding the data, but also help modify the data based on user requirements and even help create and use new stored procedures. It extends the "Chat With Your Data" to "Chat, Act and Code on Your Data". ** We welcome contributions to help make those agents more reliable and under guardrails. Feel free to contribute to more agents as well! **

## **Features**

- 🌐 **Gradio UI**: User-friendly interface for natural language interactions.
- 🤖 **AutoGen Multi-Agent System**: Agents collaborate to handle specific tasks:
  - **SchemaAgent**: Manages database schema retrieval and sharing. It is also allowed to create stored procedures.
  - **ShipmentAgent**: Handles shipment-related queries and updates.
  - **CRMAgent**: Manages customer and product-related data. 
- 🧠 **Azure OpenAI GPT-4**: Generates SQL queries and natural language responses.
- 🛢️ **Azure PostgreSQL**: Stores shipment, customer, and product data.

The system is created in a modular way as below, to make it easier for testing via plug-and-play and also further expansion:
- **pg_utils.py** -> Provides a class and tools for enabling agents to connect to the database and perform various tasks
- **agent_tools.py** -> Has functions for creating required expert agents.
- **multi_agent_chats.py** -> Provides a class to initiate various types of group chats (aka teams). 


## Follow below steps to set up:

- Ensure Python version is **3.11.9**
- Install all packages in **requirements.txt**
    - pip install -r requirements.txt
- You need an Azure account with:
  - **Azure OpenAI Service** (GPT-4 deployed). 
  - **Azure Database for PostgreSQL** (configured with necessary tables via provided SQL_Queries.sql)
    - You can use the provided helper file called db_util.py to set up your db. Just ensure to update .env file with your own credentials.
## Test the system

You can test out the system in two ways:
1. Use the provided notebooks to test with provided examples or your own.
2. Run individual python files for testing each group chat mechanism separately:
  - **SelectorGroupChat**: test_with_planner.py
  - **Roundrobin**: test_with_roundrobin.py
  - **Magentic**: test_with_magentic.py


### Group chats available to test
#### Multi-agent group chat with a **planner agent**
Provides a multi-agent human-in-loop group chat for answering user's question from the database.
This uses a team type called "SelectorGroupChat". A planer agent is defined which is tasked with breaking down the ask to simpler tasks and identifying the right sequence of calling expert agents to execute those. 


#### Multi-agent group chat in a **roundrobin fashion**
Provides a roundrobin multi-agent human-in-loop flow for answering user's question from the database.
In this type of team, agents take turn trying to address the ask considering their expertise. They all share their output message with all other agents in the chat. This is a less managed type of team work, which can work great for simple tasks but can take multiple rounds to resolve more complex asks.


#### Multi-agent group chat using **MagenticOne**[1]
A team that runs a group chat with participants managed by the MagenticOneOrchestrator. This type of team is optimized for managing more complex tasks.

##

#### Any issues? please report and reach out!

##### References
[1] [Magentic-one: A generalist multi-agent system for solving complex tasks](https://arxiv.org/abs/2411.04468)

##### Notes
- New Autogen requires Pydantic version of >=2.10. At the time of developing this code, Langchain's SQLDatabaseChain caused pydantic to throw an error. Due to this, we decided to write a separate helper class to connect to the database and enable agents to read/write.
