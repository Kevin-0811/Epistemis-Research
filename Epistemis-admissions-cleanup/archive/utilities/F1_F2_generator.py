import json
import random
import re

INPUT_FILE = "tier1.jsonl"
OUTPUT_FILE = "tier1_full_v2.jsonl"

# -----------------------------
# F1: Interpretive distortions
# -----------------------------

F1_PATTERNS = [
    # correlation → implication
    (r"\bis associated with\b", "suggests a relationship with"),
    (r"\bis correlated with\b", "may indicate a relationship with"),

    # neutral → interpretive
    (r"\bindicate(s|d)?\b", "suggest"),
    (r"\bshow(s|ed)?\b", "suggest"),

    # descriptive → directional
    (r"\baffect(s|ed)?\b", "appear to influence"),
    (r"\bdepend(s|ed)? on\b", "may be driven by"),
]

F1_INSERTIONS = [
    "which may imply that",
    "suggesting that",
    "which could indicate that",
]

# -----------------------------
# F2: Causal violations
# -----------------------------

F2_PATTERNS = [
    # remove uncertainty
    (r"\bmay\b", ""),
    (r"\bcan\b", "will"),

    # implication → causation
    (r"\bsuggest(s|ed)?\b", "demonstrate"),
    (r"\bindicate(s|d)?\b", "establish"),

    # influence → determination
    (r"\binfluence(s|d)?\b", "determine"),
    (r"\baffect(s|ed)?\b", "directly determine"),
]

F2_EXPANSIONS = [
    "across all conditions",
    "in all cases",
    "independently of other factors",
]

# -----------------------------
# Helpers
# -----------------------------

def apply_patterns(text, patterns):
    for pattern, repl in patterns:
        text = re.sub(pattern, repl, text)
    return text

def insert_clause(text, insertions):
    if "," in text:
        parts = text.split(",", 1)
        insertion = random.choice(insertions)
        return parts[0] + ", " + insertion + " " + parts[1]
    return text

def reorder_clause(text):
    if " while " in text:
        parts = text.split(" while ")
        return parts[1] + " while " + parts[0]
    if " which " in text:
        parts = text.split(" which ")
        return "Which " + parts[1].capitalize() + ", " + parts[0]
    return text

# -----------------------------
# F1 generator
# -----------------------------

def make_f1(sentence):
    s = apply_patterns(sentence, F1_PATTERNS)

    # inject interpretive clause (40%)
    if random.random() < 0.4:
        s = insert_clause(s, F1_INSERTIONS)

    # slight structural variation (20%)
    if random.random() < 0.2:
        s = reorder_clause(s)

    return s.strip()

# -----------------------------
# F2 generator
# -----------------------------

def make_f2(sentence):
    s = apply_patterns(sentence, F2_PATTERNS)

    # enforce causality jump
    if "suggest" in s:
        s = s.replace("suggest", "demonstrate")

    # add universal claim (40%)
    if random.random() < 0.4:
        s += " " + random.choice(F2_EXPANSIONS)

    # slight structural variation (30%)
    if random.random() < 0.3:
        s = reorder_clause(s)

    return re.sub(r"\s+", " ", s).strip()

# -----------------------------
# Main pipeline
# -----------------------------

def process():
    output = []
    id_counter = 1

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)

            if data["label"] != "CLEAN":
                continue

            # CLEAN
            base = data.copy()
            base["id"] = f"T1_C_{id_counter}"
            output.append(base)

            # F1
            f1 = data.copy()
            f1["id"] = f"T1_F1_{id_counter}"
            f1["current"] = make_f1(data["current"])
            f1["label"] = "F1"
            output.append(f1)

            # F2
            f2 = data.copy()
            f2["id"] = f"T1_F2_{id_counter}"
            f2["current"] = make_f2(data["current"])
            f2["label"] = "F2"
            output.append(f2)

            id_counter += 1

    random.shuffle(output)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in output:
            f.write(json.dumps(item) + "\n")

    print(f"Done. Generated {len(output)} samples.")

if __name__ == "__main__":
    process()