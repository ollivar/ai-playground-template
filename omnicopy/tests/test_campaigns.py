from fastapi.testclient import TestClient
import pytest

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from omnicopy.db.database import get_session
from omnicopy.main import app


def test_root():
    with (
        TestClient(app) as client
    ):  # Creates a test client for your FastAPI application. It allows you to simulate HTTP requests without starting a separate server.
        response = client.get("/")  # Simulates a GET request to your root endpoint.

    assert (
        response.status_code == 200
    )  # The test passes only if the response status code is 200.
    assert response.json() == {"message": "I love the World"}


def test_get_campaigns_empty(client):
    response = client.get("/campaigns")

    assert response.status_code == 200
    assert response.json() == {"data": []}


def test_create_campaign(client):
    response = client.post(
        "/campaigns",
        json={
            "name": "Test Campaign",
            "due_date": "2026-12-15T12:00:00Z",
        },
    )

    assert response.status_code == 201

    campaign = response.json()["data"]

    assert campaign["name"] == "Test Campaign"
    assert campaign["due_date"] is not None
    assert campaign["campaign_id"] is not None


def test_get_campaign_by_id(client):
    create_response = client.post(
        "/campaigns",
        json={"name": "Test Campaign"},
    )

    campaign_id = create_response.json()["data"]["campaign_id"]

    response = client.get(f"/campaigns/{campaign_id}")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Test Campaign"


def test_update_campaign(client):
    create_response = client.post(
        "/campaigns",
        json={
            "name": "Original Campaign",
            "due_date": "2026-11-01T12:00:00Z",
        },
    )

    campaign_id = create_response.json()["data"]["campaign_id"]

    response = client.put(
        f"/campaigns/{campaign_id}",
        json={"name": "Updated Campaign"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Updated Campaign"

    # Verify the change was actually saved
    get_response = client.get(f"/campaigns/{campaign_id}")

    assert get_response.json()["data"]["name"] == "Updated Campaign"

    # Updating only the name should preserve the existing due date
    assert get_response.json()["data"]["due_date"] is not None


def test_delete_campaign(client):
    create_response = client.post(
        "/campaigns",
        json={"name": "Campaign to Delete"},
    )

    campaign_id = create_response.json()["data"]["campaign_id"]

    response = client.delete(f"/campaigns/{campaign_id}")

    assert response.status_code == 204

    # Verify the campaign no longer exists
    get_response = client.get(f"/campaigns/{campaign_id}")

    assert get_response.status_code == 404


def test_get_nonexistent_campaign(client):
    response = client.get("/campaigns/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Campaign not found"


@pytest.fixture
def client():
    # Create an in-memory SQLite database
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create the database tables
    SQLModel.metadata.create_all(engine)

    # Replace the real database dependency
    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    try:
        # Don't enter the app's lifespan context here:
        # it would run the real database initialization.
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
