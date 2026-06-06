"""
Restructure KB/json into TOC-chapter subfolders.
Run from repo root: python user/epson-coding/scripts/restructure_kb.py
"""
import re, json, shutil
from pathlib import Path
from collections import defaultdict

WHXDATA  = Path('user/epson-coding/source/Help/English/Program/whxdata')
KB_ROOT  = Path('user/epson-coding/KB/json')
KB_PROG  = KB_ROOT / 'Program'
KB_OP    = KB_ROOT / 'Operator'

# ── TOC parsing ────────────────────────────────────────────────────────────────
def load_chunk(key):
    f = WHXDATA / f'{key}.new.js'
    if not f.exists():
        return []
    m = re.search(r'var toc\s*=\s*(\[.*?\]);', f.read_text(encoding='utf-8'), re.DOTALL)
    return json.loads(m.group(1)) if m else []

def collect_stems(key, chapter):
    for item in load_chunk(key):
        url = item.get('url', '')
        if url:
            yield Path(url).stem, chapter
        if item['type'] == 'book':
            child = item.get('key')
            if child:
                yield from collect_stems(child, chapter)

stem_to_chapter = {}
for item in load_chunk('toc'):
    url = item.get('url', '')
    if url:
        stem_to_chapter[Path(url).stem] = item.get('name', 'Misc')
    if item['type'] == 'book':
        ch = item['name']
        child = item.get('key')
        if child:
            for stem, _ in collect_stems(child, ch):
                stem_to_chapter[stem] = ch

# Correct known KB renames (TOC typo vs corrected KB filename)
RENAMES = {
    'Cliosed_Event':              'Closed_Event',
    'Orientation_GUI_Property':   'Orientation_Property',
    'RobotNumber_StatusBar_Property': 'RobotNumber_Property',
}
for old, new in RENAMES.items():
    if old in stem_to_chapter:
        stem_to_chapter[new] = stem_to_chapter[old]

print(f'TOC stems mapped: {len(stem_to_chapter)}')

# ── Filesystem-safe name ──────────────────────────────────────────────────────
def safe(name):
    result = ''
    for ch in name:
        if ch in ' /':
            result += '_'
        elif ch == '+':
            result += 'plus'
        elif ch in '.:(),':
            pass
        else:
            result += ch
    while '__' in result:
        result = result.replace('__', '_')
    return result.strip('_')

# ── Pointer instruction data per chapter ─────────────────────────────────────
CHAPTER_INFO = {
    "GUI Builder": {
        "category": "gui_control",
        "instruction": (
            "GUI Builder properties, events, and form-control reference. "
            "Use ONLY when writing SPEL+ code that includes an RC+ operator GUI "
            "(GSet, GGet, GShow, GShowDialog). Do NOT use for robot motion or I/O commands."
        ),
    },
    "The SPEL+ Language": {
        "category": "robot_control",
        "instruction": (
            "Core SPEL+ language — statements, functions, operators, variables, "
            "control flow, tasks, and program structure. Primary reference for all "
            "robot programming tasks."
        ),
    },
    "Vision Guide": {
        "category": "vision",
        "instruction": (
            "Vision Guide — vision objects, sequences, properties, results, and "
            "camera calibration. Use for vision-based pick-and-place, inspection, "
            "or any VRun/VGet task."
        ),
    },
    "Force Sensing": {
        "category": "force_sensing",
        "instruction": (
            "Force sensing — force/torque objects, contact detection, and compliant "
            "motion. Use when the task involves force feedback or contact-based control."
        ),
    },
    "RC+ API": {
        "category": "rc_api",
        "instruction": (
            "RC+ API (.NET/COM) — classes, methods, properties for controlling the "
            "robot from an external host PC program. NOT for SPEL+ code."
        ),
    },
    "Conveyor Tracking": {
        "category": "conveyor",
        "instruction": (
            "Conveyor tracking — VStart, VStop, conveyor setup, and tracking "
            "parameters. Use for all conveyor-synchronised robot tasks."
        ),
    },
    "ECP Motion": {
        "category": "ecp_motion",
        "instruction": (
            "External Control Point (ECP) motion — ECP coordinate systems and "
            "ECPSet. Use for tool-tip controlled motion."
        ),
    },
    "Distance Tracking Function": {
        "category": "distance_tracking",
        "instruction": "Distance tracking — DistCorrect and path-correction commands.",
    },
    "Real Time I/O": {
        "category": "realtime_io",
        "instruction": "Real-Time I/O — high-speed parallel I/O and synchronisation commands.",
    },
    "Additional Axis": {
        "category": "additional_axis",
        "instruction": "Additional axis — configuration and motion commands for auxiliary axes.",
    },
    "Building SPEL+ Applications": {
        "category": "spel_apps",
        "instruction": (
            "Building SPEL+ applications — project structure, multi-task management, "
            "32-bit/64-bit apps, and application best practices."
        ),
    },
    "Motion System": {
        "category": "motion",
        "instruction": "Motion system — joint, linear, circular motion concepts and parameters.",
    },
    "Robot Configuration": {
        "category": "robot_config",
        "instruction": "Robot configuration — arm types, local/tool frames, inertia and collision.",
    },
    "Inputs and Outputs": {
        "category": "io",
        "instruction": "Digital I/O — On/Off/In/Out/Sw, memory I/O, and I/O configuration.",
    },
    "Remote Control": {
        "category": "remote_control",
        "instruction": "Remote control — fieldbus interfaces (DeviceNet, PROFIBUS, EtherNet/IP).",
    },
    "RS-232C Communications": {
        "category": "rs232",
        "instruction": "RS-232C — Open, Close, Send, Recv serial communication commands.",
    },
    "TCP/IP Communications": {
        "category": "tcpip",
        "instruction": "TCP/IP — socket open/close, Send, Recv over Ethernet.",
    },
    "Security": {
        "category": "security",
        "instruction": "Security — user accounts, privilege levels, and access control.",
    },
    "Absolute Accuracy Calibration": {
        "category": "abs_cal",
        "instruction": "Absolute accuracy calibration — geometric calibration procedures and commands.",
    },
    "Calibration of Commercial Vision Sensor and Robot": {
        "category": "vision_cal",
        "instruction": "Commercial vision sensor and robot calibration procedures.",
    },
    "Parts Feeding": {
        "category": "parts_feeding",
        "instruction": "Parts feeding — bowl feeder integration, part detection, and feeding parameters.",
    },
    "Simulator": {
        "category": "simulator",
        "instruction": "Simulator — offline simulation features, limitations, and unsupported models.",
    },
    "Operation": {
        "category": "operation",
        "instruction": "Runtime operation — starting, stopping, pausing, and monitoring tasks.",
    },
    "The Epson RC+ 8.0 GUI": {
        "category": "rc_gui",
        "instruction": "Epson RC+ 8.0 IDE — menus, toolbars, windows, and IDE operation.",
    },
    "Introduction": {
        "category": "intro",
        "instruction": "RC+ system introduction — components, architecture, and overview.",
    },
    "Getting Started": {
        "category": "getting_started",
        "instruction": "Getting started — first project creation and basic workflow.",
    },
    "How Do I": {
        "category": "how_do_i",
        "instruction": "How Do I — task-oriented guides for common RC+ operations.",
    },
    "Safety": {
        "category": "safety",
        "instruction": "Safety — emergency stop, safeguard, and safe operation guidelines.",
    },
    "FOREWORD": {
        "category": "foreword",
        "instruction": "Foreword, trademarks, notices, and manufacturer information.",
    },
    "Misc": {
        "category": "misc",
        "instruction": (
            "Miscellaneous references not directly listed as Table of Contents items. "
            "May include sub-pages, additional properties, and supplementary content."
        ),
    },
}

