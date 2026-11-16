---
name: autoroute
description: Routes the lab 2 board on two layers with the Freerouting CLI through a Specctra DSN/SES round trip and verifies that nothing is left unconnected and there are no acute corners. Use after kicad-pcb or when /route is run.
---

# Skill: autoroute

Skill не містить готових доріжок: агент пише `tools/route.py`, який передає
плату автотрасувальнику Freerouting і повертає результат у KiCad.

## Коли застосовувати
- Плата розміщена (`/create-pcb`), але доріжок немає.
- Користувач запускає `/route` або оркестратор `/build-board`.

## Входи
| Параметр | Значення | Опис |
|---|---|---|
| `board` | `hardware/lab2.kicad_pcb` | розміщена плата |
| `freerouting` | `~/.local/opt/freerouting/freerouting-cli` або змінна `FREEROUTING` | нативна CLI-збірка Freerouting (без Java) |
| `passes` | 30 | максимум проходів автотрасування |

## Виходи
| Файл | Що містить |
|---|---|
| `tools/route.py` | скрипт трасування |
| `hardware/lab2.kicad_pcb` | плата з доріжками на F.Cu і B.Cu |
| `output/route/lab2.dsn`, `lab2.ses`, `freerouting.log` | проміжні файли (не в Git) |

## Вимоги
1. Якщо на платі вже є доріжки — `SKIP`.
2. Експорт `pcbnew.ExportSpecctraDSN(board, dsn)`.
3. З DSN видаляються всі вирази `(outline …)` (контури компонентів): Freerouting
   2.5.0 у нативній збірці зависає на них (`UnsupportedFeatureError … ComponentOutline`),
   а для трасування вони не потрібні. Скрипт друкує, скільки контурів прибрано.
4. Запуск: `freerouting-cli -de <dsn> -do <ses> --router.autorouter.max_passes=<passes> -mt 1`,
   stdin — `/dev/null`, тайм-аут 300 с; повний лог зберігається.
5. Помилка, якщо код виходу ≠ 0, немає SES, у лозі є `Exception`, або тайм-аут.
6. Імпорт `pcbnew.ImportSpecctraSES(board, ses)` і збереження `pcbnew.SaveBoard`.
7. Скрипт друкує кількість сегментів, переходів і загальну довжину доріжок.

## Кроки
1. Перевірити, що Freerouting запускається (`freerouting-cli --help`).
2. Написати `tools/route.py`; запустити.
3. DRC і перевірка кутів.

## Перевірки
```bash
python3 tools/route.py                  # "... 0 unrouted and 0 violations", довжина доріжок
kicad-cli pcb drc --format json --severity-all --schematic-parity --exit-code-violations \
  -o output/drc.json hardware/lab2.kicad_pcb       # 0 violations, 0 unconnected, 0 parity
```
Додатково (`check.py`): доріжки є на обох шарах; у кожному зламі доріжки
(точка, де сходяться рівно два сегменти поза площадкою) внутрішній кут ≥ 90°.

## Типовий сценарій помилки
| Симптом | Причина | Дія |
|---|---|---|
| Freerouting працює без кінця, CPU ≈ 0 | зависання на `ComponentOutline` | вимога 3 |
| `UnsupportedClassVersionError … class file version 69` | jar-версії потрібна Java 25 | використовувати нативну `freerouting-cli` |
| `Deprecated settings path '-mp'` | стара назва параметра | `--router.autorouter.max_passes` |
| DRC `unconnected_items` після трасування | канали між компонентами завузькі | збільшити `GAP` у розміщенні, повторити `/create-pcb` (доріжки видаляє користувач) |
| DRC `clearance` на доріжках | правила DSN не збігаються з netclass | правила задаються лише в netclass `Default` |

## Приклад
Вхід: `/route`
```text
route: exported output/route/lab2.dsn (23 component outlines removed)
route: freerouting: Auto-routing stage completed: started with 22 unrouted nets ... (0 unrouted and 0 violations)
route: 73 segments, 0 vias, total track length 290.1 mm
```
