"""
Note: this service isn't a FastAPI endpoint. It's an ordinary Python function.
It doesn't need to know how FastAPI creates or injects sessions. It only needs to know that it will receive a valid SQLModel Session.
This makes the service easier to reuse outside FastAPI.
Therefore, we don't need SessionDep here. We can just use a normal SQLModel Session.

Why doesn't the service return Response(data=db_campaign)?
    Because Response is part of your API's response structure.
    The router will decide how to present that result to an HTTP client.

Note: there are NO FastAPI decorators here. This is because this module is not a FastAPI router.
It's a service module that contains business logic for handling campaigns.
The router will call these functions to perform the actual operations, but it will handle the HTTP request and response formatting.

*Services return application results; routers translate those results into HTTP responses.*
"""

from sqlmodel import Session, select

from omnicopy.models.campaign import Campaign
from omnicopy.schemas.campaign import CampaignCreate, CampaignUpdate


# GET all campaigns from the database:
def get_all_campaigns(session: Session) -> list[Campaign]:
    """Retrieve all campaigns from the database."""
    return list(session.exec(select(Campaign)).all())


# GET a single campaign by ID:
def get_campaign_by_id(session: Session, campaign_id: int) -> Campaign | None:
    """
    Retrieve a single campaign by ID from the database.
    Notice that the service does not raise an HTTP 404 error.
    Instead, the router will interpret None and decide how to respond to the client.
    """
    return session.get(Campaign, campaign_id)


# POST a new campaign to the database:
def create_campaign(
    session: Session, campaign_data: CampaignCreate
) -> Campaign:  # the function is expected to return a Campaign object.
    """Create a new campaign in the database."""
    db_campaign = Campaign.model_validate(campaign_data)

    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)
    return db_campaign


# PUT update a campaign
def update_campaign(
    session: Session, campaign_id: int, campaign_data: CampaignUpdate
) -> Campaign | None:
    """Update an existing campaign in the database."""
    db_campaign = session.get(Campaign, campaign_id)

    if not db_campaign:
        return None

    # for key, value in campaign_data.model_dump(exclude_unset=True).items():
    #     setattr(db_campaign, key, value)

    updates = campaign_data.model_dump(exclude_unset=True)
    db_campaign.sqlmodel_update(updates)

    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)

    return db_campaign


# DELETE campaign
def delete_campaign(
    session: Session, campaign_id: int
) -> bool:  # bool communicates whether the deletion succeeded. The router can translate False into HTTP 404.
    """Delete a campaign from the database."""
    db_campaign = session.get(Campaign, campaign_id)

    if not db_campaign:
        return False

    session.delete(db_campaign)
    session.commit()
    return True
