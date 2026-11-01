from preprocessor_versions.preprocessor_v2 import preprocess

input_file = "genAIconcerns.tei.xml"
sentences = preprocess(input_file)["sentences"]

# =========================
# VALIDITY
# =========================

def is_valid_sentence(item):
    return (
        not item.get("excluded", False)
        and not item.get("is_metadata", False)
        and not item.get("is_header", False)
    )

# =========================
# LEXICAL SIGNALS (FROM GENERATOR)
# =========================

GENERALIZERS = {"all", "always", "never", "every", "none"}

GENERALIZATION_PHRASES = {
    "in all cases",
    "across all conditions",
    "independently of other factors"
}

STRONG_CAUSAL = {
    "cause", "lead", "result", "produce", "determine"
}

STRONG_ASSERTION_VERBS = {
    "demonstrate", "establish", "prove", "confirm"
}

INTERPRETIVE_VERBS = {
    "suggest", "indicate", "imply", "appear"
}

INFERENCE_PATTERNS = {
    "suggest", "indicate", "imply", "assume",
    "support", "confirm", "demonstrate", "show",
    "consistent", "agreement"
}

# =========================
# CONTEXT SUPPORT (FIXED)
# =========================

def has_contextual_support(item, sentences):

    if item.get("has_anchor"):
        return True

    linked = item.get("linked_anchor")
    if linked is not None:
        anchor_sent = sentences[linked]
        if anchor_sent.get("has_anchor") and not anchor_sent.get("excluded"):
            return True

    sid = item["sentence_id"]

    for i in range(max(0, sid - 4), sid):
        if sentences[i].get("has_anchor"):
            return True

    if get_frame(item) == "INFERENTIAL":
        return True

    return False

# =========================
# FEATURES
# =========================

def get_predicate_type(item):
    for tok in item["tokens"]:
        if tok["dep"] == "ROOT" and tok["pos"] == "VERB":
            lemma = tok["lemma"]

            if lemma in STRONG_CAUSAL:
                return "CAUSAL"

            if lemma in {"be", "have", "contain", "include"}:
                return "PROPERTY"

            return "RELATION"

    return "PROPERTY"


def get_frame(item):
    for tok in item["tokens"]:
        if tok["lemma"] in INFERENCE_PATTERNS:
            return "INFERENTIAL"

    if item.get("has_hedge", False):
        return "HEDGED"

    return "DIRECT_ASSERTION"

def has_distributional_claim(item):
    text = item["sentence"].lower()

    return any(
        w in text
        for w in {
            "most", "frequently", "typically",
            "commonly", "generally", "often"
        }
    )

def has_generalization(item):
    text = item["sentence"].lower()

    if any(tok["lemma"] in GENERALIZERS for tok in item["tokens"]):
        return True

    if any(p in text for p in GENERALIZATION_PHRASES):
        return True

    return False


def has_qualifier(item):
    for tok in item["tokens"]:
        if tok["dep"] == "mark":
            return True

        if tok["lemma"] in {"if", "when", "unless", "while", "provided"}:
            return True

        if tok["lemma"] in {"under", "within"}:
            return True

    return False


def compute_strength(item):

    tokens = set(item.get("modal_tokens", []))

    if tokens & {"can", "may", "might", "could"}:
        return "LOW"

    if tokens & {"often", "usually", "generally", "tends"}:
        return "MEDIUM"

    if tokens & {"always", "never"}:
        return "HIGH"

    if item.get("has_hedge", False):
        return "LOW"

    return "IMPLICIT_HIGH"


def has_strong_assertion(item):
    return any(tok["lemma"] in STRONG_ASSERTION_VERBS for tok in item["tokens"])


def has_interpretive_shift(item):
    return any(tok["lemma"] in INTERPRETIVE_VERBS for tok in item["tokens"])


def has_injected_clause(item):
    text = item["sentence"].lower()
    return "which" in text and any(w in text for w in {"suggest", "imply", "indicate"})

def has_extreme_claim(item):
    text = item["sentence"].lower()

    return any(p in text for p in [
        "never been equalled",
    "has never been",
    "cannot be matched",
    "unprecedented",
    "without precedent",
    "no equal",
    "unmatched",
    "unsurpassed",
    "one of the most",
    "among the most"
    ])
# =========================
# FEATURE EXTRACTION
# =========================

def extract_features(item):
    return {
        "predicate_type": get_predicate_type(item),
        "frame": get_frame(item),
        "epistemic_strength": compute_strength(item),
        "has_generalization": has_generalization(item),
        "has_qualifier": has_qualifier(item),
        "has_strong_assertion": has_strong_assertion(item),
        "has_interpretive_shift": has_interpretive_shift(item),
        "has_injected_clause": has_injected_clause(item),
        "has_extreme_claim": has_extreme_claim(item),
        "has_distributional_claim": has_distributional_claim(item)
    }

# =========================
# RULES (ALIGNED WITH GENERATOR)
# =========================

def rule_F2(f, item, sentences):
    return (
        f["predicate_type"] == "CAUSAL"
        and (f["has_strong_assertion"] or f["has_generalization"])
        and f["epistemic_strength"] in {"HIGH", "IMPLICIT_HIGH"}
        and f["frame"] == "DIRECT_ASSERTION"
        and not f["has_qualifier"]
        and not has_contextual_support(item, sentences)
    )



def rule_F1(f, item, sentences):
    return (
        f["has_generalization"] or f["has_extreme_claim"] 
        and (f["has_interpretive_shift"] or f["has_injected_clause"])
        and f["epistemic_strength"] in {"HIGH", "IMPLICIT_HIGH"}
        and f["frame"] in {"DIRECT_ASSERTION", "INFERENTIAL"}
        and not f["has_qualifier"]
        and not has_contextual_support(item, sentences)
     )   


