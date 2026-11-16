# Докази перевірки результату

## Локально (Linux Mint 22.3, KiCad 10.0.8, Freerouting CLI 2.5.0)
| Перевірка | Команда | Результат |
|---|---|---|
| Параметри | `python3 tools/params.py "<ПІБ>"` | GUID `24f9653f-a875-5d8f-9242-e476d2f1079a`, U1 8×8, U2–U4 4×4, U5 12×12 мм |
| ERC | `kicad-cli sch erc --severity-all` | 0 violations |
| DRC | `kicad-cli pcb drc --severity-all --schematic-parity` | 0 violations, 0 unconnected, 0 parity issues |
| Трасування | `python3 tools/route.py` | 22 з'єднання, 0 нерозведених, обидва шари, 0 via, ≈ 291 мм доріжок |
| Кути | `check.py --only routing` | мінімальний внутрішній кут 90° |
| Gerber | `python3 tools/fab.py` | 7 шарів RS-274X (`%FSLAX46Y46*%`, `%MOMM*%`) + Excellon + карта свердління |
| Повна перевірка | `python3 .github/agent-tools/check.py` | 45 passed, 0 failed |
| Ідемпотентність | повторний `/build-board` + SHA-256 | жоден файл не змінився |
| Зламана перевірка | видалено одну доріжку | `unconnected_items: 1`, exit code 1 |

## GitHub Actions (контейнер kicad/kicad:10.0.8)
| Run | Результат |
|---|---|
| [43811671356](https://github.com/nikita-ovcharenko-ki-2023-lpnu-ua/apcs-lab2/actions/runs/43811671356) | success, 45/45, артефакт `lab2-fab` |
| [43811839347](https://github.com/nikita-ovcharenko-ki-2023-lpnu-ua/apcs-lab2/actions/runs/43811839347) | success, 45/45, артефакт `lab2-fab` |

Pull request: [#1 lab2/finish](https://github.com/nikita-ovcharenko-ki-2023-lpnu-ua/apcs-lab2/pull/1).
