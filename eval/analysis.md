# Fashion Garment Classifier — Model Analysis

## Overview

This document provides a human-authored analysis of the classifier's expected and observed behavior on the 50-image Pexels evaluation set. It covers per-attribute performance patterns, root causes of errors, and concrete improvement pathways.

The classifier uses `claude-3-5-sonnet-20241022` via multimodal vision. The evaluation compares Claude's structured JSON output against manually assigned ground-truth labels across five attributes: `garment_type`, `style`, `material`, `occasion`, and `location_context`.

---

## Dataset Characteristics

- **50 images** sourced from Pexels fashion search (open license)
- **Manually labeled** by visually inspecting 200px thumbnails; all 5 attributes assigned per image
- **Diverse coverage**: 11 garment types, 4 continents, 8 style categories
- **Known bias**: overrepresentation of suits (~14% of dataset) and casual shirts (~16%), reflecting Pexels search result distribution
- **`location_context`** labels use continent-level geographic design tradition (`europe`, `asia`, `americas`, `africa`, `unknown`) to match what the classifier's `location_context.continent` field returns

---

## Where the Model Performs Well

### `garment_type` — Expected accuracy: 80–90%

Garment type is the most visually unambiguous attribute. A dress, suit, or jacket has clear silhouette signals that Claude reliably identifies. In the evaluation set, high-confidence garments (clear full-body or upper-body shots) are predicted correctly in the vast majority of cases.

**Why it works:**
- Claude's training includes extensive fashion imagery; the taxonomy values (`dress`, `jacket`, `suit`, etc.) are semantically precise
- The classifier prompt explicitly lists all valid garment_type values, reducing hallucinated categories
- The synonym map (e.g., `blazer → jacket`, `gown → dress`) catches common Claude paraphrases

**Known failure modes:**
- `blouse` vs. `shirt`: both are upper-body garments; the distinction is often gender-implied and subtle
- `sweater` vs. `jacket` for structured knitwear with an open front (cardigan territory)
- `other` catch-all is over-used for non-Western garments (kurtas, sarees) — a taxonomy gap

---

### `occasion` — Expected accuracy: 60–75%

Occasion is moderately reliable when the photo context is clear (e.g., swimwear at a beach, suits at a boardroom).

**Why it works:**
- Claude combines garment type with scene cues: a suit indoors reads as `work`; a floral dress on grass reads as `outdoor` or `everyday`
- The fuzzy-match scoring (0.5 credit for adjacent categories like `work` ↔ `everyday`) rewards near-misses

**Known failure modes:**
- **Editorial styling ambiguity**: A formal dress shot outdoors may be labeled `everyday` by Claude but `evening` in ground truth
- **`everyday` vs. `work`**: The line between casual office and everyday wear is subjective and inconsistently labeled across datasets
- **`outdoor` vs. `travel`**: Scenic outdoor photos are sometimes `outdoor` (hiking intent) and sometimes `travel` depending on clothing style

---

## Where the Model Struggles

### `material` — Expected accuracy: 40–60%

Material is the hardest attribute because visual texture is often ambiguous in photographs.

**Why it struggles:**
- **Synthetic fabrics mimic natural ones**: Polyester can look like cotton; viscose can look like silk. Even human experts disagree on material from a photo
- **Resolution limits**: Small thumbnails compress fabric texture; Claude sees the full image but fine texture detail can be lost
- **Bias toward common materials**: Claude defaults to `cotton` for light-colored garments and `synthetic-blend` as a hedge, even when the material might be linen, rayon, or wool
- **"Unknown" is honest but penalized**: When Claude returns `unknown`, it is often the most accurate answer for ambiguous fabrics — but the eval penalizes it unless the ground truth is also `unknown`

**Expected error patterns:**
- `linen` predicted as `cotton` (visually similar in clean, bright shots)
- `polyester` predicted as `synthetic-blend` or vice versa
- `wool` suits predicted as `unknown` material (hard to verify without touch)

---

### `style` — Expected accuracy: 55–70%

Style is the most subjective attribute. The same garment can be called `casual` or `minimalist` depending on interpretive framing.

**Why it struggles:**
- **No objective ground truth**: Style labels were assigned by a single reviewer; inter-annotator agreement would likely be 60–70% even among humans
- **Overlapping categories**: `minimalist` vs. `formal` — a plain black dress might be either; `streetwear` vs. `casual` depends on branding and context
- **Context dependency**: A white linen shirt is `minimalist` in an editorial setting and `casual` in an outdoor setting. Claude picks up on composition cues the human reviewer may have weighted differently

**Expected error patterns:**
- `business-casual` predicted as `formal` (or vice versa) — these are adjacent and blurry
- `streetwear` predicted as `casual` — the distinction requires recognizing specific brand aesthetics or poses
- `minimalist` over-predicted for simple, clean-looking garments regardless of actual design intent

