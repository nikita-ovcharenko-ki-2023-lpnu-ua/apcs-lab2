---
name: guid-params
description: Derives the lab 2 design parameters from the student's full name - a deterministic GUID, five square parts (side = group length, pin = character), nets of equal characters and free pins for the edge connector. Use first, or when /gen-params is run.
---

# Skill: guid-params

Skill не містить готового коду: агент пише `tools/params.py` за вимогами нижче.

## Коли застосовувати
- Немає `params/board.json` або змінилося ПІБ.
- Користувач запускає `/gen-params` або оркестратор `/build-board`.

## Входи
| Параметр | Приклад | Опис |
|---|---|---|
| `fullName` | `Овчаренко Нікіта Андрійович` | Прізвище, Ім'я, По батькові — рівно три слова |

## Виходи
| Файл | Що містить |
|---|---|
| `tools/params.py` | скрипт розрахунку |
| `params/board.json` | ПІБ, спосіб хешування, GUID, компоненти, мережі, вільні піни, роз'єм |

## Вимоги
1. ПІБ нормалізується: зайві пробіли прибираються, слів має бути рівно 3.
2. GUID = `uuid5(NAMESPACE_DNS, ПІБ)` у нижньому регістрі (`8-4-4-4-12`). Це
   SHA-1-хеш імені: однаковий результат на будь-якій машині. У `board.json`
   записується і GUID, і рядок способу хешування.
3. Компонент `U<i>` відповідає i-й групі GUID (i = 1…5): `size_mm` = довжина
   групи, піни нумеруються 1…N у порядку символів групи, кожен пін зберігає свій символ.
4. Мережа — символ, що трапляється у GUID **щонайменше двічі** (у різних
   компонентах або в одному — «рівнозначні піни»). Назва мережі `N_<символ>`,
   список пінів у форматі `U<i>.<pin>`. Мережі впорядковані за символом.
5. Вільний пін — символ, що трапляється **один раз**. Кожен вільний пін отримує
   власний контакт роз'єму `J1` (нумерація 1…K у порядку символів) і мережу
   `FREE_U<i>_<pin>` з двома пінами: пін компонента і пін J1.
6. JSON записується в UTF-8 з відступом 2 і `ensure_ascii=False`; якщо вміст
   не змінився — файл не перезаписується (`SKIP`).
7. Скрипт друкує GUID, таблицю компонентів і кількість мереж / вільних пінів.

## Кроки
1. Написати `tools/params.py` (CLI: `python3 tools/params.py "<ПІБ>"`).
2. Запустити його з `fullName`.
3. Виконати перевірки.

## Перевірки
```bash
python3 tools/params.py "Овчаренко Нікіта Андрійович"     # друкує GUID і 5 компонентів
python3 -c "import json,uuid; d=json.load(open('params/board.json')); assert d['guid']==str(uuid.uuid5(uuid.NAMESPACE_DNS,d['full_name']))"
python3 -c "import json; d=json.load(open('params/board.json')); print([c['size_mm'] for c in d['components']])"   # -> [8, 4, 4, 4, 12]
```
Додатково: сума пінів усіх мереж = 32 + K (32 піни компонентів і K пінів J1),
кожен пін компонента входить рівно в одну мережу.

## Типовий сценарій помилки
| Симптом | Причина | Дія |
|---|---|---|
| інший GUID для того самого ПІБ | ім'я з подвійним пробілом або в іншому регістрі / порядку слів | нормалізувати пробіли; порядок «Прізвище Ім'я По батькові» |
| `UnicodeEncodeError` | запис JSON без UTF-8 | `encoding='utf-8'`, `ensure_ascii=False` |
| пін без мережі | символ, що трапився один раз, не перенесено на J1 | вимога 5 |
| символ з двох пінів одного компонента вважається вільним | лічильник рахує компоненти, а не входження | рахувати входження символів |

## Приклад
Вхід: `/gen-params fullName="Овчаренко Нікіта Андрійович"`
```text
params: GUID 24f9653f-a875-5d8f-9242-e476d2f1079a
params: U1 24f9653f     8x8 mm, 8 pins
params: U2 a875         4x4 mm, 4 pins
params: U3 5d8f         4x4 mm, 4 pins
params: U4 9242         4x4 mm, 4 pins
params: U5 e476d2f1079a 12x12 mm, 12 pins
params: 10 nets by symbol, 4 free pins -> J1
```
Повторний запуск: `params: SKIP params/board.json (unchanged)`.
