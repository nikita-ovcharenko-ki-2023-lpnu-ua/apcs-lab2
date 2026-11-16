---
name: kicad-pcb
description: Generates the credit-card sized two-layer KiCad board - outline, design rules, footprints with nets linked to the schematic, J1 on the short edge and connectivity-driven placement that minimises wire length. Use after kicad-schematic or when /create-pcb is run.
---

# Skill: kicad-pcb

Skill не містить готової плати: агент пише `tools/pcb.py` на модулі `pcbnew` KiCad.

## Коли застосовувати
- Є схема, але немає `hardware/lab2.kicad_pcb` або на платі ще немає доріжок.
- Користувач запускає `/create-pcb` або оркестратор `/build-board`.

## Входи
| Параметр | Значення |
|---|---|
| `params` | `params/board.json` |
| `footprints` | `hardware/lib/lab2.pretty/` |
| `boardSize` | ≤ 85.6 × 53.98 мм |
| `rules` | доріжка 0.3 мм, зазор 0.25 мм, перехідний отвір 0.8 / 0.4 мм |

## Виходи
| Файл | Що містить |
|---|---|
| `tools/pcb.py` | генератор плати і розміщення |
| `hardware/lab2.kicad_pcb` | плата без доріжок (ratsnest) |
| `hardware/lab2.kicad_pro` | оновлений KiCad правилами netclass `Default` |

## Вимоги
1. Контур — прямокутник на `Edge.Cuts` розміром **рівно 85.6 × 53.98 мм**
   (не більше форм-фактора кредитної картки), 2 шари міді.
2. Netclass `Default`: ширина доріжки 0.3 мм, зазор 0.25 мм, via 0.8 / 0.4 мм.
3. Футпринти завантажуються з `hardware/lib/lab2.pretty` (`FootprintLoad`),
   отримують `Reference`/`Value`, `LIB_ID lab2:<ім'я>` і **шлях до символу
   схеми** (`KIID_PATH "/<uuid символу>"` — той самий детермінований UUID, що в
   схемі), щоб DRC з `--schematic-parity` бачив відповідність.
4. Мережі створюються з `board.json` з префіксом `/` (`/N_2`, `/FREE_U5_1`) —
   саме так KiCad називає мережі локальних міток кореневого аркуша.
5. J1 — біля **лівої короткої сторони** (центр по вертикалі, courtyard за 2 мм від краю).
6. Розміщення U1–U5: «чим більше зв'язків, тим ближче» — мінімізація сумарної
   довжини HPWL (половина периметра рамки пінів кожної мережі) перебором
   позицій на сітці 1 мм і поворотів 0/90/180/270°; спочатку компоненти з
   більшою кількістю зв'язків, потім кілька проходів покращення. Courtyard
   компонентів — не ближче 2.5 мм один до одного (канал трасування) і 2 мм до краю.
7. Детермінованість: однакові входи → однакові позиції.
8. Якщо на наявній платі вже є доріжки — `SKIP` (не руйнувати розведену плату).
9. Скрипт друкує позиції, повороти і HPWL.

## Кроки
1. Написати `tools/pcb.py`; запустити.
2. DRC без доріжок: допускаються лише `unconnected_items`.

## Перевірки
```bash
python3 tools/pcb.py
kicad-cli pcb drc --format json --severity-all --schematic-parity -o output/drc.json hardware/lab2.kicad_pcb
# violations = 0, schematic_parity = 0, unconnected_items > 0 (ще не розведено)
```

## Типовий сценарій помилки
| Симптом | Причина | Дія |
|---|---|---|
| parity `net_conflict: Pad net (N_2) doesn't match (/N_2)` | мережі без префікса `/` | вимога 4 |
| parity `missing_footprint` / `extra_footprint` | у футпринта немає шляху до символу | вимога 3 (`SetPath`) |
| DRC `courtyards_overlap` | компоненти накладаються | перевірка відстані courtyard у розміщенні |
| `no room for Ux` | плата замала для розміщення з каналами | зменшити `GAP`, але не збільшувати плату |
| `pcbnew` не імпортується | KiCad не встановлено або інший Python | системний `/usr/bin/python3` з пакета KiCad |

## Приклад
Вхід: `/create-pcb`
```text
pcb: U1  at ( 31.0,  27.0) mm, rot 270
...
pcb: J1  at (  3.9,  27.0) mm, rot   0
pcb: total HPWL 295.4 mm; board 85.6 x 53.98 mm; saved hardware/lab2.kicad_pcb
```
