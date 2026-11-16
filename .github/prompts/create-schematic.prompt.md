---
agent: pcb-engineer
description: Generate the KiCad project and schematic, then run ERC (kicad-schematic skill).
---

# /create-schematic

Застосуй skill [kicad-schematic](../skills/kicad-schematic/SKILL.md).

## Передумови
- `/create-library` виконано; `kicad-cli version` працює.

## Дії
1. Написати або перевірити `tools/schematic.py`; запустити.
2. ERC і експорт netlist; порівняти мережі з `params/board.json`.

## Очікувані файли
- `hardware/lab2.kicad_pro`, `hardware/lab2.kicad_sch`, `hardware/sym-lib-table`, `hardware/fp-lib-table`

## Перевірки
```bash
kicad-cli sch erc --format json --severity-all --exit-code-violations -o output/erc.json hardware/lab2.kicad_sch
python3 .github/agent-tools/check.py --only schematic
```

## Повідомлення про помилку
- `create-schematic: FAIL — kicad-cli sch upgrade: <помилка розбору>`
- `create-schematic: FAIL — ERC <n> violation(s): <тип першого>`
- `create-schematic: FAIL — net <name> differs from params`
