import subprocess
import time
import requests
import os
import signal
from lxml import etree

GROBID_IMAGE = "lfoppiano/grobid:0.9.0-crf"
PORT = "8070"

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


# ---------- GROBID CONTROL ----------

def start_grobid():
    print("[INFO] Starting GROBID...")
    proc = subprocess.Popen(
        ["docker", "run", "--rm", "-p", f"{PORT}:8070", GROBID_IMAGE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # wait until ready
    while True:
        try:
            r = requests.get(f"http://localhost:{PORT}/api/isalive")
            if r.status_code == 200:
                print("[INFO] GROBID is ready.")
                break
        except:
            pass
        time.sleep(1)

    return proc


def stop_grobid(proc):
    print("[INFO] Stopping GROBID...")
    proc.send_signal(signal.SIGINT)
    proc.wait()


# ---------- PROCESSING ----------

def pdf_to_tei(pdf_path):
    with open(pdf_path, "rb") as f:
        r = requests.post(
            f"http://localhost:{PORT}/api/processFulltextDocument",
            files={"input": f}
        )
    return r.text


def tei_to_text(xml_string):
    tree = etree.fromstring(xml_string.encode())

    paragraphs = tree.xpath("//tei:text//tei:body//tei:p", namespaces=NS)

    cleaned = []
    for p in paragraphs:
        # remove citation tags
        etree.strip_elements(p, "{http://www.tei-c.org/ns/1.0}ref", with_tail=False)

        text = "".join(p.itertext())
        text = " ".join(text.split())  # normalize whitespace

        if text:
            cleaned.append(text)

    return "\n\n".join(cleaned)


# ---------- MAIN LOOP ----------

def main():
    os.makedirs("tei", exist_ok=True)
    os.makedirs("txt", exist_ok=True)

    proc = start_grobid()

    try:
        while True:
            pdf_path = input("\nEnter PDF path (or 'q' to quit): ").strip()

            if pdf_path.lower() == "q":
                break

            if not os.path.exists(pdf_path):
                print("[ERROR] File not found.")
                continue

            base = os.path.splitext(os.path.basename(pdf_path))[0]

            print("[INFO] Processing:", pdf_path)

            # Step 1: PDF → TEI
            xml = pdf_to_tei(pdf_path)

            tei_path = f"tei/{base}.tei.xml"
            with open(tei_path, "w", encoding="utf-8") as f:
                f.write(xml)

            # Step 2: TEI → TXT
            text = tei_to_text(xml)

            txt_path = f"txt/{base}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"[DONE] Saved: {tei_path} and {txt_path}")

    finally:
        stop_grobid(proc)


if __name__ == "__main__":
    main()