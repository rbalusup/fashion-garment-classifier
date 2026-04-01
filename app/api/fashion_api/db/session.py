"""SQLAlchemy engine and session factory."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def create_db_engine(database_url: str, use_static_pool: bool = False):  # type: ignore[no-untyped-def]
    connect_args = {}
    kwargs: dict = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    if use_static_pool:
        # Required for in-memory SQLite so all sessions share the same connection
        kwargs["poolclass"] = StaticPool
    return create_engine(database_url, connect_args=connect_args, **kwargs)


def create_session_factory(engine):  # type: ignore[no-untyped-def]
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_dependency(session_factory: sessionmaker) -> Generator[Session, None, None]:  # type: ignore[type-arg]
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
