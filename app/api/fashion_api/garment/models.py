"""Pydantic models for garment classification."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ParseError(Exception):
    """Raised when Claude's response cannot be parsed into structured attributes."""

    def __init__(self, message: str, raw_response: str = "") -> None:
        super().__init__(message)
        self.raw_response = raw_response


# Controlled vocabulary for attributes
GARMENT_TYPES = frozenset([
    "dress", "skirt", "blouse", "shirt", "t-shirt", "jacket", "coat", "blazer",
    "trousers", "jeans", "shorts", "suit", "jumpsuit", "cardigan", "sweater",
    "hoodie", "vest", "activewear", "swimwear", "other",
])

STYLES = frozenset([
    "casual", "formal", "business-casual", "streetwear", "athleisure",
    "bohemian", "minimalist", "vintage", "preppy", "avant-garde", "romantic",
    "classic", "folk", "other",
])

MATERIALS = frozenset([
    "cotton", "denim", "leather", "silk", "wool", "linen", "polyester",
    "knit", "chiffon", "velvet", "synthetic-blend", "unknown",
])

OCCASIONS = frozenset([
    "everyday", "work", "evening", "outdoor", "sport",
    "beach", "formal-event", "travel", "lounge", "unknown",
])

LOCATION_CONTEXTS = frozenset([
    "street", "studio", "indoor-home", "office", "outdoor-nature",
    "cafe-restaurant", "event-venue", "beach", "gym", "unknown",
])

PATTERNS = frozenset([
    "solid", "stripes", "plaid", "check", "floral", "geometric",
    "abstract", "animal-print", "paisley", "tie-dye", "embroidered", "textured", "none",
])

SEASONS = frozenset(["spring/summer", "fall/winter", "all-season"])


class LocationContext(BaseModel):
    continent: str | None = None
    country: str | None = None
    city: str | None = None


class GarmentAttributes(BaseModel):
    """Structured attributes extracted by the classifier from a garment image."""

    garment_type: str
    style: str = "unknown"
    material: str = "unknown"
    color_palette: list[str] = Field(default_factory=list)
    pattern: str = "unknown"
    season: str = "unknown"
    occasion: str = "unknown"
    consumer_profile: str = "unknown"
    trend_notes: str = ""
    location_context: LocationContext = Field(default_factory=LocationContext)
    description: str = ""

    # Non-taxonomy values are stored but flagged
    validation_warnings: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        warnings = []
        if self.garment_type not in GARMENT_TYPES:
            warnings.append(f"garment_type value '{self.garment_type}' not in taxonomy")
        if self.style not in STYLES and self.style != "unknown":
            warnings.append(f"style value '{self.style}' not in taxonomy")
        if self.material not in MATERIALS and self.material != "unknown":
            warnings.append(f"material value '{self.material}' not in taxonomy")
        if self.occasion not in OCCASIONS and self.occasion != "unknown":
            warnings.append(f"occasion value '{self.occasion}' not in taxonomy")
        if self.location_context and self.location_context.continent not in LOCATION_CONTEXTS:
            pass  # location_context is free-text; no strict taxonomy check
        self.validation_warnings = warnings


class AnnotationCreate(BaseModel):
    garment_id: int
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class AnnotationUpdate(BaseModel):
    tags: list[str] | None = None
    notes: str | None = None


class AnnotationOut(BaseModel):
    id: int
    garment_id: int
    created_at: datetime
    updated_at: datetime
    tags: list[str]
    notes: str | None
    source: str

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class GarmentUpdate(BaseModel):
    designer: str | None = None
    year: int | None = None
    month: int | None = None


class GarmentListItem(BaseModel):
    id: int
    uuid: str
    image_path: str
    garment_type: str | None
    style: str | None
    color_palette: list[str]
    classification_error: str | None

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class GarmentOut(BaseModel):
    id: int
    uuid: str
    original_filename: str
    image_path: str
    uploaded_at: datetime
    classified_at: datetime | None
    description: str | None
    garment_type: str | None
    style: str | None
    material: str | None
    color_palette: list[str]
    pattern: str | None
    season: str | None
    occasion: str | None
    consumer_profile: str | None
    trend_notes: str | None
    location_continent: str | None
    location_country: str | None
    location_city: str | None
    designer: str | None
    year: int | None
    month: int | None
    classification_error: str | None
    annotations: list[AnnotationOut]

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class PaginatedGarments(BaseModel):
    items: list[GarmentListItem]
    total: int
    skip: int
    limit: int


class FilterOptions(BaseModel):
    garment_type: list[str]
    style: list[str]
    material: list[str]
    color: list[str]
    pattern: list[str]
    season: list[str]
    occasion: list[str]
    location_continent: list[str]
    location_country: list[str]
    location_city: list[str]
    designer: list[str]
    year: list[int]

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
