from pathlib import Path
import subprocess
import unicodedata
import re
from typing import List, Dict, Any
import spacy
from spacy.tokens import Span
from sympy import root

# =========================
# NLP SETUP
# =========================

nlp = spacy.load("en_core_web_md")

Span.set_extension("is_metadata", default=False, force=True)
Span.set_extension("is_header", default=False, force=True)
Span.set_extension("is_math_dominant", default=False, force=True)
Span.set_extension("has_limitation_anchor", default=False, force=True)

BASE_DIRECTORY_PATH = Path(__file__).resolve().parent
PDFTOTEXT_PATH = BASE_DIRECTORY_PATH / "pdftotext" / "pdftotext.exe"

# =========================    
# INPUT HANDLING
# =========================
    
def detect_input_type(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".txt":
        return "text"       
    raise ValueError(f"Unsupported file type: {suffix}")     

def read_text_file(file_path: str) -> str:
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(file_path).read_text(encoding="latin-1")

def input_to_text(file_path: str) -> str:
     return read_text_file(file_path)

# =========================
# NORMALIZATION
# =========================

HEADING_RE = re.compile(r"^\d+(\.\d+)*\s+[A-Z]")

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(
        ch for ch in text if ch in {"\n", "\t"} or unicodedata.category(ch)[0] != "C"
    )

    processed_lines = []

    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).rstrip()

        # If it's a section heading, force sentence boundary
        if HEADING_RE.match(line) and not line.endswith("."):
            line = line + "."

        processed_lines.append(line)

    return "\n".join(processed_lines)


EXCLUDED_HEADERS = {
    "references",
    "bibliography",
    "funding",
    "appendix"
}

def is_excluded_header(text):
    text = text.lower().strip()
    return any(h in text for h in EXCLUDED_HEADERS)
    
# =========================
# BLOCKING v2 (STRUCTURAL)
# =========================

WORD_RE = re.compile(r"[A-Za-z]{2,}")
MATH_CHARS_RE = re.compile(r"[=+\-*/^<>≤≥≈∼±√×÷∈∑∏∫∂∆→←]")
MATH_TOKEN_RE = re.compile(r"\b(\w\s*\(|\(\s*\d+|\d+\s*[-+*/=])")

SECTION_HEADERS = {
    "references",
    "bibliography",
    "funding",
    "appendix"
}

CAPTION_HINTS = {
    "fig", "figure", "table", "tab", "panel"
}

DERIVATION_HINTS = {
    "thus", "therefore", "hence", "it follows",
    "we obtain", "we derive", "we compute"
}

DEFINITION_HINTS = {
    "we define", "let", "is defined", "denote"
}

CLAIM_HINTS = {
    "we show", "we find", "we demonstrate", "we investigate"
}


# =========================
# MATH DENSITY
# =========================

def math_density(text: str) -> float:
    if not text:
        return 0.0

    alpha = len(re.findall(r"[A-Za-z]", text))
    math = len(MATH_CHARS_RE.findall(text))
    tokens = len(MATH_TOKEN_RE.findall(text))

    if alpha == 0:
        return 1.0 if (math + tokens) > 0 else 0.0

    return (math + tokens * 2) / alpha


# =========================
# SECTION DETECTION
# =========================

def is_section_header(text: str) -> bool:
    t = text.strip().lower()
    return any(h in t for h in SECTION_HEADERS)


def is_caption(text: str) -> bool:
    t = text.strip().lower()

    return (
        any(h in t for h in CAPTION_HINTS)
        and len(t.split()) < 30
    )


# =========================
# BLOCK TYPE CLASSIFICATION
# =========================

def classify_block(text: str) -> str:
    t = text.strip()
    t_low = t.lower()

    words = len(WORD_RE.findall(t))
    density = math_density(t)

    # -------------------------
    # 1. HARD STRUCTURE FILTERS
    # -------------------------
    if not t:
        return "EMPTY"

    if is_section_header(t):
        return "SECTION_HEADER"

    if is_caption(t):
        return "CAPTION"

    if density > 0.45 and words < 20:
        return "EQUATION"

    # -------------------------
    # 2. SCIENTIFIC ROLES
    # -------------------------
    if any(h in t_low for h in DEFINITION_HINTS):
        return "DEFINITION"

    if any(h in t_low for h in DERIVATION_HINTS):
        return "DERIVATION"

    if any(h in t_low for h in CLAIM_HINTS):
        return "CLAIM"

    # -------------------------
    # 3. FALLBACK PROSE
    # -------------------------
    if words > 0:
        return "PROSE"

    return "METADATA"


