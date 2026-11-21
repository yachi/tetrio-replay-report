"""Verify `tst-openers-shapes.json`: the two-bag boards on which a stood T clears three rows.

    python3 -m pipeline.openers.extract_tst_opener_shapes                       # offline, CI
    python3 -m pipeline.openers.extract_tst_opener_shapes --selftest            # prove the verifier has teeth
    python3 -m pipeline.openers.extract_tst_opener_shapes --wikitext-dir <dir>  # also re-read harddrop

A SHAPE is a board of filled cells (`cells`, x 0-9, y 0 = floor) and the four cells of a stood T
(`tst`) that clears exactly three rows when it locks there. The shapes were collected from three
kinds of source, recorded in the file's `sources` block:

  * harddrop's `Category:Triple Double openers` pages, wikitext, one `{{pfstart}}..{{pfend}}` board
    per diagram. A board is a shape when it draws exactly four `P` cells as a stood T that completes
    three rows, no muted (`L?`) cell, and then passes the survey filter below. A shape's harddrop
    name is `<page title> <board number>`, the number counting EVERY board of the page from 0.
  * the committed route pages' boards (`*-routes.json`), whose T slot is not drawn but found: every
    upright T placement on the filled cells that completes three rows. A shape's name is
    `<routes file prefix> <node id>`.
  * two boards recorded by hand: johnbeak's Gamushiro bag-2 fumens (rows recorded in the file) and
    one board a user drew.

The survey filter (every source): a whole number of tetrominoes (cells divisible by four), 36 to 52
cells, at most eight rows tall, no row already full without the T.

WHAT THE DEFAULT RUN CAN AND CANNOT RE-READ. The committed routes files are re-read here, and every
shape carrying one of their names must equal what they give. harddrop's wikitext is NOT committed
and the revisions were NOT pinned when it was fetched, so those shapes are named by id in
`HARDDROP_ONLY` and checked only with `--wikitext-dir`; the johnbeak and user-drawn boards have no
re-readable source and are named in `OFFSITE`. Each pinned list is compared with what the names
imply, both ways, so a shape that gains or loses a re-readable source makes the run fail until the
list is edited. Nothing here is a claim that the unpinned wikitext is still what was fetched.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHAPES = HERE / 'tst-openers-shapes.json'
SCHEMA = 'tst-opener-shapes/1'

FULL_CELLS = 52
MIN_CELLS, MAX_ROWS = 36, 8

#: Shapes holding fewer than `FULL_CELLS` cells, each a board part-way through the two bags (the
#: slot is drawn before the build is finished). A shape off this list with fewer cells fails, and a
#: listed one with `FULL_CELLS` fails.
PARTIAL_IDS = (17, 18, 19, 24, 27, 33, 53, 63, 64, 66, 76, 83, 98, 99, 118)
PARTIAL_REASON = 'partial: the board holds fewer pieces than a finished two-bag build'

#: Shapes with a name from no committed routes file, derived (with `--wikitext-dir`) from harddrop.
HARDDROP_ONLY = (
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
    27, 28, 29, 30, 31, 32, 33, 34, 35, 39, 40, 41, 42, 43, 44, 45, 46, 48, 49, 50, 51, 52, 53, 54,
    55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 71, 72, 73, 74, 75, 76, 77, 78, 79,
    80, 81, 82, 83, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103,
    104, 105, 106, 107, 108, 109, 110, 111)
#: Shapes with no source this repo can re-read at all (johnbeak fumens, a user-drawn board).
OFFSITE = (118, 119, 120)
OFFSITE_NAMES = ('yachi ',)  # the one name of a board a user drew

PINNED = dict(partial=PARTIAL_IDS, harddrop_only=HARDDROP_ONLY, offsite=OFFSITE)

#: One shape name from each kind of source, used to read a name's kind.
JOHNBEAK_PREFIX = 'johnbeak '


# ---- geometry (the logic of the survey scripts this file replaces) ---------------------------

def _rots(shape):
    out, s = set(), list(shape)
    for _ in range(4):
        mx = min(x for x, y in s)
        my = min(y for x, y in s)
        out.add(tuple(sorted((x - mx, y - my) for x, y in s)))
        s = [(y, -x) for x, y in s]
    return out


T_ROTS = _rots([(0, 0), (1, 0), (2, 0), (1, 1)])
STOOD = [r for r in T_ROTS if max(x for x, y in r) == 1 and max(y for x, y in r) == 2]


def occupancy(rows, filled):
    """Cells of a board drawn top row first; y = 0 is the bottom row."""
    h = len(rows)
    return {(x, h - 1 - i) for i, r in enumerate(rows) for x, c in enumerate(r) if filled(c)}


def clears(cells, slot):
    return sorted(y for y in {y for _, y in slot}
                  if all((x, y) in cells or (x, y) in slot for x in range(10)))


def tsts(cells):
    """Every stood-T placement, resting on the stack or floor, that completes exactly three rows."""
    out = []
    for r in STOOD:
        for ox in range(-1, 10):
            for oy in range(0, 10):
                c = [(ox + x, oy + y) for x, y in r]
                if any(x < 0 or x > 9 or (x, y) in cells for x, y in c):
                    continue
                if not any(y == 0 or (x, y - 1) in cells for x, y in c):
                    continue
                if len(clears(cells, set(c))) == 3:
                    out.append(tuple(sorted(c)))
    return out


def survey_ok(cells):
    n = len(cells)
    if not cells or n % 4 or n < MIN_CELLS or n > FULL_CELLS:
        return False
    h = max(y for _, y in cells) + 1
    if h > MAX_ROWS:
        return False
    return not any(all((x, y) in cells for x in range(10)) for y in range(h))


def key(cells, slot):
    return (tuple(sorted(map(tuple, cells))), tuple(sorted(map(tuple, slot))))


def is_stood_t(slot):
    cs = sorted(map(tuple, slot))
    if len(cs) != 4:
        return False
    mx, my = min(x for x, _ in cs), min(y for _, y in cs)
    return tuple(sorted((x - mx, y - my) for x, y in cs)) in STOOD


# ---- sources ------------------------------------------------------------------------------------

def hd_boards(wikitext_dir: Path, titles):
    """harddrop boards that draw a stood-T slot clearing three rows, as `name -> (cells, slot)`.

    Re-implements the extraction the shapes were made with: a board is a `{{pfstart}}..{{pfend}}`
    block; `P` is the T, any other non-empty cell is filled, a two-character `L?` cell marks a muted
    (already cleared) drawing and discards the board."""
    out = {}
    for title in titles:
        f = wikitext_dir / f'{title.replace("/", "_")}.wikitext'
        if not f.is_file():
            raise FileNotFoundError(f)
        text = f.read_text()
        for bi, m in enumerate(re.finditer(r'\{\{pfstart\}\}(.*?)\{\{pfend\}\}', text, re.S)):
            rows = []
            for r in re.finditer(r'\{\{(pfrow(?:blank)?)([^}]*)\}\}', m.group(1)):
                if r.group(1) == 'pfrowblank':
                    rows.append([''] * 10)
                else:
                    cs = r.group(2).split('|')[1:]
                    rows.append([c.strip() for c in (cs + [''] * 10)[:10]])
            if not rows:
                continue
            h = len(rows)
            p, s, muted = set(), set(), False
            for i, row in enumerate(rows):
                y = h - 1 - i
                for x, c in enumerate(row):
                    if not c:
                        continue
                    if c == 'P':
                        p.add((x, y))
                    elif c.startswith('L') and len(c) == 2:
                        muted = True
                        s.add((x, y))
                    else:
                        s.add((x, y))
            if len(p) != 4 or muted:
                continue
            ys = sorted(y for _, y in p)
            if ys[-1] - ys[0] != 2:
                continue
            if len(clears(s, p)) != 3:
                continue
            if not survey_ok(s):
                continue
            out[f'{title} {bi}'] = (sorted(s), sorted(p))
    return out


def route_boards(routes_dir: Path, prefixes):
    """Route-page nodes that are shapes, as `name -> (cells, [slot options])`."""
    out = {}
    for prefix in prefixes:
        data = json.loads((routes_dir / f'{prefix}-routes.json').read_text())
        for nd in data['nodes']:
            rows = nd.get('rows')
            if not rows:
                continue
            s = occupancy(rows, lambda c: c.isalpha() and c not in 'Uu')
            if not survey_ok(s):
                continue
            t = tsts(s)
            if t:
                out[f'{prefix} {nd["id"]}'] = (sorted(s), t)
    return out


def name_kind(name, sources):
    """('harddrop', title) | ('routes', prefix) | ('johnbeak', name) | ('user', name) | (None, name)."""
    head, _, tail = name.rpartition(' ')
    if tail.isdigit() and head in sources['harddrop']['titles']:
        return 'harddrop', head
    prefix = name.split(' ', 1)[0]
    if prefix in sources['routes']['files']:
        return 'routes', prefix
    if name.startswith(JOHNBEAK_PREFIX):
        return 'johnbeak', name
    if name in OFFSITE_NAMES:
        return 'user', name
    return None, name


def kind_label(kind, detail):
    return {'harddrop': 'harddrop', 'routes': f'routes:{detail}', 'johnbeak': 'johnbeak',
            'user': 'user'}[kind]


def decode_fumen_rows(rows):
    """johnbeak's recorded rows: the T is the `T` letter, every other letter or `G` is filled."""
    cells = occupancy(rows, lambda c: c not in '.T')
    slot = occupancy(rows, lambda c: c == 'T')
    return sorted(cells), sorted(slot)


