"""Designer annotation CRUD endpoints."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fashion_api.db.models import AnnotationORM, GarmentORM
from fashion_api.garment.models import AnnotationCreate, AnnotationOut, AnnotationUpdate


def _to_out(a: AnnotationORM) -> AnnotationOut:
    return AnnotationOut(
        id=a.id,
        garment_id=a.garment_id,
        created_at=a.created_at,
        updated_at=a.updated_at,
        tags=a.tags,
        notes=a.notes,
        source=a.source,
    )


def make_annotations_router(get_db: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/annotations", response_model=AnnotationOut, status_code=201)
    def create_annotation(
        payload: AnnotationCreate, db: Session = Depends(get_db)
    ) -> AnnotationOut:
        if not db.get(GarmentORM, payload.garment_id):
            raise HTTPException(status_code=404, detail="Garment not found")
        now = datetime.utcnow()
        annotation = AnnotationORM(
            garment_id=payload.garment_id,
            notes=payload.notes,
            created_at=now,
            updated_at=now,
            source="designer",
        )
        annotation.tags = payload.tags
        db.add(annotation)
        db.commit()
        db.refresh(annotation)
        return _to_out(annotation)

    @router.get("/annotations/{garment_id}", response_model=list[AnnotationOut])
    def list_annotations(garment_id: int, db: Session = Depends(get_db)) -> list[AnnotationOut]:
        rows = (
            db.query(AnnotationORM)
            .filter(AnnotationORM.garment_id == garment_id)
            .order_by(AnnotationORM.created_at)
            .all()
        )
        return [_to_out(a) for a in rows]

    @router.patch("/annotations/{annotation_id}", response_model=AnnotationOut)
    def update_annotation(
        annotation_id: int, payload: AnnotationUpdate, db: Session = Depends(get_db)
    ) -> AnnotationOut:
        a = db.get(AnnotationORM, annotation_id)
        if not a:
            raise HTTPException(status_code=404, detail="Annotation not found")
        updates = payload.model_dump(exclude_unset=True)
        if "tags" in updates:
            a.tags = updates["tags"]
        if "notes" in updates:
            a.notes = updates["notes"]
        a.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(a)
        return _to_out(a)

    @router.delete("/annotations/{annotation_id}", status_code=204)
    def delete_annotation(annotation_id: int, db: Session = Depends(get_db)) -> None:
        a = db.get(AnnotationORM, annotation_id)
        if not a:
            raise HTTPException(status_code=404, detail="Annotation not found")
        db.delete(a)
        db.commit()

    return router
