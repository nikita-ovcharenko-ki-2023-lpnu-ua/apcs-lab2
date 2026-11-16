# Лабораторна робота № 2 — AI-агент pcb-engineer

## Опис
Репозиторій містить AI-агента **pcb-engineer**, який автоматизовано проєктує
друковану плату в САПР **KiCad 10** за технічним завданням лабораторної роботи:
GUID з повного імені → п'ять квадратних компонентів → бібліотека → принципова
схема → плата форм-фактора кредитної картки → двошарове трасування (Freerouting)
→ ERC/DRC → Gerber RS-274X.

| Компонент | Шлях |
|---|---|
| Agent manifest | [`.github/agents/pcb-engineer.agent.md`](.github/agents/pcb-engineer.agent.md) |
| Skills (6) | [`.github/skills/`](.github/skills/) — `guid-params`, `kicad-library`, `kicad-schematic`, `kicad-pcb`, `autoroute`, `fab-output` |
| Commands (8) | [`.github/prompts/`](.github/prompts/) — `gen-params`, `create-library`, `create-schematic`, `create-pcb`, `route`, `fab`, `check`, `build-board` |
| Перевірка | [`.github/agent-tools/check.py`](.github/agent-tools/check.py) |
| Архітектура | [`docs/architecture.md`](docs/architecture.md) |
| Інструкція запуску | [`docs/usage.md`](docs/usage.md) |

## Гілки
- `develop` — лише агент з інструкціями;
- `feature/pcb-board` — результат запуску `/build-board`: скрипти, проєкт KiCad, CI;
- `master` — фінальний результат після перевірки.

## Запуск агента
**VS Code + GitHub Copilot Chat:** вибрати агента `pcb-engineer`, виконати
`/build-board fullName="Прізвище Ім'я По батькові"`.

**Claude Code:** `claude` у корені репозиторію, потім `/build-board fullName="…"`.

Потрібні KiCad 10 (`kicad-cli`, Python-модуль `pcbnew`) і Freerouting CLI — див. [`docs/usage.md`](docs/usage.md).