# =========================
# BLOCK BUILDER (SAFE)
# =========================

def build_blocks(text: str) -> List[Dict]:
    """
    Clean segmentation into structural blocks.
    No duplication bugs, no mid-loop appends.
    """

    lines = text.split("\n")

    blocks = []
    buffer = []
    start_char = 0
    cursor = 0
    prev_blank = True

    for line in lines:
        is_blank = not line.strip()
        line_len = len(line) + 1

        # start new block
        if not is_blank and prev_blank:
            if buffer:
                block_text = "\n".join(buffer)
                blocks.append({
                    "text": block_text,
                    "start_char": start_char,
                    "end_char": start_char + len(block_text),
                })
                buffer = []
            start_char = cursor

        if not is_blank or buffer:
            buffer.append(line)

        prev_blank = is_blank
        cursor += line_len

    # flush
    if buffer:
        block_text = "\n".join(buffer)
        blocks.append({
            "text": block_text,
            "start_char": start_char,
            "end_char": start_char + len(block_text),
        })

    # assign IDs
    for i, b in enumerate(blocks):
        b["block_id"] = i

    return blocks


# =========================
# BLOCKING STAGE (NEW CORE)
# =========================

def blocking(raw_blocks: List[Dict]) -> List[Dict]:
    """
    Converts raw blocks → structurally meaningful blocks.

    KEY CHANGE:
    - classification happens EARLY
    - section state is explicit
    - no global variables
    """

    blocks = []
    in_section = False

    for b in raw_blocks:
        text = b["text"]
        btype = classify_block(text)

        # section tracking (hard boundary)
        if btype == "SECTION_HEADER":
            in_section = True

        blocks.append({
            "block_id": b["block_id"],
            "text": text,
            "start_char": b.get("start_char"),
            "end_char": b.get("end_char"),

            # core structural outputs
            "block_type": btype,
            "is_section": in_section,

            # early structural hints
            "math_density": math_density(text),
        })

    return blocks


# =========================
# COALESCING + SAFE DEDUP
# =========================

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def coalesce_blocks(blocks: List[Dict]) -> List[Dict]:
    """
    Merges noise fragments safely without destroying scientific repetition.
    """

    merged = []
    buffer = None
    seen_short = set()

    def flush():
        nonlocal buffer
        if buffer:
            merged.append(buffer)
            buffer = None

    for b in blocks:
        text = b["text"]

        # merge non-text fragments
        if not WORD_RE.search(text):
            if buffer is None:
                buffer = b.copy()
            else:
                buffer["text"] += "\n" + text
            continue

        flush()
        merged.append(b)

    flush()

    # deduplicate ONLY very small blocks
    final = []
    for b in merged:
        key = normalize(b["text"])

        if len(b["text"]) < 200:
            if key in seen_short:
                continue
            seen_short.add(key)

        final.append(b)

    # reindex
    for i, b in enumerate(final):
        b["block_id"] = i

    return final

# =========================
# SENTENCE EXTRACTION
# =========================

def segment_sentences(blocks: List[Dict]) -> List[Dict]:
    sentences = []
    sid = 0

    for block in blocks:
        if block.get("is_excluded_section", False):
            continue

        # NEW: filter early
        if block["block_type"] != "PROSE":
            continue

        if math_density(block["text"]) > 0.25:
            continue

        doc = nlp(block["text"])

        for local_id, sent in enumerate(doc.sents):
            sentences.append(
                {
                    "sentence_id": sid,
                    "block_id": block["block_id"],
                    "local_sentence_id": local_id,
                    "sentence": sent.text,
                    "tokens": [
                        {
                            "text": tok.text.lower(),
                            "lemma": tok.lemma_.lower(),
                            "pos": tok.pos_,
                            "dep": tok.dep_,
                            "i": tok.i,
                            "head": tok.head.text,
                        }
                        for tok in sent
                    ],
                    "sentence_span": sent,
                    "start_char": block["start_char"] + sent.start_char,
                    "end_char": block["start_char"] + sent.end_char,
                }
            )
            sid += 1

    return sentences

# =========================
# STRUCTURE MARKERS
# =========================

from collections import Counter

