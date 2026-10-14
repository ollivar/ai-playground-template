"""
This is a simple FastAPI application that manages marketing campaigns.
It uses SQLModel for database interactions and provides endpoints to create, read, update, and delete marketing campaign records.

This application currently handles six different responsibilitities:
1. Application initialization: Sets up the FastAPI application with a root path and lifespan event for database initialization.
2. Database configuration: Configures an SQLite database and creates the necessary tables using SQLModel.
3. Database models: Defines the `Campaign` model and its associated Pydantic schemas for creating and updating campaigns.
4. Data validation: Defines CampaignCreate and CampaignUpdate Pydantic models for validating incoming request data.
5. Business Operations: Creates, retrieves, updates, and deletes campaign records in the database.
6. API routing: Exposes endpoints

All of these responsibilities are handled in a single file, which is not ideal for maintainability and scalability.
In a production application, it would be better to separate these concerns into different modules or packages.
Phase 1: Let's create a module for the database models and move the Campaign class there. This will help us keep our code organized and make it easier to manage as our application grows.
Phase 2: Let's create a module for the Pydantic models and move the CampaignCreate and CampaignUpdate classes there.
    Let's separate out the API schemas:
    Key principle: Your database structure and your API contract should be able to evolve independently.
    We will use:
        schemas/campaign.py for campaign-specific API schemas.
        schemas/responses.py for reusable API response schemas.
Phase 3: Let's create a module for the database configuration and session management. This will be super helpful if we switch to Postgres!
    Current implementation:
    main.py
    │
    ├── Creates FastAPI application
    ├── Defines API endpoints
    ├── Performs CRUD operations
    │
    └── Imports database functionality
            │
            ▼
    db/database.py
            │
            ├── Configures SQLite
            ├── Creates database engine
            ├── Creates database tables
            └── Provides database sessions

Phase 4: Extract API Routes Using APIRouter
    This is one of the most important steps in modularizing a FastAPI application.
    Our objective: Move all HTTP endpoints out of main.py and into a dedicated module (api/routes.py) that uses FastAPI's APIRouter.
         - We are not going to change the database models, schemas, or business logic yet.
    Imagine your application grows to include:
        Campaigns
        Users
        Projects
        Tasks
        Reports

    You could easily end up with 50–100 endpoints in main.py! That's difficult to maintain.
    FastAPI solves this using APIRouter.
    New architecture:
    omnicopy/
    │
    ├── api/
    │   ├── __init__.py
    │   └── campaigns.py
    │
    ├── db/
    │   ├── __init__.py
    │   └── database.py
    │
    ├── models/
    │   └── campaign.py
    │
    ├── schemas/
    │   ├── campaign.py
    │   └── responses.py
    │
    ├── services/
    │
    └── main.py
        │
        ├── FastAPI()
        │
        └── include_router()
                │
                ├── campaigns.py
                │    ├── GET    /campaigns
                │    ├── POST   /campaigns
                │    ├── PUT    /campaigns/{id}
                │    └── DELETE /campaigns/{id}
                │
                ├── users.py
                │
                └── reports.py

Phase 5 — Extract Business Logic into Services
    We'll create: omnicopy/services/campaign.py

    And learn how to separate:
        Router: What does the client want?
        Service: How do we fulfill the request?
        Model: How is the data represented and stored?

    We previously mixed HTTP concerns with db operations in api/campaigns.py. This is not ideal for maintainability and scalability.
    We want to separate the responsibilities:
                      HTTP REQUEST
                       │
                       ▼
             ┌───────────────────┐
             │       ROUTER      │
             │                   │
             │ Receives request  │
             │ Returns response  │
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │      SERVICE      │
             │                   │
             │ Implements the    │
             │ operation         │
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │      DATABASE     │
             │                   │
             │ SQLModel Session  │
             └───────────────────┘
    The router shouldn't need to know the details of inserting a campaign into the database. Instead, it should be able to say:

    "Create this campaign using the supplied data and database session."
    The service handles the operation.

Phase 6: Simplify main.py
    The main.py file should be as simple as possible. It should only contain the following:
    - FastAPI application initialization
    - Lifespan event for database initialization

There are actually three distinct operations happening during startup.
    Operation	        Purpose	                            Responsibility
Create database tables	Ensure database tables exist	Database infrastructure
Seed sample data	Populate an empty database	        Data initialization
Start FastAPI	Make the application available	        Application lifecycle

Let's move the first two operations into a separate module, omnicopy/db/init_db.py. This will make it easier to switch to a different database in the future.
    omnicopy/db/database.py manages the engine and sessions.
    omnicopy/db/init_db.py manages initial database content.

Then simplify lifespan function.
"""

# IMPORTS
from datetime import datetime, timezone

from fastapi import FastAPI
from contextlib import asynccontextmanager

from omnicopy.api.campaigns import router as campaigns_router
from omnicopy.db.database import create_db_and_tables
from omnicopy.db.init_db import seed_database


# create db on startup (everything after yield runs after startup):
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_database()

    yield


app = FastAPI(root_path="/api/v1", lifespan=lifespan)

# Tell FastAPI to register all endpoints defined in this router as part of this application.
app.include_router(campaigns_router)


# create a fxn to associate with a path
@app.get("/")
async def root():
    return {"message": "I love the World"}
