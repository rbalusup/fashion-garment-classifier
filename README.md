# Fashion Garment Classifier

AI-powered fashion inspiration library. Upload garment photos, get automatic AI classification,
search and filter by attributes, and annotate images with your own notes.

## Architecture

```
Turborepo monorepo
├── app/api    Python 3.12 + FastAPI + SQLite + Claude vision
└── app/web    React 18 + TypeScript + Vite + Tailwind CSS
```

**Pipeline:** Upload → Base64 encode → Claude claude-3-5-sonnet-20241022 → Parse JSON →
Store in SQLite → Serve via REST API → Display in React grid

## Quick Start

### Prerequisites
- Node.js 20+ and pnpm (`npm install -g pnpm`)
- Python 3.12+ and uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Anthropic API key

### Setup

```bash
# 1. Install JS dependencies
pnpm install

# 2. Install Python dependencies
cd app/api && uv sync && cd ../..

# 3. Configure environment
cp .env.example app/api/.env
# Edit app/api/.env and set ANTHROPIC_API_KEY

# 4. Start development servers
pnpm dev
#  API  → http://localhost:8001
#  Web  → http://localhost:5173
#  Docs → http://localhost:8001/docs
```

## Running Tests

```bash
# All tests
pnpm test:api        # Python: unit + integration + E2E

# Individual suites
cd app/api
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
uv run pytest tests/e2e/ -v
uv run pytest tests/ --cov=fashion_api --cov-report=term-missing
```

## Model Evaluation

```bash
cd app/api

# Download test images (one-time, ~60-80 images from Unsplash)
uv run python ../../eval/run_eval.py --download

# Run classifier against labeled test set (requires ANTHROPIC_API_KEY)
uv run python ../../eval/run_eval.py --run

# Print Markdown summary
uv run python ../../eval/run_eval.py --report
```

See [eval/reports/](eval/reports/) for the baseline evaluation report.

## Key Architectural Choices

| Decision | Rationale |
|---|---|
| **SQLite** | Zero-config local storage; easy to swap for Postgres via `FASHION_DATABASE_URL` |
| **Turborepo** | Orchestrates Python + React dev tasks from a single `pnpm dev` command |
| **Claude claude-3-5-sonnet-20241022** | Best multimodal vision for structured attribute extraction |
| **Pydantic parser** | Decoupled from HTTP layer; testable in isolation with 12 unit test cases |
| **Exact + fuzzy eval** | Exact match baseline + fuzzy credit for subjective attributes (style, occasion) |
| **AI vs designer colors** | Blue = AI output, Amber = designer annotations — consistent throughout UI |

## API Reference

```
POST   /api/upload                    Upload image → AI classification
GET    /api/garments                  List/search (q, garment_type, continent, year, ...)
GET    /api/garments/{id}             Full detail with annotations
PATCH  /api/garments/{id}             Update designer/year/month
DELETE /api/garments/{id}             Remove
POST   /api/garments/{id}/reclassify  Re-run Claude
POST   /api/annotations               Add designer annotation
GET    /api/annotations/{garment_id}  List annotations
PATCH  /api/annotations/{id}          Edit annotation
DELETE /api/annotations/{id}          Delete annotation
GET    /api/filters/options           Dynamic filter values from DB
```

Full OpenAPI docs at `http://localhost:8001/docs` when running.

## Evaluation Summary

See [eval/reports/baseline_report.md](eval/reports/baseline_report.md) after running the eval.

Quick results from the baseline run:

| Attribute | Exact Acc | Notes |
|---|---|---|
| garment_type | ~85% | Strong; jacket/coat confusion |
| location_context | ~80% | Studio vs indoor-home confusion |
| occasion | ~74% | Fuzzy gain shows subjective overlap |
| style | ~70% | streetwear/casual boundary hardest |
| material | ~63% | Silk vs synthetic visually ambiguous |
