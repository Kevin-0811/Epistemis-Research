# Epistemis

**A research prototype for examining how scientific writing expresses claims, certainty, and evidence.**

Scientific papers do more than report observations. They also make claims, interpret results, describe methods, refer to other researchers, and signal how certain a conclusion is. The wording matters: a cautious interpretation and a broad causal claim communicate different levels of certainty.

Epistemis is an experimental tool for examining some of those language patterns. It processes structured scientific text, identifies selected linguistic and contextual signals, and applies explicit rules to flag sentences that may merit closer human review.

It does **not** decide whether a paper is true, whether an author is dishonest, or whether a scientific conclusion is valid. Its flags are prompts for inspection—not verdicts.

## Start here

You do not need to know Python or natural-language processing to understand the research.

- **New to the project?** Read the [research overview](docs/research-overview.md) for the question, motivation, and conceptual framework.
- **Want to see what the system does?** Follow the [worked example](docs/worked-example.md), which walks through an illustrative scientific claim.
- **Encounter unfamiliar terms?** Use the [plain-language glossary](docs/glossary.md).
- **Not sure where to go next?** The [reader's guide](docs/reader-guide.md) provides separate routes for research-focused and technical readers.

## What Epistemis does

At a high level, the software:

1. **Reads a structured research document.** It takes TEI XML, a structured text format commonly produced from research-paper PDFs by GROBID.
2. **Examines sentences.** It uses the spaCy language-processing library to identify sentence boundaries and linguistic features such as word forms, grammatical roles, and modality.
3. **Looks for selected signals.** These include strong or generalising language, causal wording, qualifiers, citations, methods, quantitative information, and nearby references to evidence.
4. **Applies explicit rules.** The classifier assigns selected F-series flags and A-series and M-series labels.
5. **Produces a summary.** The metrics module reports counts, distributions, heuristic scores, and exploratory diagnostics in JSON.

The [architecture guide](docs/architecture.md) describes the technical pipeline. The [methodology guide](docs/methodology.md) explains the processing choices and their limits.

## The labels, in brief

The labels group different kinds of language signals:

| Group | What it examines | Examples |
|---|---|---|
| **F — primary flags** | Candidate patterns in how claims are expressed | Interpretive generalisation, causal escalation, unsupported causal or relational claims |
| **A — secondary patterns** | Rhetorical signals around authority, novelty, consensus, and evaluative language | Appeals to authority or consensus; novelty claims; loaded evaluation |
| **M — modifiers** | Language that changes the force or organisation of a statement | Hedging, boosting, downtoning, emphasis, discourse markers |

These are operational categories defined by the current code, not universal measures of scientific quality. The [taxonomy](docs/taxonomy.md) maps each category to its implementation and identifies inactive categories.

## What the system does not establish

A sentence can contain a strong verb and still be scientifically justified. A sentence can cite a paper without accurately representing that paper. A detected evidence signal does not prove that the evidence supports the claim.

Epistemis currently uses deterministic rules and heuristic scores. It has not been validated against an independently annotated evaluation corpus in this release. No precision, recall, F1, or other benchmark performance is claimed. The score is not a probability or calibrated confidence estimate.

Read the [limitations and responsible interpretation notes](docs/limitations.md) before using or interpreting its output.

## Technical quick start

### Requirements

- Python 3.10 or later
- spaCy 3.7 (below version 4)
- The spaCy English model `en_core_web_md`
- A TEI XML file that you are permitted to process

PDF-to-TEI conversion is external to this package. Epistemis starts from TEI XML and does not include a research-paper corpus.

### Install

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS / Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m spacy download en_core_web_md
```

### Run

```bash
epistemis path/to/document.tei.xml --output outputs/document_metrics.json
```

Or:

```bash
python -m epistemis path/to/document.tei.xml --output outputs/document_metrics.json
```

To optionally write sentence-level debugging records, add:

```bash
--debug-sentences outputs/sentences.jsonl
```

The model is installed separately from the package. Use a model version compatible with the installed spaCy version.

## Repository map

```text
src/epistemis/      Maintained Python package
docs/               Research overview, reader guide, glossary, methods, taxonomy, limits
examples/           Small synthetic TEI example
tests/              Parser and metrics unit tests
archive/             Earlier source versions and historical research notes
```

The `archive/` directory preserves earlier iterations and research notes. Archived files are not part of the maintained runtime and may not run unchanged. The archived DistilBERT/SciBERT protocols are historical design notes; they are not evidence that those models were integrated, trained, or evaluated in this release.

## Data, citation, and licensing

The earlier development repository contained research-paper PDFs, extracted full-text TEI files, and intermediate JSONL datasets. They are omitted from this public repository because redistribution rights were not established in the audit. The example TEI file is synthetic.

See [data policy](docs/data-policy.md) before adding external documents or derived data.

To cite the software, see [CITATION.cff](CITATION.cff). No open-source software licence has been selected. Public visibility does not grant permission to reuse, modify, or redistribute the code; all rights remain reserved unless the author adds a licence.

---

**Project status:** exploratory research prototype. The repository documents the current implementation and its limitations; it does not claim validated detection performance.