SECTION_KEYWORDS = {
    "abstract",
    "introduction",
    "methods",
    "results",
    "discussion",
    "conclusion",
    "conclusions",
    "acknowledgment",
    "acknowledgements",
    "references",
    "open research",
    "conflict of interest",
}

def normalize_for_count(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def is_section_heading(text: str) -> bool:
    stripped = text.strip()

    # numeric headings
    if re.match(r"^\d+(\.\d+)*\s+[A-Z]", stripped):
        return True

    # short title-like lines
    if (
        len(stripped.split()) <= 6
        and not stripped.endswith(".")
        and any(c.isalpha() for c in stripped)
    ):
        return True

    if stripped.lower() in SECTION_KEYWORDS:
        return True

    return False

def apply_structure_markers(sentences: List[Dict]) -> None:
    # Count normalized sentence frequencies
    normalized = [normalize_for_count(s["sentence_span"].text) for s in sentences]
    freq = Counter(normalized)

    for s in sentences:
        text = s["sentence_span"].text
        norm = normalize_for_count(text)

        # Repeated running headers (>=4)
        if freq[norm] >= 4:
            s["sentence_span"]._.is_metadata = True
            continue

        # Section headings
        if is_section_heading(text):
            s["sentence_span"]._.is_header = True

# =========================
# EPISTEMIC MODES
# =========================

E0, E1, E2, E3 = "E0", "E1", "E2", "E3"

def has_that_clause(verb):
    """
    Detects a clausal complement governed by a predicate.
    Covers explicit and implicit 'that' clauses.
    """
    for child in verb.children:
        if child.dep_ == "ccomp":
            return True
        if child.dep_ == "xcomp" and any(
            gc.dep_ == "mark" and gc.text.lower() == "that" for gc in child.children
        ):
            return True
    return False

def has_epistemic_subject(verb):
    for child in verb.children:
        if child.dep_ in {"nsubj", "nsubjpass"}:
            return True
    return False

def is_finite_predicate(verb):
    return verb.morph.get("VerbForm") == ["Fin"]

AUTHORIAL_PATTERNS = {
    "we",
    "our",
    "this study",
    "this work",
    "this paper",
}

CAUSAL_MARKERS = {
    "because",
    "although",
    "though",
    "whereas",
    "therefore",
    "thus",
     "hence",
}

def subject_span(tok):
    """
    Expand subject token to include compounds/determiners.
    """
    parts = [tok]
    parts.extend(list(tok.lefts))
    parts.extend(list(tok.rights))
    parts = sorted(parts, key=lambda t: t.i)
    return " ".join(t.text.lower() for t in parts)
    

def E_mode(sent: Span, doc=None):

    # -----------------------------
    # HARD EXCLUSIONS → E0
    # -----------------------------
    if sent._.is_metadata or sent._.is_header:
        return E0, None

    if sent._.is_math_dominant:
        return E0, None

    # -----------------------------
    # Extract core structure
    # -----------------------------
    root = None
    has_subject = False
    has_modal = False

    for tok in sent:

        if tok.dep_ == "ROOT":
            root = tok

        if tok.dep_ in {"nsubj", "nsubjpass"}:
            has_subject = True

        if tok.tag_ == "MD":
            has_modal = True

    # -----------------------------
    # Structural validity check
    # -----------------------------
    if root is None:
     return E0, None

    if root.pos_ not in {"VERB", "AUX", "ADJ", "NOUN"}:
     return E0, None

    if not has_subject:
     return E0, None

    # -----------------------------
    # E3 (strongest)
    # -----------------------------
    for tok in sent:

        if tok.dep_ == "mark" and tok.text.lower() in CAUSAL_MARKERS:
            return E3, tok.text.lower()

        if tok.dep_ in {"advcl", "acl"}:
            if any(
                child.dep_ == "mark" and child.text.lower() in CAUSAL_MARKERS
                for child in tok.children
            ):
                return E3, "subordinate_clause"

        if tok.text.lower() == "if" and has_modal:
            return E3, "counterfactual"

    # -----------------------------
    # E1 (authorial)
    # -----------------------------
    for tok in sent:
        if tok.dep_ in {"nsubj", "nsubjpass"}:
            span_text = subject_span(tok)
            if span_text in AUTHORIAL_PATTERNS:
                for t in sent:
                    if t.dep_ in {"xcomp", "ccomp"} and t.head.pos_ == "VERB":
                        return E1, "authorial_scope"
    
    if has_subject:
     return E2, "descriptive"
    # -----------------------------
    # E2 (ONLY valid declaratives)
    # -----------------------------
    return E2, "finite_structured"
    


def assign_epistemic_mode(sentences: List[Dict]) -> None:
    for s in sentences:
        mode, trigger = E_mode(s["sentence_span"])
        s["epistemic_mode"] = mode
        s["epistemic_trigger"] = trigger

# =========================
# MODALITY
# =========================

LOW_MODAL = {"may", "might", "can", "could"}

MID_MODAL = {"often", "usually", "generally", "tends", "typically"}

HIGH_MODAL = {"always", "never"}

HEDGES = {"possibly", "likely", "unlikely", "suggests"}

def detect_modality(sent: Span) -> Dict[str, Any]:
    modal_tokens = []
    hedge_tokens = []

    for tok in sent:
        t = tok.text.lower()

        # POS-based modal detection (reliable for can, may, etc.)
        if tok.tag_ == "MD":
            modal_tokens.append(t)

        # lexical modality (frequency / tendency)
        if t in MID_MODAL or t in HIGH_MODAL:
            modal_tokens.append(t)

        # hedges (separate channel)
        if t in HEDGES:
            hedge_tokens.append(t)

    return {
        "modal_tokens": list(set(modal_tokens)),
        "has_modal": len(modal_tokens) > 0,
        "has_hedge": len(hedge_tokens) > 0
    }

def assign_modality(sentences: List[Dict]) -> None:
    for s in sentences:
        mod = detect_modality(s["sentence_span"])
        s["modal_tokens"] = mod["modal_tokens"]
        s["has_modal"] = mod["has_modal"]
        s["has_hedge"] = mod["has_hedge"]

# =========================
# EXCLUSION
# =========================

ALPHA_RE = re.compile(r"[A-Za-z]+")
MATH_SYMBOLS = "\\^_+\\-\\*/=<>\u2264\u2265\u2248\u221d\u2192\u2190\u2202\u2207\u00D7\u2297\u2295\u2225\\(\\)\\[\\]\\{\\}"
GREEK = "\u0370-\u03FF"

def longest_alpha_span(text: str) -> int:
    spans = ALPHA_RE.findall(text)
    return max((len(s) for s in spans), default=0)

def exclusion(sentences):

    def is_truncated(txt):
        return bool(re.search(r"\b(we define|we derive|we obtain|which yields|where)\s*$", txt.lower()))

    for s in sentences:
        txt = s["sentence"].strip()

        # -------------------------
        # 0. Empty / trivial
        # -------------------------
        if not txt:
            s["excluded"], s["exclusion_reason"] = True, "EMPTY"
            continue

        # -------------------------
        # 1. Math / symbol noise
        # -------------------------
        if math_density(txt) > 0.45:
            s["excluded"], s["exclusion_reason"] = True, "MATH_DOMINANT"
            continue

        if re.search(r"[a-zA-Z]\s+[a-zA-Z]\s*[=]", txt):
            s["excluded"], s["exclusion_reason"] = True, "MATH_FRAGMENT"
            continue

        # -------------------------
        # 2. Structural noise
        # -------------------------
        if longest_alpha_span(txt) < 4:
            s["excluded"], s["exclusion_reason"] = True, "LAS_TOO_SHORT"
            continue

        if s["sentence_span"]._.is_metadata:
            s["excluded"], s["exclusion_reason"] = True, "METADATA"
            continue

        if s["sentence_span"]._.is_header:
            s["excluded"], s["exclusion_reason"] = True, "HEADER"
            continue

        # -------------------------
        # 3. Broken sentence detection
        # -------------------------
        if txt[0].islower() and len(txt.split()) > 6:
            s["excluded"], s["exclusion_reason"] = True, "BROKEN_START"
            continue

        if txt.strip().endswith(("which", "that", "where", "and", "or")):
            s["excluded"], s["exclusion_reason"] = True, "INCOMPLETE_END"
            continue

        if is_truncated(txt):
            s["excluded"], s["exclusion_reason"] = True, "TRUNCATED"
            continue

        # -------------------------
        # 4. Syntax check (relaxed, but not dead)
        # -------------------------
        has_root_verb = False
        has_subject = False

        for tok in s["tokens"]:
            if tok["dep"] == "ROOT" and tok["pos"] in {"VERB", "AUX"}:
                has_root_verb = True
            if tok["dep"] in {"nsubj", "nsubjpass"}:
                has_subject = True

        # allow long scientific fragments without strict verb
        if not has_root_verb:
            if len(re.findall(r"[A-Za-z]{3,}", txt)) <= 8:
                s["excluded"], s["exclusion_reason"] = True, "NO_ROOT_VERB"
                continue

        if not has_subject:
            s["excluded"], s["exclusion_reason"] = True, "NO_SUBJECT"
            continue

        # -------------------------
        # 5. Epistemic filter
        # -------------------------
        if s["epistemic_mode"] == "E0":
            s["excluded"], s["exclusion_reason"] = True, "E0"
            continue

        # -------------------------
        # PASS
        # -------------------------
        s["excluded"], s["exclusion_reason"] = False, "VALID"
# =========================
# ANCHORS
# =========================

A1_FIGURE, A2_REFERENCE, A3_QUANTITATIVE, A4_METHOD, A5_MODEL, A6_LIMITATION = (
    "A1_FIGURE",
    "A2_REFERENCE",
    "A3_QUANTITATIVE",
    "A4_METHOD",
    "A5_MODEL",
    "A6_LIMITATION",
)

# --- Improved regex coverage ---
A1_RE = re.compile(
    r"\b(fig(?:ure)?s?|table|tab\.?|panel)\s*[A-Za-z]?\d+[A-Za-z]?",
    re.I
)

A2_RE = re.compile(
    r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]"  # [1], [1,2], [1, 2, 3]
    r"|\bet al\.\b"
    r"|\([A-Z][a-z]+(?: et al\.)?,?\s*\d{4}\)"
    r"|\b(previous work|prior work|earlier studies|the literature)\b",
    re.I
)

