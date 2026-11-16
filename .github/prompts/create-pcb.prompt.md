---
agent: pcb-engineer
description: Generate the credit-card board outline, rules, footprints, nets and connectivity-driven placement (kicad-pcb skill).
---

# /create-pcb

Застосуй skill [kicad-pcb](../skills/kicad-pcb/SKILL.md).

## Передумови
- `/create-schematic` виконано, ERC = 0.
- Якщо плата вже має доріжки — команда нічого не змінює (`SKIP`).

## Дії
1. Написати або перевірити `tools/pcb.py`; запустити.
2. DRC з `--schematic-parity`: допускаються лише нерозведені з'єднання.

## Очікувані файли
- `hardware/lab2.kicad_pcb` (оновлений `hardware/lab2.kicad_pro`)

## Перевірки
```bash
kicad-cli pcb drc --format json --severity-all --schematic-parity -o output/drc.json hardware/lab2.kicad_pcb
python3 .github/agent-tools/check.py --only pcb
```

## Повідомлення про помилку
- `create-pcb: FAIL — no room for <ref> on the board`
- `create-pcb: FAIL — DRC parity <n> issue(s): <тип першого>`
- `create-pcb: FAIL — board outline <w>x<h> mm exceeds 85.6x53.98 mm`
