import os
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

# Base class for SQLAlchemy Declarative models
Base = declarative_base()

# DB Configuration
# Defaults to local SQLite file for development/testing if no DATABASE_URL is set.
# For MariaDB, set DATABASE_URL="mysql+pymysql://user:password@host:port/database"
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Build a fallback SQLite URL
    sqlite_db_path = ROOT_DIR / "csautobot.db"
    DATABASE_URL = f"sqlite:///{sqlite_db_path}"

# Setup engine with appropriate connection parameters
# pool_pre_ping=True prevents "MySQL server has gone away" errors
if DATABASE_URL.startswith("mysql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )
else:
    # SQLite compatibility settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that provides a transactional database session.
    Automatically closes the session after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions, useful in scripts and background workers.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Programmatically create all tables defined by SQLAlchemy models.
    """
    # Import repositories to ensure all SQLAlchemy models are registered on Base.metadata
    from storage import repositories  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()


def _apply_lightweight_migrations() -> None:
    """Add columns introduced after initial deploy (no Alembic)."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    dialect = engine.dialect.name

    def _add_column(table: str, column: str, ddl_sqlite: str, ddl_mysql: str) -> None:
        if table not in insp.get_table_names():
            return
        existing = {c["name"] for c in insp.get_columns(table)}
        if column in existing:
            return
        ddl = ddl_mysql if dialect.startswith("mysql") else ddl_sqlite
        with engine.begin() as conn:
            conn.execute(text(ddl))

    _add_column(
        "usage_meter",
        "fallback_provider",
        "ALTER TABLE usage_meter ADD COLUMN fallback_provider VARCHAR(50)",
        "ALTER TABLE usage_meter ADD COLUMN fallback_provider VARCHAR(50) NULL",
    )
    _add_column(
        "usage_meter",
        "is_shortcut",
        "ALTER TABLE usage_meter ADD COLUMN is_shortcut INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE usage_meter ADD COLUMN is_shortcut INT NOT NULL DEFAULT 0",
    )
    _add_column(
        "tenant_ai_settings",
        "daily_token_limit",
        "ALTER TABLE tenant_ai_settings ADD COLUMN daily_token_limit INTEGER",
        "ALTER TABLE tenant_ai_settings ADD COLUMN daily_token_limit INT NULL",
    )

