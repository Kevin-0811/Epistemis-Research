# Reader's guide

Epistemis is intended to be inspectable by both computational and research-focused readers. You do not need to read every file. Choose the route that matches what you want to understand.

## If you are approaching it as a researcher or humanities reader

You can understand the motivation and intended interpretation without reading Python.

1. **[README](../README.md)** — the short project introduction and map.
2. **[Research overview](research-overview.md)** — the research question, conceptual distinctions, label groups, and current status.
3. **[Worked example](worked-example.md)** — a sentence-level illustration of how a rule is intended to work.
4. **[Glossary](glossary.md)** — explanations of technical and linguistic terms.
5. **[Taxonomy](taxonomy.md)** — the labels, their intended interpretations, and which ones are active.
6. **[Limitations](limitations.md)** — what a flag cannot establish and what evaluation would still be needed.

The key question to keep in mind is: **What does the sentence's wording signal, what contextual information might matter, and what can the software actually infer from the features it detects?**

## If you are approaching it as a programmer or computational researcher

1. **[README](../README.md)** — dependencies, installation, and command-line use.
2. **[Architecture](architecture.md)** — the runtime sequence and module responsibilities.
3. **src/epistemis/preprocessor.py** — TEI extraction, sentence processing, structural features, and anchor heuristics.
4. **src/epistemis/classifier.py** — feature extraction, F/A/M rules, and heuristic scoring.
5. **src/epistemis/metrics.py** — document-level aggregation and command-line interface.
6. **tests/** — the current parser and metrics unit tests.
7. **[Methodology](methodology.md), [taxonomy](taxonomy.md), and [limitations](limitations.md)** — intended interpretation and research caveats.

## If you want to understand the research and implementation together

Read the research overview and worked example first, then compare each step with the architecture guide and source modules. The taxonomy is the bridge between the conceptual labels and the active conditions in the classifier.

## What not to assume

- A label is not a verdict that a claim is false or deceptive.
- An evidence anchor is not proof of adequate evidence.
- A heuristic score is not a probability or calibrated confidence.
- The archived model protocols do not mean a transformer model is running in this release.
- Passing unit tests does not establish end-to-end research validity or detection performance.

The current release is an exploratory prototype. The repository is designed to make its present approach and limits visible, not to claim that the research question has been settled.
