"""E2E test fixtures: mocked Anthropic + in-memory DB + ASGI test client."""

import json
import struct
import zlib
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from fashion_api.main import create_app

# Canned Claude response for all upload tests
MOCK_CLASSIFICATION = {
    "garment_type": "jacket",
    "style": "streetwear",
    "material": "denim",
    "color_palette": ["indigo", "#1a1a2e"],
    "pattern": "solid",
    "season": "fall/winter",
    "occasion": "everyday",
    "consumer_profile": "urban youth aged 18-30",
    "trend_notes": "Oversized silhouettes dominate the current cycle.",
    "description": "An oversized denim jacket with subtle distressed details.",
    "location_context": {"continent": "europe", "country": "france", "city": "paris"},
}


def create_minimal_jpeg() -> bytes:
    """Return a tiny but valid JPEG image (1x1 white pixel) for upload tests."""
    # Minimal JPEG: SOI + APP0 + SOF0 + DHT + SOS + EOI
    # Simplest approach: create a 1x1 PNG-like buffer using raw bytes
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
        b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
        b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e"
        b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
        b"\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04"
        b"\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa"
        b'\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br'
        b"\x82\t\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZ"
        b"cdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95"
        b"\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3"
        b"\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca"
        b"\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7"
        b"\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa"
        b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd9"
    )


def create_minimal_png() -> bytes:
    """Return a tiny 1x1 white pixel PNG."""
    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat_data = zlib.compress(b"\x00\xff\xff\xff")
    idat = chunk(b"IDAT", idat_data)
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


@pytest.fixture
def mock_classifier():
    """Patch GarmentClassifier so no real API calls are made."""
    with patch("fashion_api.garment.router._get_classifier") as mock_factory:
        instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(MOCK_CLASSIFICATION))]
        # classifier.classify_image returns (GarmentAttributes, raw_json)
        from fashion_api.garment.parser import parse_garment_attributes
        attrs = parse_garment_attributes(json.dumps(MOCK_CLASSIFICATION))
        instance.classify_image.return_value = (attrs, json.dumps(MOCK_CLASSIFICATION))
        mock_factory.return_value = instance
        yield instance


@pytest.fixture
async def client(mock_classifier):
    """AsyncClient against a test app with in-memory SQLite."""
    import fashion_api.db.models  # noqa: F401 — ensures ORM tables registered on Base

    app = create_app(testing=True)

    # ASGITransport does not trigger ASGI lifespan, so create tables explicitly
    from fashion_api.db.session import Base
    Base.metadata.create_all(bind=app.state.engine)

    # Ensure upload dir exists
    from pathlib import Path
    Path(app.state.settings.upload_dir).mkdir(parents=True, exist_ok=True)

    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
    ) as c:
        yield c
