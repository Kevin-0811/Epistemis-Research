from pathlib import Path
import re
from typing import List, Dict, Any
import spacy
from spacy.tokens import Span
from sympy import root
from lxml import etree

NS = {"tei": "http://www.tei-c.org/ns/1.0"}

EXCLUDED_SECTIONS = {
    "references", "bibliography", "acknowledgements",
    "appendix", "funding"
}

def extract_section_path(div):
    titles = []
    current = div

    while current is not None:
        head = current.find("tei:head", namespaces=NS)
        if head is not None and head.text:
            titles.append(head.text.strip().lower())
        current = current.getparent()

    return " > ".join(reversed(titles))

def parse_tei(xml_path: str):
    tree = etree.parse(xml_path)
    root = tree.getroot()

    sections = []

    for div in root.xpath("//tei:body//tei:div", namespaces=NS):

        head = div.find("tei:head", namespaces=NS)
        section_title = extract_section_path(div) if head is not None else "unknown"

        paragraphs = []
        figures = []
        tables = []

        # paragraphs
        for p in div.findall("./tei:p", namespaces=NS):

         text = "".join(p.itertext()).strip()
         if not text:
          continue

         has_citation = False
         citation_spans = []

         for ref in p.findall(".//tei:ref", namespaces=NS):
          if ref.get("type") == "bibr":
            has_citation = True
            citation_spans.append("".join(ref.itertext()).strip())

         paragraphs.append({
         "text": text,
         "has_citation": has_citation,
         "citations": citation_spans
          })

        # figure captions
        for fig in div.findall("./tei:figure", namespaces=NS):
            desc = fig.find("./tei:figDesc", namespaces=NS)
            if desc is not None:
                figures.append("".join(desc.itertext()).strip())

        # tables
        for table in div.findall(".//tei:table", namespaces=NS):
            text = "".join(table.itertext()).strip()
            if text:
                tables.append(text)

        sections.append({
            "section_title": section_title,
            "is_excluded": any(k in section_title for k in EXCLUDED_SECTIONS),
            "paragraphs": paragraphs,
            "figures": figures,
            "tables": tables
        })

    return sections

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
# BLOCKING v2 (STRUCTURAL)
# =========================

def get_section_weight(section):
    s = section.lower()

    if "methods" in s:
        return 0.6
    if "results" in s:
        return 1.2
    if "discussion" in s:
        return 1.5
    return 1.0

WORD_RE = re.compile(r"[A-Za-z]{2,}")
MATH_CHARS_RE = re.compile(r"[=+\-*/^<>≤≥≈∼±√×÷∈∑∏∫∂∆→←]")
MATH_TOKEN_RE = re.compile(r"\b(\w\s*\(|\(\s*\d+|\d+\s*[-+*/=])")


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

def build_blocks_from_tei(sections):
    blocks = []
    bid = 0

    for sec in sections:

        # paragraph blocks
        for para in sec["paragraphs"]:
         blocks.append({
         "block_id": bid,
         "text": para["text"],
         "section": sec["section_title"],
         "block_type": "paragraph",
         "is_excluded_section": sec["is_excluded"],
         "has_citation": para["has_citation"],
         "citations": para["citations"]
        })
         bid += 1

        # figure captions
        for fig in sec["figures"]:
            blocks.append({
                "block_id": bid,
                "text": fig,
                "section": sec["section_title"],
                "block_type": "figure",
                "is_excluded_section": sec["is_excluded"]
            })
            bid += 1

        # tables
        for tab in sec["tables"]:
            blocks.append({
                "block_id": bid,
                "text": tab,
                "section": sec["section_title"],
                "block_type": "table",
                "is_excluded_section": sec["is_excluded"]
            })
            bid += 1

    return blocks

# =========================
# MATH DENSITY
# =========================

def math_density(text: str) -> float:
    if not text:
        return 0.0

    tokens = text.split()
    alpha = sum(1 for t in tokens if re.search(r"[A-Za-z]", t))
    math = len(MATH_CHARS_RE.findall(text))
    tokens = len(MATH_TOKEN_RE.findall(text))

    if alpha == 0:
        return 1.0 if (math + tokens) > 0 else 0.0

    return (math + tokens * 2) / alpha

def protect_math(text):
    return re.sub(r"([=<>])", r" \1 ", text)

def segment_sentences(blocks: List[Dict]) -> List[Dict]:
    sentences = []
    sid = 0

    for block in blocks:

        doc = nlp(protect_math(block["text"]))

        for local_id, sent in enumerate(doc.sents):

            sentences.append({
                "sentence_id": sid,
                "block_id": block["block_id"],
                "section": block["section"],
                "block_type": block["block_type"],
                "sentence": sent.text,
                "tokens": [
                    {
                        "text": tok.text.lower(),
                        "lemma": tok.lemma_.lower(),
                        "pos": tok.pos_,
                        "dep": tok.dep_,
                        "i": tok.i,
                        "head": tok.head.i,
                    }
                    for tok in sent
                ],
                "sentence_span": sent,
                "section_weight": get_section_weight(block["section"]),
                "is_excluded_section": block["is_excluded_section"],
                "has_citation": block.get("has_citation", False),
                 "citations": block.get("citations", []),

            })

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

