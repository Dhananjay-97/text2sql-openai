from pathlib import Path
from uuid import uuid4

import oracledb
from fastapi import HTTPException

from build_index import create_faiss_vector
from database_schema import get_db_metadata

current_directory = Path(__file__).parent


class DatabaseIndexing:
    def __init__(self, conn):
        """
        Initializes the Database class with a connection.
        Raises HTTPException if the connection is not established.

        Parameters:
        conn : Connection to the Oracle database.
        """
        if not conn:
            raise HTTPException(
                status_code=500,
                detail="Failed to establish a connection to the database.",
            )
        self.conn = conn

    def close_connection(self):
        """
        Closes the database connection if it is open.
        """
        if self.conn:
            try:
                self.conn.close()
            except oracledb.DatabaseError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to close the database connection: {str(e)}",
                )
            finally:
                self.conn = None

    def switch_connection(self, new_conn):
        """
        Switches the current database connection to a new one.
        Closes the existing connection if it is open before switching.

        Parameters:
        new_conn : New connection to an Oracle database.
        """
        self.close_connection()
        if not new_conn:
            raise HTTPException(
                status_code=500,
                detail="Failed to establish a new connection to the database.",
            )
        self.conn = new_conn

    def create_vec(self, data, unique_id):
        create_faiss_vector(data, unique_id)

    def database_schema_info(self):

        self.unique_id = str(uuid4()).replace("-", "_")
        cursor = self.conn.cursor()

        data = get_db_metadata(cursor)

        schema_metadata_json = data[0]

        lob_data = schema_metadata_json.read()

        self.create_vec(lob_data, self.unique_id)

        cursor.close()
        self.conn.close()
        return self.unique_id
