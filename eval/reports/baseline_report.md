# Fashion Garment Classifier — Evaluation Report (Baseline)

> **Status:** Pre-run placeholder. This file will be overwritten when `uv run python eval/run_eval.py --run --report` is executed with a valid `ANTHROPIC_API_KEY`.

## Overview

| Metric | Value |
|--------|-------|
| Total images | 72 |
| Successfully classified | — |
| Missing images | — |
| Errors / parse failures | — |

## Per-Attribute Accuracy

_Run `eval/run_eval.py --run --report` to populate this table._

| Attribute | Exact | Fuzzy | High-conf Exact | N |
|-----------|------:|------:|----------------:|---|
| garment_type | — | — | — | 72 |
| style | — | — | — | 72 |
| material | — | — | — | 72 |
| occasion | — | — | — | 72 |
| location_context | — | — | — | 72 |
| **Overall** | **—** | **—** | — | 72 |

## Expected Performance (Design Targets)

Based on Claude's multimodal vision capabilities and the taxonomy design:

| Attribute | Expected Exact Range | Rationale |
|-----------|---------------------|-----------|
| garment_type | 80–90% | Visually unambiguous; taxonomy matches common categories |
| style | 55–70% | Subjective; fuzzy scoring helps with adjacent categories |
| material | 45–65% | Often uncertain from photos; many `unknown` ground-truths |
| occasion | 60–75% | Contextual; fuzzy scoring closes gap for adjacent uses |
| location_context | 65–80% | Background context usually visible |

## Notes

- Synonym map in `eval/synonym_map.json` normalizes ~120 aliases before scoring.
- Fuzzy scoring (0.5 credit) applied to `style` and `occasion` for adjacent categories.
- High-confidence subset: images where all 5 attributes labeled `confidence=high`.
- See `docs/EVAL_METHODOLOGY.md` for full methodology.
