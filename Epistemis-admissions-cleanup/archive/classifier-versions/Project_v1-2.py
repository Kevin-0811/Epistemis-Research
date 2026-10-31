from preprocessor_versions.preprocessor_v1 import preprocess

input_file = "data.txt"
sentences = preprocess(input_file)["sentences"]

def normalize_text(text):
    return text.lower().strip()

GENERALIZERS = {"all", "always", "never", "every", "none"}

STRONG_CAUSAL = {
    "cause", "causes", "caused",
    "lead", "leads", "led",
    "result", "results", "resulted",
    "produce", "produces", "produced"
}

WEAK_RELATION = {
    "affect", "affects",
    "influence", "influences",
    "impact", "impacts",
    "improve", "improves",
    "enhance", "enhances",
    "change", "changes"
}


# =========================
# FEATURE DETECTION 
# =========================

def has_weak_relation(item):
    for tok in item["tokens"]:

        if tok["pos"] == "VERB":

            # skip strong causal
            if tok["lemma"] in STRONG_CAUSAL:
                continue

            if tok["dep"] == "ROOT":
                return True

    return False


def has_strong_causal(item):
    for tok in item["tokens"]:
        if tok["pos"] == "VERB":
            if tok["lemma"] in STRONG_CAUSAL:
             return True
    return False        


def has_generalization(item):
    for tok in item["tokens"]:
        if tok["lemma"] in GENERALIZERS:
            return True
    return False


def has_qualifier(item):

    for tok in item["tokens"]:

        # subordinating conjunctions (if, when, etc.)
        if tok["dep"] == "mark":
            return True

        # prepositional phrases (in X, at X, under X)
        if tok["dep"] == "prep":
            return True

    return False


# =========================
# STRENGTH COMPUTATION
# =========================

def compute_strength(item):

    tokens = set(item.get("modal_tokens", []))
    has_hedge = item.get("has_hedge", False)

    if tokens & {"can", "may", "might", "could"}:
        return "LOW"

    if tokens & {"often", "usually", "generally", "tends", "typically"}:
        return "MEDIUM"

    if tokens & {"always", "never"}:
        return "HIGH"

    # hedges downgrade certainty
    if has_hedge:
        return "LOW"

    # default
    return "IMPLICIT_HIGH"


# =========================
# FEATURE EXTRACTION
# =========================

def extract_features(item):

    return {
        "has_strong_causal": has_strong_causal(item),
        "has_generalization": has_generalization(item),
        "has_qualifier": has_qualifier(item),
        "has_weak_relation": has_weak_relation(item),
        "epistemic_strength": compute_strength(item)
    }


# =========================
# RULES
# =========================

def rule_F2(f):
    return (
        f["has_strong_causal"]
        and f["epistemic_strength"] in {"HIGH", "IMPLICIT_HIGH"}
        and not f["has_qualifier"]
    )


def rule_F1(f):
    return (
        f["has_generalization"]
        and f["epistemic_strength"] in {"HIGH", "IMPLICIT_HIGH"}
        and not f["has_qualifier"]
    )


def rule_F3(f):
    return (
        f["has_weak_relation"]
        and f["epistemic_strength"] in {"MEDIUM", "IMPLICIT_HIGH"}
        and not f["has_qualifier"]
        and not f["has_strong_causal"]
        and not f["has_generalization"]
    )

def apply_rules(features):

    if rule_F2(features):
        return {"label": "F2", "rule": "F2_absolutist_causal"}

    elif rule_F1(features):
        return {"label": "F1", "rule": "F1_unqualified_generalization"}

    elif rule_F3(features):
        return {"label": "F3", "rule": "F3_omitted_context"}

    else:
        return {"label": "CLEAN", "rule": "CLEAN_no_violation"}


# =========================
# ANALYSIS
# =========================

def analyze_input(sentences):
    results = []

    for item in sentences:
        features = extract_features(item)
        result = apply_rules(features)

        results.append({
            "sentence": item["sentence"],
            "label": result["label"],
            "rule": result["rule"],
            "features": features
        })

    return results


results = analyze_input(sentences)
for item in results:
    print(item["sentence"], item["label"])
