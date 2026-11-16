#!/usr/bin/env python3
"""Stage 2: symbol and footprint library for U1..U5 and the edge connector J1.

Footprints: square body of exactly size_mm x size_mm (F.Fab), through-hole pads
centred on the body edges, counter-clockwise numbering from the top-left pin.
Symbols: a square box with the same pin order; pin name = GUID character.
"""
import sys

from common import (FP_LIB, HEADER_PITCH, LIB_NAME, PIN_LEN, ROOT, SCH_GRID, SYM_LIB, SYM_PITCH, fmt,
                    fp_name, load_params, side_positions, write_if_changed)

PAD_D, DRILL = 1.4, 0.8              # component pads, mm
HDR_PAD, HDR_DRILL = 1.7, 1.0        # J1 pads, mm
FONT = '(effects (font (size 1 1) (thickness 0.15)))'


def pad_xy(side: str, off: float, half: float):
    return {'L': (-half, off), 'B': (off, half), 'R': (half, -off), 'T': (-off, -half)}[side]


def footprint_component(comp: dict) -> str:
    size = comp['size_mm']
    half = size / 2
    silk = half + PAD_D / 2 + 0.25
    crt = half + PAD_D / 2 + 0.5
    name = fp_name(comp)
    lines = [
        f'(footprint "{name}"',
        '  (version 20240108)',
        '  (generator "lab2-tools")',
        '  (layer "F.Cu")',
        f'  (descr "Square part {size}x{size} mm, {len(comp["pins"])} pins, GUID group {comp["group"]}")',
        f'  (property "Reference" "REF**" (at 0 {fmt(-crt - 1)} 0) (layer "F.SilkS") {FONT})',
        f'  (property "Value" "{name}" (at 0 {fmt(crt + 1)} 0) (layer "F.Fab") {FONT})',
        '  (attr through_hole)',
        f'  (fp_rect (start {fmt(-half)} {fmt(-half)}) (end {fmt(half)} {fmt(half)}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))',
        f'  (fp_rect (start {fmt(-silk)} {fmt(-silk)}) (end {fmt(silk)} {fmt(silk)}) (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS"))',
        f'  (fp_circle (center {fmt(-silk - 0.6)} {fmt(-silk - 0.6)}) (end {fmt(-silk - 0.3)} {fmt(-silk - 0.6)}) (stroke (width 0.12) (type solid)) (fill solid) (layer "F.SilkS"))',
        f'  (fp_rect (start {fmt(-crt)} {fmt(-crt)}) (end {fmt(crt)} {fmt(crt)}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))',
        f'  (fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") {FONT})',
    ]
    for pin, (side, off) in zip(comp['pins'], side_positions(len(comp['pins']), size)):
        x, y = pad_xy(side, off, half)
        shape = 'rect' if pin['number'] == 1 else 'circle'
        lines.append(f'  (pad "{pin["number"]}" thru_hole {shape} (at {fmt(x)} {fmt(y)}) (size {PAD_D} {PAD_D}) '
                     f'(drill {DRILL}) (layers "*.Cu" "*.Mask"))')
    lines.append(')')
    return '\n'.join(lines) + '\n'


def footprint_header(n: int) -> str:
    top = -(n - 1) * HEADER_PITCH / 2
    w = HEADER_PITCH / 2 + 0.25
    lines = [
        f'(footprint "J1_1x{n:02d}_P2.54mm"',
        '  (version 20240108)',
        '  (generator "lab2-tools")',
        '  (layer "F.Cu")',
        f'  (descr "Edge connector for the free pins, 1x{n}, pitch 2.54 mm")',
        f'  (property "Reference" "REF**" (at 0 {fmt(top - 2.5)} 0) (layer "F.SilkS") {FONT})',
        f'  (property "Value" "J1_1x{n:02d}" (at 0 {fmt(-top + 2.5)} 0) (layer "F.Fab") {FONT})',
        '  (attr through_hole)',
        f'  (fp_rect (start {fmt(-w)} {fmt(top - w)}) (end {fmt(w)} {fmt(-top + w)}) (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS"))',
        f'  (fp_rect (start {fmt(-w - 0.3)} {fmt(top - w - 0.3)}) (end {fmt(w + 0.3)} {fmt(-top + w + 0.3)}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))',
        f'  (fp_rect (start {fmt(-w + 0.1)} {fmt(top - w + 0.1)}) (end {fmt(w - 0.1)} {fmt(-top + w - 0.1)}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))',
    ]
    for i in range(n):
        shape = 'rect' if i == 0 else 'oval'
        lines.append(f'  (pad "{i + 1}" thru_hole {shape} (at 0 {fmt(top + i * HEADER_PITCH)}) (size {HDR_PAD} {HDR_PAD}) '
                     f'(drill {HDR_DRILL}) (layers "*.Cu" "*.Mask"))')
    lines.append(')')
    return '\n'.join(lines) + '\n'


