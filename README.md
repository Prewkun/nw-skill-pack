# NW Skill Pack

A personal collection of [Claude Code](https://claude.ai/code) skills, covering general engineering workflows, operations, and domain-specific tools like industrial robot programming and smart screwdriving systems.

Skills are prompt definitions that extend Claude with reusable, slash-command-triggered behaviours. Each skill lives in its own directory with a `SKILL.md` that tells Claude what to do, when to trigger, and how to respond.

---

## What is a skill?

A **skill** is a markdown file (`SKILL.md`) with a YAML frontmatter block that Claude Code reads at session start. When you type `/skill-name`, Claude loads the skill's instructions and follows them for that task.

Skills can include:
- Prompt instructions only (most skills)
- Supporting scripts and knowledge bases (e.g. `epson-coding`)
- Reference files, templates, or examples

See the [Claude Code skills documentation](https://docs.anthropic.com/en/docs/claude-code/skills) for how skills are installed and loaded.

---

## Repository structure

```
nw-skill-pack/
├── user/          ← Personal skills (custom workflows and domain tools)
├── public/        ← Anthropic-provided shared skills (read-only)
├── plugins/       ← Plugin-namespaced skills (category:skill-name)
├── skills/        ← Meta-skills (used by Claude Code infrastructure)
├── KB/            ← Legacy location — see user/epson-coding/KB/
├── output/        ← Legacy location — see user/epson-coding/output/
└── scripts/       ← Legacy location — see user/epson-coding/scripts/
```

---

## Skills

### `user/` — Personal skills

Custom skills tailored to specific workflows and domain knowledge.

| Skill | What it does |
|---|---|
| `brainstorming` | Structured ideation — generates, clusters, and ranks options before committing to a path |
| `debug-mantra` | Four-step debugging discipline: reproduce → trace → falsify → breadcrumb |
| `delta-coding` | Generates Python or PLC Modbus TCP/TCP/IP communication code for the Delta SD3 Smart Screwdriving System, grounded in the official manual KB |
| `diagnose` | Root-cause diagnosis for unclear problems |
| `epson-coding` | Generates EPSON SPEL+ robot programs from natural language, grounded in the official manual KB |
| `executing-plans` | Turns a plan into a sequenced execution with checkpoints |
| `find-skills` | Discovers and recommends relevant skills for a given task |
| `management-talk` | Translates technical work into management-friendly language |
| `manual-to-web` | Converts manual/offline processes into web-ready documentation |
| `post-mortem` | Structured incident post-mortem — timeline, root cause, action items |
| `scrutinize` | Critical review of decisions, plans, or arguments for blind spots |
| `tdd` | Test-driven development loop — red → green → refactor |
| `to-issues` | Breaks down work into discrete, actionable GitHub issues |
| `to-prd` | Converts feature requests or ideas into a product requirements document |
| `triage` | Prioritises a backlog or list of problems by impact and urgency |

> Skills with supporting files (scripts, knowledge bases) keep everything self-contained in their own directory. See each skill's `SETUP.md` for installation notes.

---

### `public/` — Shared skills

Anthropic-provided skills distributed with Claude Code. These are read-only and updated by Anthropic.

| Skill | What it does |
|---|---|
| `docx` | Create, read, edit, and manipulate Word documents |
| `file-reading` | Smart file reading with format detection |
| `frontend-design` | UI and frontend implementation guidance |
| `pdf` / `pdf-reading` | Work with PDF files |
| `pptx` | Create and edit PowerPoint presentations |
| `product-self-knowledge` | Claude's own capabilities and limitations |
| `xlsx` | Work with Excel spreadsheets |

---

### `plugins/` — Plugin skills

Namespaced skills organised by domain (`category:skill-name`). Loaded as a group when the plugin is active.

**engineering** — `architecture`, `code-review`, `debug`, `deploy-checklist`, `documentation`, `incident-response`, `standup`, `system-design`, `tech-debt`, `testing-strategy`

**operations** — `capacity-plan`, `change-request`, `compliance-tracking`, `process-doc`, `process-optimization`, `risk-assessment`, `runbook`, `status-report`, `vendor-review`

**productivity** — `memory-management`, `start`, `task-management`, `update`

**cowork-plugin-management** — `cowork-plugin-customizer`, `create-cowork-plugin`

---

### `skills/` — Infrastructure skills

Meta-skills used by Claude Code itself.

| Skill | What it does |
|---|---|
| `session-start-hook` | Creates `SessionStart` hooks that install dependencies for Claude Code on the web |
| `epson-coding` | Original location — canonical version is now in `user/epson-coding/` |

---

## Installing a skill

Copy a skill folder into your Claude skills directory and restart Claude Code.

**Windows:**
```powershell
Copy-Item -Recurse user\epson-coding "$env:USERPROFILE\.claude\skills\epson-coding"
```

**macOS / Linux:**
```bash
cp -r user/epson-coding ~/.claude/skills/epson-coding
```

For skills with extra setup (scripts, knowledge bases), see the `SETUP.md` inside that skill's directory.

---

## Requirements

- Python 3.10+ (for skills with scripts)
- No extra packages needed for search/skill usage
- `anthropic` Python package only needed for `spel_generate.py --api` mode