A3_RE = re.compile(
    r"(n\s*=\s*\d+|p\s*[<=>]\s*0?\.\d+|confidence interval|ci\b|mean\s*±|std\.?|sd\b|eq\.?\s*\(?\d+\)?|equation\s*\(?\d+\)?|eqs?\.\s*\(?\d+)",
    re.I
)

A4_RE = re.compile(
    r"\b(method|procedure|protocol|experimental setup|we used|we employed)\b",
    re.I
)

A5_RE = re.compile(
    r"\b(assume|assumption|model|let\s+\w+\s+be)\b",
    re.I
)

A6_RE = re.compile(
    r"\b(however|nevertheless|limitation|limited to|future work|we note that)\b",
    re.I
)


def anchoring(sentences: List[Dict]) -> None:
    for s in sentences:
        anchors = []

        if A1_RE.search(s["sentence"]):
            anchors.append(A1_FIGURE)

        if A2_RE.search(s["sentence"]):
            anchors.append(A2_REFERENCE)

        if A3_RE.search(s["sentence"]):
            anchors.append(A3_QUANTITATIVE)

        if A4_RE.search(s["sentence"]):
            anchors.append(A4_METHOD)

        if A5_RE.search(s["sentence"]):
            anchors.append(A5_MODEL)

        if A6_RE.search(s["sentence"]):
            anchors.append(A6_LIMITATION)

        s["anchors"] = anchors
        s["has_anchor"] = bool(anchors)


