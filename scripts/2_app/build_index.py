import json
import os
from pathlib import Path

import faiss

from constants import INDEX_DIR
from utils.index import FAISSIndex
from utils.lock import acquire_lock
from utils.logging import log
from utils.oai import OAIEmbedding


def create_faiss_vector(data, unique_id):
    index_persistent_path = Path(INDEX_DIR) / unique_id
    index_persistent_path = index_persistent_path.resolve().as_posix()
    lock_path = index_persistent_path + ".lock"
    log("Index path: " + os.path.abspath(index_persistent_path))

    with acquire_lock(lock_path):
        if os.path.exists(os.path.join(index_persistent_path, "index.faiss")):
            log("Index already exists, bypassing index creation")
            return index_persistent_path
        else:
            if not os.path.exists(index_persistent_path):
                os.makedirs(index_persistent_path)

        log("Building index")

        segments = split_metadata(data)

        log(f"Number of segments: {len(segments)}")

        index = FAISSIndex(index=faiss.IndexFlatL2(1536), embedding=OAIEmbedding())
        index.insert_batch(segments)

        index.save(index_persistent_path)

        log("Index built: " + index_persistent_path)
        return index_persistent_path


def split_metadata(data):
    """Splits metadata JSON into individual table schemas with table comments and column details."""
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON input") from e

    db_schema = []
    for table_name, metadata in data_dict.items():
        # Extract table comments
        table_comments = metadata.get("table_comments", "No comments available")

        table_comments = table_comments.replace("\n", " ").replace("\\n", " ")

        # Ensure columns data is present and valid
        columns = metadata.get("columns")
        if not isinstance(columns, list):
            raise ValueError(f"Columns metadata for table {table_name} is not a list")

        # Remove '\n' from 'column_comments' key
        for column in columns:
            if "column_comments" in column:
                column["column_comments"] = column["column_comments"].replace("\n", " ")

        # Convert columns list to JSON string
        columns_json = json.dumps(columns)

        # Format the schema string
        table_schema = (
            f"table_name: {table_name}, "
            f"table_comments: {table_comments}, "
            f"columns_schema: {columns_json}"
        )
        db_schema.append(table_schema)

    return db_schema
