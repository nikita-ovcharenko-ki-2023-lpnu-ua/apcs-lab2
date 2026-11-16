#!/usr/bin/env python3
"""Stage 5: two-layer autorouting with Freerouting.

board.kicad_pcb -> Specctra DSN (pcbnew) -> freerouting-cli -> SES -> back into
the board. Freerouting routes at 0/45/90 degrees, so there are no acute corners.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pcbnew

from common import BOARD, OUTPUT, ROOT

FREEROUTING = Path(os.environ.get('FREEROUTING', Path.home() / '.local/opt/freerouting/freerouting-cli'))
PASSES = 30
TIMEOUT = 300


def strip_outlines(text: str) -> tuple[str, int]:
    """Remove (outline ...) expressions from component images.

    Freerouting 2.5.0 native build hangs on them (UnsupportedFeatureError while
    serialising ComponentOutline); outlines are not needed for routing.
    """
    out, i, removed = [], 0, 0
    while True:
        j = text.find('(outline', i)
        if j < 0:
            out.append(text[i:])
            return ''.join(out), removed
        out.append(text[i:j])
        depth, k = 0, j
        while True:
            depth += {'(': 1, ')': -1}.get(text[k], 0)
            if depth == 0:
                break
            k += 1
        i, removed = k + 1, removed + 1


def main() -> int:
    if not BOARD.exists():
        raise SystemExit('route: error: run tools/pcb.py first')
    board = pcbnew.LoadBoard(str(BOARD))
    if len(board.GetTracks()) > 0:
        print(f'route: SKIP    {BOARD.relative_to(ROOT)} (already has {len(board.GetTracks())} tracks)')
        return 0
    if not FREEROUTING.exists() and not shutil.which(str(FREEROUTING)):
        raise SystemExit(f'route: error: Freerouting not found at {FREEROUTING} (set FREEROUTING=...)')

    work = OUTPUT / 'route'
    work.mkdir(parents=True, exist_ok=True)
    dsn, ses = work / 'lab2.dsn', work / 'lab2.ses'
    ses.unlink(missing_ok=True)
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        raise SystemExit('route: error: Specctra DSN export failed')
    text, removed = strip_outlines(dsn.read_text(encoding='utf-8'))
    dsn.write_text(text, encoding='utf-8')
    print(f'route: exported {dsn.relative_to(ROOT)} ({removed} component outlines removed)')

    cmd = [str(FREEROUTING), '-de', str(dsn), '-do', str(ses),
           f'--router.autorouter.max_passes={PASSES}', '-mt', '1']
    print('route: ' + ' '.join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise SystemExit(f'route: error: freerouting did not finish in {TIMEOUT} s')
    log = result.stdout + result.stderr
    (work / 'freerouting.log').write_text(log, encoding='utf-8')
    for line in log.splitlines():
        if 'Auto-routing stage completed' in line:
            print('route: freerouting: ' + line.split('] ', 1)[-1])
    if result.returncode != 0 or not ses.exists() or 'Exception' in log:
        raise SystemExit(f'route: error: freerouting exited with {result.returncode}, see {work / "freerouting.log"}')

    if not pcbnew.ImportSpecctraSES(board, str(ses)):
        raise SystemExit('route: error: SES import failed')
    pcbnew.SaveBoard(str(BOARD), board)
    tracks = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    length = sum(pcbnew.ToMM(t.GetLength()) for t in tracks)
    print(f'route: {len(tracks)} segments, {len(vias)} vias, total track length {length:.1f} mm')
    return 0


if __name__ == '__main__':
    sys.exit(main())
