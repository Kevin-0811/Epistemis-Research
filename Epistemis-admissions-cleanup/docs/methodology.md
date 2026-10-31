# Methodology

## Input and text extraction

Epistemis consumes TEI XML, normally produced from a research-paper PDF by GROBID. It reads body divisions, paragraph text, figure descriptions, and table text. Bibliographies, appendices, acknowledgements, funding sections, and other configured sections may be excluded.

The package does not include a paper corpus. Users must supply TEI documents they are authorised to process.

## Linguistic processing

The preprocessor uses spaCy's `en_core_web_md` pipeline to segment text into sentences and extract token features: lowercased text, lemma, part of speech, dependency relation, token index, and head token. It then applies structural heuristics for repeated headers, likely headings, narrative/authorial/inferential/descriptive modes, modality, and sentence exclusion. These are approximations, not gold linguistic annotations.

## Context and anchors

The preprocessor searches for selected signals such as citation support, quantitative evidence, method descriptions, model/assumption references, and limitation markers. It attempts to link some claim-like sentences to nearby anchors within a short preceding-sentence window. Linking uses discourse cues, anaphoric patterns, and lexical overlap.

An anchor means only that a detectable structural signal was found. It does not mean that a sentence is empirically well-supported or that a citation is relevant, reliable, or correctly interpreted.

## Classification

The classifier extracts lexical and syntactic features and applies deterministic F1, F2, and F3 rules. It can also emit selected A-series and M-series labels. Exact conditions and inactive categories are documented in [taxonomy.md](taxonomy.md).

The numeric score is a hand-authored heuristic. It is not learned from data and is not calibrated to a probability of bias, deception, or error.

## Document-level metrics

The metrics engine aggregates sentence counts, primary and secondary label distributions, anchor counts and ratios, mean/median/maximum heuristic score, and several rule-based diagnostics. Some diagnostics—especially the high-score/anchored overlap called a contradiction rate in the current code—are exploratory indicators that require validation.

## Evaluation status

This repository does not include an independently annotated evaluation corpus or verified benchmark results. Dataset-construction and model-training protocols in the historical archive do not establish that those models were trained or evaluated. Do not claim performance figures without a documented evaluation protocol and reproducible results.
