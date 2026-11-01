# Limitations and responsible interpretation

Epistemis is an exploratory prototype. Its outputs require human review.

## Known limitations

1. **Surface cues are not intent.** Lexical markers may appear in legitimate scientific writing, while overstatement may occur without the current marker lists.
2. **Context is incomplete.** A sentence may be justified by methods, evidence, definitions, or qualifications elsewhere in a paper that the local anchor heuristic misses.
3. **Citation presence is not evidence quality.** The current system does not determine whether a citation is relevant, reliable, or accurately represented.
4. **Parsing errors propagate.** spaCy segmentation and dependency errors can affect feature extraction and rule outcomes.
5. **Domain and genre shift.** Rules tuned on selected scientific texts may behave differently across disciplines and paper types.
6. **The score is not calibrated.** It is a hand-weighted heuristic, not a probability, risk estimate, or validated quality measure.
7. **Metrics are exploratory.** Document summaries do not replace an independently labelled test set, precision/recall analysis, calibration, subgroup analysis, or inter-annotator agreement.
8. **Some taxonomy categories are inactive.** A4 is not currently emitted. Archived model-training protocols are not integrated into this runtime.

## Interpretation guidance

Treat each flag as a prompt for inspection. Review the full paragraph, methods, relevant citations, qualifiers, and surrounding context before drawing conclusions. Do not use Epistemis as an automated basis for judging an author, institution, paper, or research finding.

## Work needed before performance claims

- Create a documented annotation protocol and obtain independent labels.
- Split development and held-out test documents at the source-document level.
- Measure precision, recall, F1, false-positive rates, and inter-annotator agreement for each label.
- Analyse performance across disciplines and writing styles.
- Audit citation extraction, section filtering, anchor linking, and class imbalance.
- Calibrate scores or thresholds before describing them as confidence.
