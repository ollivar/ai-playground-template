import os
import psycopg

from dotenv import load_dotenv
from pathlib import Path


# Find the .env file in the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")


def test_connection():
    """Test PostgreSQL connection and verify pgvector."""

    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "ai_engineering"),
        user=os.getenv("POSTGRES_USER", "ai_user"),
        password=os.environ["POSTGRES_PASSWORD"],
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            print("✅ Connected to PostgreSQL!")
            print(cur.fetchone()[0])

            # Enable pgvector
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Check pgvector version
            cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")

            result = cur.fetchone()
            print(f"✅ pgvector version: {result[0]}")


if __name__ == "__main__":
    test_connection()
