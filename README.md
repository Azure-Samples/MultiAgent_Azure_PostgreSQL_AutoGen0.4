# **Multi-Agent PostgreSQL Data Management System with AutoGen and Azure PostgreSQL**


<div align="center">
  <img src="https://github.com/mehrsa/MultiAgent_Azure_PostgreSQL_AutoGen0.4/blob/main/Drawing%203.png" alt="Architecture">
</div>


## Follow below steps to set up:

- Ensure Python version is **3.11.9**
- Install all packages in **requirements.txt**
    - pip install -r requirements.txt
- You need an Azure account with:
  - **Azure OpenAI Service** (GPT-4 deployed). 
  - **Azure Database for PostgreSQL** (configured with necessary tables via provided SQL_Queries.sql)
    - You can use the provided helper file called db_util.py to set up your db. Just ensure to update .env file with your own credentials.

## Multi-agent group chat with a **planner agent**
Provides a multi-agent human-in-loop group chat for answering user's question from the database.
This uses a team type called "SelectorGroupChat". A planer agent is defined which is tasked with breaking down the ask to simpler tasks and identifying the right sequence of calling expert agents to execute those. 

**to test:**
- python test_with_planner.py

## Multi-agent group chat in a **roundrobin fashion**
Provides a roundrobin multi-agent human-in-loop flow for answering user's question from the database.
In this type of team, agents take turn trying to address the ask considering their expertise. They all share their output message with all other agents in the chat. This is a less managed type of team work, which can work great for simple tasks but can take multiple rounds to resolve more complex asks.

**to test:**
- python test_with_roundrobin.py

## Multi-agent group chat using **MagenticOne**[1]
A team that runs a group chat with participants managed by the MagenticOneOrchestrator. This type of team is optimized for managing more complex tasks.

**to test:**
- python test_with_magentic.py

### Any issues? please report and reach out!


#### References
[1] [Magentic-one: A generalist multi-agent system for solving complex tasks](https://arxiv.org/abs/2411.04468)
