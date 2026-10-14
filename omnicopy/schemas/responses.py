"""
Consider: Response[Campaign]
This means: "A response whose data field contains one Campaign."

Consider: Response[list[Campaign]]
This means: "A response whose data field contains a list of Campaigns."

The generic type variable T allows us to reuse the same class with different data types.
This is useful b/c we don't need to create a new response class for every different type of data we want to return from our API.
    CampaignResponse
    CampaignListResponse
    UserResponse
    UserListResponse

We can use one reusable structure.

Key concept: Generics let us define reusable classes while preserving type information.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

# The generic type variable T allows us to reuse the same class with different data types.
T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    data: T
