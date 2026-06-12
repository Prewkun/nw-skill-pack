"""
Delta SD3 Smart Screwdriving System Manual → KB Extractor
Parses Modbus and TCP/IP function codes from PDF into structured JSON records.

Usage:
    python scripts/extract_delta_kb.py
    python scripts/extract_delta_kb.py --pdf path/to/manual.pdf
"""

import re
import json
import argparse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT   = _SCRIPTS_DIR.parent

DEFAULT_PDF = _REPO_ROOT / "DELTA_IA-DCSS_SD3_UM_EN_20240306.pdf"
OUT_JSON    = _REPO_ROOT / "KB" / "json"

# Page ranges (0-indexed, end exclusive)
MODBUS_PAGES = (181, 355)
TCPIP_PAGES  = (355, 538)

CATEGORY_MAP = [
    ((10,   99),  "Operational"),   # TCP/IP only
    ((100, 199),  "Parameters"),
    ((200, 299),  "Sequence"),
    ((300, 399),  "Sources"),
    ((400, 499),  "Results"),
    ((500, 599),  "Controller"),
    ((600, 699),  "Tool"),
    ((700, 799),  "Reports"),
]

def get_category(code: int) -> str:
    for (lo, hi), cat in CATEGORY_MAP:
        if lo <= code <= hi:
            return cat
    return "Other"


# ── PDF extraction ────────────────────────────────────────────────────────────

def extract_pages(pdf_path: Path, start: int, end: int) -> str:
    try:
        import PyPDF2
    except ImportError:
        raise SystemExit("PyPDF2 not installed. Run: pip install pypdf2 pycryptodome")

    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        parts = []
        end = min(end, len(reader.pages))
        for i in range(start, end):
            raw = reader.pages[i].extract_text() or ""
            # strip running header/footer
            raw = re.sub(r"(Modbus|TCP/IP) Communication - Function Codes\s+SD3 Series\s*", "", raw)
            raw = re.sub(r"SD3 Series\s+(Modbus|TCP/IP) Communication - Function Codes\s*", "", raw)
            # strip page number stamps like "A-40 A" or "B-12 B"
            raw = re.sub(r"[AB]-\d+\s+[AB]\b", "", raw)
            parts.append(raw)
    return "\n".join(parts)


# ── Block splitter ────────────────────────────────────────────────────────────
# Real function code header: line that starts with optional spaces then #NNN + title
# TOC entries look like: #302 Write...  ·····  A-40  → filter these out
FC_HEADER = re.compile(r"(?m)^\s*(#(\d+)\s+([^·\n]+?))\s*$")

def split_function_blocks(text: str) -> list[tuple[int, str, str]]:
    """Return list of (code, title, block_text), skipping TOC stubs."""
    matches = list(FC_HEADER.finditer(text))
    blocks = []
    for idx, m in enumerate(matches):
        title_raw = m.group(3).strip()
        # skip TOC entries: they have page-ref patterns like "A-40" or "B-5" at end
        if re.search(r"\b[AB]-\d+\s*$", title_raw):
            continue
        # skip TOC entries that are pure dot leaders
        if "·" in title_raw:
            continue
        code  = int(m.group(2))
        title = re.sub(r"\s+", " ", title_raw).strip()
        start = m.start()
        end_  = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body  = text[start:end_]
        # a real content block must have "Content description" or "Handshake signal"
        if "Content description" not in body and "Handshake signal" not in body:
            continue
        blocks.append((code, title, body))
    return blocks


# ── Description & notes ───────────────────────────────────────────────────────

