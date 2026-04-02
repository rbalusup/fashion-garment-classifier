# Fashion Garment Classifier — Evaluation Report

## Overview

| Metric | Value |
|--------|-------|
| Total images | 50 |
| Successfully classified | 48 |
| Missing images | 0 |
| Errors / parse failures | 2 |

## Per-Attribute Accuracy

Exact accuracy = fraction of predictions that exactly match ground truth (after synonym normalization).  
Fuzzy accuracy = exact + 0.5 credit for adjacent categories (style and occasion only).

| Attribute | Exact | Fuzzy | High-conf Exact | N |
|-----------|------:|------:|----------------:|---|
| garment_type | 64.6% | 64.6% | 0.0% | 48 |
| style | 66.7% | 70.8% | 0.0% | 48 |
| material | 64.6% | 64.6% | 0.0% | 48 |
| occasion | 89.6% | 93.8% | 100.0% | 48 |
| location_context | 66.7% | 66.7% | 100.0% | 48 |
| **Overall** | **70.4%** | **72.1%** | — | 48 |

## Top Errors by Attribute

### garment_type
| Ground Truth | Predicted | Count |
|-------------|-----------|------:|
| suit | jacket | 3 |
| sweater | shirt | 2 |
| blouse | shirt | 2 |
| dress | blouse | 1 |
| dress | shirt | 1 |

### style
| Ground Truth | Predicted | Count |
|-------------|-----------|------:|
| formal | romantic | 3 |
| casual | minimalist | 3 |
| casual | preppy | 1 |
| casual | vintage | 1 |
| bohemian | casual | 1 |

### material
| Ground Truth | Predicted | Count |
|-------------|-----------|------:|
| cotton | linen | 4 |
| synthetic-blend | cotton | 3 |
| denim | cotton | 2 |
| synthetic-blend | velvet | 1 |
| synthetic-blend | silk | 1 |

### occasion
| Ground Truth | Predicted | Count |
|-------------|-----------|------:|
| outdoor | everyday | 2 |
| evening | formal-event | 1 |
| sport | everyday | 1 |
| everyday | outdoor | 1 |

### location_context
| Ground Truth | Predicted | Count |
|-------------|-----------|------:|
| americas | europe | 5 |
| europe | americas | 4 |
| unknown | europe | 2 |
| asia | americas | 2 |
| africa | europe | 1 |

## Notes

- Images sourced from Unsplash (open license, `source.unsplash.com` endpoint).
- Synonym map normalizes common aliases before comparison (e.g. `blazer` → `jacket`).
- Fuzzy scoring awards 0.5 credit for adjacent categories defined in `synonym_map.json`.
- High-confidence subset: images where all 5 attributes were labeled with confidence=`high`.
