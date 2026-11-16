---
description: Generate KiCad symbols and footprints for U1..U5 and J1 (kicad-library skill).
argument-hint: "[key=value ...]"
---

Act as the pcb-engineer agent defined in `.github/agents/pcb-engineer.agent.md`
(read it first and follow its rules, forbidden actions and completion criteria).

Execute the command described in `.github/prompts/create-library.prompt.md` exactly as written there,
using the skills it references from `.github/skills/`. Arguments: $ARGUMENTS
