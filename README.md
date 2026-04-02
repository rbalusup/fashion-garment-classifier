# Fashion Garment Classifier

AI-powered fashion inspiration library. Upload garment photos, get automatic AI classification via Claude vision, search and filter by attributes, and annotate images with your own notes.

---

## Features

- **AI classification** — Claude `claude-sonnet-4-6` multimodal vision extracts garment type, style, material, color palette, pattern, season, occasion, consumer profile, trend notes, and location context
- **Visual library** — responsive 5-column grid with thumbnail preview and color chips
- **Dynamic filters** — filter by garment type, style, material, pattern, season, occasion, continent/country/city, year
- **Full-text search** — searches description, trend notes, consumer profile, and annotation notes
- **Designer annotations** — add personal tags and observations to any garment with amber-highlighted cards
- **Evaluation framework** — per-attribute accuracy reporting against 72 labeled ground-truth images

---

## Architecture

```
fashion-garment-classifier/          ← monorepo root (Turborepo + pnpm)
├── app/
│   ├── api/                         ← Python 3.12 FastAPI backend
│   │   └── fashion_api/
│   │       ├── main.py              create_app() factory (testing=True for tests)
│   │       ├── config.py            pydantic-settings, FASHION_ env prefix
│   │       ├── garment/
│   │       │   ├── classifier.py    Claude multimodal, tenacity retry
│   │       │   ├── parser.py        JSON extraction + taxonomy normalization
│   │       │   ├── models.py        Pydantic schemas (GarmentOut, AnnotationOut, …)
│   │       │   ├── router.py        POST /upload, GET/PATCH/DELETE /garments
│   │       │   ├── annotations.py   CRUD for designer annotations
│   │       │   └── filters.py       SQLAlchemy queries + GET /filters/options
│   │       └── db/
│   │           ├── session.py       engine factory (StaticPool for tests)
│   │           └── models.py        ORM: GarmentORM, AnnotationORM
│   └── web/                         ← React 18 + TypeScript + Vite + Tailwind CSS
│       └── src/
│           ├── App.tsx              layout shell
│           ├── api/client.ts        typed fetch wrappers
│           ├── types/garment.ts     TypeScript interfaces
│           ├── hooks/               useGarments, useFilters, useAnnotations
│           └── components/
│               ├── GarmentGrid.tsx  responsive grid + loading skeleton
│               ├── GarmentCard.tsx  thumbnail + badge + color chips
│               ├── FilterSidebar.tsx checkbox groups from /api/filters/options
│               ├── SearchBar.tsx    300ms debounced full-text search
│               ├── UploadModal.tsx  drag-and-drop + location metadata
│               ├── DetailModal.tsx  split view: AI blue | Designer amber
│               └── AnnotationPanel.tsx amber card: tag chips + notes
├── eval/
│   ├── labels.json                  72 ground-truth labeled images
│   ├── synonym_map.json             alias → canonical + fuzzy neighbors
│   ├── run_eval.py                  --download | --run | --report
│   └── reports/                     generated eval output
└── tests/
    ├── unit/test_parser.py          12 parser tests (no API/DB deps)
    ├── integration/test_filters.py  17 location + time filter tests
    └── e2e/test_upload_classify_filter.py  7 E2E tests (Anthropic mocked)
```

---

## Tech Stack

| Layer           | Technology                                  |
| --------------- | ------------------------------------------- |
| Monorepo        | Turborepo + pnpm workspaces                 |
| Frontend        | React 18, TypeScript, Vite, Tailwind CSS v3 |
| Backend         | Python 3.12, FastAPI, Uvicorn               |
| Python packages | uv                                          |
| Database        | SQLite via SQLAlchemy 2.0                   |
| AI              | `claude-sonnet-4-6` (multimodal vision)     |
| Config          | pydantic-settings (`FASHION_` env prefix)   |
| Retries         | tenacity (3 attempts, exp backoff 2–10s)    |
| Logging         | structlog                                   |
| API tests       | pytest, pytest-asyncio, httpx AsyncClient   |

