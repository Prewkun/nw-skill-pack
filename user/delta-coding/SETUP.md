# delta-coding — Setup Guide

This skill generates Modbus TCP / TCP/IP communication code for the **Delta SD3 Smart Screwdriving System**. It uses a structured JSON knowledge base (KB) extracted from the official SD3 user manual and a BM25 search script — no extra Python packages required.

---

## Directory layout

```
user/delta-coding/
├── SKILL.md                            ← Claude skill definition
├── SETUP.md                            ← This file
├── DELTA_IA-DCSS_SD3_UM_EN_20240306.pdf ← Source manual (reference only)
├── KB/
│   ├── delta_kb_index.json             ← Lightweight index of all function codes
│   └── json/
│       ├── Modbus/                     ← Modbus function code JSON records
│       └── TCPIP/                      ← TCP/IP function code JSON records
└── scripts/
    ├── delta_search.py                 ← BM25 keyword search (no dependencies)
    └── extract_delta_kb.py             ← One-time: re-extract KB from PDF
```

---

## Step 1 — Clone and install the skill

```bash
git clone https://github.com/Prewkun/atm-skill-pack.git
```

Copy the skill into your Claude skills directory:

**Windows:**
```powershell
Copy-Item -Recurse atm-skill-pack\user\delta-coding "$env:USERPROFILE\.claude\skills\delta-coding"
```

**macOS / Linux:**
```bash
cp -r atm-skill-pack/user/delta-coding ~/.claude/skills/delta-coding
```

Restart Claude Code — `/delta-coding` will appear in the skill list.

---

## Step 2 — Verify the search script

The KB JSON files are included — no index build step needed. Test the search:

```bash
cd ~/.claude/skills/delta-coding
python scripts/delta_search.py "switch parameter manual"
```

You should see matching function code references printed. Try a few more:

```bash
python scripts/delta_search.py "read tightening result" --protocol Modbus
python scripts/delta_search.py 302 --code --verbose
python scripts/delta_search.py "clear errors" --category Results
```

---

## Step 3 (optional) — Re-extract KB from source manual

The KB was extracted from `DELTA_IA-DCSS_SD3_UM_EN_20240306.pdf` (included). If you have an updated manual:

1. Replace the PDF in the skill root (keep the same filename or update `DEFAULT_PDF` in the script)
2. Run:
   ```bash
   python scripts/extract_delta_kb.py
   ```

This regenerates all JSON records in `KB/json/Modbus/` and `KB/json/TCPIP/` and rebuilds `KB/delta_kb_index.json`.

---

## KB summary

| Protocol | Category | Coverage |
|---|---|---|
| Modbus | Parameters, Sequence, Sources, Results, Controller, Tool, Reports | Full function codes #100–#754 |
| TCP/IP | Operational, Parameters, Sequence, Sources, Results, Controller, Tool, Reports | Full function codes #20–#754 |

---

## Requirements

- Python 3.10+
- No extra packages needed for search or skill usage
- `pymodbus` only if you want to run the generated Modbus code directly: `pip install pymodbus`