def extract_description(body: str) -> str:
    m = re.search(r"Content description:\s*\n(.*?)(?=Handshake signal description:|$)", body, re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return ""

def extract_notes(body: str) -> str:
    m = re.search(r"Note[s]?:(.*?)(?=\n#|\Z)", body, re.DOTALL | re.IGNORECASE)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return ""


# ── Modbus table parser ───────────────────────────────────────────────────────
# Row format: "C8 Function code  302"  or  "CA Tool 1 / Tool 2  0: Tool 1; 1: Tool 2"
# Use [^\S\n] (space/tab but NOT newline) as column separator to avoid cross-line bleeding
MODBUS_ROW = re.compile(
    r"^([0-9A-Fa-f]{1,4}(?:[^\S\n]*(?:to|,|-)[^\S\n]*[0-9A-Fa-f]{1,4})?)"  # register / range
    r"[^\S\n]+"                                                                # 1+ non-newline space
    r"([A-Za-z][^\n]+?)(?:[^\S\n]{2,}([^\n]+))?$",                            # field  [desc]
    re.MULTILINE,
)

def parse_modbus_table(text: str) -> list[dict]:
    rows = []
    skip = {"Write", "Write / Read request", "Return status", "Description",
            "Modbus (Hex)", "Read", "Write  Read request"}
    for m in MODBUS_ROW.finditer(text):
        reg   = m.group(1).strip()
        field = m.group(2).strip()
        desc  = (m.group(3) or "").strip()
        if field in skip or len(field) < 2:
            continue
        if re.fullmatch(r"[0-9A-Fa-f\s\-,]+", field):
            continue
        # skip wrapped-cell continuation lines like "to 999999" or "1 to 999999"
        if re.match(r"^(to\s|\d)", field):
            continue
        rows.append({"register": reg, "field": field, "description": desc})
    return rows


# ── TCP/IP table parser ───────────────────────────────────────────────────────
# Row format: "1 - 2 Function code  110  6E00"
TCPIP_ROW = re.compile(
    r"^(\d+[^\S\n]*-[^\S\n]*\d+|\d+)"     # byte range or single
    r"[^\S\n]+"                             # 1+ non-newline spaces (PDF uses single space after range)
    r"([A-Za-z][^\n]+?)(?:[^\S\n]{2,}([^\n]+?))?(?:[^\S\n]{2,}([0-9A-Fa-f]{4}))?$",
    re.MULTILINE,
)

def parse_tcpip_table(text: str) -> list[dict]:
    rows = []
    skip = {"Write / Read request", "Return status", "Description", "Example"}
    for m in TCPIP_ROW.finditer(text):
        byte_range = m.group(1).strip()
        field      = m.group(2).strip()
        desc       = (m.group(3) or "").strip()
        example    = (m.group(4) or "").strip()
        if field in skip or len(field) < 2:
            continue
        rows.append({"bytes": byte_range, "field": field,
                     "description": desc, "example_hex": example})
    return rows


# ── Error code parser ─────────────────────────────────────────────────────────
# Row format: "1 Switching method error  Must be manual setting"
# Code is decimal, single space after code, then field, then 2+ spaces, then detail
ERROR_ROW = re.compile(
    r"^(\d+)[^\S\n]+([A-Za-z][^\n]+?)(?:[^\S\n]{2,}([^\n]+))?$",
    re.MULTILINE,
)

def parse_error_codes(text: str) -> dict[str, str]:
    errors = {}
    for m in ERROR_ROW.finditer(text):
        code   = m.group(1)
        desc   = re.sub(r"\s{2,}", " ", m.group(2)).strip()  # collapse double-spaces from wrapped cells
        detail = re.sub(r"\s{2,}", " ", (m.group(3) or "")).strip()
        # skip header row
        if desc.lower() in ("error description", "description", "code"):
            continue
        errors[code] = f"{desc} — {detail}" if detail else desc
    return errors

def extract_error_codes(body: str) -> dict[str, str]:
    m = re.search(r"error codes are as follows:(.*?)(?=Completed|OK\s*\n|NOK|\n#\d|\Z)", body, re.DOTALL | re.IGNORECASE)
    return parse_error_codes(m.group(1)) if m else {}


# ── Section splitter helpers ──────────────────────────────────────────────────

def get_request_section(body: str) -> str:
    """Text between the first step marker and 'Check whether' / step-2 marker."""
    # Modbus: "Modbus (Hex)  Write / Read request  Write" table up to step 2
    m = re.search(
        r"Modbus \(Hex\)\s+Write / Read request\s+Write(.*?)"
        r"(?=\d+\.\s+Check whether|\d+\.\s+Check if|Return status|$)",
        body, re.DOTALL | re.IGNORECASE
    )
    if m:
        return m.group(1)
    # TCP/IP: "Byte  Write / Read request  Description" table
    m = re.search(
        r"Byte\s+Write / Read request\s+Description(.*?)"
        r"(?=\d+\.\s+Check whether|\d+\.\s+Check if|Return status|$)",
        body, re.DOTALL | re.IGNORECASE
    )
    return m.group(1) if m else ""

def get_return_section(body: str) -> str:
    """Text of the 'Return status' table, stopping before error codes."""
    # Modbus
    m = re.search(
        r"Modbus \(Hex\)\s+Return status\s+Description(.*?)"
        r"(?=error codes are|If failed|Completed|OK\s*\nNOK|$)",
        body, re.DOTALL | re.IGNORECASE
    )
    if m:
        return m.group(1)
    # TCP/IP
    m = re.search(
        r"Byte\s+Return status\s+Description(.*?)"
        r"(?=error codes are|If failed|Completed|OK\s*\nNOK|$)",
        body, re.DOTALL | re.IGNORECASE
    )
    return m.group(1) if m else ""


# ── Record builders ───────────────────────────────────────────────────────────

def build_modbus_record(code: int, title: str, body: str) -> dict:
    return {
        "code":           code,
        "title":          title,
        "protocol":       "Modbus",
        "category":       get_category(code),
        "description":    extract_description(body),
        "request_fields": parse_modbus_table(get_request_section(body)),
        "return_fields":  parse_modbus_table(get_return_section(body)),
        "error_codes":    extract_error_codes(body),
        "notes":          extract_notes(body),
    }

def build_tcpip_record(code: int, title: str, body: str) -> dict:
    return {
        "code":           code,
        "title":          title,
        "protocol":       "TCPIP",
        "category":       get_category(code),
        "description":    extract_description(body),
        "request_fields": parse_tcpip_table(get_request_section(body)),
        "return_fields":  parse_tcpip_table(get_return_section(body)),
        "error_codes":    extract_error_codes(body),
        "notes":          extract_notes(body),
    }


# ── Dedup: keep record with most content ─────────────────────────────────────

def score(rec: dict) -> int:
    return (len(rec["description"]) + len(rec["request_fields"]) * 10
            + len(rec["return_fields"]) * 10 + len(rec["error_codes"]) * 5)

def dedup(blocks: list[tuple[int, str, str]], builder) -> list[dict]:
    best: dict[int, dict] = {}
    for code, title, body in blocks:
        rec = builder(code, title, body)
        if code not in best or score(rec) > score(best[code]):
            best[code] = rec
    return list(best.values())


# ── Safe filename ─────────────────────────────────────────────────────────────

def safe_name(title: str, maxlen: int = 45) -> str:
    s = re.sub(r"[^A-Za-z0-9 ]", "", title)
    s = re.sub(r"\s+", "_", s.strip())
    return s[:maxlen]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default=str(DEFAULT_PDF))
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    print(f"Reading PDF: {pdf_path.name}")

    all_records: list[dict] = []

    # ── Modbus ────────────────────────────────────────────────────────────────
    print("Extracting Modbus pages...")
    modbus_text   = extract_pages(pdf_path, *MODBUS_PAGES)
    modbus_blocks = split_function_blocks(modbus_text)
    modbus_recs   = dedup(modbus_blocks, build_modbus_record)
    print(f"  Raw blocks: {len(modbus_blocks)}  →  unique records: {len(modbus_recs)}")

    modbus_dir = OUT_JSON / "Modbus"
    modbus_dir.mkdir(parents=True, exist_ok=True)
    for rec in modbus_recs:
        fname = f"FC{rec['code']:04d}_{safe_name(rec['title'])}.json"
        (modbus_dir / fname).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    all_records.extend(modbus_recs)

    # ── TCP/IP ────────────────────────────────────────────────────────────────
    print("Extracting TCP/IP pages...")
    tcpip_text   = extract_pages(pdf_path, *TCPIP_PAGES)
    tcpip_blocks = split_function_blocks(tcpip_text)
    tcpip_recs   = dedup(tcpip_blocks, build_tcpip_record)
    print(f"  Raw blocks: {len(tcpip_blocks)}  →  unique records: {len(tcpip_recs)}")

    tcpip_dir = OUT_JSON / "TCPIP"
    tcpip_dir.mkdir(parents=True, exist_ok=True)
    for rec in tcpip_recs:
        fname = f"FC{rec['code']:04d}_{safe_name(rec['title'])}.json"
        (tcpip_dir / fname).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    all_records.extend(tcpip_recs)

    # ── Index ─────────────────────────────────────────────────────────────────
    index = [{"code": r["code"], "title": r["title"],
              "protocol": r["protocol"], "category": r["category"]}
             for r in all_records]
    index_path = OUT_JSON.parent / "delta_kb_index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDone!")
    print(f"  Modbus  : {len(modbus_recs)} records")
    print(f"  TCP/IP  : {len(tcpip_recs)} records")
    print(f"  Total   : {len(all_records)}")
    print(f"  Index   : {index_path}")


if __name__ == "__main__":
    main()
