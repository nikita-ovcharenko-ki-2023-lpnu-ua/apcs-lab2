#!/usr/bin/env python3
"""Stage 1: GUID from the full name -> component sizes, pins and nets.

Usage: python3 tools/params.py "<Прізвище Ім'я По батькові>" [-o params/board.json]
"""
import argparse
import json
import sys
import uuid
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / 'params' / 'board.json'
NAMESPACE = 'NAMESPACE_DNS'


def derive(full_name: str) -> dict:
    name = ' '.join(full_name.split())
    if len(name.split(' ')) != 3:
        raise ValueError('full name must be "Прізвище Ім\'я По батькові" (3 words)')
    guid = str(uuid.uuid5(getattr(uuid, NAMESPACE), name))
    groups = guid.split('-')

    components = []
    for index, group in enumerate(groups, start=1):
        components.append({
            'ref': f'U{index}',
            'group': group,
            'size_mm': len(group),
            'pins': [{'number': n, 'symbol': ch} for n, ch in enumerate(group, start=1)],
        })

    occurrences = OrderedDict()
    for comp in components:
        for pin in comp['pins']:
            occurrences.setdefault(pin['symbol'], []).append(f"{comp['ref']}.{pin['number']}")

    nets, free = [], []
    for symbol in sorted(occurrences):
        pins = occurrences[symbol]
        if len(pins) >= 2:
            nets.append({'name': f'N_{symbol}', 'symbol': symbol, 'pins': pins})
        else:
            free.append({'pin': pins[0], 'symbol': symbol})

    connector = {
        'ref': 'J1',
        'pins': [{'number': i, 'net': f"FREE_{f['pin'].replace('.', '_')}", 'to': f['pin']}
                 for i, f in enumerate(free, start=1)],
    }
    for pin in connector['pins']:
        nets.append({'name': pin['net'], 'symbol': None, 'pins': [pin['to'], f"J1.{pin['number']}"]})

    return {
        'full_name': name,
        'hash': f'uuid5({NAMESPACE}, full_name)',
        'guid': guid,
        'components': components,
        'free_pins': free,
        'connector': connector,
        'nets': nets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('full_name')
    parser.add_argument('-o', '--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    try:
        data = derive(args.full_name)
    except ValueError as err:
        print(f'params: error: {err}', file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if args.out.exists() and args.out.read_text(encoding='utf-8') == text:
        print(f'params: SKIP {args.out.relative_to(ROOT)} (unchanged)')
    else:
        args.out.write_text(text, encoding='utf-8')
        print(f'params: wrote {args.out.relative_to(ROOT)}')
    print(f"params: GUID {data['guid']}")
    for comp in data['components']:
        print(f"params: {comp['ref']} {comp['group']:<12} {comp['size_mm']}x{comp['size_mm']} mm, {len(comp['pins'])} pins")
    print(f"params: {sum(1 for n in data['nets'] if n['symbol'])} nets by symbol, {len(data['free_pins'])} free pins -> J1")
    return 0


if __name__ == '__main__':
    sys.exit(main())
