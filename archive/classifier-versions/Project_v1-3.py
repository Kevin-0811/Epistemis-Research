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
        and len(item["sentence"].strip()) > 20
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


# =========================
# NEW SIGNALS (FROM GENERATOR)
# =========================

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
    }

# =========================
# RULES (ALIGNED WITH GENERATOR)
# =========================

def rule_F2(f, item, sentences):
    return (
        f["predicate_type"] == "CAUSAL"
        and f["epistemic_strength"] in {"HIGH", "IMPLICIT_HIGH"}
        and (f["has_strong_assertion"] or f["has_generalization"])
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
        f["predicate_type"] == "CAUSAL"
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

    else:
        return {"label": "CLEAN", "rule": "clean"}

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

        results.append({
            "sentence": item["sentence"],
            "label": result["label"],
            "rule": result["rule"],
            "features": f
        })

    return results

results = analyze_input(sentences)

import json

def dump_sentences(results, path="debug_results.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for s in results:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

dump_sentences(results)            
