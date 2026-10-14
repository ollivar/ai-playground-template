"""
What have we accomplished? We've extracted a distinct responsibility into a separate function.
Your initialization logic can now be called from anywhere that needs it: seed_database()

One important caveat: This function only inserts sample campaigns if the campaign table is completely empty.
That's sufficient for our exercise, but it isn't a robust production seeding strategy.
Production systems typically use database migrations and more deliberate initialization procedures.

"""

from datetime import datetime, timezone

from sqlmodel import Session, select

from omnicopy.db.database import engine
from omnicopy.models.campaign import Campaign


def seed_database():
    with Session(engine) as session:
        existing_campaign = session.exec(select(Campaign)).first()

        if existing_campaign:
            return

        campaigns = [
            Campaign(
                name="Summer Launch",
                due_date=datetime(2024, 4, 30, tzinfo=timezone.utc),
            ),
            Campaign(
                name="Back to School",
                due_date=datetime(2024, 7, 15, tzinfo=timezone.utc),
            ),
        ]

        session.add_all(campaigns)
        session.commit()
