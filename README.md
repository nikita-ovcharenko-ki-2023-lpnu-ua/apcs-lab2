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

<!-- agent:project:start -->
## Плата

GUID: `24f9653f-a875-5d8f-9242-e476d2f1079a` (uuid5(NAMESPACE_DNS, full_name)).

| Компонент | Група GUID | Розмір, мм | Пінів |
|---|---|---|---|
| U1 | `24f9653f` | 8 × 8 | 8 |
| U2 | `a875` | 4 × 4 | 4 |
| U3 | `5d8f` | 4 × 4 | 4 |
| U4 | `9242` | 4 × 4 | 4 |
| U5 | `e476d2f1079a` | 12 × 12 | 12 |
| J1 | вільні піни | 1 × 4, крок 2.54 | 4 |

| Мережа | Піни |
|---|---|
| `N_2` | U1.1, U4.2, U4.4, U5.6 |
| `N_4` | U1.2, U4.3, U5.2 |
| `N_5` | U1.6, U2.4, U3.1 |
| `N_6` | U1.5, U5.4 |
| `N_7` | U2.3, U5.3, U5.10 |
| `N_8` | U2.2, U3.3 |
| `N_9` | U1.4, U4.1, U5.11 |
| `N_a` | U2.1, U5.12 |
| `N_d` | U3.2, U5.5 |
| `N_f` | U1.3, U1.8, U3.4, U5.7 |
| `FREE_U5_9` | U5.9, J1.1 |
| `FREE_U5_8` | U5.8, J1.2 |
| `FREE_U1_7` | U1.7, J1.3 |
| `FREE_U5_1` | U5.1, J1.4 |

Плата 85.6 × 53.98 мм, 2 шари. Проєкт KiCad — `hardware/lab2.kicad_pro`.
Відтворити: `python3 tools/params.py "<ПІБ>"`, `tools/library.py`, `tools/schematic.py`,
`tools/pcb.py`, `tools/route.py`, `tools/fab.py`; результат — `output/`.
<!-- agent:project:end -->
