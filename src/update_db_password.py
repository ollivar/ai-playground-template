import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

password = os.environ["POSTGRES_PASSWORD"]

# Run psql inside the PostgreSQL container.
# Supply the SQL through stdin rather than command-line arguments.
result = subprocess.run(
    [
        "docker",
        "exec",
        "-i",
        "ai-postgres",
        "psql",
        "-U",
        "ai_user",
        "-d",
        "ai_engineering",
        "-v",
        "ON_ERROR_STOP=1",
    ],
    input="ALTER ROLE ai_user PASSWORD :'new_password';",
    capture_output=True,
    text=True,
    env={
        **os.environ,
        "PGPASSWORD": password,
    },
)