def extract_core(sent):
    root = None
    has_subject = False
    has_modal = False

    for tok in sent:
        if tok.dep_ == "ROOT":
            root = tok
        if tok.dep_ in {"nsubj", "nsubjpass", "expl", "csubj", "csubjpass"}:
            has_subject = True
        if tok.tag_ == "MD":
            has_modal = True

    return root, has_subject, has_modal

def is_narrative(sent, root):

    if root is None:
        return False

    # past tense main verb
    is_past = root.tag_ in {"VBD", "VBN"}

    # temporal modifiers
    has_temporal = any(
        tok.dep_ in {"npadvmod", "advmod", "prep"}
        and tok.lemma_ in {"after", "before", "during", "for", "since"}
        for tok in sent
    )

    # no clausal reasoning
    has_clause = any(tok.dep_ in {"ccomp", "xcomp"} for tok in sent)

    return is_past and not has_clause and has_temporal

def is_inferential(sent):

    root = None
    for tok in sent:
        if tok.dep_ == "ROOT":
            root = tok
            break

    if root is None:
        return False

    # clausal inference
    if any(tok.dep_ in {"ccomp", "xcomp"} for tok in sent):
        return True

    # modal uncertainty
    if any(tok.tag_ == "MD" for tok in sent):
        return True

    return False

def is_authorial(sent):

    for tok in sent:
        if tok.dep_ in {"nsubj", "nsubjpass"}:
            subj = " ".join([t.text.lower() for t in tok.subtree])

            if subj in {"we", "this study", "this paper", "our work"}:
                return True

    return False

def E_mode(sent):

    # metadata / headers
    if sent._.is_metadata or sent._.is_header:
        return "E0", None

    root, has_subject, has_modal = extract_core(sent)

    if root is None or not has_subject:
        return "E0", None

    # -----------------------------
    # NARRATIVE (NEW)
    # -----------------------------
    if is_narrative(sent, root):
        return "E4", "narrative"

    # -----------------------------
    # AUTHORIAL
    # -----------------------------
    if is_authorial(sent):
        return "E1", "authorial"

    # -----------------------------
    # INFERENTIAL
    # -----------------------------
    if is_inferential(sent):
        return "E3", "inferential"

    # -----------------------------
    # DESCRIPTIVE
    # -----------------------------
    return "E2", "descriptive"

def assign_epistemic_mode(sentences: List[Dict]) -> None:
    for s in sentences:
        mode, subtype = E_mode(s["sentence_span"])
        s["epistemic_mode"] = mode
        s["epistemic_subtype"] = subtype

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

    for s in sentences:
        txt = s["sentence"].strip()
        t_low = txt.lower()

        s["math_score"] = math_density(txt)

        # -------------------------
        # HARD EXCLUSIONS (STRUCTURAL ONLY)
        # -------------------------

        # empty / trivial
        if not txt or len(txt) < 3:
            s["excluded"], s["exclusion_reason"] = True, "EMPTY"
            continue

        # excluded sections (references, appendix)
        if s["is_excluded_section"]:
            s["excluded"], s["exclusion_reason"] = True, "SECTION"
            continue

        # pure symbols / equations
        if re.fullmatch(r"[^\w]+", txt):
            s["excluded"], s["exclusion_reason"] = True, "SYMBOL_ONLY"
            continue

        # math-only fragments
        if s["math_score"] > 0.6 and len(txt.split()) < 8:
            s["excluded"], s["exclusion_reason"] = True, "MATH_FRAGMENT"
            continue

        # reference-only lines
        if re.fullmatch(r"(\[\d+\]\s*)+", txt):
            s["excluded"], s["exclusion_reason"] = True, "REFERENCE_ONLY"
            continue

        # caption-like
        if s["block_type"] in {"figure", "table"}:
            s["excluded"], s["exclusion_reason"] = True, "CAPTION"
            continue

        if re.match(r"^(fig|figure|table)\b", t_low):
            s["excluded"], s["exclusion_reason"] = True, "CAPTION_LINE"
            continue

        # connector fragments (no semantic independence)
        if t_low in {
            "where", "thus", "therefore", "hence", "which", "that"
        }:
            s["excluded"], s["exclusion_reason"] = True, "CONNECTOR"
            continue

        # incomplete trailing fragments
        if txt.endswith(("which", "that", "where", "and", "or")):
            s["excluded"], s["exclusion_reason"] = True, "INCOMPLETE"
            continue

        # very short weak fragments
        if len(txt.split()) < 4 and s["math_score"] < 0.2:
            s["excluded"], s["exclusion_reason"] = True, "TOO_SHORT"
            continue

        # -------------------------
        # EVERYTHING ELSE → KEEP
        # -------------------------
        s["excluded"], s["exclusion_reason"] = False, "VALID"
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


