# CLAUDE.md

## Project

AI-powered fashion garment classification and inspiration library.

**Stack:** Turborepo monorepo | Python 3.12 + FastAPI (app/api) | React 18 + TypeScript + Vite (app/web)

## Commands

```bash
# Start everything
pnpm dev                      # API on :8001, Web on :5173

# Tests
pnpm test:api                 # Python tests (unit + integration + E2E)
cd app/api && uv run pytest tests/ -v

# Lint / format
cd app/api && uv run ruff check fashion_api/ tests/
cd app/api && uv run ruff format fashion_api/ tests/

# Type check
cd app/api && uv run mypy fashion_api/

# Add Python dep
cd app/api && uv add <package>

# Evaluation
cd app/api && uv run python ../../eval/run_eval.py --download
cd app/api && uv run python ../../eval/run_eval.py --run
```

## Project Structure

```
app/api/fashion_api/
  garment/
    models.py      # Pydantic: GarmentAttributes, GarmentRecord, ParseError
    parser.py      # parse_garment_attributes(text) → GarmentAttributes
    classifier.py  # GarmentClassifier: Claude multimodal vision
    router.py      # FastAPI routes: upload, list, get, patch, delete
    annotations.py # FastAPI routes: annotation CRUD
    filters.py     # filter_garments() SQLAlchemy + GET /filters/options
  db/
    models.py      # SQLAlchemy ORM: GarmentORM, AnnotationORM
    session.py     # engine, get_db()
  main.py          # create_app() factory
  config.py        # Settings (FASHION_ env prefix)

tests/
  unit/test_parser.py              # 12 parse cases (no DB, no API)
  integration/test_filters.py      # 16 location + time filter tests
  e2e/test_upload_classify_filter.py  # 7 upload → classify → filter tests
```

## Key Conventions

- **Async throughout** FastAPI routes; classifier is sync (SDK I/O bound)
- **All Anthropic calls mocked in tests** — never make real API calls in tests
- **Images stored** as `uploads/<uuid4>.<ext>` — uuid is the DB key
- **color_palette** stored as JSON text in SQLite; searched via LIKE
- **AI fields** live on `garments` table; designer content on `annotations` table
- **`source="designer"`** on every Annotation — canonical ownership signal
- **`temperature=0.0`** for deterministic classifier output
- **ParseError** is a domain exception; parser never lets raw `json.JSONDecodeError` escape
- **`create_app(testing=True)`** — injects in-memory SQLite for test isolation

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | required | Anthropic API key |
| `FASHION_CLAUDE_MODEL` | `claude-sonnet-4-6` | Vision model |
| `FASHION_DATABASE_URL` | `sqlite:///./fashion.db` | SQLAlchemy URL |
| `FASHION_UPLOAD_DIR` | `uploads` | Image storage dir |
| `FASHION_MAX_UPLOAD_MB` | `10` | Max file size |
| `FASHION_LOG_LEVEL` | `INFO` | Log level |
| `FASHION_DEBUG` | `false` | Debug mode |

## Known Warnings (non-breaking, do not fix unless asked)

- `datetime.utcnow()` used for SQLite timestamps (no timezone awareness needed locally)
- Pydantic v2 class-based `Config` deprecated; use `model_config = ConfigDict(...)` if touching
