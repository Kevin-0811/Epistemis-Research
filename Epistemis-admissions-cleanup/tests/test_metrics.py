from epistemis.metrics import compute_document_metrics


def test_document_metrics_uses_statistical_median_for_even_sample():
    sentences = [
        {"sentence_id": 0, "epistemic_mode": "E2", "section": "introduction",
         "has_anchor": False, "linked_anchor": None},
        {"sentence_id": 1, "epistemic_mode": "E3", "section": "introduction",
         "has_anchor": True, "linked_anchor": None},
    ]
    results = [
        {"sentence_id": 0, "label": "CLEAN", "score": 2.0,
         "features": {"A_labels": [], "M_labels": []}},
        {"sentence_id": 1, "label": "F1", "score": 4.0,
         "features": {"A_labels": ["A3"], "M_labels": ["M2"]}},
    ]

    metrics = compute_document_metrics(sentences, results)

    assert metrics["means"]["median_score"] == 3.0
    assert metrics["counts"]["analyzed_sentences"] == 2
    assert metrics["counts"]["F_counts"] == {"CLEAN": 1, "F1": 1}
