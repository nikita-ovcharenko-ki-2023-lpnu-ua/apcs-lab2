#!/usr/bin/env python3
"""Stage 4: board outline, design rules, footprints, nets and placement.

Placement rule from the task: the more connections two parts share, the closer
they are. It is solved as minimisation of the total half-perimeter wire length
(HPWL) of all nets over a grid of positions and 4 rotations, with courtyards
kept apart by a routing gap. J1 is fixed on the left (short) edge.
"""
import itertools
import math
import sys

import pcbnew

import library
from common import (BOARD, BOARD_H, BOARD_W, FP_LIB, LIB_NAME, PROJECT, ROOT, SCHEMATIC,
                    load_params, uid)

ORIGIN = (30.0, 30.0)            # top-left corner of the board on the page, mm
EDGE_MARGIN = 2.0                # courtyard to board edge, mm
GAP = 2.5                        # courtyard to courtyard, mm (routing channel)
GRID = 1.0                       # placement grid, mm
RULES = {'track': 0.3, 'clearance': 0.25, 'via_d': 0.8, 'via_drill': 0.4}
MM = pcbnew.FromMM


def rotate(x, y, deg):
    a = math.radians(deg)
    # KiCad: positive angle is counter-clockwise on screen (Y axis points down)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


class Part:
    def __init__(self, ref, fp_name, pads, half):
        self.ref, self.fp_name, self.pads, self.half = ref, fp_name, pads, half
        self.x = self.y = 0.0
        self.rot = 0

    def pad_xy(self, number):
        px, py = self.pads[number]
        rx, ry = rotate(px, py, self.rot)
        return self.x + rx, self.y + ry


def load_parts(params):
    parts = {}
    names = [(c['ref'], library.fp_name(c)) for c in params['components']]
    names.append(('J1', f"J1_1x{len(params['connector']['pins']):02d}_P2.54mm"))
    for ref, name in names:
        fp = pcbnew.FootprintLoad(str(FP_LIB), name)
        pads = {int(p.GetNumber()): (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)) for p in fp.Pads()}
        crt = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        half = (pcbnew.ToMM(crt.GetWidth()) / 2, pcbnew.ToMM(crt.GetHeight()) / 2)
        parts[ref] = Part(ref, name, pads, half)
    return parts


def nets_by_part(params):
    nets = []
    for net in params['nets']:
        nets.append([(p.split('.')[0], int(p.split('.')[1])) for p in net['pins']])
    return nets


def hpwl(parts, nets, placed):
    total = 0.0
    for net in nets:
        pts = [parts[r].pad_xy(n) for r, n in net if r in placed]
        if len(pts) > 1:
            xs, ys = zip(*pts)
            total += (max(xs) - min(xs)) + (max(ys) - min(ys))
    return total


def extent(part):
    hw, hh = part.half
    return (hh, hw) if part.rot % 180 else (hw, hh)


def fits(part, parts, placed):
    hw, hh = extent(part)
    if part.x - hw < EDGE_MARGIN or part.x + hw > BOARD_W - EDGE_MARGIN:
        return False
    if part.y - hh < EDGE_MARGIN or part.y + hh > BOARD_H - EDGE_MARGIN:
        return False
    for ref in placed:
        other = parts[ref]
        ow, oh = extent(other)
        if abs(part.x - other.x) < hw + ow + GAP and abs(part.y - other.y) < hh + oh + GAP:
            return False
    return True


