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
"""

from datetime import datetime, timezone
from typing import Annotated, Generic, TypeVar

from fastapi import Depends, FastAPI, HTTPException
from fastapi.concurrency import asynccontextmanager
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Campaign(SQLModel, table=True):
    campaign_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    due_date: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=True, index=True
    )


class CampaignCreate(SQLModel):
    name: str
    due_date: datetime | None = None


class CampaignUpdate(SQLModel):
    name: str | None = None
    due_date: datetime | None = None


# Set up database
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}  # only needed for SQLite
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


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


T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    data: T


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
    data.name = campaign.name
    data.due_date = campaign.due_date
    session.add(data)
    session.commit()
    session.refresh(data)
    return {"data": data}


# Delete a campaign:
@app.delete("/campaigns/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: int, session: SessionDep):
    data = session.get(Campaign, campaign_id)
    if not data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    session.delete(data)
    session.commit()
    return
