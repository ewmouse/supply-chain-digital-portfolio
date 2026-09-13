from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ============================================================
# 1. 找到项目根目录
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ============================================================
# 2. 读取 .env
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# 3. 创建 PostgreSQL 连接地址
# ============================================================

db_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)


# ============================================================
# 4. 建立 Engine
# ============================================================

engine = create_engine(
    db_url,
    pool_pre_ping=True,
)


# ============================================================
# 5. 查询多行数据
# ============================================================

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


# ============================================================
# 6. 查询单行数据
# ============================================================

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