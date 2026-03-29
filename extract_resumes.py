#!/usr/bin/env python3
"""
extract_resumes.py
──────────────────
Batch resume text extractor for the resume analysis pipeline.

Reads all PDF and DOCX files from a given folder and outputs
extracted plain-text to a JSON file, ready for analysis.

Usage:
    python extract_resumes.py --folder /path/to/resumes --output extracted.json

Requirements:
    pip install pdfplumber python-docx
"""

import argparse
import json
import pathlib
import sys


def extract_pdf(path: pathlib.Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        sys.exit("pdfplumber not installed. Run: pip install pdfplumber")

    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text.strip()


def extract_docx(path: pathlib.Path) -> str:
    try:
        import docx
    except ImportError:
        sys.exit("python-docx not installed. Run: pip install python-docx")

    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs).strip()


def extract_all(folder: pathlib.Path) -> dict[str, dict]:
    """Extract text from all PDF and DOCX files in a folder."""
    results = {}
    supported = {".pdf": extract_pdf, ".docx": extract_docx}

    for f in sorted(folder.iterdir()):
        if f.suffix.lower() in supported and not f.name.startswith("_"):
            print(f"  Extracting: {f.name}")
            text = supported[f.suffix.lower()](f)
            results[f.stem] = {
                "filename": f.name,
                "extension": f.suffix.lower(),
                "char_count": len(text),
                "text": text,
            }
            print(f"    → {len(text):,} characters extracted")

    return results


def main():
    parser = argparse.ArgumentParser(description="Extract text from resume PDF/DOCX files.")
    parser.add_argument("--folder", required=True, help="Folder containing resume files")
    parser.add_argument("--output", default="extracted_resumes.json", help="Output JSON file path")
    args = parser.parse_args()

    folder = pathlib.Path(args.folder)
    if not folder.is_dir():
        sys.exit(f"Folder not found: {folder}")

    print(f"\nScanning: {folder}")
    print("─" * 50)
    results = extract_all(folder)

    output = pathlib.Path(args.output)
    output.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print("─" * 50)
    print(f"\n✓ Extracted {len(results)} resume(s) → {output}")
    for name, data in results.items():
        print(f"  • {name:40s} {data['char_count']:>7,} chars")


if __name__ == "__main__":
    main()