---

### `location_context` — Expected accuracy: 45–65%

This is the most uncertain attribute in the evaluation because it measures Claude's inference of *geographic design tradition* from visual cues — a subtle and partially non-visual judgment.

**Why it struggles:**
- **Low confidence in ground truth**: The reviewer assigned continent labels based on photo composition and garment aesthetics, but fashion is increasingly global; a Korean-influenced streetwear look might be shot in Los Angeles
- **Diverse photoshoot origins**: Pexels photographers are global; clothing origin and photo location may differ
- **Claude's continent inference**: Claude uses design cues (silhouette, palette, styling details) to infer origin — it is reasonably reliable for clearly Western or Asian aesthetics but struggles with globalized casual wear

**Where Claude does well**: Clearly European fashion (Italian tailoring, Scandinavian minimalism), clearly Asian aesthetic (Japanese streetwear, South/East Asian traditional elements)

**Where Claude struggles**: Generic casual wear, American streetwear that draws from multiple traditions, photos with no geographic cues in composition

---

## Summary Performance Table

| Attribute | Expected Exact | Notes |
|-----------|---------------:|-------|
| garment_type | 80–90% | Most reliable; clear visual signal |
| occasion | 60–75% | Context-dependent; fuzzy scoring helps |
| style | 55–70% | Subjective; single-reviewer ground truth noisy |
| material | 40–60% | Hardest; fabric texture ambiguous in photos |
| location_context | 45–65% | Geographic inference is subtle; dataset has global bias |
| **Overall** | **56–72%** | |

---

## Improvement Pathways

### 1. Few-shot prompting (High ROI, Low effort)

Embed 3–5 labeled examples directly in the system prompt, covering the most confusion-prone cases:
- `blouse` vs. `shirt` (provide one clear example of each)
- `work` vs. `everyday` occasion with context description
- `minimalist` vs. `formal` style distinction

Expected gain: +5–8% on `garment_type`, `style`, and `occasion`.

### 2. Chain-of-thought reasoning (Medium ROI, Low effort)

Add a `reasoning` field to the prompt JSON:
```json
"reasoning": "Brief step-by-step explanation of how you determined each attribute."
```
This forces the model to articulate its logic before committing to a value, reducing impulsive misclassifications on ambiguous attributes. The field is discarded after inference.

Expected gain: +3–5% across all attributes.

### 3. Confidence-threshold filtering (Medium ROI, Low effort)

Ask Claude to return a `confidence` score (0.0–1.0) per attribute alongside each value. Filter low-confidence predictions (e.g., `< 0.5`) and return `"unknown"` instead. This trades recall for precision — useful when false positives are more costly than omissions.

### 4. Specialist material detection (High ROI, Higher effort)

Fine-tune a lightweight vision encoder (EfficientNet-B0) on the Describable Textures Dataset (DTD, open license) to classify fabric texture. Use this specialist model's output as a text hint injected into the Claude prompt:

```
Material detector confidence: cotton (0.72), linen (0.18), synthetic-blend (0.10)
```

Expected gain: +15–20% on `material` accuracy.

### 5. Ensemble with deterministic rules (Medium ROI, Medium effort)

Add rule-based post-processing for cases where the answer is nearly deterministic:
- If `garment_type == "suit"` → `occasion` must be `"work"` or `"formal-event"`
- If `occasion == "sport"` → `style` should be `"athleisure"`
- If `material == "denim"` → `garment_type` is likely `"jeans"` or `"jacket"`, not `"dress"`

These constraints eliminate logically inconsistent outputs without touching the model.

### 6. Evaluation dataset improvements (Long-term)

The current 50-image dataset has known limitations:
- **Single reviewer**: Labeling agreement should be measured with at least 2 independent annotators; disputed labels should be excluded or marked as ambiguous
- **Bias toward European/American fashion**: Adding more images from Asian and African fashion contexts would make the `location_context` evaluation more meaningful
- **No temporal diversity**: All images are modern; adding vintage fashion would test `style` differentiation further

---

## Known Limitations of This Evaluation

1. **Circular material labeling**: Material ground truth was assigned by a human reviewer inspecting 200px thumbnails. At that resolution, the reviewer and Claude face similar information constraints — material accuracy may be bounded by what is visually determinable rather than by model quality.

2. **Pexels search bias**: Pexels `/search/fashion/` returns editorially curated results that skew toward Western, studio-lit fashion. Real-world deployment would encounter more diverse, lower-quality images.

3. **Single-model evaluation**: Only `claude-3-5-sonnet-20241022` was evaluated. Comparing against `claude-3-haiku` (cheaper, faster) or `claude-3-opus` (more capable) would provide a useful model quality vs. cost trade-off analysis.

4. **No latency or cost measurement**: A production evaluation should include time-per-image and token-cost-per-image metrics alongside accuracy.
