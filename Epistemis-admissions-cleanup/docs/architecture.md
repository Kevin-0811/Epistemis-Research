# Architecture

## Runtime flow

1. **Input:** GROBID TEI XML. PDF conversion is external; the package does not convert PDFs itself.
2. **TEI parsing:** extract text from body sections, paragraphs, figure descriptions, and tables. Mark configured sections such as references and appendices as excluded.
3. **Sentence processing:** spaCy's `en_core_web_md` model supplies sentence boundaries, lemmas, parts of speech, dependency labels, and token-head information.
4. **Structural and epistemic features:** identify repeated headers, likely headings, narrative/authorial/inferential/descriptive modes, modality, and exclusion conditions.
5. **Anchoring:** detect selected citation, quantitative, method, model, and limitation signals. Link some nearby claims to prior anchors with short-range and token-overlap heuristics.
6. **Classification:** apply deterministic F-series rules and emit supported A-series and M-series labels.
7. **Metrics:** aggregate counts, distributions, heuristic scores, and diagnostic ratios.
8. **Output:** JSON metrics; optional sentence-level JSONL for debugging.

## Modules

- `preprocessor.py`: TEI parsing, sentence segmentation, structural features, anchoring, and window generation.
- `classifier.py`: sentence-level feature extraction, rule application, secondary labels, and heuristic scoring.
- `metrics.py`: pipeline orchestration, document metrics, and command-line interface.

## Context windows

The preprocessor constructs overlapping six-sentence windows with a stride of three. In this release they are returned as preprocessing metadata; the deterministic classifier evaluates sentence records. Do not describe the windows as transformer-model input in this release.
