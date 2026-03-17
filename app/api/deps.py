from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db


def db_session_dependency() -> Generator[Session, None, None]:
    """
    Thin wrapper around `get_db` to make type hints and import paths explicit.

    Having a dedicated dependency function also makes it straightforward to
    swap out the session provider in tests (e.g. for an in-memory database).
    """

    yield from get_db()

