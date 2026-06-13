# Example PM Form structure — AYF (BEI-Thailand house template)

Lightweight text distillation of AYFEMP-0051798-RevA. Use as content/structure
reference; apply named styles per SKILL.md. AYF forms are English-only (no Thai siblings).

---

**Filename:** AYFEMP-0051798-RevA.docx
**Orientation:** Landscape
**`core.xml` category:** form | **subject:** Product Engineering
**Company:** Benchmark Electronics (BEI-Thailand), Product Engineering

---

## Top fill-in blanks

```
MACHINE ID: _______________   MACHINE NAME: _______________
MODEL: _______________        SERIAL NO: _______________
```

**Title (centered, bold, Heading1 style):**
PREVENTIVE MAINTENANCE INSTRUCTIONS

---

## PM Matrix Table

Column layout: `Area | Item | Execution | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13`

- Columns 1–13 = occurrence/month check points (tick marks go here).
- Rows are grouped by maintenance interval (`MONTHLY`, `SEMI-ANNUAL`).
- Header row uses `Table` style (shaded `CCCCCC`); body rows use `Text` style.

| Area | Item | Execution | 1 | 2 | … | 13 |
|---|---|---|---|---|---|---|
| **MONTHLY** | | | | | | |
| Safety | Test EMO buttons | Functional check — press each EMO and verify machine halts | ✓ | ✓ | | ✓ |
| Cleaning | Clean fixture contact pins with 99% IPA | Wipe surfaces with IPA-soaked cloth; allow to dry | ✓ | ✓ | | ✓ |
| Pneumatic | Check air supply pressure at gauge | Verify ≥ 0.5 MPa; adjust regulator if needed | ✓ | ✓ | | ✓ |
| **SEMI-ANNUAL** | | | | | | |
| Mechanical | Inspect conveyor belt tension | Visual + manual deflection check; adjust tensioner | | ✓ | | ✓ |
| Electrical | Inspect power cable insulation | Visual for cracks, chafing, exposed wire | | ✓ | | ✓ |
| Mechanical | Lubricate guide rails | Apply specified grease; wipe excess | | ✓ | | ✓ |

*(Actual rows reflect the specific machine's PM requirements.)*

---

## Sign-off Row

```
Checked By: _______________   Date: _______________   Inspected By: _______________
```

*Tick after completing the items.*

---

## Preventive Maintenance Action Record

Separate table immediately below the sign-off row:

| Date | Problem Description | Action Taken | By |
|---|---|---|---|
| | | | |
| | | | |
| | | | |
| | | | |

---

## Revision History

| Rev | Description of Change | Approved By |
|---|---|---|
| A | New release. | Agile ECO xxxxxxx |

---

**Build notes:**
- Set page orientation to landscape before inserting the PM matrix.
- The PM matrix is wide (16 columns); use a small font size or allow auto-fit.
- All content is English-only — no `ThaiTranslate` paragraphs.
- Top blanks are best implemented as a borderless 2×2 table or form fields.
- Filename must follow `AYF<cust>-<7digits>-Rev<X>.docx` convention.