---

## Local Setup

### Prerequisites

- Node.js 20+, pnpm (`npm install -g pnpm`)
- Python 3.12+, uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Install

```bash
# JavaScript deps
pnpm install

# Python deps
cd app/api && uv sync && cd ../..
```

### Configure

```bash
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY=sk-ant-...
```

### Run (development)

```bash
pnpm dev
# API  → http://localhost:8001
# Web  → http://localhost:5173
# Docs → http://localhost:8001/docs
```

Turborepo runs the API and web dev servers in parallel. The Vite proxy forwards `/api` and `/uploads` requests to the FastAPI server.

---

## Running Tests

```bash
# All tests via Turborepo
pnpm test

# Python tests only (from repo root)
cd app/api && uv run pytest ../../tests/ -v

# Individual suites
uv run pytest ../../tests/unit/ -v
uv run pytest ../../tests/integration/ -v
uv run pytest ../../tests/e2e/ -v
```

### Test architecture

**Unit tests** (`tests/unit/test_parser.py`, 12 cases) — test `parse_garment_attributes()` in isolation: no database, no Claude API. Covers clean JSON, markdown fences, embedded JSON, missing fields, unknown taxonomy values, case normalization.

**Integration tests** (`tests/integration/test_filters.py`, 17 cases) — use an in-memory SQLite database seeded with 12 garments across 6 continents (Europe, Asia, Americas, Africa, Oceania) and years 2023–2025. Tests verify location hierarchy filters, time filters, and compound filters.

**E2E tests** (`tests/e2e/test_upload_classify_filter.py`, 7 cases) — full ASGI round-trip via `httpx.AsyncClient + ASGITransport`. Anthropic is mocked via `unittest.mock.patch`. Tests cover upload → classify → filter flow, invalid file types, and confirmed mock isolation.

---

## Running the Evaluation

```bash
# 1. Download 72 Unsplash images (idempotent)
cd app/api && uv run python ../../eval/run_eval.py --download

# 2. Classify and save results (requires ANTHROPIC_API_KEY)
uv run python ../../eval/run_eval.py --run

# 3. Print Markdown accuracy report
uv run python ../../eval/run_eval.py --report

# All phases at once
uv run python ../../eval/run_eval.py --download --run --report
```

See `docs/EVAL_METHODOLOGY.md` for full methodology details.

---

## API Reference

| Method   | Path                               | Description                                          |
| -------- | ---------------------------------- | ---------------------------------------------------- |
| `POST`   | `/api/upload`                      | Multipart upload → classify → return GarmentRecord   |
| `GET`    | `/api/garments`                    | Paginated list with full-text search and all filters |
| `GET`    | `/api/garments/{id}`               | Full detail including annotations                    |
| `PATCH`  | `/api/garments/{id}`               | Update designer/year/month fields                    |
| `DELETE` | `/api/garments/{id}`               | Delete record + image file                           |
| `POST`   | `/api/garments/{id}/reclassify`    | Re-run Claude on existing image                      |
| `POST`   | `/api/annotations`                 | Create annotation                                    |
| `GET`    | `/api/annotations/{garment_id}`    | List annotations for garment                         |
| `PATCH`  | `/api/annotations/{annotation_id}` | Edit annotation                                      |
| `DELETE` | `/api/annotations/{annotation_id}` | Delete annotation                                    |
| `GET`    | `/api/filters/options`             | Distinct values per filterable field                 |
| `GET`    | `/uploads/{filename}`              | Serve uploaded image files                           |

**Query params for `GET /api/garments`:** `q` (full-text), `garment_type`, `style`, `material`, `pattern`, `season`, `occasion`, `continent`, `country`, `city`, `year`, `month`, `page`, `page_size`.

---

## Environment Variables

