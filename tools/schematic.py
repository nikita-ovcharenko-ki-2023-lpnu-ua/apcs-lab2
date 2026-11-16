#!/usr/bin/env python3
"""Stage 3: KiCad project and schematic.

Every pin gets a short wire stub and a net label; pins with the same GUID
character share a label (= are connected). Free pins are wired by FREE_* labels
to J1, which sits on the left edge of the sheet. The generated file is upgraded
to the native KiCad format with `kicad-cli sch upgrade`, then ERC is run.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import library
from common import (HW, LIB_NAME, PIN_LEN, PROJECT, ROOT, SCH_GRID, SCHEMATIC, SYM_PITCH, fmt, load_params,
                    side_positions, uid, write_if_changed)

TEMPLATE_PRO = Path('/usr/share/kicad/template/kicad.kicad_pro')
STUB = 2 * SCH_GRID
# instance positions on the A4 sheet (multiples of 2.54 mm); J1 on the left edge
LAYOUT = {'J1': (25.4, 101.6), 'U1': (88.9, 63.5), 'U2': (152.4, 63.5), 'U3': (215.9, 63.5),
          'U4': (88.9, 139.7), 'U5': (177.8, 139.7)}


def lib_tables() -> dict:
    sym = ('(sym_lib_table\n  (version 7)\n'
           f'  (lib (name "{LIB_NAME}")(type "KiCad")(uri "${{KIPRJMOD}}/lib/{LIB_NAME}.kicad_sym")(options "")(descr "Lab 2 parts"))\n)\n')
    fp = ('(fp_lib_table\n  (version 7)\n'
          f'  (lib (name "{LIB_NAME}")(type "KiCad")(uri "${{KIPRJMOD}}/lib/{LIB_NAME}.pretty")(options "")(descr "Lab 2 footprints"))\n)\n')
    return {HW / 'sym-lib-table': sym, HW / 'fp-lib-table': fp}


def project_text() -> str:
    data = json.loads(TEMPLATE_PRO.read_text(encoding='utf-8'))
    data['meta']['filename'] = PROJECT.name
    return json.dumps(data, indent=2) + '\n'


def pin_points(comp_ref: str, n_pins: int):
    """Sheet coordinates of pin ends and outward direction for every pin."""
    x0, y0 = LAYOUT[comp_ref]
    k = n_pins // 4
    half = k * SYM_PITCH / 2 + SYM_PITCH / 2
    end = half + PIN_LEN
    points = []
    for side, off in side_positions(n_pins, 0, pitch=SYM_PITCH):
        lx, ly = {'L': (-end, -off), 'B': (off, -end), 'R': (end, off), 'T': (-off, end)}[side]
        direction = {'L': (-1, 0), 'B': (0, 1), 'R': (1, 0), 'T': (0, -1)}[side]
        points.append(((x0 + lx, y0 - ly), direction, side))
    return points


def header_points(n: int):
    x0, y0 = LAYOUT['J1']
    top = (n - 1) * SCH_GRID / 2
    return [((x0 + 3.81, y0 - (top - i * SCH_GRID)), (1, 0), 'R') for i in range(n)]


def label_corner(ref, n_pins):
    """Reference/Value positions in the free corners of the symbol (pins sit mid-side)."""
    x, y = LAYOUT[ref]
    if ref == 'J1':
        top = (n_pins - 1) * SCH_GRID / 2 + SCH_GRID
        return (x, y - top - SCH_GRID), (x, y + top + SCH_GRID)
    half = n_pins // 4 * SYM_PITCH / 2 + SYM_PITCH / 2
    d = half + SCH_GRID
    return (x + d, y - d), (x + d, y + d)


def instance(ref, lib_id, value, footprint, n_pins, root_uuid):
    x, y = LAYOUT[ref]
    (rx, ry), (vx, vy) = label_corner(ref, n_pins)
    pins = '\n'.join(f'    (pin "{i}" (uuid "{uid("pin", ref, i)}"))' for i in range(1, n_pins + 1))
    return f'''  (symbol (lib_id "{lib_id}") (at {fmt(x)} {fmt(y)} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
    (uuid "{uid("symbol", ref)}")
    (property "Reference" "{ref}" (at {fmt(rx)} {fmt(ry)} 0) (effects (font (size 1.524 1.524) (bold yes)) (justify left)))
    (property "Value" "{value}" (at {fmt(vx)} {fmt(vy)} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "{footprint}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Description" "" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))
{pins}
    (instances (project "{LIB_NAME}" (path "/{root_uuid}" (reference "{ref}") (unit 1))))
  )'''


def stub_and_label(point, direction, side, net, key):
    (x, y), (dx, dy) = point, direction
    x2, y2 = x + dx * STUB, y + dy * STUB
    angle = {'L': 180, 'R': 0, 'T': 90, 'B': 270}[side]
    justify = {'L': 'right bottom', 'R': 'left bottom', 'T': 'left bottom', 'B': 'right bottom'}[side]
    return (f'  (wire (pts (xy {fmt(x)} {fmt(y)}) (xy {fmt(x2)} {fmt(y2)})) (stroke (width 0) (type default)) (uuid "{uid("wire", key)}"))\n'
            f'  (label "{net}" (at {fmt(x2)} {fmt(y2)} {angle}) (effects (font (size 1.27 1.27)) (justify {justify})) (uuid "{uid("label", key)}"))')


def schematic_text(params: dict) -> str:
    root = uid('schematic')
    pin_net = {}
    for net in params['nets']:
        for p in net['pins']:
            if not p.startswith('J1.'):
                pin_net.setdefault(p, net['name'])
    j1_pins = params['connector']['pins']

    lib_syms = [library.symbol_component(c).replace(f'(symbol "{c["ref"]}"', f'(symbol "{LIB_NAME}:{c["ref"]}"', 1)
                for c in params['components']]
    lib_syms.append(library.symbol_header(len(j1_pins)).replace('(symbol "J1"', f'(symbol "{LIB_NAME}:J1"', 1))

    body = []
    for comp in params['components']:
        n = len(comp['pins'])
        body.append(instance(comp['ref'], f'{LIB_NAME}:{comp["ref"]}', comp['ref'],
                             f'{LIB_NAME}:{library.fp_name(comp)}', n, root))
        for pin, (pt, d, side) in zip(comp['pins'], pin_points(comp['ref'], n)):
            ref = f'{comp["ref"]}.{pin["number"]}'
            body.append(stub_and_label(pt, d, side, pin_net[ref], ref))
    body.append(instance('J1', f'{LIB_NAME}:J1', 'J1', f'{LIB_NAME}:J1_1x{len(j1_pins):02d}_P2.54mm', len(j1_pins), root))
    for pin, (pt, d, side) in zip(j1_pins, header_points(len(j1_pins))):
        body.append(stub_and_label(pt, d, side, pin['net'], f'J1.{pin["number"]}'))

    title = f'Lab 2: GUID {params["guid"]}'
    return (f'(kicad_sch (version 20231120) (generator "lab2-tools")\n'
            f'  (uuid "{root}")\n  (paper "A4")\n'
            f'  (title_block (title "{title}") (date "2026-11-16") (rev "1"))\n'
            '  (lib_symbols\n' + '\n'.join(lib_syms) + '\n  )\n'
            + '\n'.join(body) +
            '\n  (sheet_instances (path "/" (page "1")))\n)\n')


def upgraded(text: str) -> str:
    """Return the schematic in the native format written by kicad-cli."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for path, content in lib_tables().items():
            (tmp_dir / path.name).write_text(content, encoding='utf-8')
        shutil.copytree(HW / 'lib', tmp_dir / 'lib')
        sch = tmp_dir / SCHEMATIC.name
        sch.write_text(text, encoding='utf-8')
        (tmp_dir / PROJECT.name).write_text(project_text(), encoding='utf-8')
        r = subprocess.run(['kicad-cli', 'sch', 'upgrade', '--force', str(sch)], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f'schematic: error: kicad-cli sch upgrade failed: {r.stderr.strip() or r.stdout.strip()}')
        return sch.read_text(encoding='utf-8')


def main() -> int:
    params = load_params()
    if not (HW / 'lib').exists():
        raise SystemExit('schematic: error: run tools/library.py first')
    files = dict(lib_tables())
    if not PROJECT.exists():
        files[PROJECT] = project_text()
    files[SCHEMATIC] = upgraded(schematic_text(params))
    for path, text in files.items():
        print(f'schematic: {write_if_changed(path, text):<7} {path.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
