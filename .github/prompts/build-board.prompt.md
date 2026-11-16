---
agent: pcb-engineer
description: Orchestrator - run gen-params, create-library, create-schematic, create-pcb, route, fab and check in order, stopping at the first error.
argument-hint: fullName="Прізвище Ім'я По батькові"
---

# /build-board (orchestrator)

Повний сценарій проєктування плати. Кожен крок — окрема command зі своїми
передумовами й перевірками; оркестратор лише викликає їх і передає результати.

## Передумови
- Прочитано manifest `.github/agents/pcb-engineer.agent.md`.
- `kicad-cli version`, `python3 -c "import pcbnew"`, `freerouting-cli --help` працюють.
- Задано `fullName` (інакше — запитати).

## Дії
Виконати **строго по черзі**; після кожного кроку — його розділ «Перевірки».

| # | Command | Вхід | Результат для наступного кроку |
|---|---|---|---|
| 1 | `/gen-params` | `fullName` | `params/board.json` |
| 2 | `/create-library` | `board.json` | `hardware/lib/` |
| 3 | `/create-schematic` | бібліотека | `lab2.kicad_sch`, ERC = 0 |
| 4 | `/create-pcb` | схема, футпринти | розміщена плата, parity = 0 |
| 5 | `/route` | розміщена плата | розведена плата, DRC = 0 |
| 6 | `/fab` | розведена плата | Gerber, зображення, CI |
| 7 | `/check` | усе | підсумок `PASS`/`FAIL` |

Обробка помилок:
- `FAIL` на кроці → **зупинитися**, наступні кроки не запускати; показати крок,
  команду, вивід і ймовірну причину з таблиці помилок skill.
- Не послаблювати правила DRC і не вимикати перевірки; виправлення — у скрипті
  `tools/` або в інструкції skill, потім `/build-board` повторно.
- Повторний запуск після успіху — лише `SKIP` і `PASS`, `git status` без змін.

## Очікувані файли
Усі файли з «Очікуваних файлів» команд 1–6.

## Перевірки
```bash
python3 .github/agent-tools/check.py; echo "exit code: $?"   # -> 0
```
```text
build-board: 1/7 gen-params        PASS
...
build-board: 7/7 check             PASS
build-board: DONE
```

## Повідомлення про помилку
`build-board: STOPPED at step <n>/7 (<command>) — <причина>. Fix and run /build-board again.`