# =========================
# INFERENCE DETECTION (UPGRADED)
# =========================

ANAPHORIC_DET = {"this", "these", "such"}

EPISTEMIC_VERBS = {
    "suggest",
    "indicate",
    "imply",
    "show",
    "demonstrate",
    "reveal",
    "confirm",
    "support",
    "agree",
    "align",
    "correspond",
    "consistent with",
    "in line with",
    "agrees with",
    "matches",
    "aligns with",
    "match",
    "agree",
    "be consistent",
    "be in agreement",
    "correspond",
}   

EVIDENCE_SUBJECTS = {
    "result",
    "results",
    "finding",
    "findings",
    "data",
    "evidence",
    "pattern",
    "observation",
}


def detect_anaphoric_inference(sent):

    root = None
    for tok in sent:
        if tok.dep_ == "ROOT":
            root = tok
            break

    if root is None:
        return False

    # verb must be epistemic
    if root.lemma_.lower() not in EPISTEMIC_VERBS:
        return False

    subject = None
    for child in root.children:
        if child.dep_ in {"nsubj", "nsubjpass"}:
            subject = child
            break

    if subject is None:
        return False

    subj_tokens = list(subject.subtree)
    subj_lemmas = {t.lemma_.lower() for t in subj_tokens}

    # either anaphoric determiner OR evidence noun
    if not (
        any(t.lemma_.lower() in ANAPHORIC_DET for t in subj_tokens)
        or any(l in EVIDENCE_SUBJECTS for l in subj_lemmas)
    ):
        return False

    # must have a clausal complement
    if not any(c.dep_ in {"ccomp", "xcomp"} for c in root.children):
        return False

    return True


