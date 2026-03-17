from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import config


def _build_sqlite_url() -> str:
    """
    Build the SQLite URL from the central configuration.

    Using a helper keeps the URL construction explicit and testable.
    """

    # Use a file-based SQLite DB inside the configured data directory.
    return f"sqlite:///{config.sqlite_path.as_posix()}"


SQLALCHEMY_DATABASE_URL = _build_sqlite_url()

# `check_same_thread=False` is required for SQLite when using the same
# connection across multiple threads, which is common in ASGI servers.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that yields a database session.

    Routes should take a `Session` parameter with `Depends(get_db)` so that
    connection lifecycle is handled consistently.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

