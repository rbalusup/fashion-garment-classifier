"""
Fashion Garment Classifier — Evaluation Runner

Usage:
    uv run python eval/run_eval.py --download   # Fetch images from Unsplash (idempotent)
    uv run python eval/run_eval.py --run        # Classify images and compare to labels
    uv run python eval/run_eval.py --report     # Print Markdown summary to stdout
    uv run python eval/run_eval.py --download --run --report  # All phases
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import httpx

EVAL_DIR = Path(__file__).parent
IMAGES_DIR = EVAL_DIR / "images"
REPORTS_DIR = EVAL_DIR / "reports"
LABELS_FILE = EVAL_DIR / "labels.json"
SYNONYM_FILE = EVAL_DIR / "synonym_map.json"
RESULTS_FILE = REPORTS_DIR / "eval_results.json"

# Load .env from repo root so ANTHROPIC_API_KEY is available without shell export
_env_file = EVAL_DIR.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

UNSPLASH_BASE = "https://source.unsplash.com/800x1000/"
ATTRIBUTES = ["garment_type", "style", "material", "occasion", "location_context"]

# Fuzzy credit for adjacent categories (0.5 credit instead of 0)
FUZZY_ATTRIBUTES = {"style", "occasion"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_labels() -> dict:
    with open(LABELS_FILE) as f:
        return json.load(f)


def load_synonyms() -> dict:
    with open(SYNONYM_FILE) as f:
        return json.load(f)


def normalize(value: str, attribute: str, synonyms: dict) -> str:
    """Lowercase + synonym-map a single attribute value."""
    v = (value or "").lower().strip()
    attr_map = synonyms.get(attribute, {})
    return attr_map.get(v, v)


def fuzzy_neighbors(attribute: str, canonical: str, synonyms: dict) -> set[str]:
    """Return the set of adjacent canonical values that earn 0.5 credit."""
    neighbors = synonyms.get("fuzzy_neighbors", {}).get(attribute, {})
    return set(neighbors.get(canonical, []))


# ---------------------------------------------------------------------------
# Phase 1: Download images
# ---------------------------------------------------------------------------

def download_images(labels: dict, timeout: int = 20) -> None:
    """Download evaluation images from Unsplash. Idempotent — skips existing files."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    images = labels["images"]
    print(f"[download] {len(images)} images in labels.json")

    downloaded = skipped = failed = 0
    for img in images:
        dest = IMAGES_DIR / img["filename"]
        if dest.exists():
            skipped += 1
            continue

        query = img.get("query", "fashion garment")
        url = img.get("source_url") or f"{UNSPLASH_BASE}?{query.replace(' ', ',')}"
        print(f"  → {img['id']}  {url}")
        try:
            resp = httpx.get(url, timeout=timeout, follow_redirects=True)
            resp.raise_for_status()
            content = resp.content
            # Verify we got an image (Unsplash returns JPEG)
            if not content[:3] in (b"\xff\xd8\xff", b"\x89PN"):
                # Accept any binary blob — Unsplash may vary
                pass
            dest.write_bytes(content)
            downloaded += 1
            # Be polite to Unsplash — no API key needed but rate-limit courtesy
            time.sleep(0.3)
        except Exception as exc:
            print(f"    WARN: failed to download {img['filename']}: {exc}", file=sys.stderr)
            failed += 1

    print(f"[download] done — downloaded={downloaded} skipped={skipped} failed={failed}")


# ---------------------------------------------------------------------------
# Phase 2: Run classifier
# ---------------------------------------------------------------------------

