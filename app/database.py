import logging
from sqlmodel import SQLModel, Session, create_engine
from app.config import get_settings
from contextlib import contextmanager
from sqlalchemy import text, inspect

logger = logging.getLogger(__name__)

engine = create_engine(
    get_settings().database_uri, 
    echo=get_settings().env.lower() in ["dev", "development", "test", "testing", "staging"],
    pool_size=get_settings().db_pool_size,
    max_overflow=get_settings().db_additional_overflow,
    pool_timeout=get_settings().db_pool_timeout,
    pool_recycle=get_settings().db_pool_recycle,
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    _ensure_legacy_schema_updates()


def _ensure_legacy_schema_updates():
    with engine.begin() as connection:
        try:
            inspector = inspect(connection)
            if "friend" in inspector.get_table_names():
                friend_columns = {col["name"] for col in inspector.get_columns("friend")}
                if friend_columns and "status" not in friend_columns:
                    connection.execute(
                        text("ALTER TABLE friend ADD COLUMN status VARCHAR NOT NULL DEFAULT 'pending'")
                    )
                    connection.execute(
                        text("CREATE INDEX IF NOT EXISTS ix_friend_status ON friend (status)")
                    )
        except Exception as e:
            logger.error(f"Schema update error: {e}")
            raise

def drop_all():
    SQLModel.metadata.drop_all(bind=engine)
    
def _session_generator():
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

def get_session():
    yield from _session_generator()

@contextmanager
def get_cli_session():
    yield from _session_generator()