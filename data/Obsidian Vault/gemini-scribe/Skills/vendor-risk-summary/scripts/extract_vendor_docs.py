#!/usr/bin/env python3
"""
extract_vendor_docs.py

Locates a vendor's Obsidian note + compliance PDFs and extracts raw text
from all of them into one combined dump. Does NOT summarize or interpret
anything -- that part is left to the calling Claude instance, per
SKILL.md, so summarization always works from real extracted text rather
than the script guessing at structure.

Usage:
    python3 extract_vendor_docs.py "/path/to/Obsidian Vault/vendor1"
    python3 extract_vendor_docs.py "/path/to/Obsidian Vault/vendor1/vendor1.md"

Looks for, in the same folder as the vendor note (or its attachments/
subfolder):
    - the vendor markdown note itself (e.g. vendor1.md)
    - a Master Services Agreement PDF
    - a Data Processing Addendum PDF
    - a PCI-DSS PDF
    - a SOC2 PDF
Filename matching is fuzzy (case-insensitive substring match) since
naming conventions vary across vendor folders.

Output: writes <vendor>_extracted.txt next to the vendor note, and also
prints it to stdout. Each section is clearly delimited and tagged with
its source filename so citations stay traceable.
"""

import sys
import re
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber --break-system-packages",
          file=sys.stderr)
    sys.exit(1)

# Fuzzy filename patterns -> canonical doc type label
DOC_PATTERNS = {
    "Master Services Agreement": [r"master.?services.?agreement", r"\bmsa\b"],
    "Data Processing Addendum":   [r"data.?processing.?addendum", r"\bdpa\b"],
    "PCI-DSS Attestation":        [r"pci.?dss", r"\bpci\b"],
    "SOC2 Report":                [r"soc.?2", r"soc2"],
}


def find_vendor_folder(path_arg: str) -> Path:
    p = Path(path_arg).expanduser()
    if p.is_file():
        return p.parent
    if p.is_dir():
        return p
    raise FileNotFoundError(f"Path not found: {p}")


def find_vendor_note(folder: Path) -> Path | None:
    # Prefer a .md file matching the folder name, else any single .md in the folder
    candidates = list(folder.glob("*.md"))
    if not candidates:
        return None
    folder_name = folder.name.lower()
    for c in candidates:
        if c.stem.lower() == folder_name:
            return c
    return candidates[0]


def find_pdfs(folder: Path) -> dict[str, Path]:
    search_dirs = [folder]
    attach = folder / "attachments"
    if attach.is_dir():
        search_dirs.append(attach)

    found = {}
    for d in search_dirs:
        for pdf in d.glob("*.pdf"):
            name_lower = pdf.name.lower()
            for doc_type, patterns in DOC_PATTERNS.items():
                if doc_type in found:
                    continue
                if any(re.search(pat, name_lower) for pat in patterns):
                    found[doc_type] = pdf
    return found


def extract_pdf_text(pdf_path: Path) -> str:
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            text_parts.append(f"--- page {i} ---\n{page_text}")
    return "\n".join(text_parts)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 extract_vendor_docs.py <vendor_path>", file=sys.stderr)
        sys.exit(1)

    folder = find_vendor_folder(sys.argv[1])
    vendor_name = folder.name

    note_path = find_vendor_note(folder)
    pdfs = find_pdfs(folder)

    missing = [d for d in DOC_PATTERNS if d not in pdfs]

    out = []
    out.append(f"VENDOR FOLDER: {folder}")
    out.append(f"VENDOR NAME (from folder): {vendor_name}")
    out.append(f"DOCUMENTS FOUND: {', '.join(pdfs.keys()) if pdfs else 'none'}")
    out.append(f"DOCUMENTS MISSING: {', '.join(missing) if missing else 'none'}")
    out.append("")

    if note_path:
        out.append(f"===== VENDOR NOTE: {note_path.name} =====")
        out.append(note_path.read_text(errors="replace"))
        out.append("")
    else:
        out.append("===== VENDOR NOTE: NOT FOUND =====\n")

    for doc_type, pdf_path in pdfs.items():
        out.append(f"===== {doc_type.upper()}: {pdf_path.name} =====")
        try:
            out.append(extract_pdf_text(pdf_path))
        except Exception as e:
            out.append(f"[ERROR extracting text: {e}]")
        out.append("")

    for doc_type in missing:
        out.append(f"===== {doc_type.upper()}: NOT FOUND IN VENDOR FOLDER =====\n")

    combined = "\n".join(out)
    out_path = folder / f"{vendor_name}_extracted.txt"
    out_path.write_text(combined)

    print(combined)
    print(f"\n\n[Saved combined extraction to: {out_path}]", file=sys.stderr)


if __name__ == "__main__":
    main()
