# epson-coding — Setup Guide

This skill generates EPSON SPEL+ robot programs from natural language. It requires a local knowledge base (KB) extracted from the official EPSON manual and a pre-built search index.

---

## Directory layout

```
user/epson-coding/
├── SKILL.md                    ← Claude skill definition
├── SETUP.md                    ← This file
├── KB/
│   ├── json/
│   │   ├── Operator/           ← 421 operator command JSON records
│   │   └── Program/            ← 3687 program reference JSON records
│   ├── spel_kb_index.json      ← Lightweight index of all 4108 entries
│   ├── spel_operator_kb.md     ← Full operator reference (human readable)
│   └── spel_search_index.pkl   ← Pre-built BM25 search index
├── scripts/
│   ├── spel_search.py          ← BM25 search (no dependencies)
│   ├── spel_generate.py        ← Automated generation via Claude API
│   ├── extract_spel_kb.py      ← One-time: extract KB from EPSON HTML manual
│   └── kb_cleanup.py           ← Maintenance: clean KB and rebuild index
└── output/                     ← Generated .prg files saved here
```

---

## Step 1 — Clone and install the skill

```bash
git clone https://github.com/Prewkun/nw-skill-pack.git
```

Copy the skill into your Claude skills directory:

**Windows:**
```powershell
Copy-Item -Recurse nw-skill-pack\user\epson-coding "$env:USERPROFILE\.claude\skills\epson-coding"
```

**macOS / Linux:**
```bash
cp -r nw-skill-pack/user/epson-coding ~/.claude/skills/epson-coding
```

Restart Claude Code — `/epson-coding` will appear in the skill list.

---

## Step 2 — Verify the search index

A pre-built `KB/spel_search_index.pkl` is included. Test it:

```bash
cd ~/.claude/skills/epson-coding
python scripts/spel_search.py "pick and place jump" --context
```

You should see matching SPEL+ command references printed. If the index is missing, rebuild it:

```bash
python scripts/kb_cleanup.py
```

---

## Step 3 (optional) — Re-extract KB from source manual

The KB was extracted from the official **EPSON RC+ SPEL+ e-Manual**. The source HTML is not included (EPSON copyright). If you have your own copy:

1. Place it at `Manual/English/` inside the skill directory
2. Run:
   ```bash
   python scripts/extract_spel_kb.py
   python scripts/kb_cleanup.py
   ```

This produces `KB/json/`, `KB/spel_kb_index.json`, `KB/spel_operator_kb.md`, and rebuilds `KB/spel_search_index.pkl`.

---

## Step 4 (optional) — Automated generation via Claude API

`spel_generate.py` calls the Claude API directly from the command line:

```bash
python scripts/spel_generate.py "pick and place for 3 parts with vacuum gripper"
python scripts/spel_generate.py "palletizing 4x3 grid" --save output/pallet.prg
python scripts/spel_generate.py "conveyor tracking with vision" --dry-run
```

Requires `ANTHROPIC_API_KEY`. Add it to a `.env` file in the skill root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Or set it as an environment variable.

---

## KB summary

| Section | Entries | Content |
|---|---|---|
| Operator | 421 | Motion, I/O, error handling, task control |
| Program | 3687 | Language reference, functions, statements |
| **Total** | **4108** | Full SPEL+ command coverage |

---

## Requirements

- Python 3.10+
- No extra packages for search / skill usage
- `anthropic` package only for `spel_generate.py`: `pip install anthropic`
