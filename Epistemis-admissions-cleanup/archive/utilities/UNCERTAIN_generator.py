import json
import re
from collections import Counter

INPUT_FILES = ["tier2_uncertain.jsonl", "tier2_uncertain__.jsonl"]
OUTPUT_FILE = "tier2_filtered.jsonl"

# -----------------------------
# CONFIG
# -----------------------------

KEEP_RATIO = 0.6        # 🔴 MAIN CONTROL (0.55–0.7 range)
REPEAT_THRESHOLD = 10   # 🔴 repetition tolerance

BANNED = [
    "without clearly specifying the limits of applicability",
    "which is taken to suggest causation even without controlled intervention",
    "even though the underlying definition is not consistently maintained",
]

MODEL_TERMS = [
    "model", "system", "framework", "simulation", "network"
]

# -----------------------------
# CLEANING
# -----------------------------

def clean_text(text):
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\.\s*,", ".", text)
    return text

# -----------------------------
# LIGHT SCORING (NO OVERKILL)
# -----------------------------

def score_sample(sample):
    text = sample["current"]
    category = sample.get("category", "")
    t = text.lower()

    score = 0

    # ✔ reasonable length
    length = len(text.split())
    if 8 <= length <= 40:
        score += 1

    # ✔ moderate structure (not over-comma'd)
    if text.count(",") <= 2:
        score += 1

    # ✔ slight reward for semantic signal
    if any(w in t for w in [
        "suggesting", "implying", "reflecting", "indicating", "assumed"
    ]):
        score += 1

    # ✔ validate C5 (but not harsh)
    if category == "C5":
        if any(w in t for w in MODEL_TERMS):
            score += 1

    # ✔ penalize obvious prefix spam (light)
    if t.startswith(("in practice,", "in general,", "in many cases,")):
        score -= 0.5

    return score

# -----------------------------
# REPETITION CONTROL
# -----------------------------

def phrase_signature(text):
    # tail-focused signature
    return " ".join(text.lower().split()[-6:])

def remove_repetition(samples, threshold=10):
    counts = Counter(phrase_signature(s["current"]) for s in samples)

    filtered = []
    for s in samples:
        sig = phrase_signature(s["current"])
        if counts[sig] <= threshold:
            filtered.append(s)

    return filtered

# -----------------------------
# MAIN PIPELINE
# -----------------------------

def process():

    all_samples = []

    # LOAD + CLEAN
    for file in INPUT_FILES:
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                s = json.loads(line)

                text = clean_text(s["current"])

                # only remove truly bad samples
                if any(b in text.lower() for b in BANNED):
                    continue

                s["current"] = text
                all_samples.append(s)

    print(f"Loaded: {len(all_samples)}")

    # SCORE ALL (no filtering yet)
    scored = [(score_sample(s), s) for s in all_samples]

    # SORT (best first)
    scored.sort(key=lambda x: x[0], reverse=True)

    # KEEP TOP %
    cutoff = int(len(scored) * KEEP_RATIO)
    kept = [s for _, s in scored[:cutoff]]

    print(f"After top-{int(KEEP_RATIO*100)}%: {len(kept)}")

    # REPETITION FILTER (RELAXED)
    final = remove_repetition(kept, threshold=REPEAT_THRESHOLD)

    print(f"After repetition filter: {len(final)}")

    # SAVE
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in final:
            f.write(json.dumps(item) + "\n")

# -----------------------------

if __name__ == "__main__":
    process()