def rule_F3(f, item, sentences):
    return (
        f["predicate_type"] in {"CAUSAL", "RELATION"}
        and f["frame"] == "DIRECT_ASSERTION"
        and f["epistemic_strength"] in {"HIGH", "IMPLICIT_HIGH"}
        and not f["has_qualifier"]
        and not has_contextual_support(item, sentences)
    )

# =========================
# APPLY
# =========================

def apply_rules(f, item, sentences):

    if rule_F2(f, item, sentences):
        return {"label": "F2", "rule": "causal_escalation"}

    elif rule_F1(f, item, sentences):
        return {"label": "F1", "rule": "interpretive_generalization"}

    elif rule_F3(f, item, sentences):
        return {"label": "F3", "rule": "unsupported_causal"}

    elif item.get("epistemic_mode") == "E4":
        return {"label": "CLEAN", "rule": "narrative"}
    else:
        return {"label": "CLEAN", "rule": "clean"}
    

#==========================
# A-SERIES
# ==========================

AUTHORITY_TERMS = {
    "experts", "scientists", "researchers",
    "harvard", "nasa", "who", "cdc", "mit"
}
def has_assertion_verb(item):
    return any(
        tok["lemma"] in STRONG_ASSERTION_VERBS
        or tok["lemma"] in INFERENCE_PATTERNS
        for tok in item["tokens"]
    )

def detect_A1(item):
    for tok in item["tokens"]:

        # authority noun as subject OR object of attribution
        if tok["lemma"] in AUTHORITY_TERMS:

            # subject case
            if tok["dep"] in {"nsubj", "nsubjpass"}:
                if has_assertion_verb(item):
                    if not has_contextual_support(item, sentences):
                        return True

            # "according to X"
            if tok["dep"] == "pobj" and tok["head"] and tok["head"] == "to":
                if not has_contextual_support(item, sentences):
                    return True

    return False

CONSENSUS_PHRASES = {
    "most studies", "many studies", "the literature shows",
    "widely accepted", "generally accepted", "overwhelming evidence"
}

def has_quantification(item):
    return any(
        tok["text"].isdigit() or tok["lemma"] in {"percent", "%", "ratio"}
        for tok in item["tokens"]
    )

def detect_A3(item):

    text = item["sentence"].lower()

    if any(p in text for p in CONSENSUS_PHRASES):

        if not has_quantification(item) and not item.get("has_anchor"):
            return True

    return False

LOADED_TERMS = {
    "remarkable", "compelling", "striking",
    "concerning", "troubling", "robust",
    "powerful", "dramatic"
}

def detect_A5(item):

    for tok in item["tokens"]:

        if tok["lemma"] in LOADED_TERMS:

            # must modify a noun or predicate
            if tok["dep"] in {"amod", "advmod"}:
                return True

    return False

NOVELTY_TERMS = {
    "novel", "groundbreaking", "innovative",
    "cutting-edge", "state-of-the-art"
}

def detect_A2(item):

    text = item["sentence"].lower()

    has_novelty = any(t in text for t in NOVELTY_TERMS)

    if not has_novelty:
        return False

    # must be tied to claim verb
    for tok in item["tokens"]:
        if tok["lemma"] in {"solve", "prove", "replace", "outperform"}:
            return True

    return False

def detect_A4(item):

    strong = item.get("epistemic_strength") in {"HIGH", "IMPLICIT_HIGH"}
    has_citation = item.get("has_anchor")

    # MUST be strong + cited + no hedge/qualifier
    if strong and has_citation and not item.get("has_qualifier") and not item.get("has_hedge"):
        return True

    return False

def detect_A_series(item, F_label):

    A = []

    if F_label is None:
        # restrict to high-confidence only
        if detect_A5(item):
            A.append("A5")
        return A

    if detect_A1(item):
        A.append("A1")

    if detect_A3(item):
        A.append("A3")

    if detect_A5(item):
        A.append("A5")

    if detect_A2(item):
        A.append("A2")

    if detect_A4(item):
        A.append("A4")

    return A

# =========================
# SCORING
# =========================

A_WEIGHTS = {
    "A1": 2,
    "A3": 2,
    "A5": 1,
    "A2": 1,
    "A4": 0.5
}

F_WEIGHTS = {
    "F2": 4,
    "F1": 3,
    "F3": 2,
    "CLEAN": 0,
    None: 0
}

def compute_score(item, F_label, A_labels):

    score = F_WEIGHTS[F_label]

    score += sum(A_WEIGHTS[a] for a in A_labels)

    if item.get("has_hedge"):
        score -= 1

    if item.get("has_modal"):
        score -= 0.5

    if item.get("has_anchor") or item.get("linked_anchor") is not None:
        score -= 1

    return max(score, 0)    

# =========================
# ANALYSIS
# =========================

def analyze_input(sentences):

    results = []

    for item in sentences:

        if not is_valid_sentence(item):
            continue

        f = extract_features(item)
        result = apply_rules(f, item, sentences)
        A_labels = detect_A_series(item, result["label"])
        score = compute_score(item, result["label"], A_labels)
        results.append({
            "sentence": item["sentence"],
            "label": result["label"],
            "rule": result["rule"],
            "features": f
            |{"A_labels": A_labels},
            "score": score

        })

    return results

results = analyze_input(sentences)

import json

def dump_sentences(results, path="debug_results.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for s in results:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

dump_sentences(results)            
