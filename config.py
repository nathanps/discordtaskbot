import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
REPO_PATH = os.getenv("REPO_PATH", ".")
CSV_FILENAME = os.getenv("CSV_FILENAME", "tasks.csv")

# Task states
STATES = ("open", "in-progress", "done")

# Default limit for tasklist
DEFAULT_LIMIT = 15


def get_csv_path(guild_id: int) -> str:
    """Get the CSV path for a specific guild. Creates directory if needed."""
    server_dir = os.path.join(REPO_PATH, "servers", str(guild_id))
    os.makedirs(server_dir, exist_ok=True)
    return os.path.join(server_dir, CSV_FILENAME)
