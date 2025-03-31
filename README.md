# **Multi-Agent AI System with AutoGen 0.4 and Azure PostgreSQL**


## Follow below steps to set up:

- Ensure Python version is **3.11.9**
- Install all packages in **requirements.txt**
    - pip install -r requirements.txt
- You need an Azure account with:
  - **Azure OpenAI Service** (GPT-4 deployed). 
  - **Azure Database for PostgreSQL** (configured with necessary tables via provided SQL_Queries.sql)
    - You can use the provided helper file called db_util.py to set up your db. Just ensure to update .env file with your own credentials.

## Multi-agent group chat with a **planner agent**
Provides a sequential multi-agent human-in-loop flow for answering user's question from the database.

**to test:**
- python test_with_planner.py

## Multi-agent group chat in a **roundrobin fashion**
Provides a sequential multi-agent human-in-loop flow for answering user's question from the database.

**to test:**
- python test_with_roundrobin.py

### Any issues? please report and reach out!