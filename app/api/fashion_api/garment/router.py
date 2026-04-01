"""Garment upload, CRUD, search, and reclassify endpoints."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
import structlog
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from fashion_api.config import Settings
from fashion_api.db.models import GarmentORM
from fashion_api.garment.classifier import GarmentClassifier
from fashion_api.garment.filters import filter_garments
from fashion_api.garment.models import (
    GarmentListItem,
    GarmentOut,
    GarmentUpdate,
    PaginatedGarments,
)

logger = structlog.get_logger(__name__)

ALLOWED_MIMETYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _make_garment_out(g: GarmentORM) -> GarmentOut:
    return GarmentOut(
        id=g.id,
        uuid=g.uuid,
        original_filename=g.original_filename,
        image_path=g.image_path,
        uploaded_at=g.uploaded_at,
        classified_at=g.classified_at,
        description=g.description,
        garment_type=g.garment_type,
        style=g.style,
        material=g.material,
        color_palette=g.color_palette,
        pattern=g.pattern,
        season=g.season,
        occasion=g.occasion,
        consumer_profile=g.consumer_profile,
        trend_notes=g.trend_notes,
        location_continent=g.location_continent,
        location_country=g.location_country,
        location_city=g.location_city,
        designer=g.designer,
        year=g.year,
        month=g.month,
        classification_error=g.classification_error,
        annotations=[
            {
                "id": a.id,
                "garment_id": a.garment_id,
                "created_at": a.created_at,
                "updated_at": a.updated_at,
                "tags": a.tags,
                "notes": a.notes,
                "source": a.source,
            }
            for a in g.annotations
        ],
    )


def _get_classifier(settings: Settings) -> GarmentClassifier:
    return GarmentClassifier(api_key=settings.anthropic_api_key, model=settings.claude_model)


def make_garment_router(settings: Settings, get_db: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/upload", response_model=GarmentOut, status_code=201)
    async def upload_garment(
        file: UploadFile,
        continent: str | None = Form(default=None),
        country: str | None = Form(default=None),
        city: str | None = Form(default=None),
        designer: str | None = Form(default=None),
        year: int | None = Form(default=None),
        month: int | None = Form(default=None),
        db: Session = Depends(get_db),
    ) -> GarmentOut:
        # Validate file type
        content_type = file.content_type or ""
        suffix = Path(file.filename or "").suffix.lower()
        if content_type not in ALLOWED_MIMETYPES and suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type '{content_type}'. Upload a JPEG, PNG, WebP, or GIF.",
            )

        # Read and size-check
        image_bytes = await file.read()
        if len(image_bytes) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds {settings.fashion_max_upload_mb} MB limit.",
            )

        # Save to disk
        garment_uuid = str(uuid.uuid4())
        ext = suffix or ".jpg"
        filename = f"{garment_uuid}{ext}"
        upload_path = Path(settings.upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)
        file_path = upload_path / filename
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(image_bytes)

        # Insert minimal DB row
        now = datetime.utcnow()
        garment = GarmentORM(
            uuid=garment_uuid,
            original_filename=file.filename or filename,
            image_path=f"uploads/{filename}",
            uploaded_at=now,
            location_continent=continent,
            location_country=country,
            location_city=city,
            designer=designer,
            year=year or now.year,
            month=month or now.month,
        )
        db.add(garment)
        db.commit()
        db.refresh(garment)

        # Classify with Claude
        try:
            classifier = _get_classifier(settings)
            attrs, raw_json = classifier.classify_image(file_path)
            garment.description = attrs.description
            garment.garment_type = attrs.garment_type
            garment.style = attrs.style
            garment.material = attrs.material
            garment.color_palette = attrs.color_palette
            garment.pattern = attrs.pattern
            garment.season = attrs.season
            garment.occasion = attrs.occasion
            garment.consumer_profile = attrs.consumer_profile
            garment.trend_notes = attrs.trend_notes
            # Only override location from AI if not already set by user
            if not garment.location_continent and attrs.location_context.continent:
                garment.location_continent = attrs.location_context.continent
            if not garment.location_country and attrs.location_context.country:
                garment.location_country = attrs.location_context.country
            if not garment.location_city and attrs.location_context.city:
                garment.location_city = attrs.location_context.city
            garment.classified_at = datetime.utcnow()
            garment.classification_raw = raw_json
        except Exception as exc:
            logger.error("classification_failed", error=str(exc), uuid=garment_uuid)
            garment.classification_error = str(exc)

        db.commit()
        db.refresh(garment)
        return _make_garment_out(garment)

    @router.get("/garments", response_model=PaginatedGarments)
    def list_garments(
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
        db: Session = Depends(get_db),
    ) -> PaginatedGarments:
        return filter_garments(
            db,
            q=q,
            garment_type=garment_type,
            style=style,
            material=material,
            color=color,
            pattern=pattern,
            season=season,
            occasion=occasion,
            continent=continent,
            country=country,
            city=city,
            year=year,
            month=month,
            designer=designer,
            skip=skip,
            limit=limit,
        )

    @router.get("/garments/{garment_id}", response_model=GarmentOut)
    def get_garment(garment_id: int, db: Session = Depends(get_db)) -> GarmentOut:
        g = db.get(GarmentORM, garment_id)
        if not g:
            raise HTTPException(status_code=404, detail="Garment not found")
        return _make_garment_out(g)

    @router.patch("/garments/{garment_id}", response_model=GarmentOut)
    def update_garment(
        garment_id: int, update: GarmentUpdate, db: Session = Depends(get_db)
    ) -> GarmentOut:
        g = db.get(GarmentORM, garment_id)
        if not g:
            raise HTTPException(status_code=404, detail="Garment not found")
        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(g, field, value)
        db.commit()
        db.refresh(g)
        return _make_garment_out(g)

    @router.delete("/garments/{garment_id}", status_code=204)
    def delete_garment(garment_id: int, db: Session = Depends(get_db)) -> JSONResponse:
        g = db.get(GarmentORM, garment_id)
        if not g:
            raise HTTPException(status_code=404, detail="Garment not found")
        # Remove image file
        img_path = Path(settings.upload_dir) / Path(g.image_path).name
        img_path.unlink(missing_ok=True)
        db.delete(g)
        db.commit()
        return JSONResponse(status_code=204, content=None)

    @router.post("/garments/{garment_id}/reclassify", response_model=GarmentOut)
    def reclassify_garment(garment_id: int, db: Session = Depends(get_db)) -> GarmentOut:
        g = db.get(GarmentORM, garment_id)
        if not g:
            raise HTTPException(status_code=404, detail="Garment not found")
        img_path = Path(settings.upload_dir) / Path(g.image_path).name
        if not img_path.exists():
            raise HTTPException(status_code=404, detail="Image file not found on disk")
        try:
            classifier = _get_classifier(settings)
            attrs, raw_json = classifier.classify_image(img_path)
            g.garment_type = attrs.garment_type
            g.style = attrs.style
            g.material = attrs.material
            g.color_palette = attrs.color_palette
            g.pattern = attrs.pattern
            g.season = attrs.season
            g.occasion = attrs.occasion
            g.consumer_profile = attrs.consumer_profile
            g.trend_notes = attrs.trend_notes
            g.description = attrs.description
            g.classified_at = datetime.utcnow()
            g.classification_raw = raw_json
            g.classification_error = None
        except Exception as exc:
            g.classification_error = str(exc)
        db.commit()
        db.refresh(g)
        return _make_garment_out(g)

    return router
