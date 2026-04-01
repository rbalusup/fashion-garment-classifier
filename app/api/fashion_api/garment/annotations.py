"""Annotation routes — implemented in commit 6."""

from typing import Any

from fastapi import APIRouter


def make_annotations_router(get_db: Any) -> APIRouter:
    router = APIRouter()
    return router