All variables use the `FASHION_` prefix (set in `.env`):

| Variable                | Default                  | Description                     |
| ----------------------- | ------------------------ | ------------------------------- |
| `ANTHROPIC_API_KEY`     | —                        | Required. Anthropic API key     |
| `FASHION_CLAUDE_MODEL`  | `claude-sonnet-4-6`      | Claude model for classification |
| `FASHION_DATABASE_URL`  | `sqlite:///./fashion.db` | SQLAlchemy DB URL               |
| `FASHION_UPLOAD_DIR`    | `uploads`                | Directory for uploaded images   |
| `FASHION_MAX_UPLOAD_MB` | `10`                     | Max upload file size            |
| `FASHION_LOG_LEVEL`     | `INFO`                   | structlog log level             |
| `FASHION_DEBUG`         | `false`                  | FastAPI debug mode              |

---

## Project Structure Notes

- `create_app(testing=True)` uses an in-memory SQLite DB with `StaticPool` so all connections share the same in-memory database — required for `httpx.ASGITransport` which bypasses ASGI lifespan events.
- The parser (`garment/parser.py`) is a pure function with no external dependencies — ideal for fast unit testing without fixtures.
- Color palette is stored as JSON text in the `garments.color_palette` column and deserialized by a Python property on the ORM model.
- The evaluation `--run` phase adds the API source path to `sys.path` before importing `fashion_api` — no installation required.

---

## Evaluation

This section addresses the five key dimensions for evaluating this proof of concept.

### 1. Functionality — Does the core workflow work end to end?

Yes. The full pipeline is operational:

- Upload a JPEG/PNG → stored in `uploads/`, classified by Claude vision, persisted to SQLite
- Browse the visual library with real-time search and multi-attribute filters
- Filter by garment type, style, material, season, pattern, occasion, continent/country/city, year/month
- Add personal annotations to any garment; they appear with amber styling distinct from AI content
- Reclassify an existing image to refresh Claude attributes

Known limitations of this POC:

- SQLite is single-writer; a production deployment would use PostgreSQL
- Images stored on local filesystem; production would use S3
- No user authentication; the system is a single-user personal library

### 2. Model Quality — How well does the classifier perform?

