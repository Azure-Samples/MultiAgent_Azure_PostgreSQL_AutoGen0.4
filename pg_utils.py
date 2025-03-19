from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os
from dotenv import load_dotenv
import asyncio
import nest_asyncio
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_core.models import UserMessage
import json  # Import json module to convert data to JSON string

# Load environment variables from the .env file from the same directory as notebook 
load_dotenv()

# Retrieve environment variables
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_DB = os.getenv('POSTGRES_DB')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')

class Question(BaseModel):
    question: str


class PostgresChain():
    def __init__(self):
        self.conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB
        )

        self.llm = AzureOpenAIChatCompletionClient(
        azure_deployment=AZURE_OPENAI_DEPLOYMENT,
        model="gpt-4",
        api_version="2024-12-01-preview",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY
        )
        #self.schema = self.get_schema_info()

    async def get_schema(self) -> str:
        schema = await self.get_schema_info()
        return schema

    def __close__(self):
        self.conn.close()
    async def get_schema_info(self) -> str:

        try: 
            with open('schema.json', 'r') as f:
                schema = json.load(f)
                return schema
        except:
            query = """
            SELECT
                cols.table_schema,
                cols.table_name,
                cols.column_name,
                cols.data_type,
                cols.is_nullable,
                cons.constraint_type,
                cons.constraint_name,
                fk.references_table AS referenced_table,
                fk.references_column AS referenced_column
            FROM information_schema.columns cols
            LEFT JOIN information_schema.key_column_usage kcu
                ON cols.table_schema = kcu.table_schema
                AND cols.table_name = kcu.table_name
                AND cols.column_name = kcu.column_name
            LEFT JOIN information_schema.table_constraints cons
                ON kcu.table_schema = cons.table_schema
                AND kcu.table_name = cons.table_name
                AND kcu.constraint_name = cons.constraint_name
            LEFT JOIN (
                SELECT
                    rc.constraint_name,
                    kcu.table_name AS references_table,
                    kcu.column_name AS references_column
                FROM information_schema.referential_constraints rc
                JOIN information_schema.key_column_usage kcu
                    ON rc.unique_constraint_name = kcu.constraint_name
            ) fk
                ON cons.constraint_name = fk.constraint_name
            WHERE cols.table_schema = 'public'
            ORDER BY cols.table_schema, cols.table_name, cols.ordinal_position;
            """
            schema_cur = self.conn.cursor()
            schema_cur.execute(query)
            columns = [desc[0] for desc in self.cur.description]
            rows = schema_cur.fetchall()
            self.conn.commit()
            # Convert the result to a list of dictionaries
            schema_info = [dict(zip(columns, row)) for row in rows]
            with open('schema.json', 'w') as f:
                json.dump(schema_info, f)
            return json.dumps(schema_info, indent=2)
 
    async def nl2query(self, user_q: str):
    # Generate SQL query from natural language question
        q = Question(question=user_q)
        prompt = f"Translate the following natural language question to a postgresql query syntax without any prefix: {q.question} ensure the query adheres with following schema: {self.schema}. Make sure conditions are not case sensitive."
        messages = [
        UserMessage(content=prompt, source="user"),
        ]
        response = await self.llm.create(messages=messages)

        sql_query = response.content
        return sql_query
    async def execute_query(self, query: str) -> list:
        # Execute the SQL query against PostgreSQL
        query_cursor = self.conn.cursor()
        query_cursor.execute(query)
        result = query_cursor.fetchall()
        self.conn.commit()
        return result


    # # Method to add a new customer to the CRM database
    # def add_customer(self, parameters: dict) -> str:
    #     # Begin a transaction
    #     try:
    #         # Prepare the parameter placeholders
    #         param_placeholders = ', '.join([f":{k}" for k in parameters.keys()])
    #         # Construct the SQL command to execute the stored procedure
    #         self.cur.callproc("add_customer", param_placeholders)
    #         # Return a success message
    #         self.conn.commit()
    #         return "Customer added successfully."
    #     except Exception as e:
    #         self.conn.rollback()
    #         return f"An error occurred while executing the stored procedure: {e}"

    # # Method to create a new shipment in the shipment database
    # def send_shipment(self,procedure_name, parameters):

    #     try:
    #         # If 'items' is a list, convert it to JSON string
    #         if isinstance(parameters.get('items'), list):
    #             parameters['items'] = json.dumps(parameters['items'])
    #         # Prepare the parameter placeholders
    #         param_placeholders = ', '.join([f":{k}" for k in parameters.keys()])
    #         # Construct the SQL command
    #         self.cur.callproc(procedure_name, param_placeholders)
    #         # Commit the transaction
    #         self.conn.commit()
    #         return "Shipment sent successfully."
    #     except Exception as e:
    #         self.conn.rollback()
    #         return f"An error occurred while executing the stored procedure: {e}"



# if __name__ == "__main__":
#     # nest_asyncio.apply()
#     pg = PostgresChain()
#     print(pg.schema)
#     query = asyncio.run(pg.nl2query("Which products with names are currently tracking in transit?"))
#     print(query)
#     print(asyncio.run(pg.execute_query(query)))
