"""
Database Configuration and Session Management
---------------------------------------------------
File: omnicopy/db/database.py
This file manages the database connection and sessions.

One subtle detail:
SQLModel must import the table models before create_all() executes, or their tables may not be registered in its metadata.

Key concept: Database configuration should not be scattered throughout your application.
Code that manages database infrastructure should be independent of the business entities that use it.
"""

from sqlmodel import Session, SQLModel, create_engine

from typing import Annotated
from fastapi import Depends

# Define the SQLite database URL and engine - how SQLAlchemy connects to the db
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}  # only needed for SQLite
engine = create_engine(sqlite_url, connect_args=connect_args)  # manage db connectivity


# Create db tables if don't exist
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# Provide a db session
def get_session():
    with Session(engine) as session:
        yield session


# Tells FastAPI how to inject a session into an endpoint function. This is a type alias for convenience.
SessionDep = Annotated[Session, Depends(get_session)]
