"""GarmentClassifier: Claude multimodal vision integration."""

import base64
import json
import mimetypes
from pathlib import Path

import structlog
from anthropic import APIError, Anthropic, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from fashion_api.garment.models import GarmentAttributes, ParseError
from fashion_api.garment.parser import parse_garment_attributes

logger = structlog.get_logger(__name__)

CLASSIFICATION_PROMPT = """You are an expert fashion analyst with deep knowledge of global garment design, textile traditions, and consumer trends. Examine this garment photograph carefully.

Return ONLY a valid JSON object — no prose, no markdown code fences, no extra keys. Use null for any field you cannot determine with confidence.

{
  "description": "A rich 2-4 sentence natural-language description covering silhouette, construction details, distinctive decorative elements, and how the garment might be worn.",
  "garment_type": "One of: dress, skirt, blouse, shirt, t-shirt, jacket, coat, blazer, trousers, jeans, shorts, suit, jumpsuit, cardigan, sweater, hoodie, vest, activewear, swimwear, other",
  "style": "One dominant aesthetic: casual, formal, business-casual, streetwear, athleisure, bohemian, minimalist, vintage, preppy, avant-garde, romantic, classic, folk, other",
  "material": "Primary fabric: cotton, denim, leather, silk, wool, linen, polyester, knit, chiffon, velvet, synthetic-blend, unknown",
  "color_palette": ["List of 2-5 dominant color names or hex codes, most prominent first"],
  "pattern": "One of: solid, stripes, plaid, check, floral, geometric, abstract, animal-print, paisley, tie-dye, embroidered, textured, none",
  "season": "One of: spring/summer, fall/winter, all-season",
  "occasion": "One of: everyday, work, evening, outdoor, sport, beach, formal-event, travel, lounge, unknown",
  "consumer_profile": "Concise demographic + lifestyle description",
  "trend_notes": "1-2 sentences on current or emerging trends this garment represents.",
  "location_context": {
    "continent": "Most likely continent of design origin or cultural inspiration (europe, asia, africa, americas, oceania) or null",
    "country": "Specific country if determinable from design cues or null",
    "city": "Specific fashion city if strongly implied or null"
  }
}"""


def _detect_media_type(image_path: Path) -> str:
    ext = image_path.suffix.lower()
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    return mapping.get(ext, mimetypes.guess_type(str(image_path))[0] or "image/jpeg")


class GarmentClassifier:
    """Classifies a garment image using Claude's multimodal vision API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError)),
        reraise=True,
    )
    def classify_image(self, image_path: str | Path) -> tuple[GarmentAttributes, str]:
        """Classify a garment image.

        Returns:
            (GarmentAttributes, raw_json_str) — structured attributes + raw Claude output
              for audit storage.

        Raises:
            ParseError: If Claude's response cannot be parsed.
            APIError / RateLimitError: After 3 retries.
        """
        path = Path(image_path)
        image_bytes = path.read_bytes()
        media_type = _detect_media_type(path)
        b64_data = base64.standard_b64encode(image_bytes).decode()

        logger.info("classify_start", model=self._model, file=path.name, size_kb=len(image_bytes) // 1024)

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            temperature=0.0,  # type: ignore[arg-type]
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64_data,
                            },
                        },
                        {"type": "text", "text": CLASSIFICATION_PROMPT},
                    ],
                }
            ],
        )

        raw_text = response.content[0].text  # type: ignore[union-attr]
        logger.info("classify_done", model=self._model, file=path.name)

        attributes = parse_garment_attributes(raw_text)
        return attributes, raw_text
