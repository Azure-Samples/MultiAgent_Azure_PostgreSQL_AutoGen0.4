import psycopg2
import os
from dotenv import load_dotenv
load_dotenv(override=True)

# Retrieve environment variables
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_DB= os.getenv('POSTGRES_DB')

def execute_sql_file(cursor, sql_file_path):
    with open(sql_file_path, 'r') as file:
        sql = file.read()
        print(f"Executing SQL file: {sql_file_path}")
        print(sql)  # Debug print to verify the content of the SQL file
        try:
            cursor.execute(sql)
        except Exception as e:
            print(f"Error executing SQL file: {e}")
        


if __name__ == "__main__":

    try:
        # Establish the connection
        connection = psycopg2.connect(
            host = POSTGRES_HOST,
            database = POSTGRES_DB,
            user = POSTGRES_USER,
            password = POSTGRES_PASSWORD,
            port= POSTGRES_PORT
        )

        # Create a cursor object
        cursor = connection.cursor()
        # Execute a query to verify the setup
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"Successfully Connected to - {db_version}")
    except Exception as error:
        print(f"Error connecting to the database: {error}")


        # Replace with path to the SQL file
        file_path = "SQL_Queries.sql"
    try:
        # Execute the SQL file
        execute_sql_file(cursor, file_path)
        # Commit the changes
        connection.commit()
        # Close the cursor and connection
        cursor.close()
        connection.close()
        print(f"Successfully set up the tables and closed the connection.")
    except Exception as e:
        print(f"Error setting up the tables: {e}")
        # Rollback the changes
        connection.rollback()
        # Close the cursor and connection
        cursor.close()
        connection.close()
        print("Rolled back the changes and closed the connection.")


 