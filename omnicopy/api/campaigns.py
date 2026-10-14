"""
APIRouter is a FastAPI class that allows you to group endpoints.

Your API module knows about the database, but your database module doesn't need to know about your API.

Current relationship:
                    main.py
                       │
                       │ include_router()
                       ▼
                api/campaigns.py
                       │
              ┌────────┼─────────┐
              │        │         │
              ▼        ▼         ▼
          schemas/   models/     db/
              │        │         │
              │        │         ▼
              │        │     SessionDep
              │        │         │
              │        │         ▼
              │        │     get_session()
              │        │         │
              │        │         ▼
              │        └────► SQLite
              │
              ▼
        Request/response
          validation
"""

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from omnicopy.db.database import SessionDep
from omnicopy.models.campaign import Campaign
from omnicopy.schemas.campaign import CampaignCreate, CampaignUpdate
from omnicopy.schemas.responses import Response
from omnicopy.services import campaign as campaign_service


# Define a router for the campaigns endpoints.
# This allows us to group all the endpoints related to campaigns together, and also allows us to include this router in the main FastAPI application.
router = APIRouter(
    prefix="/campaigns",  # This means every endpoint registered with this router automatically begins with /campaigns.
    tags=["Campaigns"],  # groups these endpoints together in Swagger UI.
    responses={404: {"description": "Not found"}},
)


# Define a GET endpoint to retrieve all campaigns.
@router.get("", response_model=Response[list[Campaign]])
async def read_campaigns(session: SessionDep):
    """Retrieve all campaigns from the database, using the service."""
    # campaigns = session.exec(select(Campaign)).all()
    campaigns = campaign_service.get_all_campaigns(session)
    return Response(data=campaigns, message="Campaigns retrieved successfully.")


# Return a single campaign by ID:
@router.get("/{campaign_id}", response_model=Response[Campaign])
async def read_campaign(campaign_id: int, session: SessionDep):
    campaign = campaign_service.get_campaign_by_id(session, campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return Response(data=campaign)


# Create a new campaign:
@router.post(
    "", status_code=201, response_model=Response[Campaign]
)  # defines an HTTP Endpoint
async def create_campaign(
    campaign: CampaignCreate,  # Receives validated request data
    session: SessionDep,  # Obtains a database session from the dependency injection system.
):

    db_campaign = campaign_service.create_campaign(
        session, campaign
    )  # Calls the service to create a new campaign in the database.

    return Response(data=db_campaign)  # Formats the API response


# Update an existing campaign:
@router.put("/{campaign_id}", response_model=Response[Campaign])
async def update_campaign(
    campaign_id: int, campaign: CampaignUpdate, session: SessionDep
):
    db_campaign = campaign_service.update_campaign(session, campaign_id, campaign)

    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return Response(data=db_campaign)


# Delete a campaign:
@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: int, session: SessionDep):

    deleted = campaign_service.delete_campaign(session, campaign_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Campaign not found")