# ---- verification -------------------------------------------------------------------------------

def verify(data, wikitext_dir=None, routes_dir=HERE, pinned=PINNED):
    """Return (problems, report). A problem is (tag, message); the tags are what --selftest asserts."""
    probs, rep = [], {}

    def bad(tag, msg):
        probs.append((tag, msg))

    if data.get('schema') != SCHEMA:
        bad('schema', f'schema is {data.get("schema")!r}')
    shapes, src = data['shapes'], data['sources']
    ids = [s['id'] for s in shapes]
    for i in sorted({i for i in ids if ids.count(i) > 1}):
        bad('dup', f'shape id {i} appears more than once')
    seen = {}
    for s in shapes:
        k = key(s['cells'], s['tst'])
        if k in seen and seen[k] != s['id']:
            bad('dup', f'shapes {seen[k]} and {s["id"]} are the same board and slot')
        seen.setdefault(k, s['id'])
    by_id = {s['id']: s for s in shapes}

    # geometry of every shape
    partial = set()
    for s in shapes:
        cells = set(map(tuple, s['cells']))
        slot = set(map(tuple, s['tst']))
        i = s['id']
        if len(cells) != len(s['cells']):
            bad('geom', f'{i}: repeated cell')
        if any(not (0 <= x <= 9 and y >= 0) for x, y in cells | slot):
            bad('geom', f'{i}: a cell is off the board')
        if cells & slot:
            bad('geom', f'{i}: the T overlaps the stack')
        if not is_stood_t(slot):
            bad('slot', f'{i}: the slot is not a stood T')
        elif len(clears(cells, slot)) != 3:
            bad('clear3', f'{i}: the T clears {len(clears(cells, slot))} rows, not three')
        if len(cells) % 4:
            bad('geom', f'{i}: {len(cells)} cells is not whole tetrominoes')
        if len(cells) != FULL_CELLS:
            partial.add(i)
        if any(all((x, y) in cells for x in range(10)) for y in range(max(y for _, y in cells) + 1)):
            bad('geom', f'{i}: a row is full without the T')
        if max(y for _, y in cells) + 1 > MAX_ROWS:
            bad('geom', f'{i}: taller than {MAX_ROWS} rows')
    if partial != set(pinned['partial']):
        bad('stale', f'partial shapes differ from PARTIAL_IDS: extra {sorted(partial - set(pinned["partial"]))}'
                     f', missing {sorted(set(pinned["partial"]) - partial)}')
    rep['partial'] = len(partial)

    # names, their kinds, and the per-shape source record
    kinds = {}
    for s in shapes:
        ks = []
        for n in s['names']:
            kind, detail = name_kind(n, src)
            if kind is None:
                bad('name', f'{s["id"]}: name {n!r} belongs to no recorded source')
                continue
            lab = kind_label(kind, detail)
            if lab not in ks:
                ks.append(lab)
        kinds[s['id']] = ks
    recorded = src.get('by_shape', {})
    if {str(i): v for i, v in kinds.items()} != recorded:
        bad('sources', 'sources.by_shape differs from what the shape names imply')

    # the committed routes files, re-read
    rb = route_boards(routes_dir, sorted(src['routes']['files']))
    route_names = {n for s in shapes for n in s['names'] if name_kind(n, src)[0] == 'routes'}
    for n in sorted(route_names - set(rb)):
        bad('derive', f'route name {n!r} is not a shape in the routes file')
    byname = {}
    for s in shapes:
        for n in s['names']:
            byname.setdefault(n, []).append(s)
    for n, (cells, opts) in sorted(rb.items()):
        for slot in opts:
            sh = [s for s in byname.get(n, []) if key(s['cells'], s['tst']) == key(cells, slot)]
            if not sh:
                bad('derive', f'routes board {n!r} (cells and slot as re-derived) is not under that name')
    rep['route_boards'] = len(rb)

    # johnbeak rows recorded in the file
    jb = src['johnbeak']['fumens']
    for n, entries in jb.items():
        for e in entries:
            cells, slot = decode_fumen_rows(e['rows'])
            sh = [s for s in byname.get(n, []) if key(s['cells'], s['tst']) == key(cells, slot)]
            if not sh:
                bad('derive', f'johnbeak {n!r}: its recorded rows are not the shape under that name')
    jb_names = {n for s in shapes for n in s['names'] if name_kind(n, src)[0] == 'johnbeak'}
    for n in sorted(jb_names - set(jb)):
        bad('derive', f'johnbeak name {n!r} has no recorded fumen')
    rep['johnbeak'] = len(jb)

    # pinned lists, both ways
    want_h, want_off = set(), set()
    for s in shapes:
        ks = kinds[s['id']]
        if any(k.startswith('routes:') for k in ks):
            continue
        (want_h if 'harddrop' in ks else want_off).add(s['id'])
    for label, have, want in (('HARDDROP_ONLY', set(pinned['harddrop_only']), want_h),
                              ('OFFSITE', set(pinned['offsite']), want_off)):
        if have != want:
            bad('stale', f'{label} is stale: pinned-not-derived {sorted(have - want)}, '
                         f'derived-not-pinned {sorted(want - have)}')
    rep['harddrop_only'] = len(want_h)
    rep['offsite'] = len(want_off)

    # harddrop wikitext, when given
    if wikitext_dir is not None:
        titles = src['harddrop']['titles']
        try:
            hb = hd_boards(Path(wikitext_dir), titles)
        except FileNotFoundError as e:
            bad('derive', f'wikitext file missing: {e}')
            hb = {}
        hd_names = {n for s in shapes for n in s['names'] if name_kind(n, src)[0] == 'harddrop'}
        for n in sorted(hd_names - set(hb)):
            bad('derive', f'harddrop name {n!r} is not a shape on the wikitext page')
        for n, (cells, slot) in sorted(hb.items()):
            sh = [s for s in byname.get(n, []) if key(s['cells'], s['tst']) == key(cells, slot)]
            if not sh:
                bad('derive', f'harddrop board {n!r} (as re-derived) is not a shape under that name')
        rep['harddrop_boards'] = len(hb)
    return probs, rep


