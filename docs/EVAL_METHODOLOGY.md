# Evaluation Methodology

This document describes how the Fashion Garment Classifier is evaluated against labeled ground-truth data.

---

## Dataset

### Source

Images are sourced from **Pexels** ([pexels.com/search/fashion](https://www.pexels.com/search/fashion/)) — free to use under the Pexels license, no API key required for direct CDN access. Each image is downloaded at `800px` wide via its direct CDN URL:

```
https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg?auto=compress&cs=tinysrgb&w=800
```

Unlike query-based image search (which returns different images each time), Pexels CDN URLs are deterministic: the same URL always yields the same image. This makes the evaluation reproducible across runs.

### Size

50 labeled images covering:

| Dimension | Coverage |
|-----------|----------|
| Garment types | 11 of 13 taxonomy values |
| Styles | 8 of 10 taxonomy values |
| Materials | 6 of 10 taxonomy values |
| Occasions | 7 of 9 taxonomy values |
| Location contexts | 5 of 6 (all continents present) |

### Storage

Images are downloaded to `eval/images/pexels-{id}.jpg` (gitignored). The download phase is idempotent — existing files are skipped. The Pexels ID is preserved in the filename for traceability.

### Labeling

Labels are in `eval/labels.json` (version 1.1). Each image record includes:

- `id` — sequential identifier (`img_001` … `img_050`)
- `filename` — local filename (`pexels-{id}.jpg`)
- `pexels_id` — numeric Pexels photo ID
- `source_url` — full CDN URL for deterministic download
- `attributes` — ground-truth values for all 5 evaluated attributes
- `labeling_confidence` — `high`, `medium`, or `low` per attribute

**Labeling process:** All 50 images were visually inspected and labeled by a human reviewer. Thumbnails (200px) were examined per image; labels reflect what is clearly visible in the photograph. The `labeling_confidence` field captures uncertainty.

Confidence is based on:
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
5. **location_context** — geographic design tradition of the garment (`europe`, `asia`, `americas`, `africa`, `oceania`, `unknown`). This maps to what Claude's `location_context.continent` field returns (the inferred cultural/geographic origin of the design), not the literal photo background/setting.

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
