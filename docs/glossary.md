# Plain-language glossary

This glossary explains terms as they are used in the Epistemis project. Some have broader meanings in linguistics, philosophy, and research methodology.

| Term | Meaning in this project |
|---|---|
| **Epistemic** | Relating to knowledge, evidence, belief, or how certain a statement presents itself to be. |
| **Rhetoric / rhetorical** | The choices a writer makes to present, frame, qualify, or persuade through language. It does not necessarily mean deception. |
| **Claim** | A statement that asserts something about the world, a result, a relationship, or an interpretation. |
| **Overstatement** | Wording that appears stronger or broader than the available justification may warrant. Whether it truly is an overstatement requires examining the evidence and context. |
| **Generalisation** | A claim that extends beyond a particular observation, case, sample, or condition. Words such as "always" and "all" can signal broad scope. |
| **Causal claim** | A statement that one factor causes or produces a change in another. Causation is stronger than merely observing that two things occur together. |
| **Qualifier** | A word or phrase that limits the scope or force of a claim, such as "in this sample", "under these conditions", or "may". |
| **Hedge** | Language that reduces commitment or signals uncertainty, such as "may", "might", or "suggests". |
| **Booster** | Language that strengthens commitment, such as "clear" or "conclusive" in relevant grammatical contexts. |
| **Evidence anchor** | A detectable signal associated with a citation, measurement, method, model, assumption, or limitation. It is not proof that the evidence supports the claim. |
| **Contextual support** | Relevant material in or near a document that may change how a sentence should be interpreted. The current software detects only selected signals and does not fully understand document context. |
| **TEI XML** | A structured text format used to represent documents, including sections, paragraphs, and references. Epistemis takes TEI XML as input. |
| **GROBID** | Software that extracts scholarly document structure and text, commonly converting research-paper PDFs into TEI XML. Conversion is outside this package's runtime. |
| **NLP (natural-language processing)** | Computational methods for processing human language, including identifying sentences, words, grammatical roles, and linguistic patterns. |
| **spaCy** | The Python NLP library used by Epistemis for sentence segmentation and linguistic features. |
| **Lemma** | A normalised dictionary form of a word. For example, "causes" and "caused" may be represented by the lemma "cause". |
| **Part of speech** | A grammatical category such as noun, verb, adjective, or adverb. |
| **Dependency relation** | A label describing a grammatical relationship between words, such as a subject or modifier. |
| **Rule-based classification** | Classification using explicitly written conditions rather than learning the decision rules from a labelled training dataset. |
| **Heuristic score** | A score based on hand-designed rules or weights. It is not automatically a probability, confidence level, or validated measure. |
| **Precision** | Among the cases a system flags, the proportion that are judged correct against a defined reference annotation. |
| **Recall** | Among all cases judged relevant in a reference annotation, the proportion the system successfully flags. |
| **F1 score (evaluation statistic)** | A combined measure of precision and recall. This is different from the project's **F1 label**, which names one of its primary rule categories. The shared abbreviation is coincidental; they are not the same thing. An evaluation F1 score cannot be calculated meaningfully without a defined evaluation set and annotations. |
| **Inter-annotator agreement** | A measure of how consistently independent human annotators apply the same annotation scheme. |

## A note on the word "bias"

Epistemis may examine signals that could be relevant to rhetorical overstatement, but it does not detect a person's intent or establish bias as a psychological or moral characteristic. In this repository, prefer phrases such as **candidate signal**, **rule match**, or **flagged sentence** over definitive claims about an author or paper.
