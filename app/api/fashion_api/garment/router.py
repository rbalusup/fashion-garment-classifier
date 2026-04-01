"""Garment routes — implemented in commit 6."""

from typing import Any

from fastapi import APIRouter


def make_garment_router(settings: Any, get_db: Any) -> APIRouter:
    router = APIRouter()
    return router
