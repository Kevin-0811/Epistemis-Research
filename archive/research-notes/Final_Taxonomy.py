"""
F1 — Unsupported Generalization Signals (UGS)
Causal family associated with rhetorical broadness, evidentiary thinness, and lack of anchoring.
A claim is classified as UGS when it meets all criteria below.

F1.1 Required Structural Form

UGS applies only to clauses that:
Assert a pattern, effect, trend, or mechanism at a general level, AND
Present the assertion as epistemically grounded through vague evidentiary language, AND
Fail to provide the necessary anchors that would legitimize the generalization.

F1.2 Trigger Conditions (ALL MUST BE TRUE)
A sentence is UGS if:

It contains a generalization marker, such as:
“studies show”, “research suggests”, “evidence indicates”, “it is known that”, “it is widely believed”, “the literature shows”

It lacks all of the following anchor classes:
* Specific study identifiers (e.g., “Smith et al. 2019”)
* Methodological constraints (e.g., “using fMRI”, “in vitro”, “double-blind”)
* Domain/system qualifiers (e.g., “in mice”, “in astrocytes”, “in early development”)

The claim asserts or implies a population-level or mechanism-level generalization.

F1.3 Boundary Conditions

UGS does not apply when:
Generalization markers are followed by methodological or organismal qualifiers.
Generalization markers describe the state of literature, and not a factual claim. (e.g., “Studies show a growing interest in biomechanics.”)

====================================================

F2 — Absolutist Causal Assertions (ACA)
Causal family capturing unwarranted certainty in causal, mechanistic, or determinative claims.

F2.1 Required Structural Form

ACA applies to clauses that:
Express or imply a direct causal relationship, AND
Use strong or categorical causal verbs or constructions, AND
Lack the qualifiers normally required to delimit scientific causal claims.

F2.2 Causal Markers (MUST BE PRESENT)

Allowed markers include, but are not limited to:
“causes”, “is caused by”
“drives”, “is driven by”
“leads to”, “results in”
“determines”, “ensures”
“proves”, “demonstrates” (when followed by a mechanism/effect structure)

F2.3 Trigger Conditions (ALL MUST BE TRUE)

A sentence is ACA if:
A causal predicate appears.
The claim lacks experimental, organismal, environmental, or methodological qualifiers, such as:

* organism: “in mice”, “in yeast”, “in humans with PTSD”
* context: “under hypoxia”, “after sleep deprivation”
* modality: “using calcium imaging”, “via knockout mutants”
* population constraints: “in a sample of 34 participants”

The claim implies universality, i.e., it presents the causal relationship as context-free.

F2.4 Boundary Conditions

ACA does not apply when:
The causal relationship is explicitly bounded.
The verb is causal but the sentence is descriptive rather than assertive (e.g., “We tested whether X causes Y”).
The sentence is hypothetical or conditional (e.g., “If X causes Y, then…”).
====================================================
F3 — Omitted Contextualization Signals (OCS)
Causal family associated with missing obligatory scientific context, especially in causal or mechanistic statements.
OCS is the hardest category by far. You do not detect “absence” in the abstract; you detect failure to meet contextual obligations given the type of claim.

F3.1 Required Structural Form

OCS applies only to:
Causal, mechanistic, or evaluative scientific claims,
For which standard scientific reporting norms require at least one contextual anchor.

F3.2 Obligated Context Classes

At least one of these context classes must appear in a well-formed claim:
Organism-level descriptors(in mice, in C. elegans, in human adolescents)
Experimental modality(using EEG, with optogenetics, via RNA-seq)
Environmental/modulating conditions(under oxidative stress, at high temperature, after fasting)
Population descriptors(in 34 adults, across 5 cohorts)
Temporal constraints(after 24 hours, during REM sleep)

F3.3 Trigger Conditions (ALL MUST BE TRUE)

A sentence is OCS if:
It is a causal/mechanistic/evaluative claim.
It lacks all five contextual anchor classes.
It thereby implies a mechanism or phenomenon that is unrealistically context-free.

F3.4 Boundary Conditions

OCS does not apply when:
The claim is a conceptual/theoretical statement rather than empirical.
The context is provided in the immediately preceding sentence (you’ll need a 2-sentence window during inference).
The claim is intentionally general because it describes an abstract model.

====================================================

RESOLUTION RULE (THE CORE OF THE TAXONOMY)
When analyzing a clause, determine:

Is it anchored? If yes → skip F1, F2, F3. Label = None unless an A-series applies.
If unanchored, what is the rhetorical function?

* If the sentence uses vague evidentiary language → F1
* If the sentence expresses strong or universal causal force → F2
* If the sentence is a causal/mechanistic claim with missing obligatory context → F3

If none match, return None.

# ====================================================

A-SERIES — SPECIFIC DISTORTION PATTERNS
(Secondary labels, multi-label, can co-occur with any F-family or with each other.)
A-series labels describe the type of epistemic distortion, regardless of whether the root cause is F1, F2 or F3.
They never override the F-label; they refine it.

A1 — Illicit Authority Reification
Treating institutional or expert prestige as epistemic proof.

A1.1 Required Elements

A1 applies when:
A named institution, expert, authority, organization, or “prestige-bearing entity” is referenced, AND
The reference is used as a direct warrant for the conclusion or claim, AND
The sentence lacks methodological/empirical justification other than the authority itself.

A1.2 Trigger Examples

“According to Harvard scientists, X must be correct.”
“NASA confirms this mechanism works.”
“The WHO has established that the treatment is effective.”

A1.3 Boundary Conditions

Not A1 when:
The authority is cited as provenance but not justification.
The authority is part of normal attribution (“WHO data set was used”).

A2 — Appeal to Novelty / Innovation Prestige
Arguing that newness, disruptiveness, or innovation implies epistemic superiority.

A2.1 Required Elements

A2 applies when:
The novelty/modernity of a method/model is highlighted, AND
The novelty itself is used as a warrant for correctness, significance, or necessity.

A2.2 Trigger Examples

“This groundbreaking paradigm solves the problem once and for all.”
“A novel technique that is clearly superior simply because it is new.”
“This modern approach must replace outdated methods.”

A2.3 Boundary Conditions

Not A2 when:
Novelty is factual description without epistemic claim.
The evaluation is tied to performance metrics, not newness.

A3 — Appeal to Consensus / Quantity-as-Truth
Using the number of studies, researchers, or publications as proof of correctness.

A3.1 Required Elements

A3 applies when:
The breadth, number, or unanimity of literature is cited, AND
The magnitude is used as the core epistemic justification.

A3.2 Trigger Examples

“Most studies agree that…”
“The literature overwhelmingly confirms…”
“Everyone in the field accepts that…”

A3.3 Boundary Conditions

Not A3 when:
The breadth is descriptive without epistemic inflation (“20 studies report X happens in mice”).
The consensus is presented alongside methodological rationale.

A4 — Selective Citation / Cherry-Picking
Asymmetric evidence selection used to inflate or protect a claim.

A4.1 Required Elements

A4 applies when:
Some evidence is cited, AND
Contradictory or limiting evidence is omitted in a way that strengthens the rhetorical force, AND
The structure of the argument depends on selectivity.

A4.2 Detectable Forms

Exclusive reference to positive results.
Omission of known conflicting trials when making general claims.
Presenting a subset of evidence as representative of the entire body.

A4.3 Boundary Conditions

Not A4 when:

The focus is explicitly narrow (“In studies of adolescent rats…”).
Conflicting evidence is omitted because the scope is legitimately bounded.

A5 — Loaded Evaluative Language
Value-laden descriptors that bias interpretation by adding emotional, value-based, or persuasive shading.

A5.1 Required Elements

A5 applies when:
Adjectives/adverbs/verbs introduce evaluative shading, AND
The shading steers the reader toward an epistemic or normative conclusion.

A5.2 Trigger Examples

“deeply troubling results”
“remarkably robust findings”
“highly compelling evidence”

A5.3 Boundary Conditions

Not A5 when:

The descriptor encodes a conventional scientific property (e.g., “robust” in statistics if clearly technical).
The evaluative term is part of a quoted phrase or domain-specific jargon.

# ====================================================
M-SERIES — RHETORICAL MODIFIERS (NON-BIAS)
(Multi-label; do not create bias on their own, but influence strength, tone, and interpretation.)
These markers modulate tone but do not constitute epistemic distortion unless combined with an F- or A-series pattern.

M1 — Hedgers
Express epistemic uncertainty. They soften claims.
Common Forms
“may”, “might”, “could”, “possibly”, “likely”, “appears to”, “suggests that”
Function
Reduce commitment strength; mitigate the force of causal or general claims.

M2 — Boosters
Increase apparent strength or certainty.
Common Forms
“clearly”, “strongly”, “decisively”, “undeniably”, “conclusively”
Function
Increase rhetorical commitment and can escalate F2 or A5 severity, but are not bias alone.

M3 — Downtoners
Lower perceived magnitude or intensity.
Common Forms
“slightly”, “somewhat”, “marginally”, “modestly”
Function
Often used to temper claims; can sometimes hide effect weakness.

M4 — Emphasis Markers
Used to draw attention to a point without altering its epistemic status.
Common Forms
“notably”, “importantly”, “crucially”, “significantly” (non-statistical usage only)

M5 — Structural / Discourse Markers
Organize argument flow.
Common Forms
“however”, “therefore”, “in contrast”, “nonetheless”, “moreover”, “consequently”
Function
Signal rhetorical structure, not bias.

Compatibility With F-Series

F = the primary rhetorical function
A = the type of distortion used
M = tone and intensity markers

Example:
“Most studies clearly show that X causes Y.”
→ F1 (unsupported generalization)
→ A3 (consensus appeal)
→ M2 (booster)
"""