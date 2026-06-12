---
name: delta-coding
description: Generate Delta robot programs from a natural-language description. Use when the user calls /delta-coding, mentions writing a program for a Delta robot, or describes a robot task for a Delta arm.
argument-hint: "<describe the robot task>"
---

# /delta-coding

Generate production-quality code for Delta robots. Always search the local KB before writing code — never guess syntax.

## Usage

```
/delta-coding <describe the robot task>
```

Describe what the robot should do: @$1

If no task is provided, ask the user what the robot should do.

---

<!-- Steps and rules will be filled in together -->
