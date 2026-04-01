"""Parse Claude's text response into structured GarmentAttributes."""

import json
import re

from fashion_api.garment.models import GarmentAttributes, LocationContext, ParseError


def parse_garment_attributes(response_text: str) -> GarmentAttributes:
    """Parse a Claude response string into GarmentAttributes.

    Handles:
    - Plain JSON objects
    - JSON wrapped in ```json ... ``` or ``` ... ``` markdown fences
    - JSON embedded after a prose sentence
    - Partial data (missing optional fields filled with "unknown")

    Raises:
        ParseError: If no valid JSON object can be extracted, or if
                    the required 'garment_type' field is absent.
    """
    raw = response_text.strip()

    # 1. Strip markdown fences: ```json ... ``` or ``` ... ```
    fenced = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", raw, re.DOTALL)
    if fenced:
        raw = fenced.group(1).strip()

    # 2. Extract first {...} block (handles prose prefix from Claude)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ParseError("No JSON object found in response", raw_response=response_text)

    json_str = match.group(0)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ParseError(f"Invalid JSON: {exc}", raw_response=response_text) from exc

    if not isinstance(data, dict):
        raise ParseError("Response JSON is not an object", raw_response=response_text)

    # 3. Require garment_type
    if "garment_type" not in data or not data["garment_type"]:
        raise ParseError("Missing required field: garment_type", raw_response=response_text)

    # 4. Normalize string values to lowercase
    str_fields = ["garment_type", "style", "material", "pattern", "season", "occasion",
                  "consumer_profile", "trend_notes", "description"]
    for field in str_fields:
        if field in data and isinstance(data[field], str):
            data[field] = data[field].lower().strip()

    # 5. Normalize color_palette
    if "color_palette" in data and isinstance(data["color_palette"], list):
        data["color_palette"] = [
            c.lower().strip() if isinstance(c, str) else str(c)
            for c in data["color_palette"]
        ]

    # 6. Flatten location_context into a LocationContext model
    location_raw = data.pop("location_context", {}) or {}
    if isinstance(location_raw, dict):
        def _norm(v: object) -> str | None:
            return v.lower().strip() if isinstance(v, str) else None

        location = LocationContext(
            continent=_norm(location_raw.get("continent")),
            country=_norm(location_raw.get("country")),
            city=_norm(location_raw.get("city")),
        )
    else:
        location = LocationContext()
    data["location_context"] = location

    # 7. Remove unknown keys (Pydantic will ignore them, but be explicit)
    known_fields = set(GarmentAttributes.model_fields.keys())
    filtered = {k: v for k, v in data.items() if k in known_fields}

    try:
        return GarmentAttributes(**filtered)
    except Exception as exc:
        raise ParseError(f"Failed to build GarmentAttributes: {exc}", raw_response=response_text) from exc
