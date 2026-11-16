---
name: fab-output
description: Runs ERC and DRC (with schematic parity) and generates Gerber RS-274X, Excellon drill files, an archive and schematic/board images for the report; also the CI script and GitHub Actions workflow that repeat the checks in the official KiCad container. Use after autoroute or when /fab is run.
---

# Skill: fab-output

Skill не містить готових файлів: агент пише `tools/fab.py`, `ci.sh` і
`.github/workflows/ci.yml` за вимогами нижче.

## Коли застосовувати
- Плата розведена (`/route`), потрібні звіти й виробничі файли.
- Користувач запускає `/fab` або оркестратор `/build-board`.

## Входи
| Параметр | Значення |
|---|---|
| `schematic`, `board` | `hardware/lab2.kicad_sch`, `hardware/lab2.kicad_pcb` |
| `layers` | `F.Cu, B.Cu, F.Mask, B.Mask, F.Silkscreen, B.Silkscreen, Edge.Cuts` |
| `kicadImage` | офіційний образ `kicad/kicad:<версія локального KiCad>` |

## Виходи
| Файл | Що містить |
|---|---|
| `tools/fab.py` | скрипт звітів і виробничих файлів |
| `output/erc.json`, `output/drc.json` | звіти ERC і DRC |
| `output/gerbers/` | Gerber RS-274X шари, Excellon `.drl`, карта свердління, job-файл |
| `output/lab2-gerbers.zip` | архів для виробника |
| `output/images/` | схема і плата (PDF, PNG), SVG плати, 3D-рендер |
| `ci.sh`, `.github/workflows/ci.yml` | CI |

## Вимоги
### `tools/fab.py`
1. ERC: `kicad-cli sch erc --format json --severity-all --exit-code-violations`.
2. DRC: `kicad-cli pcb drc --format json --severity-all --schematic-parity --exit-code-violations`.
   Рахуються `violations`, `unconnected_items` і `schematic_parity`.
3. Будь-яке порушення ERC/DRC → помилка, Gerber **не** генерується.
4. Gerber: `kicad-cli pcb export gerbers --layers <layers> --no-x2` (класичний
   RS-274X з `%FS…%` і `%MO…%`); свердління — Excellon у мм і карта свердління.
   Каталог `output/gerbers/` перед генерацією очищується (тільки він).
5. Архів `output/lab2-gerbers.zip` з усіма файлами каталогу.
6. Зображення: PDF схеми, PDF і SVG плати (шари міді, шовкографія, контур;
   SVG — лише область плати), 3D-рендер верхньої сторони; PNG з PDF через
   `pdftoppm`, якщо він є. Прапорець `--no-render` пропускає 3D-рендер (у CI немає GPU).

### `ci.sh` і workflow
7. `ci.sh` (bash, `set -euo pipefail`, LF, 755): друкує версію KiCad, запускає
   `python3 tools/fab.py --no-render`, потім `python3 .github/agent-tools/check.py`.
   Трасування в CI не виконується — перевіряється закомічена розведена плата.
8. Workflow `CI`: `push` і `pull_request` на `develop`, `master`, а також
   `workflow_dispatch`; `permissions: contents: read`; одна job у контейнері
   `kicad/kicad:<версія>` з `options: --user root`; кроки: checkout (остання
   мажорна версія), `bash ./ci.sh`, завантаження `output/` як артефакту
   `lab2-fab` (`if-no-files-found: error`). Без `secrets.*`.

## Кроки
1. Написати `tools/fab.py`; запустити.
2. Написати `ci.sh` і workflow; запустити `./ci.sh` локально.

## Перевірки
```bash
python3 tools/fab.py           # "ERC 0 violation(s), DRC 0 violation(s)", 10 файлів у output/gerbers
head -12 output/gerbers/lab2-F_Cu.gtl | grep -E '^%FS|^%MO'   # RS-274X заголовок
./ci.sh                        # останній рядок "ci: OK"
```

## Типовий сценарій помилки
| Симптом | Причина | Дія |
|---|---|---|
| `kicad-cli … exit 5` | знайдено порушення з `--exit-code-violations` | читати JSON-звіт, виправити причину на відповідному етапі |
| Gerber без `%FS`/`%MO` у перших рядках | вимкнено формат RS-274X / неправильний шар | перевірити `--layers`, не використовувати застарілі формати |
| CI: `permission denied` у контейнері | образ KiCad працює не від root | `options: --user root` |
| CI: `ModuleNotFoundError: pcbnew` | запуск не системним Python | `python3` з образу KiCad |
| 3D-рендер падає без дисплея | немає GPU/X у CI | рендер лише локально; у CI — `--no-render` або пропуск |

## Приклад
Вхід: `/fab`
```text
fab: ERC 0 violation(s), DRC 0 violation(s)
fab: 10 files in output/gerbers: lab2-B_Cu.gbl, ..., lab2.drl
fab: archive output/lab2-gerbers.zip; images in output/images
```
