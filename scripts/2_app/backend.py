import json
import logging
import os
import re
from pathlib import Path

import oracledb
from decouple import config
from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database_util import DatabaseIndexing
from find_context import find_context
from function_description import describe_get_info_from_database
from openai import OpenAI
from printer import ColorPrinter as Printer
from prompt_setup import database_query_bot_setup
from rewrite_question import rewrite_question
from schemas import CombinedRequest, DatabaseConfig, QueryRequest, SessionData
from utils_fun import calc_costing, read_sqlite_file

session_dir = "sessions"
os.makedirs(session_dir, exist_ok=True)

# Setup the OpenAI API client with the specified model
MODEL = config("OPENAI_CHAT_MODEL")
client = OpenAI(api_key=config("OPENAI_API_KEY"))

####

# OPENAI_API_KEY = read_sqlite_file("data.sqlite")
# client = OpenAI(api_key=str(OPENAI_API_KEY))

####


current_directory = Path(__file__).parent

# Define and create necessary folders
folders_to_create = ["index"]
for folder_name in folders_to_create:
    folder_path = current_directory / folder_name
    if not folder_path.exists():
        folder_path.mkdir()
        print(f"Folder '{folder_name}' created.")
    else:
        print(f"Folder '{folder_name}' already exists.")

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_database_connection(db_config: DatabaseConfig):
    if not isinstance(db_config, DatabaseConfig):
        raise ValueError("Expected db_config to be an instance of DatabaseConfig")
    user = config(f"{db_config.db_name.upper()}_USER")
    password = config(f"{db_config.db_name.upper()}_PASSWORD")
    dsn = config(f"{db_config.db_name.upper()}_DSN")

    try:
        return oracledb.connect(user=user, password=password, dsn=dsn)
    except oracledb.DatabaseError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to the database: {str(e)}"
        )


# Dependency function to get a DatabaseIndexing instance
def db_dependency(db_config: DatabaseConfig = Depends()):
    conn = create_database_connection(db_config)
    try:
        yield conn
    finally:
        conn.close()


def get_info_from_database(query) -> str:
    try:
        return json.dumps(query)
    except TypeError as te:
        return f"Type error in query: {str(te)}. Please check data types and format."
    except Exception as e:
        return f"Error generating query: {str(e)}. Please try again."


@app.get("/")
async def bot_status():
    return {"status": "SQL Query Bot Running"}


@app.post("/select_database")
async def select_database(db_config: DatabaseConfig = Body(...)):
    """Selects a database based on the user input, establishes a connection."""
    try:
        conn = create_database_connection(db_config)
        db_indexer = DatabaseIndexing(conn)
        database_info = db_indexer.database_schema_info()
        unique_id = json.dumps(database_info)

        return {
            "message": f"Connected to {db_config.db_name} database successfully!",
            "unique_id": unique_id[1:-1],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Function to validate JSON structure.
def validate_json(input_json):
    """Ensure the JSON schema information is valid."""
    try:
        json.loads(json.dumps(input_json))
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON format: " + str(e))


@app.post("/process_and_generate_sql")
async def process_and_generate_sql(request: CombinedRequest):
    """
    Endpoint to retrieve database information based on the query and unique identifier for table
    storage, and then generate SQL from a natural language query using the retrieved schema information.
    """

    rewritten_question = rewrite_question(request.query, request.conversation_history)

    # Iterate backwards through the history to find the last "user" message
    for i in range(len(request.conversation_history.history) - 1, -1, -1):
        conversation = request.conversation_history.history[i]

        if conversation.role == "user":
            conversation.content = rewritten_question  # Update content
            updated = True
            break

    docs = find_context(request.query, f"index/{request.unique_id}")

    # Extract text fields from SearchResultEntity
    results = re.findall(r"text='(.*?)', vector", str(docs))

    try:
        validate_json(results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Convert schema info to string format
    schema_string_json = json.dumps(results, indent=2)

    tools = [describe_get_info_from_database(schema_string_json)]

    # Preparing messages for the API call
    history_dump = [
        {"role": conv.role, "content": conv.content}
        for conv in request.conversation_history.history
    ]
    messages = [{"role": "system", "content": database_query_bot_setup}, *history_dump]

    # Log the messages to see their content
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Messages sent to API: %s", json.dumps(messages, indent=2))

    # Call to AI model to generate SQL query
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.01,
        tools=tools,
        tool_choice={
            "type": "function",
            "function": {"name": "get_info_from_database"},
        },
    )

    # Collect response and process tool calls
    response_message = response.choices[0].message
    messages.append(response_message)

    # # Process tool calls made by the model
    while response_message.tool_calls:
        tool_calls = response_message.tool_calls
        available_functions = {
            "get_info_from_database": get_info_from_database,
        }
        for call in tool_calls:
            func_name: str = call.function.name
            func_to_call = available_functions[func_name]
            func_args: dict = json.loads(call.function.arguments)
            func_response = func_to_call(**func_args)

            messages.append(
                {
                    "tool_call_id": call.id,
                    "role": "tool",
                    "name": func_name,
                    "content": func_response,
                }
            )

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="none",
        )
        response_message = response.choices[0].message

    return {
        "message": response.choices[0].message,
        "token_usage": response.usage,
        "cost": calc_costing(
            response.usage.prompt_tokens, response.usage.completion_tokens
        ),
        "rewritten_query": rewritten_question,
    }


@app.post("/execute_query")
async def execute_query(request: QueryRequest):
    conn = create_database_connection(request.db_config)
    try:
        cursor = conn.cursor()
        cursor.execute(request.query)
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        cursor.close()
        return {"status": "success", "result": result, "columns": column_names}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@app.post("/save_session")
async def save_session(session: SessionData):
    session_path = os.path.join(session_dir, f"{session.filename}.json")
    # session_path = os.path.join(session_dir, session.filename)
    # session_path = session.filename
    try:
        with open(session_path, "w") as file:
            json.dump(session.data, file)
        return {"message": f"Session saved as {session.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list_recent_sessions")
async def list_recent_sessions():
    """
    Endpoint to list the last 10 saved session files based on modification time.
    """
    try:
        # Get list of files in the session directory
        sessions = [f for f in os.listdir(session_dir) if f.endswith(".json")]
        # Sort files by last modified time, in descending order
        sessions.sort(
            key=lambda x: os.path.getmtime(os.path.join(session_dir, x)), reverse=True
        )
        # Select the top 10
        recent_sessions = sessions[:10]
        # Optional: Retrieve metadata from files if needed
        sessions_info = []
        for session in recent_sessions:
            path = os.path.join(session_dir, session)
            with open(path, "r") as file:
                data = json.load(file)
                # Assuming metadata includes a 'timestamp' or other relevant info
                sessions_info.append(
                    {
                        "filename": session,
                        "timestamp": data.get(
                            "timestamp", "Unknown"
                        ),  # Modify as per actual data structure
                    }
                )
        return {"sessions": sessions_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/load_session/{filename}")
async def load_session(filename: str):
    session_path = os.path.join(session_dir, filename)
    try:
        with open(session_path, "r") as file:
            data = json.load(file)
        return {"data": data, "message": f"Session loaded from {filename}"}
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="File not found. Please check the filename and try again.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)

