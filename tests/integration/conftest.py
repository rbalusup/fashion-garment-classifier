"""Integration test fixtures: in-memory SQLite + 12-record seed."""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fashion_api.db.models import GarmentORM
from fashion_api.db.session import Base

# ---------------------------------------------------------------------------
# Seed data: 12 garments covering all filter permutations
# (id_key, garment_type, style, uploaded_at, continent, country, city)
# ---------------------------------------------------------------------------
SEED = [
    ("g001", "jacket",   "streetwear",       "2024-03-15", "europe",   "france",    "paris"),
    ("g002", "dress",    "formal",            "2024-07-22", "europe",   "italy",     "milan"),
    ("g003", "coat",     "minimalist",        "2025-01-10", "europe",   "uk",        "london"),
    ("g004", "jeans",    "casual",            "2024-11-05", "asia",     "japan",     "tokyo"),
    ("g005", "suit",     "formal",            "2025-02-28", "asia",     "japan",     "tokyo"),
    ("g006", "t-shirt",  "casual",            "2023-08-19", "americas", "usa",       "new york"),
    ("g007", "blouse",   "business-casual",   "2024-06-01", "americas", "usa",       "new york"),
    ("g008", "shorts",   "athleisure",        "2024-09-14", "americas", "brazil",    "rio de janeiro"),
    ("g009", "hoodie",   "streetwear",        "2025-03-03", "americas", "usa",       "los angeles"),
    ("g010", "sweater",  "casual",            "2023-12-20", "europe",   "germany",   "berlin"),
    ("g011", "jumpsuit", "bohemian",          "2024-04-11", "africa",   "morocco",   "marrakech"),
    ("g012", "vest",     "minimalist",        "2025-01-25", "oceania",  "australia", "sydney"),
]


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def seeded_session(db_engine):
    """Session with all 12 seed garments. Shared across the session for speed."""
    factory = sessionmaker(bind=db_engine)
    session = factory()

    for key, gtype, style, date_str, continent, country, city in SEED:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        g = GarmentORM(
            uuid=str(uuid.uuid4()),
            original_filename=f"{key}.jpg",
            image_path=f"uploads/{key}.jpg",
            uploaded_at=dt,
            garment_type=gtype,
            style=style,
            location_continent=continent,
            location_country=country,
            location_city=city,
            year=dt.year,
            month=dt.month,
        )
        session.add(g)
    session.commit()
    yield session
    session.close()


@pytest.fixture
def db_session(seeded_session) -> Session:
    """Yields the shared seeded session (read-only tests only)."""
    return seeded_session
