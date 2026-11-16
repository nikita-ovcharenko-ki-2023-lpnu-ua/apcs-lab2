#!/usr/bin/env python3
"""Stage 6: ERC, DRC and manufacturing output.

output/erc.json, output/drc.json  - reports (the stage fails on any violation)
output/gerbers/                   - Gerber RS-274X layers, Excellon drill, drill map, job file
output/lab2-gerbers.zip           - the same set in one archive
output/images/                    - schematic and board PDF/PNG and a 3D render for the report
"""
import argparse
import json
import shutil
import subprocess
import sys
import zipfile

from common import BOARD, OUTPUT, ROOT, SCHEMATIC

LAYERS = 'F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts'


def run(*args):
    result = subprocess.run(['kicad-cli', *args], capture_output=True, text=True)
    if result.returncode not in (0, 5):          # 5 = violations found with --exit-code-violations
        raise SystemExit(f'fab: error: kicad-cli {" ".join(args[:3])} failed: {result.stderr.strip() or result.stdout.strip()}')
    return result.returncode


def count_violations(path, keys):
    data = json.loads(path.read_text(encoding='utf-8'))
    if 'sheets' in data:
        return sum(len(s['violations']) for s in data['sheets'])
    return sum(len(data.get(k, [])) for k in keys)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-render', action='store_true', help='skip the 3D render (no GPU in CI)')
    args = parser.parse_args()
    for path in (SCHEMATIC, BOARD):
        if not path.exists():
            raise SystemExit(f'fab: error: {path.relative_to(ROOT)} not found')
    OUTPUT.mkdir(exist_ok=True)

    erc = OUTPUT / 'erc.json'
    run('sch', 'erc', '--format', 'json', '--severity-all', '--exit-code-violations', '-o', str(erc), str(SCHEMATIC))
    n_erc = count_violations(erc, [])
    drc = OUTPUT / 'drc.json'
    run('pcb', 'drc', '--format', 'json', '--severity-all', '--schematic-parity', '--exit-code-violations',
        '-o', str(drc), str(BOARD))
    n_drc = count_violations(drc, ['violations', 'unconnected_items', 'schematic_parity'])
    print(f'fab: ERC {n_erc} violation(s), DRC {n_drc} violation(s)')
    if n_erc or n_drc:
        raise SystemExit('fab: error: fix ERC/DRC violations before generating manufacturing files')

    gerbers = OUTPUT / 'gerbers'
    shutil.rmtree(gerbers, ignore_errors=True)
    gerbers.mkdir()
    run('pcb', 'export', 'gerbers', '--layers', LAYERS, '--no-x2', '-o', f'{gerbers}/', str(BOARD))
    run('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-units', 'mm', '--generate-map',
        '--map-format', 'gerberx2', '-o', f'{gerbers}/', str(BOARD))
    archive = OUTPUT / 'lab2-gerbers.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(gerbers.iterdir()):
            z.write(f, f.name)

    images = OUTPUT / 'images'
    images.mkdir(exist_ok=True)
    run('sch', 'export', 'pdf', '-o', str(images / 'schematic.pdf'), str(SCHEMATIC))
    run('pcb', 'export', 'pdf', '--layers', 'F.Cu,B.Cu,F.Silkscreen,Edge.Cuts', '--mode-single',
        '-o', str(images / 'pcb.pdf'), str(BOARD))
    run('pcb', 'export', 'svg', '--layers', 'F.Cu,B.Cu,F.Silkscreen,Edge.Cuts', '--mode-single',
        '--page-size-mode', '2', '--exclude-drawing-sheet', '-o', str(images / 'pcb.svg'), str(BOARD))
    if not args.no_render:
        run('pcb', 'render', '--side', 'top', '--width', '1600', '--height', '1000', '--quality', 'basic',
            '-o', str(images / 'pcb-3d.png'), str(BOARD))
    if shutil.which('pdftoppm'):
        for name in ('schematic', 'pcb'):
            subprocess.run(['pdftoppm', '-r', '150', '-png', '-singlefile', str(images / f'{name}.pdf'),
                            str(images / name)], check=True)

    files = sorted(f.name for f in gerbers.iterdir())
    print(f'fab: {len(files)} files in {gerbers.relative_to(ROOT)}: {", ".join(files)}')
    print(f'fab: archive {archive.relative_to(ROOT)}; images in {images.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
