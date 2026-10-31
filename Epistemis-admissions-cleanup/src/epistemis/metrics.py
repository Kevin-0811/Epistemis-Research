import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import median

from .classifier import analyze_input
from .preprocessor import preprocess

def run_pipeline(input_file, debug_path=None):

    data = preprocess(input_file, debug_path=debug_path)
    sentences = data["sentences"]

    results = analyze_input(sentences)

    return sentences, results

def compute_document_metrics(sentences, results):

    total_sentences = len(sentences)

    valid_sentences = [
        s for s in sentences
        if not s.get("excluded") and not s.get("is_metadata") and not s.get("is_header")
    ]

    analyzed_sentences = len(results)

    # =========================
    # COUNTS
    # =========================

    E_counts = Counter(s["epistemic_mode"] for s in valid_sentences)
    F_counts = Counter(r["label"] for r in results)

    A_counts = Counter()
    M_counts = Counter()

    for r in results:
        A_counts.update(r["features"]["A_labels"])
        M_counts.update(r["features"]["M_labels"])

    # =========================
    # ANCHORS
    # =========================

    anchor_sentences = [s for s in valid_sentences if s.get("has_anchor")]
    linked_sentences = [s for s in valid_sentences if s.get("linked_anchor") is not None]

    anchor_count = len(anchor_sentences)
    linked_anchor_count = len(linked_sentences)

    # =========================
    # INFERENCE HEALTH
    # =========================

    inferential_sentences = [
        s for s in valid_sentences if s.get("epistemic_mode") == "E3"
    ]

    orphan_inference = [
        s for s in inferential_sentences if s.get("linked_anchor") is None
    ]

    orphan_inference_rate = (
        len(orphan_inference) / len(inferential_sentences)
        if inferential_sentences else 0
    )

    # =========================
    # LINK DISTANCE
    # =========================

    link_distances = [
        s["sentence_id"] - s["linked_anchor"]
        for s in linked_sentences
    ]

    avg_link_distance = (
        sum(link_distances) / len(link_distances)
        if link_distances else 0
    )

    # =========================
    # ANCHOR UTILIZATION
    # =========================

    anchor_ids = {s["sentence_id"] for s in anchor_sentences}

    used_anchors = set(
        s.get("linked_anchor")
        for s in valid_sentences
        if s.get("linked_anchor") is not None
    )

    anchor_utilization = (
        len(anchor_ids & used_anchors) / anchor_count
        if anchor_count else 0
    )

    # =========================
    # SCORES
    # =========================

    scores = [r["score"] for r in results]

    if scores:
        sorted_scores = sorted(scores)
        mean_score = sum(scores) / len(scores)
        median_score = median(sorted_scores)
        max_score = max(scores)
        high_risk_rate = len([s for s in scores if s >= 4]) / len(scores)
    else:
        mean_score = median_score = max_score = high_risk_rate = 0

    # =========================
    # CONTRADICTION SIGNAL
    # =========================

    contradictions = 0

    for r in results:
        sid = r["sentence_id"]
        sent = sentences[sid]

        # high score but has anchor → suspicious
        if r["score"] >= 4 and sent.get("has_anchor"):
            contradictions += 1

    contradiction_rate = (
        contradictions / len(results)
        if results else 0
    )

    # =========================
    # SECTION DISTRIBUTION
    # =========================

    section_counts = Counter(s["section"] for s in valid_sentences)

    # =========================
    # NORMALIZATION
    # =========================

    def normalize(counter, total):
        return {k: v / total for k, v in counter.items()} if total > 0 else {}

    # =========================
    # OUTPUT
    # =========================

    return {

        "counts": {
            "total_sentences": total_sentences,
            "valid_sentences": len(valid_sentences),
            "analyzed_sentences": analyzed_sentences,

            "E_counts": dict(E_counts),
            "F_counts": dict(F_counts),
            "A_counts": dict(A_counts),
            "M_counts": dict(M_counts),

            "anchor_count": anchor_count,
            "linked_anchor_count": linked_anchor_count,

            "section_counts": dict(section_counts),
        },

        "ratios": {
            "E_distribution": normalize(E_counts, len(valid_sentences)),
            "F_distribution": normalize(F_counts, analyzed_sentences),
            "A_distribution": normalize(A_counts, analyzed_sentences),
            "M_distribution": normalize(M_counts, analyzed_sentences),

            "anchor_ratio": anchor_count / len(valid_sentences) if valid_sentences else 0,
            "linked_anchor_ratio": linked_anchor_count / len(valid_sentences) if valid_sentences else 0,
        },

        "means": {
            "mean_score": mean_score,
            "median_score": median_score,
            "max_score": max_score
        },

        "diagnostics": {
            "orphan_inference_rate": orphan_inference_rate,
            "avg_link_distance": avg_link_distance,
            "anchor_utilization": anchor_utilization,
            "high_risk_rate": high_risk_rate,
            "contradiction_rate": contradiction_rate
        }
    }

def dump_metrics(metrics, path="document_metrics.json"):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def main(argv=None):
    parser = argparse.ArgumentParser(description="Compute document-level Epistemis metrics from a GROBID TEI XML file.")
    parser.add_argument("tei_file", type=Path, help="Path to a GROBID TEI XML file")
    parser.add_argument("--output", type=Path, default=Path("document_metrics.json"), help="Where to write metrics JSON")
    parser.add_argument("--debug-sentences", type=Path, default=None, help="Optionally write preprocessed sentences as JSONL")
    args = parser.parse_args(argv)

    if not args.tei_file.is_file():
        parser.error(f"Input TEI file does not exist: {args.tei_file}")

    sentences, results = run_pipeline(args.tei_file, debug_path=args.debug_sentences)
    metrics = compute_document_metrics(sentences, results)
    dump_metrics(metrics, args.output)
    print(f"Metrics written to {args.output}")
    print(f"Sentences: {len(sentences)} | analyzed: {len(results)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())