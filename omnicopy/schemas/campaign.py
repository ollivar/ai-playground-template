# LAYER 2: Pydantic Models
"""
These define the shape of information entering and leaving your application.
Why separate these from your database model? Because your database and API have different responsibilities.

For example, your database might contain:
    campaign_id
    name
    due_date
    created_at
    internal_status

But when someone creates a campaign through your API, you might only allow:
    name
    due_date

The client shouldn't necessarily be able to modify every database field.

CampaignCreate is an API data contract, not a database table

Key concept: Schemas define the contract between your application and its users.
"""

from datetime import datetime
from pydantic import BaseModel


# For schemas that are only responsible for API validation, I prefer using Pydantic's BaseModel directly:
class CampaignCreate(BaseModel):
    name: str
    due_date: datetime | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    due_date: datetime | None = None
