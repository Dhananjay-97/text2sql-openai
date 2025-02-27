def describe_get_info_from_database(schema_string) -> dict:
    return {
        "type": "function",
        "function": {
            "name": "get_info_from_database",
            "description": """Answer the question based on the database schema.
            Only use tables from provided info and if not available, ask the user for more information.
            Argument should be a fully formed SQL query.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": f"""SQL query extracting info from the database to answer the user's question.
                        The relevant information is as follows:
                        {schema_string}
                        The query should be returned in string format as a single command.
                        """,
                    }
                },
                "required": ["query"],
            },
        },
    }
