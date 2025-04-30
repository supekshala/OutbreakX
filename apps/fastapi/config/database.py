from collections.abc import Generator
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from sqlalchemy.ext.declarative import declarative_base

# Load environment variables from .env file
from urllib.parse import urlparse
import os
from urllib.parse import urlparse


load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")


def get_ogr_pg_dsn() -> str:
    from dotenv import load_dotenv

    load_dotenv()

    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    dbname = os.getenv("DB_NAME")
    password = os.getenv("DB_PASSWORD")

    if not all([host, user, dbname, password]):
        raise ValueError(
            f"Missing DB config: host={host}, user={user}, dbname={dbname}, password={bool(password)}"
        )

    return f"host={host} user={user} dbname={dbname} password={password}"


engine = create_engine(SQLALCHEMY_DATABASE_URL)

print(f"Database engine created")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

try:
    with engine.connect() as connection:
        print("Successfully connected to the database!")
except Exception as e:
    print(f"Error connecting to the database: {e}")


def get_ogr_pg_dsn() -> str:
    # OGR2OGR expects a different DSN format than SQLAlchemy
    return f"host={os.getenv('DB_HOST')} user={os.getenv('DB_USER')} dbname={os.getenv('DB_NAME')} password={os.getenv('DB_PASSWORD')}"


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
