#!/usr/bin/env python3
"""Read-only verification for the /check command of the pcb-engineer agent.

It never edits files under Git; it only writes reports to output/check/.
Exit code 0 = every check passed.

Usage: python3 .github/agent-tools/check.py [--only GROUP[,GROUP...]]
Groups: agent, skills, commands, params, library, schematic, pcb, routing, fab, git
"""
import argparse
import contextlib
import json
import math
import os
import re
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output' / 'check'
PARAMS = ROOT / 'params' / 'board.json'
HW = ROOT / 'hardware'
SCH = HW / 'lab2.kicad_sch'
PCB = HW / 'lab2.kicad_pcb'
FP_LIB = HW / 'lib' / 'lab2.pretty'
SYM_LIB = HW / 'lib' / 'lab2.kicad_sym'
GERBERS = ROOT / 'output' / 'gerbers'
MAX_W, MAX_H = 85.6, 53.98
GROUPS = ['agent', 'skills', 'commands', 'params', 'library', 'schematic', 'pcb', 'routing', 'fab', 'git']
SKILLS = ['guid-params', 'kicad-library', 'kicad-schematic', 'kicad-pcb', 'autoroute', 'fab-output']
COMMANDS = ['gen-params', 'create-library', 'create-schematic', 'create-pcb', 'route', 'fab', 'check', 'build-board']

results = []


@contextlib.contextmanager
def quiet_stderr():
    """pcbnew prints wxWidgets debug noise to fd 2; hide it during a check."""
    sys.stderr.flush()
    saved = os.dup(2)
    with open(os.devnull, 'w') as devnull:
        os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            os.dup2(saved, 2)
            os.close(saved)


def check(group, name):
    def deco(fn):
        try:
            with quiet_stderr():
                out = fn()
            ok = out is True or out is None
            results.append((group, name, ok, '' if ok else str(out)))
        except Exception as err:  # a check must never crash the whole run
            results.append((group, name, False, f'{type(err).__name__}: {str(err).splitlines()[0] if str(err) else ""}'))
        return fn
    return deco


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def need(p: Path) -> Path:
    if not p.exists():
        raise FileNotFoundError(f'{rel(p)} not found')
    return p


def sections(path: Path, names):
    text = need(path).read_text(encoding='utf-8')
    missing = [n for n in names if not re.search(rf'^##\s+{re.escape(n)}', text, re.M)]
    return True if not missing else f'missing sections: {", ".join(missing)}'


def frontmatter(path: Path) -> dict:
    m = re.match(r'^---\r?\n(.*?)\r?\n---', need(path).read_text(encoding='utf-8'), re.S)
    data = {}
    for line in (m.group(1).splitlines() if m else []):
        kv = re.match(r'^([\w-]+):\s*(.*)$', line)
        if kv:
            data[kv.group(1)] = kv.group(2).strip()
    return data


def kicad(*args):
    return subprocess.run(['kicad-cli', *args], capture_output=True, text=True, cwd=ROOT)


def params():
    return json.loads(need(PARAMS).read_text(encoding='utf-8'))


def pcbnew_mod():
    import pcbnew  # noqa: imported lazily, available with KiCad
    return pcbnew


# ------------------------------------------------------------------ agent / skills / commands
def run_agent():
    manifest = ROOT / '.github/agents/pcb-engineer.agent.md'
    check('agent', 'manifest: role, task, scope, rules, forbidden actions, completion criteria')(
        lambda: sections(manifest, ['Роль', 'Технічне завдання', 'Область відповідальності',
                                    'Правила роботи з файлами', 'Заборонені дії', 'Критерії успішного завершення']))
    check('agent', 'manifest frontmatter has name and description')(
        lambda: True if {'name', 'description'} <= frontmatter(manifest).keys() else 'name/description missing')


def run_skills():
    names = ['Коли застосовувати', 'Входи', 'Виходи', 'Вимоги', 'Кроки', 'Перевірки', 'Типовий сценарій помилки', 'Приклад']
    for skill in SKILLS:
        path = ROOT / f'.github/skills/{skill}/SKILL.md'
        check('skills', f'{skill}: all sections incl. requirements')(lambda p=path: sections(p, names))
        check('skills', f'{skill}: frontmatter name matches directory')(
            lambda p=path, s=skill: True if frontmatter(p).get('name') == s else 'name mismatch')
        check('skills', f'{skill}: specification only, no ready-made files')(
            lambda p=path: True if [f.name for f in p.parent.iterdir()] == ['SKILL.md']
            else f'unexpected files: {[f.name for f in p.parent.iterdir() if f.name != "SKILL.md"]}')