**Evaluation dataset:** 50 fashion images from [pexels.com/search/fashion](https://www.pexels.com/search/fashion/) (Pexels license, open access). Images were visually inspected and manually labeled across 5 attributes.

**Expected per-attribute accuracy** (run `eval/run_eval.py --run --report` to get live numbers):

| Attribute          | Expected Exact | Notes                                                                 |
| ------------------ | -------------: | --------------------------------------------------------------------- |
| `garment_type`     |         80–90% | Most reliable; clear silhouette signal                                |
| `occasion`         |         60–75% | Context-dependent; fuzzy scoring (+0.5 for adjacent) helps            |
| `style`            |         55–70% | Subjective; single-reviewer ground truth                              |
| `material`         |         40–60% | Hardest; fabric texture is often ambiguous in photos                  |
| `location_context` |         45–65% | Inferred geographic design tradition; global fashion makes this noisy |

**Key finding:** Claude excels at structural/categorical attributes (`garment_type`) and struggles with visually ambiguous or subjective ones (`material`, `style`). See `eval/analysis.md` for full analysis.

```bash
# Reproduce the evaluation
cd app/api
uv run python ../../eval/run_eval.py --download   # fetch 50 Pexels images
uv run python ../../eval/run_eval.py --run        # classify + score (needs ANTHROPIC_API_KEY)
uv run python ../../eval/run_eval.py --report     # print Markdown accuracy table
```

### 3. Code Quality — Is it well-structured, readable, and tested?

**Structure:** Clean separation — `garment/` (domain logic), `db/` (ORM), `core/` (config/logging/retry). Each agent concept has its own `models.py`, `router.py`, and `parser.py`.

**Test pyramid:**

- **12 unit tests** (`tests/unit/test_parser.py`): `parse_garment_attributes()` is a pure function — no DB, no API. Tests cover clean JSON, markdown fences, embedded JSON, missing fields, unknown values, malformed input.
- **17 integration tests** (`tests/integration/test_filters.py`): In-memory SQLite seeded with 12 garments; tests verify location hierarchy filters and time filters work correctly.
- **7 E2E tests** (`tests/e2e/test_upload_classify_filter.py`): Full ASGI round-trip via `httpx.AsyncClient`; Anthropic is mocked. Tests verify upload → classify → filter flow end-to-end.

**Type safety:** Strict mypy mode; all functions annotated. Ruff for formatting (line length 100).

**Observability:** Structured logging via `structlog`; retry telemetry via `tenacity` with exponential backoff.

### 4. Product Thinking — Sensible trade-offs for a POC?

| Decision              | Choice                                    | Rationale                                                     |
| --------------------- | ----------------------------------------- | ------------------------------------------------------------- |
| Database              | SQLite                                    | Zero infrastructure for a personal library POC                |
| Storage               | Local filesystem                          | No S3 credentials needed; upgrade path is clear               |
| Image source for eval | Pexels CDN URLs                           | Deterministic, no API key, open license                       |
| LLM output            | Strict JSON prompt                        | Simpler than function calling; works with all Claude versions |
| Test isolation        | `create_app(testing=True)` + `StaticPool` | In-memory DB per test run; no teardown needed                 |
| Monorepo              | Turborepo + pnpm                          | Unified `pnpm dev` starts API + web; one lockfile             |
| UI differentiation    | Blue (AI) / Amber (designer)              | Clear provenance signal; prevents confusion about data origin |

### 5. Communication — Is the README clear and honest about limitations?

Known limitations documented here and in `eval/analysis.md`:

- **Material classification is unreliable** (~40–60% accuracy): fabric texture is often indistinguishable in photos — even for human annotators
- **Style is subjective**: ground truth was labeled by a single reviewer; inter-rater agreement would likely be 60–70%
- **`location_context` is noisy**: geographic design tradition is subtle and increasingly irrelevant as fashion globalizes
- **SQLite concurrency**: single-writer DB; unsuitable for concurrent multi-user access
- **No auth**: single-user; would need authentication before multi-tenant deployment
- **Evaluation sample**: I have considered 50 images are sufficient for this POC but too small for production model selection decisions

- **Not used dataset for images**: TODO: I have scraped the garment specific images from[pexels.com/search/fashion](https://www.pexels.com/search/fashion/) for this work. We could improve this project by getting the fashion related images from [Kaggle](https://www.kaggle.com/datasets/validmodel/indo-fashion-dataset) or [HuggingFace](https://huggingface.co/datasets/ashraq/fashion-product-images-small) wherein ground truth comes from real dataset, then we can build the dataset, load, and map the images to the labels and generate a jsom file out of it to run the evals.

---

## Project images

![Project setup in VSCode](https://github.com/rbalusup/fashion-garment-classifier/blob/main/docs/images/project-in-vscode.png)

![Application Main Page](https://github.com/rbalusup/fashion-garment-classifier/blob/main/docs/images/application-page-1.png)
![Application Detail Page](https://github.com/rbalusup/fashion-garment-classifier/blob/main/docs/images/application-page-2.png)

![Evaluation Test Run CLI1](https://github.com/rbalusup/fashion-garment-classifier/blob/main/docs/images/eval-1.png)
![Evaluation Test Run CLI2](https://github.com/rbalusup/fashion-garment-classifier/blob/main/docs/images/eval-2.png)

![Evaluation Report Run CLI1](https://github.com/rbalusup/fashion-garment-classifier/blob/main/docs/images/eval-report-1.png)
![Evaluation Report Run CLI2](https://github.com/rbalusup/fashion-garment-classifier/blob/main/docs/images/eval-report-2.png)
