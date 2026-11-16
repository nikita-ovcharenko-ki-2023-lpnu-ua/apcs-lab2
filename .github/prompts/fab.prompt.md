---
agent: pcb-engineer
description: Run ERC/DRC and generate Gerber RS-274X, drill files, images and the CI files (fab-output skill).
---

# /fab

Застосуй skill [fab-output](../skills/fab-output/SKILL.md).

## Передумови
- `/route` виконано, DRC = 0.

## Дії
1. Написати або перевірити `tools/fab.py`; запустити.
2. Написати або перевірити `ci.sh` і `.github/workflows/ci.yml` (версії образу KiCad і
   `actions/*` — актуальні на момент запуску); запустити `./ci.sh`.

## Очікувані файли
- `output/gerbers/*`, `output/lab2-gerbers.zip`, `output/images/*`, `output/erc.json`, `output/drc.json`
- `tools/fab.py`, `ci.sh`, `.github/workflows/ci.yml`

## Перевірки
```bash
python3 tools/fab.py
python3 .github/agent-tools/check.py --only fab
```

## Повідомлення про помилку
- `fab: FAIL — ERC/DRC violations, Gerber files not generated`
- `fab: FAIL — <file> is not RS-274X (no %FS/%MO header)`
