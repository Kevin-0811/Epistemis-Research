"""
DISTILBERT DATASET PROTOCOL (FINAL, NUMERICALLY CONSISTENT)

This is engineered for triage behavior, not generic classification.

1. Dataset Size
Total samples: 5000

Rationale:

Enough to learn 4-way boundary + calibration
Keeps manual labeling feasible
Allows structured tiering
2. Input Format (fixed)

Each sample:

prev_sentence + " " + current_sentence + " " + next_sentence

Rules:

If neighbor invalid → replace with nearest valid sentence
No empty context
No paragraph concatenation
3. Label Set (strict)
CLEAN
F1
F2
UNCERTAIN

Constraints:

❌ No F3 here (reserved for SciBERT)
❌ No multi-label
4. Global Label Distribution (locked)
CLEAN:     2250  (45%)
UNCERTAIN: 1250  (25%)
F1:         750  (15%)
F2:         750  (15%)
5. Tier Distribution (behavioral structure)
Tier 1 (Easy):        2250 (45%)
Tier 2 (Borderline):  1500 (30%)
Tier 3 (Deceptive):   1250 (25%)
6. Tier × Label Matrix (FINAL)

This is the core of the protocol.

🔵 Tier 1 — EASY (2250)
CLEAN: 1500
F1:     375
F2:     375
UNCERTAIN: 0
Definition:
Locally decidable with zero hesitation
Purpose:
Train high-confidence decisions
🟡 Tier 2 — BORDERLINE (1500)
UNCERTAIN: 1000
CLEAN:      250
F1:         125
F2:         125
Definition:
Requires interpretation beyond surface cues
Ambiguous or weak signals
Purpose:
Train when to escalate
🔴 Tier 3 — DECEPTIVE (1250)
CLEAN:  500
UNCERTAIN: 250
F1:     250
F2:     250
Definition:
Misleading surface structure
Violates shallow heuristics
Purpose:
Train robustness against false cues
7. Labeling Rules (strict decision criteria)
CLEAN
Claim is bounded, qualified, or descriptive
No epistemic inflation
F1 — Unsupported Generalization
Vague evidence:
“studies show…”
“it is known…”
No anchors / qualifiers
F2 — Absolutist Causality
Strong causal verb:
causes, drives, leads to
No constraints (organism, method, condition)
UNCERTAIN

Use ONLY if:

Not decidable from ±1 sentence context
OR
Ambiguous between CLEAN / F1 / F2

Hard constraint:

UNCERTAIN ≠ difficult
UNCERTAIN = context-dependent
8. Tier Assignment Rules
Tier 1:
Immediate classification
No ambiguity
Tier 2:
Requires thought
borderline cases
Tier 3:
Misleading structure:
citation but still wrong
technical tone masking bias
qualified but appears strong
9. Data Sampling Strategy (from PubMed + arXiv)
Section weighting:
Introduction + Discussion → 60–70%
Methods + Results → 30–40%
Targeted extraction:
CLEAN:
anchored
bounded claims
F1:
search patterns:
“studies suggest”
“research shows”
F2:
causal verbs:
causes, drives, leads to
UNCERTAIN:
hedging
weak anchoring
ambiguous scope
Tier 3:
actively hunt:
citation + strong claim
method + overgeneralization
10. Training Configuration (minimal spec)
Model:

DistilBERT + classification head

Loss:
Weighted CrossEntropy

Weights:

CLEAN:     1.0
F1:        1.5
F2:        1.5
UNCERTAIN: 1.2
Hyperparameters:
LR: 3e-5
Batch size: 16–32
Epochs: 3
Max length: 128
11. Target Metrics (must meet these)
CLEAN:
Precision ≥ 95%
Recall   ≥ 85%
F1 + F2:
Precision ≥ 85–90%
Recall   ≥ 60–75%
UNCERTAIN:
Recall ≥ 80–90% (on true ambiguous cases)
12. System-Level Metrics (more important than accuracy)
False CLEAN rate:
≤ 3–5%

(critical — prevents missed bias)

Direct detection rate (F1/F2):
≥ 60%
Escalation rate:
20–35% of total samples
13. Dataset Validation Checks (before training)

Reject dataset if:

❌ UNCERTAIN > 1300

→ hesitation bias

❌ Tier 3 weak or missing deception

→ shallow heuristics

❌ F1 lacks diversity

→ low recall

❌ No contrast pairs

→ boundary not learnable

14. Construction Workflow
Step 1:

Run preprocessor → extract candidates

Step 2:

Assign labels (CLEAN/F1/F2/UNCERTAIN)

Step 3:

Assign tier (1/2/3)

Step 4:

Track counts continuously

Step 5:

Stop exactly at:

2250 / 1250 / 750 / 750
Step 6:

Shuffle entire dataset

15. Core Design Principle

You are not building:

a classifier

You are building:

a calibrated triage decision system
Final Summary (compressed)
TOTAL: 5000

LABELS:
CLEAN: 2250
UNC:   1250
F1:     750
F2:     750

TIERS:
T1: 2250 → high confidence
T2: 1500 → escalation
T3: 1250 → deception robustness

"""