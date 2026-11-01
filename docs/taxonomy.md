# Taxonomy and implementation mapping

The project distinguishes primary flags (F), secondary rhetorical patterns (A), and rhetorical modifiers (M). These are operational heuristics, not findings that a paper is false, deceptive, or scientifically unsound.

## F-series: primary flags

| Label | Intended interpretation | Current runtime condition (high level) |
|---|---|---|
| F1 | Interpretive generalisation | Generalisation/extreme-claim signal combined with interpretive shift or injected clause; high/implicit-high strength; direct or inferential frame; no detected qualifier or contextual support. |
| F2 | Causal escalation | Causal predicate plus strong assertion or generalisation; high/implicit-high strength; direct assertion; no detected qualifier or contextual support. |
| F3 | Unsupported causal/relational claim | Causal or relational predicate; direct assertion; high/implicit-high strength; no detected qualifier, reporting-sentence exemption, or contextual support. |

The classifier applies F2 before F1 and F3. Exact lexical sets and feature extraction live in `classifier.py`.

## A-series: secondary patterns

| Label | Intended interpretation | Current runtime status |
|---|---|---|
| A1 | Illicit authority reification | Implemented heuristic |
| A2 | Appeal to novelty/innovation prestige | Implemented heuristic |
| A3 | Appeal to consensus / quantity-as-truth | Implemented heuristic |
| A4 | Selective citation / cherry-picking | **Not active**; detector exists but invocation is commented out |
| A5 | Loaded evaluative language | Implemented heuristic |

A1, A2, A3, and A5 may be emitted on the relevant classifier path. A4 should not be presented as an active detector.

## M-series: rhetorical modifiers

| Label | Signal |
|---|---|
| M1 | Hedgers |
| M2 | Boosters |
| M3 | Downtoners |
| M4 | Emphasis markers |
| M5 | Structural/discourse markers |

These markers are intended to modify interpretation rather than establish a bias finding by themselves. Their effect on the numeric heuristic score is defined in the classifier.

## Implementation caveats

- The prose taxonomy evolved across versions. The active classifier is the latest version wired into the root metrics engine, not every historical definition.
- Boundary conditions are only approximated by lexical or dependency rules.
- Citation detection is not citation-quality or evidence-sufficiency analysis.
- Describe these as detected *signals* or *candidate patterns*, not definitive rhetorical violations.
