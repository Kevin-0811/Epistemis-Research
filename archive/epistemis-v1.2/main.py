# main.py

from pathlib import Path
import requests
import json
import sys

# =========================
# IMPORTS
# =========================

from preprocessor_v2 import preprocess
from compiler import analyze_input

# =========================
# CONFIG
# =========================

GROBID_URL = "http://localhost:8070/api/processFulltextDocument"

TEMP_DIR = Path("temp")
OUTPUT_DIR = Path("outputs")

TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# =========================
# GROBID
# =========================

def process_pdf_with_grobid(pdf_path: str) -> Path:

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    print("[1/6] Sending PDF to GROBID...")

    with open(pdf_path, "rb") as pdf_file:

        files = {
            "input": (pdf_path.name, pdf_file, "application/pdf")
        }

        response = requests.post(
            GROBID_URL,
            files=files,
            data={
                "consolidateHeader": "1",
                "consolidateCitations": "1",
                "includeRawCitations": "1",
                "includeRawAffiliations": "1",
            },
            timeout=300
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"GROBID failed ({response.status_code}):\n{response.text}"
        )

    tei_path = TEMP_DIR / f"{pdf_path.stem}.tei.xml"

    with open(tei_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"[2/6] TEI generated → {tei_path}")

    return tei_path


# =========================
# SERIALIZATION
# =========================

def save_results(results, output_name):

    output_path = OUTPUT_DIR / f"{output_name}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"[6/6] Results saved → {output_path}")


# =========================
# PIPELINE
# =========================

def compile_document(pdf_path: str):

    pdf_path = Path(pdf_path)

    print("\n===== EPISTEMIS COMPILATION =====\n")

    # -------------------------
    # GROBID
    # -------------------------

    tei_path = process_pdf_with_grobid(pdf_path)

    # -------------------------
    # PREPROCESSING
    # -------------------------

    print("[3/6] Running preprocessing pipeline...")

    preprocess_output = preprocess(str(tei_path))

    sentences = preprocess_output["sentences"]

    print(f"       Sentences extracted: {len(sentences)}")

    # -------------------------
    # COMPILATION
    # -------------------------

    print("[4/6] Running semantic compiler...")

    results = analyze_input(sentences)

    print(f"       Diagnostics generated: {len(results)}")

    # -------------------------
    # FINAL ARTIFACT
    # -------------------------

    compilation_artifact = {
        "source_pdf": str(pdf_path),
        "tei_path": str(tei_path),
        "sentence_count": len(sentences),
        "results_count": len(results),
        "results": results
    }

    # -------------------------
    # SAVE
    # -------------------------

    print("[5/6] Serializing artifacts...")

    save_results(
        compilation_artifact,
        pdf_path.stem
    )

    print("\n===== COMPILATION COMPLETE =====\n")

    return compilation_artifact

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("python main.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    compile_document(pdf_path)