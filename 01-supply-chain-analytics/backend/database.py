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



engine = create_engine(
    db_url,
    pool_pre_ping=True,
)



def fetch_all(query: str, params: dict | None = None):

    with engine.connect() as connection:

        result = connection.execute(
            text(query),
            params or {},
        )

        rows = result.mappings().all()

        return [
            dict(row)
            for row in rows
        ]



def fetch_one(query: str, params: dict | None = None):

    with engine.connect() as connection:

        result = connection.execute(
            text(query),
            params or {},
        )

        row = result.mappings().first()

        if row is None:
            return None

        return dict(row)

def execute_readonly_query(
    query: str
):

    with engine.connect() as connection:

        transaction = (
            connection.begin()
        )

        try:

            
            connection.execute(
                text(
                    "SET TRANSACTION READ ONLY"
                )
            )


            
            safe_query = f"""
                SELECT *
                FROM (
                    {query}
                ) AS generated_query
                LIMIT 200
            """


            result = (
                connection.execute(
                    text(safe_query)
                )
            )


            rows = (
                result
                .mappings()
                .all()
            )


            
            transaction.rollback()


            return [
                dict(row)
                for row in rows
            ]


        except Exception:

            transaction.rollback()

            raise