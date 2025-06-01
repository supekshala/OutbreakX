import logging
from typing import Generator
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os
import time
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

def get_ogr_pg_dsn() -> str:
    """Generate OGR PostgreSQL DSN string from environment variables."""
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    dbname = os.getenv("DB_NAME")
    password = os.getenv("DB_PASSWORD")

    if not all([host, user, dbname, password]):
        raise ValueError(
            f"Missing DB config: host={host}, user={user}, dbname={dbname}, password={bool(password)}"
        )

    return f"host={host} user={user} dbname={dbname} password={password}"

def create_db_engine():
    """Create a database engine with connection pooling and retry logic."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Enable connection health checks
        pool_recycle=300,     # Recycle connections after 5 minutes
        pool_size=5,          # Number of connections to keep open
        max_overflow=10,      # Number of connections to create if pool is full
        pool_timeout=30,      # Seconds to wait before giving up on getting a connection
        echo_pool='debug' if os.getenv('ENV') == 'development' else False
    )
    return engine

# Initialize engine and session factory
engine = create_db_engine()
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )
)

Base = declarative_base()

def init_db():
    """Initialize database tables."""
    from sqlalchemy import text  # Import here to avoid circular imports
    try:
        # Test connection first
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise

def check_db_connection(retries: int = 3, delay: int = 2) -> bool:
    """Check if database is reachable with retry logic."""
    from sqlalchemy import text  # Import here to avoid circular imports
    for attempt in range(retries):
        try:
            with engine.connect() as conn:
                # Wrap the SQL in text() to make it executable
                conn.execute(text("SELECT 1"))
                logger.info("✅ Database connection successful")
                return True
        except exc.SQLAlchemyError as e:
            logger.warning(
                f"❌ Database connection attempt {attempt + 1}/{retries} failed: {str(e)}"
            )
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            continue
    return False

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Dependency function that yields database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        db.close()

# Test connection on import
if not check_db_connection():
    logger.warning("⚠️ Warning: Initial database connection check failed")
else:
    logger.info("✅ Database connection established successfully")