# ── Group all KB files by chapter ─────────────────────────────────────────────
chapter_files = defaultdict(list)   # chapter → [(section_root, Path)]

for section_root in [KB_PROG, KB_OP]:
    for jf in section_root.rglob('*.json'):
        if jf.name.startswith('_'):
            continue
        ch = stem_to_chapter.get(jf.stem, 'Misc')
        chapter_files[ch].append((section_root, jf))

print('\nChapter file counts (Program + Operator):')
for ch, files in sorted(chapter_files.items(), key=lambda x: -len(x[1])):
    print(f'  {len(files):4d}  {ch}')

# ── Move files into chapter subfolders ────────────────────────────────────────
moved_total = 0

for chapter, files in chapter_files.items():
    folder_name = safe(chapter)
    for section_root, jf in files:
        dest_dir = section_root / folder_name
        dest_dir.mkdir(exist_ok=True)
        shutil.move(str(jf), str(dest_dir / jf.name))
        moved_total += 1

print(f'\nMoved {moved_total} files into chapter folders')

# ── Write _folder.json pointer in each chapter dir ────────────────────────────
folders_written = 0
for chapter in chapter_files:
    folder_name = safe(chapter)
    info = CHAPTER_INFO.get(chapter, {
        "category": safe(chapter).lower(),
        "instruction": f"Reference material for the '{chapter}' section of the EPSON RC+ help.",
    })
    pointer = {
        "type": "folder_index",
        "toc_chapter": chapter,
        "category": info["category"],
        "title": chapter,
        "instruction": info["instruction"],
    }
    for section_root in [KB_PROG, KB_OP]:
        dest_dir = section_root / folder_name
        if dest_dir.exists() and any(dest_dir.glob('*.json')):
            out = dest_dir / '_folder.json'
            out.write_text(json.dumps(pointer, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            folders_written += 1

print(f'Wrote {folders_written} _folder.json pointer files')

# ── Clean up empty legacy dirs ────────────────────────────────────────────────
for old in [KB_PROG / 'gui_control', KB_PROG / 'robot_control']:
    if old.exists():
        remaining = [f for f in old.rglob('*.json') if not f.name.startswith('_')]
        if not remaining:
            shutil.rmtree(old)
            print(f'Removed empty legacy dir: {old.name}')
        else:
            print(f'Legacy dir {old.name} still has {len(remaining)} files — left intact')

print('\nDone.')
