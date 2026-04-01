"""SQLAlchemy engine and session factory."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def create_db_engine(database_url: str):  # type: ignore[no-untyped-def]
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, connect_args=connect_args)


def create_session_factory(engine):  # type: ignore[no-untyped-def]
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_dependency(session_factory: sessionmaker) -> Generator[Session, None, None]:  # type: ignore[type-arg]
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