def run_classification(labels: dict, synonyms: dict) -> list[dict]:
    """Classify each image with the real GarmentClassifier and save results."""
    # Import here so the script can be imported/used without API key for --report
    sys.path.insert(0, str(EVAL_DIR.parent / "app" / "api"))

    from fashion_api.garment.classifier import GarmentClassifier
    from fashion_api.garment.models import ParseError

    classifier = GarmentClassifier(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model=os.environ.get("FASHION_CLAUDE_MODEL", "claude-sonnet-4-6"),
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    images = labels["images"]
    results = []

    print(f"[run] classifying {len(images)} images …")
    for i, img in enumerate(images, 1):
        img_path = IMAGES_DIR / img["filename"]
        if not img_path.exists():
            print(f"  [{i}/{len(images)}] SKIP  {img['id']} — image not found")
            results.append({
                "id": img["id"],
                "filename": img["filename"],
                "status": "missing",
                "ground_truth": img["attributes"],
                "predicted": None,
                "scores": {},
            })
            continue

        print(f"  [{i}/{len(images)}] {img['id']} … ", end="", flush=True)
        try:
            attrs, _raw = classifier.classify_image(img_path)
            predicted = {
                "garment_type": attrs.garment_type,
                "style": attrs.style,
                "material": attrs.material,
                "occasion": attrs.occasion,
                "location_context": attrs.location_context.continent
                if hasattr(attrs.location_context, "continent")
                else (attrs.location_context or {}).get("continent", "unknown")
                if isinstance(attrs.location_context, dict)
                else str(attrs.location_context),
            }
            # Normalize predictions
            predicted_norm = {
                attr: normalize(predicted.get(attr, "unknown"), attr, synonyms)
                for attr in ATTRIBUTES
            }
            # Normalize ground truth
            truth_norm = {
                attr: normalize(img["attributes"].get(attr, "unknown"), attr, synonyms)
                for attr in ATTRIBUTES
            }

            scores = _compute_scores(predicted_norm, truth_norm, synonyms)
            print(f"OK  exact={_exact_avg(scores):.2f}")

            results.append({
                "id": img["id"],
                "filename": img["filename"],
                "status": "ok",
                "ground_truth": img["attributes"],
                "ground_truth_norm": truth_norm,
                "predicted_raw": predicted,
                "predicted_norm": predicted_norm,
                "confidence": img.get("labeling_confidence", {}),
                "scores": scores,
            })
        except ParseError as exc:
            print(f"PARSE_ERROR  {exc}")
            results.append({
                "id": img["id"],
                "filename": img["filename"],
                "status": "parse_error",
                "ground_truth": img["attributes"],
                "predicted": None,
                "scores": {},
            })
        except Exception as exc:
            print(f"ERROR  {exc}")
            results.append({
                "id": img["id"],
                "filename": img["filename"],
                "status": "error",
                "error": str(exc),
                "ground_truth": img["attributes"],
                "predicted": None,
                "scores": {},
            })
        # Be polite to the API
        time.sleep(0.5)

    # Persist raw results
    RESULTS_FILE.write_text(json.dumps(results, indent=2))
    print(f"[run] results saved to {RESULTS_FILE}")
    return results


def _compute_scores(predicted: dict, truth: dict, synonyms: dict) -> dict:
    scores = {}
    for attr in ATTRIBUTES:
        p = predicted.get(attr, "unknown")
        t = truth.get(attr, "unknown")
        if p == t:
            scores[attr] = 1.0
        elif attr in FUZZY_ATTRIBUTES and p in fuzzy_neighbors(attr, t, synonyms):
            scores[attr] = 0.5
        else:
            scores[attr] = 0.0
    return scores


def _exact_avg(scores: dict) -> float:
    if not scores:
        return 0.0
    return sum(1.0 if v == 1.0 else 0.0 for v in scores.values()) / len(scores)


# ---------------------------------------------------------------------------
# Phase 3: Report
# ---------------------------------------------------------------------------

def generate_report(results: list[dict] | None = None, synonyms: dict | None = None) -> str:
    if results is None:
        if not RESULTS_FILE.exists():
            return "No results file found. Run `--run` first.\n"
        with open(RESULTS_FILE) as f:
            results = json.load(f)

    if synonyms is None:
        synonyms = load_synonyms()

    ok_results = [r for r in results if r["status"] == "ok"]
    high_conf_results = [
        r for r in ok_results
        if all(
            r.get("confidence", {}).get(a, "low") == "high"
            for a in ATTRIBUTES
        )
    ]

    total = len(results)
    ok = len(ok_results)
    missing = sum(1 for r in results if r["status"] == "missing")
    errors = sum(1 for r in results if r["status"] in ("error", "parse_error"))

    lines = [
        "# Fashion Garment Classifier — Evaluation Report",
        "",
        "## Overview",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total images | {total} |",
        f"| Successfully classified | {ok} |",
        f"| Missing images | {missing} |",
        f"| Errors / parse failures | {errors} |",
        "",
    ]

    if not ok_results:
        lines.append("_No successful classifications to report._\n")
        return "\n".join(lines)

    # Per-attribute accuracy
    lines += [
        "## Per-Attribute Accuracy",
        "",
        "Exact accuracy = fraction of predictions that exactly match ground truth (after synonym normalization).  ",
        "Fuzzy accuracy = exact + 0.5 credit for adjacent categories (style and occasion only).",
        "",
        "| Attribute | Exact | Fuzzy | High-conf Exact | N |",
        "|-----------|------:|------:|----------------:|---|",
    ]

    for attr in ATTRIBUTES:
        exact_scores = [r["scores"].get(attr, 0.0) for r in ok_results]
        fuzzy_scores = [r["scores"].get(attr, 0.0) for r in ok_results]
        exact_acc = sum(1.0 for s in exact_scores if s == 1.0) / len(exact_scores)
        fuzzy_acc = sum(s for s in fuzzy_scores) / len(fuzzy_scores)

        if high_conf_results:
            hc_scores = [r["scores"].get(attr, 0.0) for r in high_conf_results]
            hc_exact = sum(1.0 for s in hc_scores if s == 1.0) / len(hc_scores)
        else:
            hc_exact = float("nan")

        hc_str = f"{hc_exact:.1%}" if high_conf_results else "—"
        lines.append(
            f"| {attr} | {exact_acc:.1%} | {fuzzy_acc:.1%} | {hc_str} | {len(exact_scores)} |"
        )

    # Overall
    all_exact = [
        sum(1.0 for s in r["scores"].values() if s == 1.0) / len(ATTRIBUTES)
        for r in ok_results if r["scores"]
    ]
    all_fuzzy = [
        sum(r["scores"].values()) / len(ATTRIBUTES)
        for r in ok_results if r["scores"]
    ]
    overall_exact = sum(all_exact) / len(all_exact) if all_exact else 0
    overall_fuzzy = sum(all_fuzzy) / len(all_fuzzy) if all_fuzzy else 0
    lines += [
        f"| **Overall** | **{overall_exact:.1%}** | **{overall_fuzzy:.1%}** | — | {ok} |",
        "",
    ]

    # Top-5 errors per attribute
    lines += ["## Top Errors by Attribute", ""]
    for attr in ATTRIBUTES:
        error_counts: dict[tuple[str, str], int] = defaultdict(int)
        for r in ok_results:
            if r["scores"].get(attr, 0.0) < 1.0:
                t = r.get("ground_truth_norm", {}).get(attr, "?")
                p = r.get("predicted_norm", {}).get(attr, "?")
                if p and p != "?":
                    error_counts[(t, p)] += 1

        lines.append(f"### {attr}")
        if not error_counts:
            lines.append("_No errors._")
        else:
            lines += [
                "| Ground Truth | Predicted | Count |",
                "|-------------|-----------|------:|",
            ]
            top5 = sorted(error_counts.items(), key=lambda x: -x[1])[:5]
            for (truth_val, pred_val), cnt in top5:
                lines.append(f"| {truth_val} | {pred_val} | {cnt} |")
        lines.append("")

    lines += [
        "## Notes",
        "",
        "- Images sourced from Unsplash (open license, `source.unsplash.com` endpoint).",
        "- Synonym map normalizes common aliases before comparison (e.g. `blazer` → `jacket`).",
        "- Fuzzy scoring awards 0.5 credit for adjacent categories defined in `synonym_map.json`.",
        "- High-confidence subset: images where all 5 attributes were labeled with confidence=`high`.",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Fashion Garment Classifier evaluation runner")
    parser.add_argument("--download", action="store_true", help="Download images from Unsplash")
    parser.add_argument("--run", action="store_true", help="Run classifier and save results")
    parser.add_argument("--report", action="store_true", help="Print Markdown report to stdout")
    args = parser.parse_args()

    if not any([args.download, args.run, args.report]):
        parser.print_help()
        sys.exit(1)

    labels = load_labels()
    synonyms = load_synonyms()

    results = None

    if args.download:
        download_images(labels)

    if args.run:
        results = run_classification(labels, synonyms)

    if args.report:
        report_md = generate_report(results, synonyms)
        print(report_md)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORTS_DIR / "baseline_report.md"
        report_path.write_text(report_md)
        print(f"\n[report] saved to {report_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
