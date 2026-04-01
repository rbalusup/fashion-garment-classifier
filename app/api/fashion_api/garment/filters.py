"""Filter queries and dynamic filter options endpoint."""

import json
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from fashion_api.db.models import AnnotationORM, GarmentORM
from fashion_api.garment.models import FilterOptions, GarmentListItem, PaginatedGarments


def filter_garments(
    db: Session,
    q: str | None = None,
    garment_type: str | None = None,
    style: str | None = None,
    material: str | None = None,
    color: str | None = None,
    pattern: str | None = None,
    season: str | None = None,
    occasion: str | None = None,
    continent: str | None = None,
    country: str | None = None,
    city: str | None = None,
    year: int | None = None,
    month: int | None = None,
    designer: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> PaginatedGarments:
    """Query garments with optional filters and full-text search."""
    query = db.query(GarmentORM)

    # Structured attribute filters (exact match, case-insensitive)
    if garment_type:
        query = query.filter(func.lower(GarmentORM.garment_type) == garment_type.lower())
    if style:
        query = query.filter(func.lower(GarmentORM.style) == style.lower())
    if material:
        query = query.filter(func.lower(GarmentORM.material) == material.lower())
    if pattern:
        query = query.filter(func.lower(GarmentORM.pattern) == pattern.lower())
    if season:
        query = query.filter(func.lower(GarmentORM.season) == season.lower())
    if occasion:
        query = query.filter(func.lower(GarmentORM.occasion) == occasion.lower())

    # Location filters
    if continent:
        query = query.filter(func.lower(GarmentORM.location_continent) == continent.lower())
    if country:
        query = query.filter(func.lower(GarmentORM.location_country) == country.lower())
    if city:
        query = query.filter(func.lower(GarmentORM.location_city) == city.lower())

    # Time filters
    if year is not None:
        query = query.filter(GarmentORM.year == year)
    if month is not None:
        query = query.filter(GarmentORM.month == month)

    # Designer filter
    if designer:
        query = query.filter(func.lower(GarmentORM.designer) == designer.lower())

    # Color filter — LIKE on JSON text column
    if color:
        query = query.filter(GarmentORM._color_palette.ilike(f"%{color}%"))

    # Full-text search across description, trend_notes, consumer_profile + annotation notes
    if q:
        term = f"%{q}%"
        query = (
            query.outerjoin(AnnotationORM, GarmentORM.id == AnnotationORM.garment_id)
            .filter(
                or_(
                    GarmentORM.description.ilike(term),
                    GarmentORM.trend_notes.ilike(term),
                    GarmentORM.consumer_profile.ilike(term),
                    AnnotationORM.notes.ilike(term),
                    AnnotationORM._tags.ilike(term),
                )
            )
            .distinct()
        )

    total = query.count()
    rows = query.order_by(GarmentORM.uploaded_at.desc()).offset(skip).limit(limit).all()

    items = [
        GarmentListItem(
            id=r.id,
            uuid=r.uuid,
            image_path=r.image_path,
            garment_type=r.garment_type,
            style=r.style,
            color_palette=r.color_palette,
            classification_error=r.classification_error,
        )
        for r in rows
    ]

    return PaginatedGarments(items=items, total=total, skip=skip, limit=limit)


def get_filter_options(db: Session) -> FilterOptions:
    """Return distinct values for each filterable field, drawn from actual data."""

    def distinct_str(col: Any) -> list[str]:
        return sorted(
            {r[0] for r in db.query(col).filter(col.isnot(None)).distinct().all() if r[0]}
        )

    def distinct_int(col: Any) -> list[int]:
        return sorted(
            {r[0] for r in db.query(col).filter(col.isnot(None)).distinct().all() if r[0]}
        )

    # Color palette requires JSON explosion
    all_palettes = (
        db.query(GarmentORM._color_palette)
        .filter(GarmentORM._color_palette.isnot(None))
        .all()
    )
    colors: set[str] = set()
    for (palette_json,) in all_palettes:
        try:
            colors.update(c for c in json.loads(palette_json) if c)
        except (json.JSONDecodeError, TypeError):
            pass

    return FilterOptions(
        garment_type=distinct_str(GarmentORM.garment_type),
        style=distinct_str(GarmentORM.style),
        material=distinct_str(GarmentORM.material),
        color=sorted(colors),
        pattern=distinct_str(GarmentORM.pattern),
        season=distinct_str(GarmentORM.season),
        occasion=distinct_str(GarmentORM.occasion),
        location_continent=distinct_str(GarmentORM.location_continent),
        location_country=distinct_str(GarmentORM.location_country),
        location_city=distinct_str(GarmentORM.location_city),
        designer=distinct_str(GarmentORM.designer),
        year=distinct_int(GarmentORM.year),
    )


def make_filters_router(get_db: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/filters/options", response_model=FilterOptions)
    def filters_options(db: Session = Depends(get_db)) -> FilterOptions:
        return get_filter_options(db)

    return router
