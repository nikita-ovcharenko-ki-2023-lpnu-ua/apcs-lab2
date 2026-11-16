---
agent: pcb-engineer
description: Derive GUID, component sizes, pins and nets from the student's full name (guid-params skill).
argument-hint: fullName="Прізвище Ім'я По батькові"
---

# /gen-params

Застосуй skill [guid-params](../skills/guid-params/SKILL.md). Параметр: `${input:fullName}`.

## Передумови
- `python3 --version` ≥ 3.10.
- Задано ПІБ із трьох слів (якщо не задано — запитати користувача).

## Дії
1. Написати або перевірити `tools/params.py` за розділом «Вимоги» skill.
2. Запустити `python3 tools/params.py "<fullName>"`.
3. Показати таблицю: компонент → група GUID → розмір → кількість пінів, і перелік мереж.

## Очікувані файли
- `tools/params.py`, `params/board.json`

## Перевірки
```bash
python3 -c "import json,uuid; d=json.load(open('params/board.json')); assert d['guid']==str(uuid.uuid5(uuid.NAMESPACE_DNS,d['full_name'])); print('PASS')"
```

## Повідомлення про помилку
- `gen-params: FAIL — full name must have 3 words`
- `gen-params: FAIL — GUID does not match uuid5(NAMESPACE_DNS, full_name)`
