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

"""

# IMPORTS
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.concurrency import asynccontextmanager
from sqlmodel import Session, select

from omnicopy.db.database import create_db_and_tables, engine, get_session
from omnicopy.models.campaign import Campaign
from omnicopy.schemas.campaign import CampaignCreate, CampaignUpdate
from omnicopy.schemas.responses import Response

# Tells FastAPI how to inject a session into an endpoint function. This is a type alias for convenience.
SessionDep = Annotated[Session, Depends(get_session)]


# create db on startup (everything after yield runs after startup):
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        if not session.exec(select(Campaign)).first():
            session.add_all(
                [
                    Campaign(
                        name="Summer Launch",
                        due_date=datetime(2024, 4, 30, tzinfo=timezone.utc),
                    ),
                    Campaign(
                        name="Back to School",
                        due_date=datetime(2024, 7, 15, tzinfo=timezone.utc),
                    ),
                ]
            )
            session.commit()
    yield


app = FastAPI(root_path="/api/v1", lifespan=lifespan)


# create a fxn to associate with a path
@app.get("/")
async def root():
    return {"message": "Yo World"}


# Return a list of campaigns:
@app.get("/campaigns", response_model=Response[list[Campaign]])
async def read_campaigns(session: SessionDep):
    campaigns = session.exec(select(Campaign)).all()
    return Response(data=campaigns)


# Return a single campaign by ID:
@app.get("/campaigns/{campaign_id}", response_model=Response[Campaign])
async def read_campaign(campaign_id: int, session: SessionDep):
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return Response(data=campaign)


# Create a new campaign:
@app.post("/campaigns", status_code=201, response_model=Response[Campaign])
async def create_campaign(campaign: CampaignCreate, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign)
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)
    return {"data": db_campaign}


# Update an existing campaign:
@app.put("/campaigns/{campaign_id}", response_model=Response[Campaign])
async def update_campaign(
    campaign_id: int, campaign: CampaignUpdate, session: SessionDep
):
    data = session.get(Campaign, campaign_id)

    if not data:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # data.name = campaign.name
    # data.due_date = campaign.due_date
    updates = campaign.model_dump(exclude_unset=True)
    data.sqlmodel_update(updates)
    session.add(data)
    session.commit()
    session.refresh(data)
    return Response(data=data)


# Delete a campaign:
@app.delete("/campaigns/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: int, session: SessionDep):
    data = session.get(Campaign, campaign_id)
    if not data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    session.delete(data)
    session.commit()
    return
