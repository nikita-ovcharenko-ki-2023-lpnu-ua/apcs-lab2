"""Shared helpers: project paths, deterministic UUIDs, pin geometry."""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARAMS = ROOT / 'params' / 'board.json'
HW = ROOT / 'hardware'
LIB_NAME = 'lab2'
SYM_LIB = HW / 'lib' / f'{LIB_NAME}.kicad_sym'
FP_LIB = HW / 'lib' / f'{LIB_NAME}.pretty'
PROJECT = HW / f'{LIB_NAME}.kicad_pro'
SCHEMATIC = HW / f'{LIB_NAME}.kicad_sch'
BOARD = HW / f'{LIB_NAME}.kicad_pcb'
OUTPUT = ROOT / 'output'

BOARD_W, BOARD_H = 85.6, 53.98          # credit-card form factor, mm
SCH_GRID = 2.54                          # schematic connection grid, mm
SYM_PITCH = 5.08                         # pin pitch of U1..U5 symbols, mm
PIN_LEN = 5.08                           # symbol pin length, mm
HEADER_PITCH = 2.54                      # J1 pin pitch, mm

_NS = uuid.uuid5(uuid.NAMESPACE_URL, 'apcs-lab2')


def uid(*parts) -> str:
    """Deterministic UUID, so regenerated files are byte-identical."""
    return str(uuid.uuid5(_NS, '/'.join(str(p) for p in parts)))


def load_params() -> dict:
    if not PARAMS.exists():
        raise SystemExit(f'error: {PARAMS.relative_to(ROOT)} not found, run tools/params.py first')
    return json.loads(PARAMS.read_text(encoding='utf-8'))


def fp_name(comp: dict) -> str:
    n = comp['size_mm']
    return f"{comp['ref']}_{n}x{n}mm"


def side_positions(n_pins: int, length: float, pitch: float | None = None):
    """Pin positions for a square part, counter-clockwise from the top-left pin.

    Returns a list of (side, offset) where side is 'L', 'B', 'R', 'T' and offset
    is measured along the side from its centre (top->bottom on L, left->right on B,
    bottom->top on R, right->left on T). With pitch=None the side is split evenly.
    """
    if n_pins % 4:
        raise ValueError('pin count must be a multiple of 4')
    k = n_pins // 4
    step = pitch if pitch is not None else length / k
    offsets = [(i - (k - 1) / 2) * step for i in range(k)]
    result = []
    for side in 'LBRT':
        result.extend((side, off) for off in offsets)
    return result


def write_if_changed(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding='utf-8') == text:
        return 'SKIP'
    state = 'UPDATED' if path.exists() else 'CREATED'
    path.write_text(text, encoding='utf-8')
    return state


def fmt(v: float) -> str:
    s = f'{v:.4f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s
