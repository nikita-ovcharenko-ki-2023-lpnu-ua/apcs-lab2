---
description: Route the board on two layers with Freerouting via Specctra DSN/SES (autoroute skill).
argument-hint: "[key=value ...]"
---

Act as the pcb-engineer agent defined in `.github/agents/pcb-engineer.agent.md`
(read it first and follow its rules, forbidden actions and completion criteria).

Execute the command described in `.github/prompts/route.prompt.md` exactly as written there,
using the skills it references from `.github/skills/`. Arguments: $ARGUMENTS