# ---- selftest -----------------------------------------------------------------------------------

def synthetic_wikitext(data, out: Path):
    """A wikitext tree the shapes' harddrop names re-derive from: one page per title, the shape's
    board at its recorded number, every other board blank (skipped, but counted in the numbering)."""
    boards = {}
    for s in data['shapes']:
        for n in s['names']:
            kind, title = name_kind(n, data['sources'])
            if kind == 'harddrop':
                boards.setdefault(title, {})[int(n.rpartition(' ')[2])] = s
    for title in data['sources']['harddrop']['titles']:
        bs = boards.get(title, {})
        blocks = []
        for bi in range(max(bs, default=-1) + 1):
            if bi not in bs:
                blocks.append('{{pfstart}}\n{{pfrowblank}}\n{{pfend}}')
                continue
            s = bs[bi]
            cells = set(map(tuple, s['cells']))
            slot = set(map(tuple, s['tst']))
            h = max(y for _, y in cells | slot) + 1
            rows = []
            for y in range(h - 1, -1, -1):
                cs = ['P' if (x, y) in slot else 'I' if (x, y) in cells else '' for x in range(10)]
                rows.append('{{pfrow|' + '|'.join(cs) + '}}')
            blocks.append('{{pfstart}}\n' + '\n'.join(rows) + '\n{{pfend}}')
        (out / f'{title.replace("/", "_")}.wikitext').write_text('\n'.join(blocks))


