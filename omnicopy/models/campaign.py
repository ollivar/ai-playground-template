"""
Because the Campaign class describes how a campaign is stored in the database.
It doesn't need to know anything about API routes, HTTP requests, or application startup.
"""

# LAYER 1: Database Models
"""
Notice that this file knows nothing about FastAPI endpoints.
It only defines the database model.
Key concept: A database model represents persistent data, not the API that exposes it
"""
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class Campaign(SQLModel, table=True):
    campaign_id: int | None = Field(default=None, primary_key=True)

    name: str = Field(index=True)

    due_date: datetime | None = Field(default=None, index=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=True, index=True
    )