def run_commands():
    names = ['Передумови', 'Дії', 'Очікувані файли', 'Перевірки', 'Повідомлення про помилку']
    for cmd in COMMANDS:
        path = ROOT / f'.github/prompts/{cmd}.prompt.md'
        check('commands', f'{cmd}: preconditions, actions, files, checks, error messages')(
            lambda p=path: sections(p, names))

    @check('commands', 'build-board calls the 7 steps in order')
    def _():
        text = need(ROOT / '.github/prompts/build-board.prompt.md').read_text(encoding='utf-8')
        steps = text.split('## Дії', 1)[1] if '## Дії' in text else ''
        pos = [steps.find(f'`/{c}`') for c in COMMANDS[:7]]
        if min(pos) < 0:
            return 'not every command is referenced in "Дії"'
        return True if pos == sorted(pos) else f'wrong order {pos}'


# ------------------------------------------------------------------ design data
def expected_nets(p):
    groups = p['guid'].split('-')
    occ = defaultdict(list)
    for i, g in enumerate(groups, 1):
        for n, ch in enumerate(g, 1):
            occ[ch].append(f'U{i}.{n}')
    nets, free = {}, []
    for ch in sorted(occ):
        if len(occ[ch]) > 1:
            nets[f'N_{ch}'] = sorted(occ[ch])
        else:
            free.append(occ[ch][0])
    for k, pin in enumerate(free, 1):
        nets[f'FREE_{pin.replace(".", "_")}'] = sorted([pin, f'J1.{k}'])
    return nets


def run_params():
    @check('params', 'GUID = uuid5(NAMESPACE_DNS, full name)')
    def _():
        p = params()
        want = str(uuid.uuid5(uuid.NAMESPACE_DNS, p['full_name']))
        return True if p['guid'] == want and len(p['full_name'].split()) == 3 else f'{p["guid"]} != {want}'

    @check('params', 'component sizes and pins follow the GUID groups')
    def _():
        p = params()
        groups = p['guid'].split('-')
        for comp, g in zip(p['components'], groups):
            if comp['size_mm'] != len(g) or ''.join(x['symbol'] for x in comp['pins']) != g:
                return f'{comp["ref"]} does not match group {g}'
        return True if len(p['components']) == 5 else 'expected 5 components'

    @check('params', 'nets: equal characters connected, single characters on J1')
    def _():
        p = params()
        got = {n['name']: sorted(n['pins']) for n in p['nets']}
        want = expected_nets(p)
        diff = [k for k in set(got) | set(want) if got.get(k) != want.get(k)]
        return True if not diff else f'differs: {", ".join(sorted(diff)[:4])}'


def run_library():
    @check('library', 'footprints: body N x N mm on F.Fab, N pads, J1 pads = free pins')
    def _():
        pcbnew = pcbnew_mod()
        p = params()
        problems = []
        for comp in p['components']:
            n = comp['size_mm']
            name = f'{comp["ref"]}_{n}x{n}mm'
            fp = pcbnew.FootprintLoad(str(need(FP_LIB)), name)
            if fp is None:
                problems.append(f'{name} not loadable')
                continue
            fab = [g for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.F_Fab and g.GetClass() == 'PCB_SHAPE']
            sizes = [(round(pcbnew.ToMM(g.GetBoundingBox().GetWidth()) - pcbnew.ToMM(g.GetWidth()), 2),
                      round(pcbnew.ToMM(g.GetBoundingBox().GetHeight()) - pcbnew.ToMM(g.GetWidth()), 2)) for g in fab]
            if (float(n), float(n)) not in sizes:
                problems.append(f'{name} body {sizes}')
            if fp.GetPadCount() != len(comp['pins']):
                problems.append(f'{name} has {fp.GetPadCount()} pads')
        k = len(p['connector']['pins'])
        j1 = pcbnew.FootprintLoad(str(FP_LIB), f'J1_1x{k:02d}_P2.54mm')
        if j1 is None or j1.GetPadCount() != k:
            problems.append('J1 footprint missing or wrong pad count')
        return True if not problems else '; '.join(problems)

    @check('library', 'symbol library contains U1..U5 and J1')
    def _():
        text = need(SYM_LIB).read_text(encoding='utf-8')
        missing = [r for r in ['U1', 'U2', 'U3', 'U4', 'U5', 'J1'] if f'(symbol "{r}"' not in text]
        return True if not missing else f'missing symbols {missing}'


