from pydantic import BaseModel
from psycopg2 import pool
import pwinput
import asyncio
from typing import Dict
import os
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_core.models import UserMessage
import json  # Import json module to convert data to JSON string
from dotenv import load_dotenv
load_dotenv(override=True)

# Retrieve environment variables
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_DB = os.getenv('POSTGRES_DB')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')


class Question(BaseModel):
    question: str

def init_pool(pw):
    # Initialize connection pool
    connection_pool = pool.SimpleConnectionPool(
        1, 20,  # minconn, maxconn
        user=os.getenv('POSTGRES_USER'),
        password=pw,
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        database=os.getenv('POSTGRES_DB')
    )
    return connection_pool

class PostgresChain():
    def __init__(self, connection_pool):

        self.llm = AzureOpenAIChatCompletionClient(
        azure_deployment=AZURE_OPENAI_DEPLOYMENT,
        model="gpt-4",
        api_version="2024-12-01-preview",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY
        )
        self.conn = connection_pool.getconn()
        self.pool = connection_pool

    def __close__(self, pool=False):
        self.pool.putconn(self.conn)
        if pool:
            self.pool.closeall()


    async def get_schema_info(self) -> str:
        print("Getting schema")
        try:
            with open('schema.json', 'r') as f:
                schema = await json.load(f)
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
            columns = [desc[0] for desc in schema_cur.description]
            rows = schema_cur.fetchall()
            schema_cur.close()
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
        try:
            query_cursor = self.conn.cursor()
            query_cursor.execute(query)
            if query.startswith("DELETE"):
                result = ["Delete operation successful"]
            else:
                result = query_cursor.fetchall()
            self.conn.commit()
            query_cursor.close()
            return result
        except Exception as e:
            self.conn.rollback()
            return [e]
        
    async def exec_add_customer(self, procedure_name: str, input_vals: list) -> str:

        try:
            cursor = self.conn.cursor()
            values = input_vals
            param_placeholders = ', '.join(['%s'] * len(values))
            sql_command = f"CALL {procedure_name}({param_placeholders});"

            cursor.execute(sql_command, tuple(values))
            cursor.close()
            self.conn.commit()
            return "Customer added successfully."

        except Exception as e:
            self.conn.rollback()
            return f"An error occurred while executing the stored procedure: {e}"
        
    async def exec_send_shipment(self, procedure_name: str, input_vals: list) -> str:
        try:
            cursor = self.conn.cursor()
            # If 'items' is a list, convert it to JSON string
            values =[]
            for item in input_vals:
                if isinstance(item, list):
                    item = json.dumps(item)
                    values.append(item)
                else:
                    values.append(item)

            # Define the parameter placeholders for the stored procedure
            param_placeholders = ', '.join([
                '%s::INTEGER',  # customer_id
                '%s::INTEGER',  # origin_id
                '%s::INTEGER',  # destination_id
                '%s::DATE',     # shipment_date
                '%s::JSONB',    # items
                '%s::VARCHAR',  # status
                '%s::VARCHAR',  # tracking_status
                '%s::INTEGER'   # location_id
            ])

            # Construct the SQL command
            sql_command = f"CALL {procedure_name}({param_placeholders});"

            # Execute the stored procedure
            cursor.execute(sql_command, tuple(values))
            cursor.close()
            self.conn.commit()
            return f"Shipment sent successfully."
        except Exception as e:
            print(e)
            self.conn.rollback()
            return f"An error occurred while executing the stored procedure: {e}"

# if __name__ == "__main__":

    # pg = PostgresChain()
    # a= asyncio.run(pg.exec_send_shipment("send_shipment", 
    #                                      [11, 1, 2, date(2023, 10, 1),[{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 3}],
    #                                       "in transit", "in transit", 1]))
    # print(a)
    # pg.__close__(pool=True)
    # print("connections closed succssfully")