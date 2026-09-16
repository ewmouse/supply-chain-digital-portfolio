from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL



PROJECT_ROOT = Path(__file__).resolve().parents[1]



load_dotenv(PROJECT_ROOT / ".env")



db_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)



engine = create_engine(db_url)



with engine.connect() as connection:

    result = connection.execute(
        text(
            """
            SELECT
                current_database(),
                current_user;
            """
        )
    )

    row = result.fetchone()

    print("Database connection successful!")
    print("Database:", row[0])
    print("User:", row[1])