def run_schematic():
    OUT.mkdir(parents=True, exist_ok=True)

    @check('schematic', 'ERC: 0 violations')
    def _():
        rep = OUT / 'erc.json'
        r = kicad('sch', 'erc', '--format', 'json', '--severity-all', '-o', str(rep), str(need(SCH)))
        if not rep.exists():
            return f'kicad-cli failed: {r.stderr.strip()[:120]}'
        v = [x for s in json.loads(rep.read_text())['sheets'] for x in s['violations']]
        return True if not v else f'{len(v)} violation(s), first: {v[0]["type"]}'

    @check('schematic', 'schematic nets equal params nets')
    def _():
        net_xml = OUT / 'netlist.xml'
        kicad('sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(net_xml), str(need(SCH)))
        got = {}
        for net in ET.parse(need(net_xml)).getroot().iter('net'):
            got[net.get('name').lstrip('/')] = sorted(f'{n.get("ref")}.{n.get("pin")}' for n in net.iter('node'))
        want = {n['name']: sorted(n['pins']) for n in params()['nets']}
        diff = [k for k in set(got) | set(want) if got.get(k) != want.get(k)]
        return True if not diff else f'differs: {", ".join(sorted(diff)[:4])}'


def board():
    return pcbnew_mod().LoadBoard(str(need(PCB)))


def run_pcb():
    @check('pcb', f'outline <= {MAX_W} x {MAX_H} mm, 2 copper layers')
    def _():
        pcbnew = pcbnew_mod()
        b = board()
        bb = b.GetBoardEdgesBoundingBox()
        w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
        if w > MAX_W + 0.11 or h > MAX_H + 0.11:          # + Edge.Cuts line width
            return f'outline {w:.2f} x {h:.2f} mm'
        return True if b.GetCopperLayerCount() == 2 else f'{b.GetCopperLayerCount()} copper layers'

    @check('pcb', 'all footprints inside the outline, J1 at a short edge')
    def _():
        pcbnew = pcbnew_mod()
        b = board()
        edge = b.GetBoardEdgesBoundingBox()
        refs = {}
        for fp in b.GetFootprints():
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            if not edge.Contains(bb):
                return f'{fp.GetReference()} outside the board'
            refs[fp.GetReference()] = bb
        if sorted(refs) != ['J1', 'U1', 'U2', 'U3', 'U4', 'U5']:
            return f'footprints {sorted(refs)}'
        j1 = refs['J1']
        d_left = pcbnew.ToMM(j1.GetLeft() - edge.GetLeft())
        d_right = pcbnew.ToMM(edge.GetRight() - j1.GetRight())
        short_is_x = edge.GetHeight() <= edge.GetWidth()
        return True if short_is_x and min(d_left, d_right) <= 5 else f'J1 is {min(d_left, d_right):.1f} mm from a short edge'

    @check('pcb', 'footprint bodies keep their GUID sizes on the board')
    def _():
        pcbnew = pcbnew_mod()
        sizes = {c['ref']: c['size_mm'] for c in params()['components']}
        for fp in board().GetFootprints():
            ref = fp.GetReference()
            if ref in sizes and fp.GetFPID().GetLibItemName().wx_str() != f'{ref}_{sizes[ref]}x{sizes[ref]}mm':
                return f'{ref} uses {fp.GetFPID().GetLibItemName().wx_str()}'
        return True


def run_routing():
    OUT.mkdir(parents=True, exist_ok=True)

    @check('routing', 'DRC: 0 violations, 0 unconnected, 0 schematic parity issues')
    def _():
        rep = OUT / 'drc.json'
        kicad('pcb', 'drc', '--format', 'json', '--severity-all', '--schematic-parity', '-o', str(rep), str(need(PCB)))
        d = json.loads(need(rep).read_text())
        counts = {k: len(d.get(k, [])) for k in ('violations', 'unconnected_items', 'schematic_parity')}
        if any(counts.values()):
            first = next(x['type'] for k in counts for x in d.get(k, []))
            return f'{counts}, first: {first}'
        return True

    @check('routing', 'tracks on both copper layers')
    def _():
        b = board()
        layers = Counter(b.GetLayerName(t.GetLayer()) for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK')
        return True if layers.get('F.Cu') and layers.get('B.Cu') else f'tracks per layer: {dict(layers)}'

    @check('routing', 'no acute corners (interior angle >= 90 deg)')
    def _():
        pcbnew = pcbnew_mod()
        b = board()
        pads = {(p.GetPosition().x, p.GetPosition().y) for p in b.GetPads()}
        vias = {(v.GetPosition().x, v.GetPosition().y) for v in b.GetTracks() if v.GetClass() == 'PCB_VIA'}
        ends = defaultdict(list)
        for t in b.GetTracks():
            if t.GetClass() != 'PCB_TRACK':
                continue
            s, e = t.GetStart(), t.GetEnd()
            ends[(t.GetLayer(), s.x, s.y)].append((e.x - s.x, e.y - s.y))
            ends[(t.GetLayer(), e.x, e.y)].append((s.x - e.x, s.y - e.y))
        for (layer, x, y), vecs in ends.items():
            if (x, y) in pads or (x, y) in vias or len(vecs) != 2:
                continue
            (ax, ay), (bx, by) = vecs
            cos = (ax * bx + ay * by) / (math.hypot(ax, ay) * math.hypot(bx, by))
            angle = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
            if angle < 90 - 1e-6:
                return f'{angle:.0f} deg at ({pcbnew.ToMM(x):.2f}, {pcbnew.ToMM(y):.2f}) mm'
        return True


def run_fab():
    @check('fab', 'Gerber RS-274X for copper, mask, silkscreen, outline + Excellon drill')
    def _():
        need(GERBERS)
        suffixes = {'F_Cu': 'gtl', 'B_Cu': 'gbl', 'F_Mask': 'gts', 'B_Mask': 'gbs',
                    'F_Silkscreen': 'gto', 'B_Silkscreen': 'gbo', 'Edge_Cuts': 'gm1'}
        for layer, ext in suffixes.items():
            f = need(GERBERS / f'lab2-{layer}.{ext}')
            head = f.read_text(errors='replace')[:2000]
            if '%FS' not in head or '%MO' not in head:
                return f'{f.name}: no RS-274X %FS/%MO header'
        drl = need(GERBERS / 'lab2.drl').read_text(errors='replace')
        return True if drl.startswith('M48') else 'lab2.drl is not Excellon'


def run_git():
    @check('git', '.gitignore ignores output/ and KiCad local files')
    def _():
        lines = [l.strip() for l in need(ROOT / '.gitignore').read_text().splitlines()]
        missing = [x for x in ['output/', '*.kicad_prl', '*-backups/', 'fp-info-cache', '.env'] if x not in lines]
        return True if not missing else f'missing {missing}'

    @check('git', 'no output/, local KiCad files or secrets tracked')
    def _():
        files = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True).stdout.split('\n')
        bad = [f for f in files if f.startswith('output/') or f.endswith(('.kicad_prl', '.lck')) or '-backups/' in f
               or re.search(r'(^|/)\.env', f)]
        if bad:
            return f'tracked: {bad[:3]}'
        pattern = re.compile(r'(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)')
        hits = [f for f in files if f and (ROOT / f).is_file() and (ROOT / f).stat().st_size < 2_000_000
                and pattern.search((ROOT / f).read_text(errors='ignore'))]
        return True if not hits else f'possible secret in {hits}'


RUNNERS = {'agent': run_agent, 'skills': run_skills, 'commands': run_commands, 'params': run_params,
           'library': run_library, 'schematic': run_schematic, 'pcb': run_pcb, 'routing': run_routing,
           'fab': run_fab, 'git': run_git}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--only', help='comma-separated groups')
    args = parser.parse_args()
    groups = args.only.split(',') if args.only else GROUPS
    unknown = [g for g in groups if g not in RUNNERS]
    if unknown:
        parser.error(f'unknown group(s): {unknown}')
    for g in groups:
        RUNNERS[g]()
    width = max(len(g) for g, *_ in results)
    for group, name, ok, detail in results:
        print(f'[{"PASS" if ok else "FAIL"}] {group:<{width}}  {name}' + ('' if ok else f'\n         -> {detail}'))
    failed = sum(1 for r in results if not r[2])
    print(f'\ncheck: {len(results) - failed} passed, {failed} failed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
