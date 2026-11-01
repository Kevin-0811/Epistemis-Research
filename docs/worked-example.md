# Worked example: reading a possible claim escalation

This example is **illustrative**. It explains the kind of pattern the current rules are designed to notice. It is not a report from a completed run of Epistemis, and it does not claim that the exact sentence below has been processed by the installed spaCy model.

## 1. Start with two sentences

Consider these fictional statements:

**Sentence A**

> The treatment may cause improvement under the tested conditions.

**Sentence B**

> The treatment always causes improvement.

Sentence A is qualified: "may" signals uncertainty, and "under the tested conditions" limits the scope. Sentence B is much broader: "always" makes a general claim, and "causes" expresses a causal relationship.

Neither sentence is automatically true or false. The point is that they make different commitments and should be examined differently.

## 2. What the current F2 rule looks for

The F2 rule is designed to flag a particular combination:

1. The sentence contains a causal predicate recognised by the classifier.
2. It also contains a strong assertion or a generalising expression.
3. The computed epistemic strength is high or implicitly high.
4. The sentence is treated as a direct assertion.
5. No qualifying language is detected by the relevant rule.
6. The current context heuristic does not find a supporting anchor.

Sentence B is the clearer conceptual example of the pattern: "always" is a generaliser and "causes" is causal language. Sentence A contains a hedge and an explicit condition, both of which matter to the rule logic.

This is a description of the rule's intended logic—not a promise of a particular runtime label. Actual classification depends on the linguistic features extracted by spaCy, the data passed to the classifier, and the surrounding document context.

## 3. What happens inside the pipeline

| Stage | What the software examines | Plain-language meaning |
|---|---|---|
| TEI parsing | Structured paragraphs and document sections | Extract the text and its location in the paper |
| Sentence processing | Sentence boundaries and token-level grammar | Identify words and how they function in the sentence |
| Feature extraction | Causal verbs, generalisers, hedges, qualifiers, and other cues | Describe the wording in a structured way |
| Context and anchors | Selected nearby signals for citations, methods, measurements, models, or limitations | Look for contextual material that might matter to interpretation |
| Rule application | Explicit F, A, and M conditions | Check whether the extracted features match a defined pattern |
| Metrics | Counts, distributions, and heuristic scores | Summarise what the rules produced |

The classifier is deterministic: it applies explicit conditions to the features it receives. It is not a trained language model deciding whether the statement is scientifically justified.

## 4. How a human should interpret a flag

A responsible reviewer would not stop at the highlighted sentence. They would inspect:

- the research question and scope of the study;
- the methods and sample;
- the results and uncertainty;
- the limitations section;
- the surrounding paragraph and relevant citations;
- whether the authors have qualified the claim elsewhere.

For example, a universal-sounding sentence may be justified in a narrow formal or mathematical context. A causal verb may be warranted by an appropriate experimental design. Conversely, a cautious-sounding sentence may still overstate what the evidence supports.

The wording is a reason to inspect the argument, not enough information to judge it.

## 5. Why the example matters

The project is interested in the relationship between **how a claim is worded** and **what contextual signals are detectable nearby**. The prototype makes selected features and rule conditions explicit so a researcher can inspect them.

It does not determine whether the evidence actually entails the claim. That remains a task for human scholarly judgement—and, for research evaluation, systematic annotation and validation.
