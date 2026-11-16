---
description: Orchestrator - run gen-params, create-library, create-schematic, create-pcb, route, fab and check in order, stopping at the first error.
argument-hint: "[key=value ...]"
---

Act as the pcb-engineer agent defined in `.github/agents/pcb-engineer.agent.md`
(read it first and follow its rules, forbidden actions and completion criteria).

Execute the command described in `.github/prompts/build-board.prompt.md` exactly as written there,
using the skills it references from `.github/skills/`. Arguments: $ARGUMENTS
