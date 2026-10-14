from datetime import date, datetime, timezone
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
                    Campaign(name="Summer Launch", due_date=date(2024, 4, 30)),
                    Campaign(name="Back to School", due_date=date(2024, 7, 15)),
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