def selftest():
    data = json.loads(SHAPES.read_text())
    probs, _ = verify(data)
    if probs:
        print('selftest: the committed file does not verify, mutants would prove nothing')
        for p in probs[:5]:
            print('  ', p)
        return 1
    results = []

    def mutant(name, fn, tag, wikitext=False, pinned=PINNED, wt_control=None):
        d = copy.deepcopy(data)
        fn(d)
        if wikitext:
            with tempfile.TemporaryDirectory() as td:
                synthetic_wikitext(data, Path(td))
                p, _ = verify(d, wikitext_dir=td, pinned=pinned)
        else:
            p, _ = verify(d, pinned=pinned)
        killed = any(t == tag for t, _ in p)
        results.append((name, killed, tag))

    by_id = {s['id']: s for s in data['shapes']}
    route_id = next(i for i, ks in data['sources']['by_shape'].items() if any(k.startswith('routes:') for k in ks))
    route_id = int(route_id)
    hd_id = HARDDROP_ONLY[len(HARDDROP_ONLY) // 2]
    off_id = OFFSITE[0]

    def move_cell(i):
        def f(d):
            s = next(s for s in d['shapes'] if s['id'] == i)
            s['cells'][0] = [s['cells'][0][0], s['cells'][0][1] + 30]
        return f

    def drop_cell(i):
        def f(d):
            s = next(s for s in d['shapes'] if s['id'] == i)
            s['cells'].pop()
        return f

    def shift_slot(d):
        s = next(s for s in d['shapes'] if s['id'] == off_id)
        s['tst'] = [[x, y + 3] for x, y in s['tst']]

    def dup_shape(d):
        s = copy.deepcopy(d['shapes'][0])
        s['id'] = max(x['id'] for x in d['shapes']) + 1
        d['shapes'].append(s)

    def dup_id(d):
        d['shapes'][1]['id'] = d['shapes'][0]['id']

    mutant('a: a cell moved (routes-derived shape)', move_cell(route_id), 'derive')
    mutant('a: a cell moved (harddrop shape, wikitext re-read)', move_cell(hd_id), 'derive', wikitext=True)
    mutant('a: a cell dropped (harddrop shape, wikitext re-read)', drop_cell(hd_id), 'derive', wikitext=True)
    mutant('b: the T slot does not clear three rows', shift_slot, 'clear3')
    mutant('c: a duplicate shape', dup_shape, 'dup')
    mutant('c: a duplicate id', dup_id, 'dup')
    mutant('d: a stale pinned list (id removed)', lambda d: None, 'stale',
           pinned=dict(PINNED, harddrop_only=tuple(i for i in HARDDROP_ONLY if i != hd_id)))
    mutant('d: a stale pinned list (id added)', lambda d: None, 'stale',
           pinned=dict(PINNED, offsite=OFFSITE + (route_id,)))
    mutant('d: a stale partial list', lambda d: None, 'stale',
           pinned=dict(PINNED, partial=PARTIAL_IDS[1:]))

    # control: the synthetic wikitext of the unmutated file must verify, or the wikitext mutants mean nothing
    with tempfile.TemporaryDirectory() as td:
        synthetic_wikitext(data, Path(td))
        p, rep = verify(data, wikitext_dir=td)
    control_ok = not p
    for name, killed, tag in results:
        print(f'  {"killed  " if killed else "SURVIVED"} {name} [{tag}]')
    print(f'  control: synthetic wikitext re-derives every harddrop shape: {"ok" if control_ok else "FAILED " + str(p[:3])}')
    k = sum(1 for _, ok, _ in results if ok)
    print(f'selftest: killed {k}/{len(results)} mutants')
    return 0 if control_ok and k == len(results) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--wikitext-dir', help='directory of harddrop <title>.wikitext snapshots')
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    data = json.loads(SHAPES.read_text())
    probs, rep = verify(data, wikitext_dir=a.wikitext_dir)
    for tag, msg in probs:
        print(f'FAIL [{tag}] {msg}')
    print(f'shapes: {len(data["shapes"])}, ids unique, every slot a stood T clearing three rows; '
          f'partial (named) {rep["partial"]}')
    print(f'routes files re-read: {rep["route_boards"]} shape boards found, all names agree; '
          f'johnbeak recorded fumens agree: {rep["johnbeak"]}')
    print(f'pinned, not re-readable offline: harddrop-only {rep["harddrop_only"]}, offsite {rep["offsite"]}')
    if a.wikitext_dir:
        print(f'harddrop wikitext re-read ({a.wikitext_dir}): {rep.get("harddrop_boards", 0)} shape boards, all names agree')
    else:
        print('harddrop wikitext NOT re-read (no --wikitext-dir); revisions of that wikitext are not pinned')
    return 1 if probs else 0


if __name__ == '__main__':
    sys.exit(main())