def sym_text(value, at, hide=False, size=1.27):
    h = ' (hide yes)' if hide else ''
    return f'(at {fmt(at[0])} {fmt(at[1])} 0) (effects (font (size {size} {size})){h})'


def symbol_component(comp: dict) -> str:
    n = len(comp['pins'])
    k = n // 4
    half = k * SYM_PITCH / 2 + SYM_PITCH / 2
    end = half + PIN_LEN
    name = comp['ref']
    out = [
        f'  (symbol "{name}" (pin_names (offset 0.508)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
        f'    (property "Reference" "U" {sym_text("U", (0, half + 1.27))})',
        f'    (property "Value" "{name}" {sym_text(name, (0, -half - 1.27))})',
        f'    (property "Footprint" "{LIB_NAME}:{fp_name(comp)}" {sym_text("", (0, 0), hide=True)})',
        f'    (property "Datasheet" "" {sym_text("", (0, 0), hide=True)})',
        f'    (property "Description" "Square part {comp["size_mm"]}x{comp["size_mm"]} mm, GUID group {comp["group"]}" {sym_text("", (0, 0), hide=True)})',
        f'    (symbol "{name}_0_1" (rectangle (start {fmt(-half)} {fmt(half)}) (end {fmt(half)} {fmt(-half)}) '
        '(stroke (width 0.254) (type default)) (fill (type background))))',
        f'    (symbol "{name}_1_1"',
    ]
    for pin, (side, off) in zip(comp['pins'], side_positions(n, 0, pitch=SYM_PITCH)):
        # library coordinates: Y axis points up
        x, y, angle = {'L': (-end, -off, 0), 'B': (off, -end, 90),
                       'R': (end, off, 180), 'T': (-off, end, 270)}[side]
        out.append(f'      (pin passive line (at {fmt(x)} {fmt(y)} {angle}) (length {PIN_LEN}) '
                   f'(name "{pin["symbol"]}" (effects (font (size 1.27 1.27)))) '
                   f'(number "{pin["number"]}" (effects (font (size 1.27 1.27)))))')
    out.append('    )')
    out.append('  )')
    return '\n'.join(out)


def symbol_header(n: int) -> str:
    top = (n - 1) * SCH_GRID / 2
    out = [
        '  (symbol "J1" (pin_names (offset 1.016) (hide yes)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
        f'    (property "Reference" "J" {sym_text("J", (0, top + 2.54))})',
        f'    (property "Value" "J1" {sym_text("J1", (0, -top - 2.54))})',
        f'    (property "Footprint" "{LIB_NAME}:J1_1x{n:02d}_P2.54mm" {sym_text("", (0, 0), hide=True)})',
        f'    (property "Datasheet" "" {sym_text("", (0, 0), hide=True)})',
        f'    (property "Description" "Edge connector for the free pins" {sym_text("", (0, 0), hide=True)})',
        f'    (symbol "J1_0_1" (rectangle (start -1.27 {fmt(top + 1.27)}) (end 1.27 {fmt(-top - 1.27)}) '
        '(stroke (width 0.254) (type default)) (fill (type background))))',
        '    (symbol "J1_1_1"',
    ]
    for i in range(n):
        out.append(f'      (pin passive line (at 3.81 {fmt(top - i * SCH_GRID)} 180) (length 2.54) '
                   f'(name "{i + 1}" (effects (font (size 1.27 1.27)))) (number "{i + 1}" (effects (font (size 1.27 1.27)))))')
    out.append('    )')
    out.append('  )')
    return '\n'.join(out)


def main() -> int:
    params = load_params()
    report = []
    for comp in params['components']:
        path = FP_LIB / f'{fp_name(comp)}.kicad_mod'
        report.append((write_if_changed(path, footprint_component(comp)), path))
    n_free = len(params['connector']['pins'])
    path = FP_LIB / f'J1_1x{n_free:02d}_P2.54mm.kicad_mod'
    report.append((write_if_changed(path, footprint_header(n_free)), path))

    symbols = [symbol_component(c) for c in params['components']] + [symbol_header(n_free)]
    lib = '(kicad_symbol_lib\n  (version 20231120)\n  (generator "lab2-tools")\n' + '\n'.join(symbols) + '\n)\n'
    report.append((write_if_changed(SYM_LIB, lib), SYM_LIB))
    for state, path in report:
        print(f'library: {state:<7} {path.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
