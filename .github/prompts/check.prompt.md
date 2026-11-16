---
agent: pcb-engineer
description: Verify the agent, parameters, library, schematic, board, routing, Gerber files and Git state without changing the design.
---

# /check

Команда **нічого не змінює** у файлах під Git; пише лише в `output/`.

## Передумови
- KiCad (`kicad-cli`, модуль `pcbnew`) встановлено.

## Дії
1. `python3 .github/agent-tools/check.py` — групи `agent`, `skills`, `commands`,
   `params`, `library`, `schematic`, `pcb`, `routing`, `fab`, `git`.
2. Ручна перевірка: кожен згенерований файл виконує пункти «Вимоги» свого skill;
   у skills немає готових файлів-заготовок.
3. `git status --short` — такий самий, як до запуску.
4. Підсумок `PASS`/`FAIL`; хоча б один `FAIL` → загальний `FAIL`.

## Очікувані файли
- Жодних змін під Git; звіти в `output/`.

## Перевірки
```bash
python3 .github/agent-tools/check.py; echo "exit code: $?"
git status --short
```

## Повідомлення про помилку
- `check: FAIL — <N> check(s) failed` + рядки `[FAIL]` з причиною.