# --- tightened prepositional evidence ---
def detect_prepositional_evidence(sent):

    for tok in sent:

        # based on (must attach to verb/clause)
        if tok.lemma_ == "base" and tok.dep_ in {"advcl", "prep"}:
            if any(child.text.lower() == "on" for child in tok.children):
                return True

        # according to
        if tok.lemma_ == "accord":
            if any(child.text.lower() == "to" for child in tok.children):
                return True

        # derived from
        if tok.lemma_ == "derive":
            if any(child.text.lower() == "from" for child in tok.children):
                return True

    return False


# =========================
# LINKING (CONTROLLED)
# =========================

MAX_ANCHOR_DISTANCE = 3
MAX_ANCHORS_TRACKED = 2


def link_anchor_claim(sentences):

    recent_anchors = []  # list of (sentence_id)

    for i, s in enumerate(sentences):

        sid = s["sentence_id"]

        # --- hard reset on limitation ---
        if A6_LIMITATION in s["anchors"]:
            recent_anchors = []

        # --- if sentence has anchor ---
        if s["has_anchor"]:

            if A6_LIMITATION not in s["anchors"]:
                recent_anchors.append(sid)
                recent_anchors = recent_anchors[-MAX_ANCHORS_TRACKED:]

            s["linked_anchor"] = sid
            continue

        # --- distance-based pruning ---
        recent_anchors = [
            a for a in recent_anchors if (sid - a) <= MAX_ANCHOR_DISTANCE
        ]

        # --- inference check ---
        if detect_anaphoric_inference(s["sentence_span"]) or detect_prepositional_evidence(s["sentence_span"]):

            if recent_anchors:
                # choose closest anchor
                s["linked_anchor"] = recent_anchors[-1]
            else:
                s["linked_anchor"] = None

        else:
            s["linked_anchor"] = None

def finalize_sentences(sentences: List[Dict]) -> None:
    for s in sentences:
        s.pop("sentence_span", None)

# =========================
# WINDOWS
# =========================

def build_windows(sentences, window_size=6, stride=3):
    windows = []
    for i in range(0, len(sentences) - window_size + 1, stride):
        chunk = sentences[i : i + window_size]
        windows.append(
            {
                "sentence_ids": [s["sentence_id"] for s in chunk],
                "block_ids": list({s["block_id"] for s in chunk}),
                "text": " ".join(s["sentence"] for s in chunk),
                "sentences": chunk,
            }
        )
    return windows

def enrich_windows(windows):
    for w in windows:
        scores = [(1.0 if s["excluded"] else 0.0) for s in w["sentences"]]
        w["noise_score"] = sum(scores) / len(scores)
        w["linguistic_density"] = sum(
            len(re.findall(r"[A-Za-z]", s["sentence"])) for s in w["sentences"]
        ) / max(sum(len(s["sentence"]) for s in w["sentences"]), 1)
        w["usable_for_heuristics"] = (
            w["noise_score"] <= 0.5 and w["linguistic_density"] >= 0.35
        )

# =========================
# PIPELINE
# =========================

def preprocess(file_path: str) -> Dict[str, Any]:
    raw_input = input_to_text(file_path)
    normalized_input = normalize_text(raw_input)

    raw_blocks = build_blocks(normalized_input)
    raw_blocks = coalesce_blocks(raw_blocks)
    blocks = blocking(raw_blocks)

    sentences = segment_sentences(blocks)

    apply_structure_markers(sentences)
    assign_epistemic_mode(sentences)
    assign_modality(sentences)
    exclusion(sentences)
    anchoring(sentences)

    # FIX: link globally BEFORE windows
    link_anchor_claim(sentences)

    finalize_sentences(sentences)

    windows = build_windows(sentences)
    enrich_windows(windows)

    return {
        "blocks": blocks,
        "sentences": sentences,
        "windows": windows,
    }




