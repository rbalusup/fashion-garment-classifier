"""E2E tests: upload → classify (mocked) → filter.

7 test cases covering the full request lifecycle with no real API calls.
"""

import pytest
from httpx import AsyncClient

from tests.e2e.conftest import MOCK_CLASSIFICATION, create_minimal_png


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def upload(client: AsyncClient, **form_data: str) -> dict:  # type: ignore[type-arg]
    img = create_minimal_png()
    return (
        await client.post(
            "/api/upload",
            files={"file": ("test.png", img, "image/png")},
            data=form_data,
        )
    ).json()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestUploadClassifyFilter:

    # 1. Upload returns Claude-classified garment_type
    async def test_upload_returns_classification(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/upload",
            files={"file": ("t.png", create_minimal_png(), "image/png")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["garment_type"] == MOCK_CLASSIFICATION["garment_type"]
        assert body["style"] == MOCK_CLASSIFICATION["style"]
        assert "id" in body

    # 2. Uploaded item stores user-supplied location metadata
    async def test_upload_stores_location_metadata(self, client: AsyncClient) -> None:
        body = await upload(client, continent="americas", country="usa", city="new york")
        item_id = body["id"]

        get_resp = await client.get(f"/api/garments/{item_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        # User-supplied location takes precedence
        assert data["location_continent"] == "americas"
        assert data["location_country"] == "usa"
        assert data["location_city"] == "new york"

    # 3. Continent filter returns only matching item
    async def test_filter_by_continent_returns_matching_item(self, client: AsyncClient) -> None:
        # Upload two with different continents
        body_eu = await upload(client, continent="europe", country="france", city="paris")
        body_as = await upload(client, continent="asia", country="japan", city="tokyo")

        resp = await client.get("/api/garments?continent=europe")
        assert resp.status_code == 200
        result_ids = {item["id"] for item in resp.json()["items"]}
        assert body_eu["id"] in result_ids
        assert body_as["id"] not in result_ids

    # 4. Year filter returns items from current year
    async def test_filter_by_year_returns_current_year_uploads(self, client: AsyncClient) -> None:
        from datetime import datetime
        current_year = datetime.utcnow().year

        body = await upload(client, continent="oceania", country="australia", city="sydney")

        resp = await client.get(f"/api/garments?year={current_year}")
        assert resp.status_code == 200
        ids = {item["id"] for item in resp.json()["items"]}
        assert body["id"] in ids

    # 5. Full smoke test: upload → classify → filter by continent+country → item in results
    async def test_full_upload_classify_filter_flow(self, client: AsyncClient) -> None:
        body = await upload(client, continent="africa", country="morocco", city="marrakech")
        assert body["garment_type"] == "jacket"  # from mock

        resp = await client.get("/api/garments?continent=africa&country=morocco")
        assert resp.status_code == 200
        ids = {item["id"] for item in resp.json()["items"]}
        assert body["id"] in ids

    # 6. Invalid file type is rejected with 422
    async def test_upload_invalid_file_type_rejected(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/upload",
            files={"file": ("doc.txt", b"not an image", "text/plain")},
        )
        assert resp.status_code == 422

    # 7. Mock is used — no real Anthropic API calls
    async def test_classification_uses_mock_not_real_api(self, client: AsyncClient, mock_classifier) -> None:
        await client.post(
            "/api/upload",
            files={"file": ("x.png", create_minimal_png(), "image/png")},
        )
        # The mock classifier was called once
        mock_classifier.classify_image.assert_called_once()
        # And the garment_type from the mock is what we get
        resp = await client.get("/api/garments?garment_type=jacket")
        assert resp.json()["total"] >= 1