def place(parts, nets):
    j1 = parts['J1']
    j1.x, j1.y = EDGE_MARGIN + j1.half[0], BOARD_H / 2
    placed = ['J1']
    weight = {r: sum(1 for net in nets for rr, _ in net if rr == r) for r in parts}
    order = sorted((r for r in parts if r != 'J1'), key=lambda r: -weight[r])
    xs = [EDGE_MARGIN + i * GRID for i in range(int((BOARD_W - 2 * EDGE_MARGIN) / GRID) + 1)]
    ys = [EDGE_MARGIN + i * GRID for i in range(int((BOARD_H - 2 * EDGE_MARGIN) / GRID) + 1)]

    def best_spot(part, placed_now):
        best = None
        for rot, x, y in itertools.product((0, 90, 180, 270), xs, ys):
            part.x, part.y, part.rot = x, y, rot
            if not fits(part, parts, placed_now):
                continue
            cost = hpwl(parts, nets, placed_now + [part.ref])
            if best is None or cost < best[0] - 1e-9:
                best = (cost, x, y, rot)
        if best is None:
            raise SystemExit(f'pcb: error: no room for {part.ref} on the board')
        _, part.x, part.y, part.rot = best

    for ref in order:
        best_spot(parts[ref], placed)
        placed.append(ref)
    # local improvement: re-place every part while the others stay fixed
    for _ in range(3):
        before = hpwl(parts, nets, placed)
        for ref in order:
            others = [r for r in placed if r != ref]
            best_spot(parts[ref], others)
        if hpwl(parts, nets, placed) >= before - 1e-6:
            break
    return hpwl(parts, nets, placed)


def build_board(params, parts):
    board = pcbnew.NewBoard(str(BOARD))
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetTrackWidth(MM(RULES['track']))
    nc.SetClearance(MM(RULES['clearance']))
    nc.SetViaDiameter(MM(RULES['via_d']))
    nc.SetViaDrill(MM(RULES['via_drill']))

    ox, oy = ORIGIN
    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(pcbnew.VECTOR2I(MM(ox), MM(oy)))
    rect.SetEnd(pcbnew.VECTOR2I(MM(ox + BOARD_W), MM(oy + BOARD_H)))
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(MM(0.1))
    board.Add(rect)

    netinfo = {}
    for net in params['nets']:
        # schematic labels are local to the root sheet, so KiCad names the nets "/<label>"
        item = pcbnew.NETINFO_ITEM(board, f"/{net['name']}")
        board.Add(item)
        netinfo[net['name']] = item
    pin_net = {p: n['name'] for n in params['nets'] for p in n['pins']}

    for ref, part in parts.items():
        fp = pcbnew.FootprintLoad(str(FP_LIB), part.fp_name)
        fp.SetParent(board)
        fp.SetFPID(pcbnew.LIB_ID(LIB_NAME, part.fp_name))
        fp.SetReference(ref)
        fp.SetValue(ref)
        fp.SetPath(pcbnew.KIID_PATH(f'/{uid("symbol", ref)}'))
        fp.SetSheetfile(SCHEMATIC.name)
        fp.SetSheetname('Root')
        fp.SetPosition(pcbnew.VECTOR2I(MM(ox + part.x), MM(oy + part.y)))
        fp.SetOrientationDegrees(part.rot)
        for pad in fp.Pads():
            name = pin_net.get(f'{ref}.{pad.GetNumber()}')
            if name:
                pad.SetNet(netinfo[name])
        board.Add(fp)
    return board


def main() -> int:
    params = load_params()
    if not SCHEMATIC.exists():
        raise SystemExit('pcb: error: run tools/schematic.py first')
    if BOARD.exists():
        existing = pcbnew.LoadBoard(str(BOARD))
        if len(existing.GetTracks()) > 0:
            print(f'pcb: SKIP    {BOARD.relative_to(ROOT)} (already routed; delete tracks to re-place)')
            return 0
    parts = load_parts(params)
    nets = nets_by_part(params)
    cost = place(parts, nets)
    board = build_board(params, parts)
    pcbnew.SaveBoard(str(BOARD), board)
    for ref, p in parts.items():
        print(f'pcb: {ref:<3} at ({p.x:5.1f}, {p.y:5.1f}) mm, rot {p.rot:3d}')
    print(f'pcb: total HPWL {cost:.1f} mm; board {BOARD_W} x {BOARD_H} mm; saved {BOARD.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
