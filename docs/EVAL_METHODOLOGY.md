# Evaluation Methodology

This document describes how the Fashion Garment Classifier is evaluated against labeled ground-truth data.

---

## Dataset

### Source

Images are sourced from **Unsplash** via the `source.unsplash.com` endpoint — open license, no API key required, programmatic access. Each image is requested at `800×1000px` with a fashion-specific query string (e.g. `denim jacket streetwear`, `floral summer dress`).

### Size

72 labeled images covering:

| Dimension | Coverage |
|-----------|----------|
| Garment types | all 13 taxonomy values |
| Styles | all 10 taxonomy values |
| Materials | 9 of 10 taxonomy values |
| Occasions | all 9 taxonomy values |
| Location contexts | all 10 taxonomy values |

### Storage

Images are stored as `eval/images/<filename>.jpg` (gitignored). The download phase is idempotent — existing files are skipped. Filenames are pseudo-random hex strings to avoid query-string leakage into model prompts.

### Labeling

Labels are in `eval/labels.json`. Each image record includes:

- `id` — sequential identifier (`img_001` … `img_072`)
- `filename` — local filename
- `query` — Unsplash search query used to fetch the image (for human review)
- `attributes` — ground-truth values for all 5 evaluated attributes
- `labeling_confidence` — `high`, `medium`, or `low` per attribute, set during manual review

Labeling was performed manually. Confidence is based on:
- **high** — attribute is unambiguous and clearly visible
- **medium** — attribute is likely but could be interpreted differently
- **low** — attribute is a best guess with meaningful uncertainty

---

## Evaluated Attributes

Five attributes are evaluated:

1. **garment_type** — primary category (dress, jacket, coat, shirt, blouse, sweater, trousers, jeans, shorts, skirt, suit, jumpsuit, other)
2. **style** — aesthetic style (casual, formal, business-casual, streetwear, athleisure, bohemian, minimalist, vintage, preppy, other)
3. **material** — primary fabric/material (cotton, denim, leather, silk, wool, linen, polyester, knit, synthetic-blend, unknown)
4. **occasion** — intended use context (everyday, work, evening, outdoor, sport, beach, formal-event, travel, unknown)
5. **location_context** — photo environment (street, studio, indoor-home, office, outdoor-nature, cafe-restaurant, event-venue, beach, gym, unknown)

---

## Normalization

Claude's output is normalized before comparison via `eval/synonym_map.json`:

1. **Lowercase + strip whitespace** — applied to all values
2. **Synonym map** — common aliases are mapped to canonical taxonomy values. Examples:
   - `blazer` → `jacket`
   - `gown` → `dress`
   - `satin` → `silk`
   - `smart casual` → `business-casual`
   - `tuxedo` → `suit`
3. **Unknown values** — if Claude returns a value not in the taxonomy and not in the synonym map, it is kept as-is (scores 0 for exact match)

The same normalization is applied to ground-truth labels to handle any labeling inconsistencies.

---

## Scoring

### Exact Match

A prediction scores **1.0** if, after normalization, it exactly matches the ground-truth label.

```
exact_accuracy(attr) = count(predictions == truth) / total_predictions
```

### Fuzzy Match (partial credit)

For **style** and **occasion** only, adjacent categories earn **0.5 credit**. Adjacency is defined in `synonym_map.json` under `fuzzy_neighbors`:

| Attribute | Example adjacencies |
|-----------|---------------------|
| style | `business-casual` ↔ `formal`, `casual` ↔ `streetwear` |
| occasion | `work` ↔ `everyday`, `evening` ↔ `formal-event` |

```
fuzzy_accuracy(attr) = (count(exact) × 1.0 + count(adjacent) × 0.5) / total
```

### Overall Accuracy

The overall accuracy is the mean per-attribute score across all 5 attributes.

### High-Confidence Subset

A separate accuracy figure is reported for images where all 5 attributes were labeled with `confidence=high`. This provides an upper bound on achievable accuracy by excluding ambiguous cases.

---

## Report Format

The `--report` phase outputs a Markdown table:

| Attribute | Exact | Fuzzy | High-conf Exact | N |
|-----------|------:|------:|----------------:|---|
| garment_type | X% | X% | X% | 72 |
| style | X% | X% | X% | 72 |
| … | … | … | … | … |
| **Overall** | **X%** | **X%** | — | 72 |

Followed by a **Top-5 Errors** table per attribute showing the most common ground-truth → predicted mismatches.

---

## Running the Evaluation

```bash
# From repo root, with Python env activated:
cd app/api

# Phase 1: Download (idempotent)
uv run python ../../eval/run_eval.py --download

# Phase 2: Classify (costs API tokens, ~72 Claude calls)
uv run python ../../eval/run_eval.py --run

# Phase 3: Report (reads eval/reports/eval_results.json)
uv run python ../../eval/run_eval.py --report
```

Raw per-image results are saved to `eval/reports/eval_results.json` after `--run`.
The Markdown report is saved to `eval/reports/baseline_report.md` after `--report`.

---

## Limitations

- **Unsplash image variability**: `source.unsplash.com` returns a different image each time if the URL is not cached. The `--download` phase saves the image permanently to avoid re-fetching, but initial downloads may vary from run to run.
- **Labeling subjectivity**: fashion categorization is inherently ambiguous. Labels reflect one annotator's interpretation.
- **Color and material**: Claude can observe color but often cannot determine exact material from a photo alone; `unknown` is expected for material on many images.
- **location_context**: evaluated as the `continent` field from Claude's `location_context` object, which maps to the photo's visual background rather than geographic origin.
