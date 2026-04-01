"""Unit tests for parse_garment_attributes().

All 12 cases test the parser in isolation — no DB, no API, no Anthropic calls.
"""

import json

import pytest

from fashion_api.garment.models import ParseError
from fashion_api.garment.parser import parse_garment_attributes

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FULL_JSON = {
    "garment_type": "jacket",
    "style": "streetwear",
    "material": "denim",
    "color_palette": ["indigo", "black"],
    "pattern": "solid",
    "season": "fall/winter",
    "occasion": "everyday",
    "consumer_profile": "urban youth",
    "trend_notes": "Oversized silhouettes dominate SS25.",
    "description": "An oversized denim jacket with distressed detailing.",
    "location_context": {"continent": "Europe", "country": "France", "city": "Paris"},
}


def make_json(**overrides: object) -> str:
    data = {**FULL_JSON, **overrides}
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


class TestParseGarmentAttributes:
    # 1. Happy path — clean JSON, all fields
    def test_clean_json_all_fields(self) -> None:
        result = parse_garment_attributes(make_json())
        assert result.garment_type == "jacket"
        assert result.style == "streetwear"
        assert result.material == "denim"
        assert result.color_palette == ["indigo", "black"]
        assert result.location_context.continent == "europe"
        assert result.location_context.country == "france"
        assert result.location_context.city == "paris"

    # 2. Markdown ```json fence stripped
    def test_markdown_json_fence_stripped(self) -> None:
        raw = f"```json\n{make_json()}\n```"
        result = parse_garment_attributes(raw)
        assert result.garment_type == "jacket"
        assert result.material == "denim"

    # 3. Markdown ``` (no language tag) stripped
    def test_markdown_plain_fence_stripped(self) -> None:
        raw = f"```\n{make_json()}\n```"
        result = parse_garment_attributes(raw)
        assert result.garment_type == "jacket"

    # 4. JSON embedded after a prose sentence
    def test_json_embedded_in_prose(self) -> None:
        raw = f"Here are the garment attributes: {make_json()}"
        result = parse_garment_attributes(raw)
        assert result.garment_type == "jacket"
        assert result.style == "streetwear"

    # 5. Missing optional field defaults to "unknown"
    def test_missing_optional_material_defaults_to_unknown(self) -> None:
        data = {k: v for k, v in FULL_JSON.items() if k != "material"}
        result = parse_garment_attributes(json.dumps(data))
        assert result.material == "unknown"

    # 6. Missing required field (garment_type) raises ParseError
    def test_missing_garment_type_raises_parse_error(self) -> None:
        data = {k: v for k, v in FULL_JSON.items() if k != "garment_type"}
        with pytest.raises(ParseError, match="garment_type"):
            parse_garment_attributes(json.dumps(data))

    # 7. Malformed/truncated JSON raises ParseError
    def test_malformed_json_raises_parse_error(self) -> None:
        raw = '{"garment_type": "jacket", "style": "streetwear"'  # truncated
        with pytest.raises(ParseError):
            parse_garment_attributes(raw)

    # 8. Plain text with no JSON raises ParseError
    def test_plain_text_no_json_raises_parse_error(self) -> None:
        with pytest.raises(ParseError):
            parse_garment_attributes("I cannot classify this image due to insufficient detail.")

    # 9. Capitalized values normalized to lowercase
    def test_capitalized_values_normalized_to_lowercase(self) -> None:
        raw = make_json(garment_type="Jacket", style="StreetWear", material="Denim")
        result = parse_garment_attributes(raw)
        assert result.garment_type == "jacket"
        assert result.style == "streetwear"
        assert result.material == "denim"

    # 10. Unknown taxonomy value stored with validation warning
    def test_unknown_taxonomy_value_stored_with_warning(self) -> None:
        raw = make_json(garment_type="kilt")
        result = parse_garment_attributes(raw)
        assert result.garment_type == "kilt"
        assert any("kilt" in w for w in result.validation_warnings)

    # 11. Extra fields from Claude are ignored
    def test_extra_fields_ignored(self) -> None:
        data = {**FULL_JSON, "confidence": 0.95, "model_notes": "High certainty"}
        result = parse_garment_attributes(json.dumps(data))
        assert result.garment_type == "jacket"
        assert not hasattr(result, "confidence")
        assert not hasattr(result, "model_notes")

    # 12. Partial data — only garment_type + material present; rest filled with "unknown"
    def test_partial_data_fills_unknowns(self) -> None:
        raw = json.dumps({"garment_type": "jeans", "material": "denim"})
        result = parse_garment_attributes(raw)
        assert result.garment_type == "jeans"
        assert result.material == "denim"
        assert result.style == "unknown"
        assert result.occasion == "unknown"
        assert result.season == "unknown"
        assert result.location_context.continent is None
