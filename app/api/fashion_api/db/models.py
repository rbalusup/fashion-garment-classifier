"""SQLAlchemy ORM models for garments and annotations."""

import json
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fashion_api.db.session import Base


class AnnotationORM(Base):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    garment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("garments.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    _tags: Mapped[str | None] = mapped_column("tags", Text, default="[]")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="designer")

    garment: Mapped["GarmentORM"] = relationship("GarmentORM", back_populates="annotations")

    @property
    def tags(self) -> list[str]:
        try:
            return json.loads(self._tags or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self._tags = json.dumps(value)


class GarmentORM(Base):
    __tablename__ = "garments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # AI-generated fields
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    garment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    material: Mapped[str | None] = mapped_column(String(100), nullable=True)
    _color_palette: Mapped[str | None] = mapped_column("color_palette", Text, nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(100), nullable=True)
    season: Mapped[str | None] = mapped_column(String(50), nullable=True)
    occasion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    consumer_profile: Mapped[str | None] = mapped_column(String(150), nullable=True)
    trend_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location
    location_continent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Designer-editable
    designer: Mapped[str | None] = mapped_column(String(150), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Audit
    classification_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    annotations: Mapped[list[AnnotationORM]] = relationship(
        "AnnotationORM",
        back_populates="garment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def color_palette(self) -> list[str]:
        try:
            return json.loads(self._color_palette or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @color_palette.setter
    def color_palette(self, value: list[str]) -> None:
        self._color_palette = json.dumps(value)


# Indexes for common filter columns
Index("ix_garment_type", GarmentORM.garment_type)
Index("ix_style", GarmentORM.style)
Index("ix_occasion", GarmentORM.occasion)
Index("ix_season", GarmentORM.season)
Index("ix_location_continent", GarmentORM.location_continent)
Index("ix_year", GarmentORM.year)
