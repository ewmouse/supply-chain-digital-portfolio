from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# 找到项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# 从 .env 中读取数据库配置
load_dotenv(PROJECT_ROOT / ".env")


# 创建数据库地址
db_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)


# 建立数据库 Engine
engine = create_engine(db_url)


# 真正打开一次连接，并执行SQL
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