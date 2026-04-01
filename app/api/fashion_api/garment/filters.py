"""Filter routes — implemented in commit 4."""

from typing import Any

from fastapi import APIRouter


def make_filters_router(get_db: Any) -> APIRouter:
    router = APIRouter()
    return router
