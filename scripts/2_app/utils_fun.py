import re
import sqlite3
from datetime import datetime

import pandas as pd
import tiktoken

import streamlit as st
import tiktoken

user_avatar = "👨‍💻"
assistant_avatar = "🤖"


def display_conversation(conversation_history):
    """Display the conversation history"""

    # Loop over all messages in the conversation
    for message in conversation_history:
        # Change avatar based on the role
        avatar = user_avatar if message["role"] == "user" else assistant_avatar

        # Display the message content
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

            if "api_call_cost" in message:
                st.caption(f"Cost: US${message['api_call_cost']:.5f}")


def clear_conversation():
    """Clear the conversation history."""
    if (
        st.button("🧹 Clear conversation", use_container_width=True)
        or "conversation_history" not in st.session_state
    ):
        st.session_state.conversation_history = []
        st.session_state.total_cost = 0
        st.session_state.total_tokens = 0



def calc_cost(token_usage):
    # https://openai.com/pricing

    return (token_usage["prompt_tokens"] * 0.0010 / 1000) + (
        token_usage["completion_tokens"] * 0.0020 / 1000
    )


def calc_costing(prompt_tokens, completion_tokens):
    # https://openai.com/pricing
    return (prompt_tokens * 0.0010 / 1000) + (completion_tokens * 0.0020 / 1000)


def token_count(token_usage):
    return token_usage["total_tokens"]


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens


def read_sqlite_file(file_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()

    # Get the list of tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Print the contents of each table
    for table_name in tables:

        table_name = table_name[0]

        # Get the data from the table
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()

        # Print the rows (values only)
        for row in rows:
            for value in row:
                return value

    # Close the connection
    conn.close()
