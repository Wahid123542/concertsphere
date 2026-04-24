import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Force .env values to override any old shell variables
load_dotenv(override=True)


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL is not set.")

    return psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor,
        connect_timeout=10,
        sslmode="require",
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )