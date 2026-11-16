---
name: kicad-schematic
description: Generates the KiCad project files and the schematic that connects equal GUID pins by net labels and routes free pins to J1 on the left edge of the sheet, then normalises it with kicad-cli and runs ERC. Use after kicad-library or when /create-schematic is run.
---

# Skill: kicad-schematic

Skill не містить готової схеми: агент пише `tools/schematic.py`, який будує
схему з `params/board.json` і бібліотеки.

## Коли застосовувати
- Є бібліотека `hardware/lib/`, але немає `hardware/lab2.kicad_sch` або змінились параметри.
- Користувач запускає `/create-schematic` або оркестратор `/build-board`.

## Входи
| Параметр | Значення |
|---|---|
| `params` | `params/board.json` |
| `library` | `hardware/lib/lab2.kicad_sym`, `hardware/lib/lab2.pretty/` |
| `projectTemplate` | шаблон проєкту KiCad з установки (`/usr/share/kicad/template/kicad.kicad_pro`) |

## Виходи
| Файл | Що містить |
|---|---|
| `tools/schematic.py` | генератор |
| `hardware/lab2.kicad_pro` | проєкт (створюється з шаблону KiCad, якщо його немає) |
| `hardware/sym-lib-table`, `hardware/fp-lib-table` | бібліотека `lab2` з `${KIPRJMOD}/lib/...` |
| `hardware/lab2.kicad_sch` | принципова схема |

## Вимоги
1. Аркуш A4; у штампі — назва з GUID.
2. Кожен символ U1–U5 і J1 — екземпляр з детермінованим UUID
   (`uuid5` від імені об'єкта); `lib_symbols` містить копії символів бібліотеки
   (`lab2:U1` …). Позиції екземплярів кратні 2.54 мм; J1 — біля **лівого краю
   аркуша** (вільні піни виведено на край схеми), U1–U5 — сіткою праворуч.
3. З'єднання: від кінця кожного піна — короткий провід (wire) назовні і мітка
   мережі (`label`) з назвою мережі з `board.json`. Однакові мітки = одна мережа.
   Вільні піни компонентів і піни J1 з'єднуються мітками `FREE_*`.
4. Немає незадіяних пінів і неприв'язаних міток.
5. Згенерований текст нормалізується до рідного формату KiCad:
   `kicad-cli sch upgrade --force` у тимчасовому каталозі разом із бібліотеками
   і таблицями; результат порівнюється з наявним файлом (`SKIP`, якщо однаковий).
6. Таблиці бібліотек і проєкт створюються, лише якщо їх немає або вони відрізняються.

## Кроки
1. Написати `tools/schematic.py`; запустити.
2. ERC і порівняння мереж.

## Перевірки
```bash
python3 tools/schematic.py
kicad-cli sch erc --format json --severity-all --exit-code-violations -o output/erc.json hardware/lab2.kicad_sch   # -> 0 violations
kicad-cli sch export netlist --format kicadxml -o output/netlist.xml hardware/lab2.kicad_sch
```
Мережі зі `output/netlist.xml` (без префікса `/`) мають точно збігатися з
мережами `params/board.json` — це порівнює `check.py`.

## Типовий сценарій помилки
| Симптом | Причина | Дія |
|---|---|---|
| `kicad-cli sch upgrade` → помилка розбору | синтаксис S-виразу, невідомий токен | порівняти з форматом KiCad, виправити генератор |
| ERC `pin_not_connected` | мітку поставлено не на кінець проводу/піна | мітка — на кінці проводу, провід починається в точці піна |
| ERC `label_dangling` | мітка мережі з одним входженням | мережі з одним піном — лише через J1 (`FREE_*`) |
| ERC `lib_symbol_mismatch` | копія символу в схемі відрізняється від бібліотеки | будувати `lib_symbols` тією самою функцією, що й бібліотеку |
| символ на схемі без футпринта | порожнє поле `Footprint` | `lab2:<ім'я футпринта>` |

## Приклад
Вхід: `/create-schematic`
```text
schematic: CREATED hardware/sym-lib-table
schematic: CREATED hardware/fp-lib-table
schematic: CREATED hardware/lab2.kicad_pro
schematic: CREATED hardware/lab2.kicad_sch
ERC: Found 0 violations
```
