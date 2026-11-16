# Claude Code entry point

This repository contains the **pcb-engineer** AI agent (lab 2: automated PCB design in KiCad 10).
The agent is defined in the GitHub Copilot format; Claude Code uses the same files:

- manifest: `.github/agents/pcb-engineer.agent.md` — read it before any command and follow its rules;
- skills: `.github/skills/*/SKILL.md` (specifications: requirements and checks, no ready-made files);
- commands: `.github/prompts/*.prompt.md`, exposed as `/gen-params`, `/create-library`, `/create-schematic`,
  `/create-pcb`, `/route`, `/fab`, `/check`, `/build-board` through the thin wrappers in `.claude/commands/`.

Never commit, push, rewrite history or delete files outside `output/` without explicit permission.