def is_background_citation(text):
    t = text.lower()
    return (
        "in the literature" in t
        or "various studies" in t
        or "a number of works" in t
        or "have been studied" in t
        or "have been proposed" in t
    )


def anchoring(sentences: List[Dict]) -> None:

    CLAIM_VERBS = {
        "show", "demonstrate", "suggest", "indicate",
        "reveal", "confirm", "find", "observe"
    }

    EVIDENCE_NOUNS = {
        "result", "results", "data", "evidence",
        "analysis", "measurement", "observation"
    }

    def has_valid_proposition(sent):
        root = None
        has_subject = False

        for tok in sent:
            if tok.dep_ == "ROOT":
                root = tok
            if tok.dep_ in {"nsubj", "nsubjpass"}:
                has_subject = True

        if root is None:
            return False

        if root.pos_ not in {"VERB", "AUX"}:
            return False

        return has_subject

    def is_claim_structure(sent):
        for tok in sent:
            if tok.lemma_.lower() in CLAIM_VERBS:
                return True
        return False

    def is_evidence_subject(sent):
        for tok in sent:
            if tok.dep_ in {"nsubj", "nsubjpass"}:
                if tok.lemma_.lower() in EVIDENCE_NOUNS:
                    return True
        return False

    def has_citation_evidence(s, sent):
        if not s.get("has_citation"):
            return False

        # citation must attach to clause, not float
        for tok in sent:
            if tok.dep_ in {"obl", "nmod"}:
                if tok.text.startswith("["):
                    return True

        # fallback: allow if claim structure exists
        return is_claim_structure(sent)

    def is_quantitative_evidence(sent):
        has_number = False
        has_relation = False

        for tok in sent:
            if tok.like_num:
                has_number = True
            if tok.dep_ == "ROOT" and tok.lemma_ in {"be", "increase", "decrease"}:
                has_relation = True

        return has_number and has_relation

    def is_method_anchor(sent):
        for tok in sent:
            if tok.dep_ == "ROOT" and tok.lemma_ in {"use", "employ", "implement"}:
                return True
        return False

    def is_model_anchor(sent):
        for tok in sent:
            if tok.lemma_ in {"assume", "model"}:
                return True
        return False

    def is_limitation(sent):
        for tok in sent:
            if tok.lemma_ in {"however", "limit", "restrict"}:
                return True
        return False

    for s in sentences:

        if s.get("excluded"):
            s["anchors"] = []
            s["has_anchor"] = False
            continue

        sent = s["sentence_span"]
        anchors = []

        # -------------------------
        # GATE 1: must be a valid proposition
        # -------------------------
        if not has_valid_proposition(sent):
            s["anchors"] = []
            s["has_anchor"] = False
            continue

        # -------------------------
        # A6: LIMITATION (highest priority)
        # -------------------------
        if is_limitation(sent):
            anchors = [A6_LIMITATION]

        # -------------------------
        # A2: CITATION SUPPORT (semantic)
        # -------------------------
        elif has_citation_evidence(s, sent) and (
            is_claim_structure(sent) or is_evidence_subject(sent)
        ):
            anchors = ["A2_SUPPORT"]

        # -------------------------
        # A3: QUANTITATIVE (structured, not raw numbers)
        # -------------------------
        elif is_quantitative_evidence(sent):
            anchors = [A3_QUANTITATIVE]

        # -------------------------
        # A4: METHOD
        # -------------------------
        elif is_method_anchor(sent):
            anchors = [A4_METHOD]

        # -------------------------
        # A5: MODEL / ASSUMPTION
        # -------------------------
        elif is_model_anchor(sent):
            anchors = [A5_MODEL]

        else:
            anchors = []

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
    "behavior", "trend", "response", "variation"
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

def is_strong_inference(sent, raw_text):
    t_low = raw_text.lower()

    return (
        detect_anaphoric_inference(sent)
        or detect_prepositional_evidence(sent)
        or any(w in t_low for w in {"thus", "therefore", "hence", "consequently"})
    )


def is_weak_inference(sent):
    for tok in sent:
        if tok.dep_ == "ROOT" and tok.lemma_ in {
            "increase", "decrease", "lead", "result", "affect", "depend"
        }:
            return True

    if len(sent) > 12:
        return True

    return False

MAX_ANCHORS_TRACKED = 4
MAX_ANCHOR_DISTANCE = 4

