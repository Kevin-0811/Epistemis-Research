from preprocessor_versions.preprocessor_v2 import preprocess

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

GENERALIZERS = {"all", "always", "never", "every", "none","often", "frequently", "generally", "commonly", "typically"}

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

            if lemma in {"be", "have", "contain", "include", "show", "depict"}:
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


def has_strong_assertion(item):
    return any(tok["lemma"] in STRONG_ASSERTION_VERBS for tok in item["tokens"])

REPORTING_SUBJECTS = {"figure", "table", "fig", "tab"}
REPORTING_VERBS = {"show", "present", "illustrate", "depict"}

def is_reporting_sentence(item):
    tokens = item["tokens"]

    for tok in tokens:
        if tok["lemma"] in REPORTING_VERBS:
            # check subject
            for child in tokens:
                if child["dep"] == "nsubj" and child["lemma"].lower() in REPORTING_SUBJECTS:
                    return True
    return False

def has_interpretive_shift(item):
    return any(tok["lemma"] in INTERPRETIVE_VERBS for tok in item["tokens"])


def has_injected_clause(item):
    text = item["sentence"].lower()
    return "which" in text and any(w in text for w in {"suggest", "imply", "indicate"})

def get_head_token(item, tok):

    head = tok.get("head")

    if isinstance(head, str):
        for t in item["tokens"]:
            if t["text"] == head:
                return t

    return None    

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
        "is_reporting": is_reporting_sentence(item)
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
        (f["has_generalization"] or f["has_extreme_claim"] )
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
        and not is_reporting_sentence(item)
        and not has_contextual_support(item, sentences)
    )

# =========================
# APPLY
# =========================

def apply_rules(f, item, sentences):

    if f["is_reporting"]:
        return {"label": "CLEAN", "rule": "reporting"}

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

def detect_A1(item, sentences):
    for tok in item["tokens"]:

        # authority noun as subject OR object of attribution
        if tok["lemma"] in AUTHORITY_TERMS:

            # subject case
            if tok["dep"] in {"nsubj", "nsubjpass"}:
                if has_assertion_verb(item):
                    if not has_contextual_support(item, sentences):
                        return True

            if tok["dep"] == "pobj":
              head = get_head_token(item, tok)
              if head and head["lemma"] == "to":
               return True
    return False

CONSENSUS_PHRASES = {
    "most studies", "many studies", "the literature shows",
    "widely accepted", "generally accepted", "overwhelming evidence",
    "previous research", "previous studies", "previous work", "prior research", "prior studies", "prior work"
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
    "remarkable", "compel", "striking", "significant",
    "concerning", "troubling", "robust",
    "powerful", "dramatic", "significant", "notable",
    "substantial", "alarming", "worrying", "surprising", "robust", "clear", "conclusive"
}

def detect_A5(item):

    for tok in item["tokens"]:

        term = tok["lemma"] if tok["lemma"] in LOADED_TERMS else tok["text"].lower()

        if term in LOADED_TERMS and tok["dep"] in {"amod", "advmod"}:

            head = get_head_token(item, tok)

            if head and head["lemma"] in {
                "result", "improvement", "performance",
                "method", "approach", "model", "effect"
            }:
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

    if strong and has_citation and not item.get("has_qualifier") and not item.get("has_hedge"):
        return True

    return False

def detect_A_series(item, F_label, sentences):

    A = []

    if F_label is None:
        # restrict to high-confidence only
        if detect_A5(item):
            A.append("A5")
        return A

    if detect_A1(item, sentences):
        A.append("A1")

    if detect_A3(item):
        A.append("A3")

    if detect_A5(item):
        A.append("A5")

    if detect_A2(item):
        A.append("A2")

    #if detect_A4(item):
       # A.append("A4")

    return A

# ==========================
# M Series
# ==========================

HEDGERS = {
    "may", "might", "could", "possibly", "likely",
    "appear", "suggest"
}

def detect_M1(item):
    return any(tok["lemma"] in HEDGERS for tok in item["tokens"])

BOOSTERS = {"clear", "strong", "undeniable", "conclusive"}

def detect_M2(item):
    for tok in item["tokens"]:
        if tok["lemma"] in BOOSTERS and tok["dep"] in {"advmod", "amod"}:
            return True
    return False

DOWNTONERS = {"slightly", "somewhat", "marginally", "modestly"}

def detect_M3(item):
    return any(tok["lemma"] in DOWNTONERS for tok in item["tokens"])

EMPHASIS = {"notably", "importantly", "crucially"}

def detect_M4(item):

    for tok in item["tokens"]:
        if tok["lemma"] in EMPHASIS:

            # exclude statistical usage
            if tok["lemma"] == "significantly":
                continue

            return True

    return False

DISCOURSE = {
    "however", "therefore", "moreover",
    "nonetheless", "consequently"
}

def detect_M5(item):
    return any(tok["lemma"] in DISCOURSE for tok in item["tokens"])

def detect_M_series(item):

    M = []

    if detect_M1(item):
        M.append("M1")

    if detect_M2(item):
        M.append("M2")

    if detect_M3(item):
        M.append("M3")

    if detect_M4(item):
        M.append("M4")

    if detect_M5(item):
        M.append("M5")

    return M    

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

    if item.get("has_anchor") or item.get("linked_anchor") is not None:
        score -= 1
    
    M = detect_M_series(item)
    if "M1" in M:
        score -= 1
    if "M2" in M:
        score += 1
    if "M3" in M:
        score -= 0.5
    if "M4" in M:
        score += 0.5            

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
        A_labels = detect_A_series(item, result["label"], sentences)
        M_labels = detect_M_series(item)
        score = compute_score(item, result["label"], A_labels)
        results.append({
            "sentence": item["sentence"],
            "sentence_id": item["sentence_id"],
            "label": result["label"],
            "rule": result["rule"],
            "features": f
            |{"A_labels": A_labels, "M_labels": M_labels},
            "score": score

        })

    return results

import json

def dump_sentences(results, path="debug_results.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for s in results:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


def run_analysis(input_file):

    sentences = preprocess(input_file)["sentences"]

    results = analyze_input(sentences)

    return {
        "sentences": sentences,
        "results": results
    }


if __name__ == "__main__":

    input_file = "sample_paper.txt"

    output = run_analysis(input_file)

    dump_sentences(output["results"])