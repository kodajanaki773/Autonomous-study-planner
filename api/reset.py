import argparse
import os
from urllib.parse import urlparse

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.db import database_url
from seed import seed_data


def reset_database() -> None:
    if os.getenv("ENVIRONMENT", "").lower() not in {"development", "test"}:
        raise RuntimeError("Database reset is permitted only when ENVIRONMENT is development or test.")
    if os.getenv("ALLOW_DATABASE_RESET", "").lower() != "true":
        raise RuntimeError("Set ALLOW_DATABASE_RESET=true in the local API environment to enable reset.")

    url = database_url()
    parsed = urlparse(url)
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1", "db"}:
        raise RuntimeError("Reset refused: only local PostgreSQL hosts are allowed.")
    if parsed.path.lstrip("/") != "aarogya_drishti":
        raise RuntimeError("Reset refused: database name must be exactly aarogya_drishti.")

    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()

    config = Config("alembic.ini")
    command.upgrade(config, "head")
    seed_data()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset and reseed the local synthetic demo database.")
    parser.add_argument(
        "--confirm-reset",
        action="store_true",
        help="Required explicit confirmation; drops all objects in the guarded local database.",
    )
    arguments = parser.parse_args()
    if not arguments.confirm_reset:
        parser.error("Pass --confirm-reset to confirm this destructive operation.")
    reset_database()
    print("Local database reset and reseeded with synthetic demo data.")