def link_anchor_claim(sentences):

    recent_anchors = []  # (sentence_id, sentence_span)

    for i, s in enumerate(sentences):

        sid = s["sentence_id"]
        sent = s["sentence_span"]
        raw_text = s["sentence"]
        t_low = raw_text.lower()

        # -------------------------
        # RESET on limitation
        # -------------------------
        if A6_LIMITATION in s.get("anchors", []):
            recent_anchors = []

        # -------------------------
        # REGISTER anchor (no self-linking)
        # -------------------------
        if s.get("has_anchor"):
            recent_anchors.append((sid, sent))
            recent_anchors = recent_anchors[-MAX_ANCHORS_TRACKED:]
            s["linked_anchor"] = None
            continue

        # -------------------------
        # PRUNE anchors by distance
        # -------------------------
        recent_anchors = [
            (aid, a_sent)
            for (aid, a_sent) in recent_anchors
            if (sid - aid) <= MAX_ANCHOR_DISTANCE
        ]

        if not recent_anchors:
            s["linked_anchor"] = None
            continue

        # -------------------------
        # INFERENCE CHECK
        # -------------------------
        strong = is_strong_inference(sent, raw_text)
        weak = is_weak_inference(sent)

        if not strong and not weak:
            s["linked_anchor"] = None
            continue

        # -------------------------
        # ANAPHORIC SHORTCUT (high precision)
        # -------------------------
        if detect_anaphoric_inference(sent):
            s["linked_anchor"] = recent_anchors[-1][0]
            continue

        # -------------------------
        # DISCOURSE SHORTCUT
        # -------------------------
        if t_low.startswith(("thus", "therefore", "hence", "consequently")):
            s["linked_anchor"] = recent_anchors[-1][0]
            continue

        # -------------------------
        # SEMANTIC MATCHING (IMPROVED)
        # -------------------------
        current_lemmas = {
            tok.lemma_.lower()
            for tok in sent
            if tok.is_alpha and not tok.is_stop
        }

        best_anchor = None
        best_score = 0

        for aid, a_sent in recent_anchors:

            anchor_lemmas = {
                tok.lemma_.lower()
                for tok in a_sent
                if tok.is_alpha and not tok.is_stop
            }

            # base overlap
            overlap = len(current_lemmas & anchor_lemmas)

            # weighted overlap (important syntactic roles)
            important_overlap = sum(
                1 for tok in sent
                if tok.dep_ in {"nsubj", "dobj"} and tok.lemma_.lower() in anchor_lemmas
            )

            score = overlap + 2 * important_overlap

            if score > best_score:
                best_score = score
                best_anchor = aid

        # -------------------------
        # DECISION LOGIC
        # -------------------------

        if strong:
         if best_score >= 2:
            s["linked_anchor"] = best_anchor
         elif detect_anaphoric_inference(sent) or raw_text.lower().startswith(("thus", "therefore", "hence")):
        # only allow fallback for strong discourse signals
            s["linked_anchor"] = recent_anchors[-1][0]
         else:
            s["linked_anchor"] = None

        else:
            # weak inference → require minimal semantic signal
            if best_score >= 2:
                s["linked_anchor"] = best_anchor
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


def debug_summary(sections, blocks, sentences):
    print("\n===== PIPELINE DIAGNOSTICS =====")

    print(f"\nSections: {len(sections)}")
    print(f"Blocks: {len(blocks)}")
    print(f"Sentences: {len(sentences)}")

    excluded = sum(1 for s in sentences if s.get("excluded"))
    print(f"Excluded sentences: {excluded} ({excluded/len(sentences):.2%})")

    with_citation = sum(1 for s in sentences if s.get("has_citation"))
    print(f"Sentences with citation: {with_citation}")

    anchors = sum(1 for s in sentences if s.get("has_anchor"))
    print(f"Anchored sentences: {anchors}")

    linked = sum(1 for s in sentences if s.get("linked_anchor") is not None)
    print(f"Linked sentences: {linked}")

    print("\nTop sections:")
    section_counts = {}
    for s in sentences:
        sec = s["section"]
        section_counts[sec] = section_counts.get(sec, 0) + 1

    for k, v in sorted(section_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"{k[:50]} → {v}")


import json

def dump_sentences(sentences, path="debug_sentences.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for s in sentences:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

# =========================
# PIPELINE
# =========================

def preprocess(xml_path: str) -> Dict[str, Any]:

    sections = parse_tei(xml_path)
    blocks = build_blocks_from_tei(sections)

    sentences = segment_sentences(blocks)

    apply_structure_markers(sentences)
    assign_epistemic_mode(sentences)
    assign_modality(sentences)
    exclusion(sentences)
    anchoring(sentences)

    link_anchor_claim(sentences)
    finalize_sentences(sentences)

    dump_sentences(sentences)
    return {
        "sentences": sentences,
    }




