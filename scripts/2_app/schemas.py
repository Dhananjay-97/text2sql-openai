from typing import Literal
from pydantic import BaseModel, Field
from typing import Dict, List


class SessionData(BaseModel):
    data: Dict
    filename: str


class DatabaseConfig(BaseModel):
    """Configuration model for database connection parameters."""

    db_name: str


class Conversation(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ConversationHistory(BaseModel):
    history: list[Conversation] = Field(
        default_factory=lambda: [{"role": "assistant", "content": ""}]
    )


class CombinedRequest(BaseModel):
    query: str  # Query to retrieve database information
    unique_id: str  # Unique ID for file handling and directory structuring
    conversation_history: ConversationHistory


class QueryRequest(BaseModel):
    query: str
    db_config: DatabaseConfig


class QueryExplain(BaseModel):
    query: str
