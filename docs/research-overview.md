# Epistemis: research overview

## The question behind the project

Scientific writing has to do two things at once: report observations and communicate what those observations are taken to mean. A paper may describe a measurement, interpret a result, propose a causal explanation, or generalise beyond the conditions directly examined.

Those moves are not interchangeable. Compare:

- "The intervention was followed by a change in the measured outcome."
- "The intervention caused the change in the measured outcome."
- "The intervention always causes improvement."

Each sentence makes a different kind of commitment. The last makes a universal claim; the middle makes a causal claim. Whether either is justified depends on the study design, evidence, limitations, and wider context—not just the wording.

Epistemis explores whether selected linguistic and nearby contextual signals can help a reader identify sentences whose wording may deserve closer examination.

## The central idea

The project treats rhetorical and epistemic signals as things that can be described operationally. Instead of asking a computer to decide whether a paper is "biased" or "bad science", the current prototype looks for narrower patterns, such as:

- broad generalisations or unusually strong claims;
- causal or relational language;
- hedges and qualifiers that limit a claim;
- references to citations, methods, measurements, models, and limitations;
- selected appeals to authority, consensus, novelty, or evaluative language.

The software uses explicit, hand-written rules to combine some of these signals. A flag therefore means that a sentence matched a defined pattern. It does not establish the author's intention, the truth of the sentence, or the adequacy of the evidence.

## Why a computational approach?

A human reader can notice these patterns, but long documents contain many sentences and repeated rhetorical moves. A computational prototype can help organise candidate passages for review, apply a consistent set of stated conditions, and make its rule logic inspectable.

The trade-off is important. Explicit rules are easier to inspect than an opaque prediction, but they are also limited by the vocabulary, grammatical patterns, and context the programmer anticipated. They can miss relevant cases and flag harmless ones.

Epistemis is therefore best understood as an aid to close reading and methodological exploration—not an automated referee of scientific knowledge.

## How to understand its three label groups

### F: primary flags

F labels identify candidate patterns in the construction of a claim. The current runtime implements:

- **F1 — interpretive generalisation:** a generalising or extreme-claim signal combined with an interpretive shift, under specified strength and context conditions.
- **F2 — causal escalation:** causal wording combined with strong assertion or generalisation, without detected qualification or contextual support under the current rules.
- **F3 — unsupported causal/relational claim:** a direct causal or relational statement that meets the current strength and context conditions.

The labels are defined by code conditions. They are not determinations that an argument is invalid.

### A: secondary rhetorical patterns

A labels identify selected rhetorical signals around authority, novelty, consensus, and evaluative language. A1, A2, A3, and A5 have active detection paths in the current classifier. A4 has a detector function but is not currently emitted because its invocation is commented out.

### M: rhetorical modifiers

M labels record selected modifiers such as hedging, boosting, downtoning, emphasis, and discourse markers. They describe language features; they do not by themselves establish overstatement.

See the [taxonomy and implementation mapping](taxonomy.md) for the precise current status of each category.

## What a result can and cannot tell a reader

A flag can help a reviewer locate a sentence and ask better questions:

- Is the scope of the claim wider than the study's scope?
- Does the wording imply causation where the design only supports association?
- Is there a meaningful qualifier?
- Where is the evidence, method, or limitation discussed?
- Does the surrounding paragraph change the interpretation?

A flag cannot answer those questions on its own. Citation presence is not proof of citation quality; a nearby method reference is not proof that the method supports the claim; and a strong phrase is not automatically inappropriate.

## Current research status

This public release is a deterministic, rule-based prototype. It uses spaCy for linguistic processing and GROBID-compatible TEI XML as input. It does not include a research-paper corpus or an independently annotated evaluation set. The archived DistilBERT/SciBERT protocols are historical research notes, not integrated or evaluated models in this release.

No benchmark performance is claimed. Before performance claims would be justified, the project would need a documented annotation protocol, independent annotators, source-document-level development and held-out test sets, and label-wise evaluation such as precision, recall, F1, and inter-annotator agreement.

## Suggested reading

- For an intuitive demonstration, read the [worked example](worked-example.md).
- For key terms, use the [glossary](glossary.md).
- For a guided route through the repository, use the [reader's guide](reader-guide.md).
- For exact rule conditions and inactive labels, read the [taxonomy](taxonomy.md).
- For processing details, read the [methodology](methodology.md) and [architecture](architecture.md).
- For caveats, read [limitations](limitations.md).
