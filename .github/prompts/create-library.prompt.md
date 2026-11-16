---
agent: pcb-engineer
description: Generate KiCad symbols and footprints for U1..U5 and J1 (kicad-library skill).
---

# /create-library

Застосуй skill [kicad-library](../skills/kicad-library/SKILL.md).

## Передумови
- `/gen-params` виконано (`params/board.json` існує).
- `python3 -c "import pcbnew"` працює (KiCad встановлено).

## Дії
1. Написати або перевірити `tools/common.py` і `tools/library.py`.
2. Запустити `python3 tools/library.py`.
3. Завантажити кожен футпринт через `pcbnew.FootprintLoad` і звірити кількість площадок.

## Очікувані файли
- `hardware/lib/lab2.pretty/*.kicad_mod` (6 шт.), `hardware/lib/lab2.kicad_sym`

## Перевірки
```bash
python3 tools/library.py
python3 .github/agent-tools/check.py --only library
```

## Повідомлення про помилку
- `create-library: FAIL — KiCad cannot load footprint <name>`
- `create-library: FAIL — <ref> body is <a>x<b> mm, expected <N>x<N> mm`
