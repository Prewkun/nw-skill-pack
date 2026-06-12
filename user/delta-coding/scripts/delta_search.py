"""
Delta SD3 KB Search — BM25 (no extra dependencies required)

Usage:
    python scripts/delta_search.py "switch parameter manual"
    python scripts/delta_search.py "read tightening result" -n 5
    python scripts/delta_search.py "clear errors" --protocol Modbus
    python scripts/delta_search.py "subscription status" --protocol TCPIP
    python scripts/delta_search.py "502" --code          # lookup by function code number
"""

import re
import json
import math
import argparse
from pathlib import Path
from collections import Counter

# ── Config ────────────────────────────────────────────────────────────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT   = _SCRIPTS_DIR.parent
KB_DIR       = _REPO_ROOT / "KB" / "json"


# ── Load KB ───────────────────────────────────────────────────────────────────

def load_records(protocol: str | None = None) -> list[dict]:
    """Load all JSON records from KB, optionally filtered by protocol."""
    records = []
    dirs = []
    if protocol in (None, "Modbus", "both"):
        dirs.append(KB_DIR / "Modbus")
    if protocol in (None, "TCPIP", "both"):
        dirs.append(KB_DIR / "TCPIP")

    for d in dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                records.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
    return records


# ── Text representation for BM25 ─────────────────────────────────────────────

def record_to_text(rec: dict) -> str:
    """Flatten a record into searchable text, with field repetition for weighting."""
    parts = [
        rec.get("title", ""),       # high weight: repeat 3x
        rec.get("title", ""),
        rec.get("title", ""),
        rec.get("category", ""),
        rec.get("protocol", ""),
        rec.get("description", ""),
        rec.get("notes", ""),
        f"code {rec.get('code', '')} #{rec.get('code', '')}",
    ]
    for f in rec.get("request_fields", []):
        parts.append(f.get("field", ""))
        parts.append(f.get("description", ""))
    for f in rec.get("return_fields", []):
        parts.append(f.get("field", ""))
        parts.append(f.get("description", ""))
    for code, desc in rec.get("error_codes", {}).items():
        parts.append(desc)
    return " ".join(parts)


# ── Tokenizer ─────────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9/\-_]", " ", text)
    return [t for t in text.split() if len(t) > 1]


# ── BM25 ──────────────────────────────────────────────────────────────────────

class BM25:
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b  = b
        self.tokenized = [tokenize(doc) for doc in corpus]
        self.N  = len(corpus)
        self.avgdl = sum(len(d) for d in self.tokenized) / max(self.N, 1)
        self.df: dict[str, int] = {}
        for doc in self.tokenized:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

    def score(self, doc_tokens: list[str], query_tokens: list[str]) -> float:
        tf = Counter(doc_tokens)
        dl = len(doc_tokens)
        s  = 0.0
        for term in query_tokens:
            if term not in self.df:
                continue
            f   = tf.get(term, 0)
            idf = math.log((self.N - self.df[term] + 0.5) / (self.df[term] + 0.5) + 1)
            num = f * (self.k1 + 1)
            den = f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            s  += idf * num / den
        return s

    def search(self, query: str, top_n: int = 10) -> list[tuple[int, float]]:
        q_tokens = tokenize(query)
        scores = [(i, self.score(doc, q_tokens)) for i, doc in enumerate(self.tokenized)]
        scores.sort(key=lambda x: -x[1])
        return [(i, s) for i, s in scores[:top_n] if s > 0]


# ── Formatter ─────────────────────────────────────────────────────────────────

def format_record(rec: dict, score: float, verbose: bool = False) -> str:
    lines = [
        f"{'─'*70}",
        f"  #{rec['code']}  {rec['title']}",
        f"  [{rec['protocol']} · {rec['category']}]   score={score:.2f}",
    ]
    if rec.get("description"):
        lines.append(f"\n  {rec['description']}")

    if verbose:
        if rec.get("request_fields"):
            lines.append("\n  Request registers / bytes:")
            for f in rec["request_fields"]:
                reg = f.get("register") or f.get("bytes", "")
                lines.append(f"    {reg:<14} {f['field']:<30} {f['description']}")

        if rec.get("return_fields"):
            lines.append("\n  Return registers / bytes:")
            for f in rec["return_fields"]:
                reg = f.get("register") or f.get("bytes", "")
                lines.append(f"    {reg:<14} {f['field']:<30} {f['description']}")

        if rec.get("error_codes"):
            lines.append("\n  Error codes:")
            for code, desc in rec["error_codes"].items():
                lines.append(f"    {code:<6} {desc}")

        if rec.get("notes"):
            lines.append(f"\n  Notes: {rec['notes']}")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Search the Delta SD3 KB")
    parser.add_argument("query",    help="Search keywords or function code number")
    parser.add_argument("-n",       type=int, default=8, help="Number of results (default: 8)")
    parser.add_argument("--protocol", choices=["Modbus", "TCPIP", "both"], default=None,
                        help="Filter by protocol (default: both)")
    parser.add_argument("--category", default=None,
                        help="Filter by category: Parameters / Sequence / Sources / Results / Controller / Tool / Reports / Operational")
    parser.add_argument("--code",   action="store_true",
                        help="Treat query as a function code number (exact lookup)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show full register/byte tables and error codes")
    args = parser.parse_args()

    records = load_records(args.protocol)
    if not records:
        print("No KB records found. Run extract_delta_kb.py first.")
        return

    # Filter by category
    if args.category:
        records = [r for r in records if r.get("category", "").lower() == args.category.lower()]

    # Exact code lookup
    if args.code:
        try:
            target = int(args.query)
        except ValueError:
            print("--code requires a numeric function code, e.g. --code 302")
            return
        hits = [r for r in records if r["code"] == target]
        if not hits:
            print(f"No records found for function code #{target}")
            return
        for r in hits:
            print(format_record(r, score=1.0, verbose=True))
        return

    # BM25 search
    corpus = [record_to_text(r) for r in records]
    bm25   = BM25(corpus)
    results = bm25.search(args.query, top_n=args.n)

    if not results:
        print(f"No results for: {args.query!r}")
        return

    print(f"\nSearch: {args.query!r}  →  {len(results)} result(s)\n")
    for idx, score in results:
        print(format_record(records[idx], score, verbose=args.verbose))
    print(f"\n{'─'*70}")
    print(f"Tip: add -v / --verbose to see full register tables and error codes")
    print(f"     add --protocol Modbus  or  --protocol TCPIP  to filter")


if __name__ == "__main__":
    main()
