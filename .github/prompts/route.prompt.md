---
agent: pcb-engineer
description: Route the board on two layers with Freerouting via Specctra DSN/SES (autoroute skill).
---

# /route

Застосуй skill [autoroute](../skills/autoroute/SKILL.md).

## Передумови
- `/create-pcb` виконано.
- `freerouting-cli --help` працює (шлях — `~/.local/opt/freerouting/freerouting-cli` або змінна `FREEROUTING`).
- Якщо доріжки вже є — `SKIP`.

## Дії
1. Написати або перевірити `tools/route.py`; запустити.
2. DRC: 0 порушень, 0 нерозведених, 0 розбіжностей; перевірити кути й шари.

## Очікувані файли
- `hardware/lab2.kicad_pcb` з доріжками; `output/route/` (не в Git)

## Перевірки
```bash
kicad-cli pcb drc --format json --severity-all --schematic-parity --exit-code-violations -o output/drc.json hardware/lab2.kicad_pcb
python3 .github/agent-tools/check.py --only routing
```

## Повідомлення про помилку
- `route: FAIL — freerouting did not finish in 300 s`
- `route: FAIL — <n> unconnected item(s) after routing`
- `route: FAIL — acute corner at (<x>, <y>) mm`
