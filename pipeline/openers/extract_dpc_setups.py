"""Transcribe harddrop's DPC setup pages into `dpc-setups.json`, and gate the transcription.

    python3 -m pipeline.openers.extract_dpc_setups                    # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_dpc_setups --selftest         # prove the verifier has teeth
    python3 -m pipeline.openers.extract_dpc_setups --wikitext-dir <d> # re-parse the pinned revisions
    python3 -m pipeline.openers.extract_dpc_setups --wikitext-dir <d> --write  # ...and rewrite the file

WHAT A DPC IS, in the page's own words (quoted in the JSON's `source.definition`): after a Perfect Clear
loop that takes 8 lines (20 pieces from three bags), the board is empty and one piece is left over; a DPC
setup uses that piece and two bags to make a T-spin and a second Perfect Clear. So a setup is drawn as a
board built from EMPTY, the T placed (`P`), the rows it clears gone (the residue, `G`), and the Perfect
Clears that finish on the residue (the solutions).

THE SOURCES are six harddrop wiki pages: `DPC Setups` (the minimal setups, one or two per left-over
piece) and the five `Extra DPC Setups - Extra <X> Shapes` pages. harddrop publishes no licence for wiki
content (as for SDPC Spin), so every page credits by link. No page is committed: each is pinned as a
MediaWiki revision (`oldid`, MediaWiki's own `revision_sha1`, our `snapshot_sha256` and `snapshot_bytes`),
which `check_wikitext_sources` discovers (`*-setups.json`) and refetches weekly, re-running this module
with `--wikitext-dir`. The first read was through a fetch service, because this repo's sandbox cannot reach
harddrop.com directly; that is safe to rely on only because MediaWiki's sha1 of the revision equals the sha1
of the bytes read (checked when the file was written, and by every refetch since).

THE TRANSCRIPTION IS A PARSE, NOT A HAND COPY. Unlike the route and technique pages, every board here is
read by `parse_page` (below) and written out; nothing is retyped. That is why `--wikitext-dir` compares
the WHOLE board list, board for board, against a re-parse of the pinned bytes: a hand copy needs a second
reader to be trusted, a parse needs only its input to be pinned. Each cell token is mapped once
(`TOKENS`): blank → `.`, a piece letter as itself, `G` (cells placed before the diagram), `P` (the T being
placed), the extra piece's marks (`'X` → lower case `x`, and the bare marks `N`, `F`, `Y`, `+`). An
unknown token is a failure, never a guess.

WHAT IS DERIVED, AND CHECKED HERE. A board drawing `P` and no `G` is a SETUP SPIN: the T placed on a board
built from empty. Each one becomes a `setups` entry with
  * `t_cells`: the four P cells, which must be one T tetromino (rule `t:`);
  * `lines`: the rows the T completes, at least one, each holding a P cell (rule `lines:`);
  * `base`: the board less the T, by occupancy, bottom-aligned, with no full row and a cell count that is
    whole pieces less at most one cleared line (rule `base:`; `cleared_before` is 1 for the SPC setups,
    which clear a line before the T);
  * `drawn_before`: the board drawn just before it in the same table when that board, read by occupancy, is
    the base (the page's own "before" drawing, with the extra piece marked), else null. Measured, never
    required: some sections draw the setup only with the T in.
  * `same_as`: the other setups with the identical base AND T cells (as drawn), grouped by id. A board drawn
    on several pages is one shape; the corpus matcher reports every name it carries, never one of them.
A board drawing `P` that completes no row is `t_build` (the T laid into the stack as a building piece, or a
T-spin zero, which the pages do not score), not a setup. The roles of the other boards (`residue`,
`solution`, `spin_on_residue`, `board`, `t_build`) are recorded and not used
by the matcher. A `solution` is a board whose non-empty rows are all full (a Perfect Clear frame).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
OUT = HERE / 'dpc-setups.json'
W = 10

#: wikitext cell token -> transcription letter
TOKENS = {'': '.', ' ': '.', 'G': 'G', 'P': 'P', 'N': 'N', 'F': 'F', 'Y': 'Y', '+': '+',
          **{x: x for x in 'IJLOSTZ'}, **{"'" + x: x.lower() for x in 'IJLOSTZ'}}
PIECES = set('IJLOSTZ')
#: the four T tetrominoes, as (row, col) offsets from their top-left
T_SHAPES = [frozenset(s) for s in (
    {(0, 0), (0, 1), (0, 2), (1, 1)},       # flat, nub down
    {(0, 1), (1, 0), (1, 1), (1, 2)},       # flat, nub up
    {(0, 0), (1, 0), (2, 0), (1, 1)},       # stood, nub right
    {(0, 1), (1, 1), (2, 1), (1, 0)},       # stood, nub left
)]

_PF = re.compile(r'\{\{pfstart\}\}(.*?)\{\{pfend\}\}', re.S)
_EVENT = re.compile(r'^(={1,4})([^=\n]+?)\1\s*$|^\{\||\{\{pfstart\}\}(.*?)\{\{pfend\}\}', re.S | re.M)
_ROW = re.compile(r'\{\{pfrow(blank)?(?:\|([^}]*))?\}\}')


class Bad(Exception):
    pass


def parse_page(text: str) -> list[dict]:
    """Every `{{pfstart}} … {{pfend}}` board of one page, in order: its heading path, the number of `{|`
    seen before it, and its rows (top to bottom, TOKENS-mapped). Raises on a ragged row or unknown token."""
    out: list[dict] = []
    heads: list[tuple[int, str]] = []
    table = 0
    for m in _EVENT.finditer(text):
        if m.group(1):
            lvl = len(m.group(1))
            heads = [h for h in heads if h[0] < lvl] + [(lvl, m.group(2).strip())]
            continue
        if m.group(0).startswith('{|'):
            table += 1
            continue
        rows = []
        for blank, cells in _ROW.findall(m.group(3)):
            if blank:
                rows.append('.' * W)
                continue
            toks = [c.strip() if c.strip() else c for c in cells.split('|')]
            if len(toks) != W:
                raise Bad(f'board {len(out)}: a pfrow with {len(toks)} cells: {cells!r}')
            bad = [t for t in toks if t not in TOKENS]
            if bad:
                raise Bad(f'board {len(out)}: unknown cell token(s) {bad}')
            rows.append(''.join(TOKENS[t] for t in toks))
        if not rows:
            raise Bad(f'board {len(out)}: no rows')
        out.append({'heading': [h for _, h in heads], 'table': table, 'rows': rows})
    return out


def role(rows: list[str]) -> str:
    cells = ''.join(rows)
    has_p, has_g = 'P' in cells, 'G' in cells
    if has_p:
        if has_g:
            return 'spin_on_residue'
        # the T completes a row: the setup's spin. Otherwise the T is a build piece (the Extra T page lays
        # one into the stack before the spin), or a T-spin zero, neither of which the page scores
        return 'spin' if any('.' not in r and 'P' in r for r in rows) else 't_build'
    nonempty = [r for r in rows if r != '.' * W]
    if nonempty and all('.' not in r for r in nonempty):
        return 'solution'
    if has_g and not (set(cells) - {'.', 'G'}):
        return 'residue'
    return 'board'


def occ(rows: list[str]) -> list[str]:
    """Occupancy, leading empty rows dropped."""
    o = [''.join('.' if c == '.' else 'x' for c in r) for r in rows]
    while o and o[0] == '.' * W:
        o.pop(0)
    return o


def derive(pages: list[dict]) -> tuple[list[dict], list[dict]]:
    """(boards, setups) from the pages' parsed boards. Raises Bad on a rule a setup breaks."""
    boards, setups = [], []
    for pg in pages:
        prev = None
        for i, b in enumerate(pg['boards']):
            bid = f'{pg["key"]}.{i:03d}'
            boards.append({'id': bid, 'page': pg['key'], 'heading': b['heading'], 'table': b['table'],
                           'role': role(b['rows']), 'rows': b['rows']})
            if boards[-1]['role'] == 'spin':
                setups.append(setup_of(bid, pg['key'], b, prev))
            prev = (bid, b)
    key = {}
    for s in setups:
        key.setdefault((tuple(s['base']), tuple(map(tuple, s['t_cells']))), []).append(s['id'])
    for s in setups:
        s['same_as'] = [x for x in key[(tuple(s['base']), tuple(map(tuple, s['t_cells'])))] if x != s['id']]
    return boards, setups


def setup_of(bid: str, page: str, b: dict, prev) -> dict:
    rows = b['rows']
    top = next(i for i, r in enumerate(rows) if r != '.' * W)
    frame = rows[top:]
    h = len(frame)
    tc = sorted((r, c) for r, row in enumerate(frame) for c, ch in enumerate(row) if ch == 'P')
    r0, c0 = min(r for r, _ in tc), min(c for _, c in tc)
    if len(tc) != 4 or frozenset((r - r0, c - c0) for r, c in tc) not in T_SHAPES:
        raise Bad(f't: {bid}: the P cells {tc} are not one T tetromino')
    full = [r for r, row in enumerate(frame) if '.' not in row]
    if not full or any(not any(rr == r for rr, _ in tc) for r in full):
        raise Bad(f'lines: {bid}: full rows {full}, each must hold a P cell and there must be one')
    base = [''.join('.' if ch in '.P' else 'x' for ch in row) for row in frame]
    if any('.' not in row for row in base):
        raise Bad(f'base: {bid}: the board less the T has a full row')
    n = sum(row.count('x') for row in base)
    # built from empty, so the cells are whole pieces less the lines cleared before the T: an SPC setup
    # clears one line first (its name's S), so n + 10 is a multiple of four. More than one is a failure
    cleared_before = next((k for k in (0, 1) if (n + 10 * k) % 4 == 0), None)
    if cleared_before is None:
        raise Bad(f'base: {bid}: {n} cells less the T, not whole pieces less at most one cleared line')
    while base and base[0] == '.' * W:          # the T may stand above the rest of the stack
        base.pop(0)
    drawn_before = None
    if prev is not None and prev[1]['table'] == b['table'] and role(prev[1]['rows']) == 'board' \
            and occ(prev[1]['rows']) == base:
        drawn_before = prev[0]
    return {'id': bid, 'page': page, 'heading': b['heading'], 'base': base,
            't_cells': [[r, c] for r, c in tc], 'frame_rows': h,
            'lines': len(full), 'pieces': (n + 10 * cleared_before) // 4, 'cleared_before': cleared_before,
            'drawn_before': drawn_before}


def snapshot_checks(data: dict, d: Path) -> list[str]:
    """`--wikitext-dir`: each pinned revision's bytes hashed against the record, re-parsed, and the whole
    transcription re-derived and compared."""
    bad = []
    pages = []
    for pg in data['pages']:
        f = d / pg['snapshot_file']
        tag = pg['key']
        if not f.exists():
            bad.append(f'{tag}: {pg["snapshot_file"]} is not in {d}')
            continue
        raw = f.read_bytes()
        if hashlib.sha256(raw).hexdigest() != pg['snapshot_sha256'] or len(raw) != pg['snapshot_bytes']:
            bad.append(f'{tag}: hash: sha256/bytes {hashlib.sha256(raw).hexdigest()} / {len(raw)} are not the '
                       f'recorded ones')
        if hashlib.sha1(raw).hexdigest() != pg['revision_sha1']:
            bad.append(f'{tag}: hash: sha1 {hashlib.sha1(raw).hexdigest()} is not MediaWiki\'s revision sha1')
        try:
            pages.append({'key': tag, 'boards': parse_page(raw.decode('utf8'))})
        except Bad as e:
            bad.append(f'{tag}: parse: {e}')
    # a hash failure does not stop the re-parse: the comparison below is the check a refetch is for
    if [x for x in bad if ': hash: ' not in x]:
        return bad
    try:
        boards, setups = derive(pages)
    except Bad as e:
        return bad + [f'derive: {e}']
    if boards != data['boards']:
        diff = [a['id'] for a, b in zip(boards, data['boards']) if a != b]
        bad.append(f'boards: the re-parse differs from the recorded boards ({len(boards)} parsed, '
                   f'{len(data["boards"])} recorded; first differing: {diff[:3]})')
    if setups != data['setups']:
        bad.append('setups: the re-derived setups differ from the recorded ones')
    return bad


def offline_checks(data: dict) -> list[str]:
    """The committed file alone: every setup re-derived from its recorded board, and the bookkeeping."""
    bad = []
    keys = [p['key'] for p in data['pages']]
    if len(set(keys)) != len(keys):
        bad.append(f'pages: duplicate keys {keys}')
    for p in data['pages']:
        for k in ('title', 'url', 'oldid', 'revision_sha1', 'snapshot_sha256', 'snapshot_bytes', 'snapshot_file'):
            if k not in p:
                bad.append(f'pages: {p.get("key")} has no {k}')
    pages = []
    for p in data['pages']:
        mine = [b for b in data['boards'] if b['page'] == p['key']]
        if [b['id'] for b in mine] != [f'{p["key"]}.{i:03d}' for i in range(len(mine))]:
            bad.append(f'boards: {p["key"]} ids are not consecutive')
        for b in mine:
            if any(len(r) != W or set(r) - set(TOKENS.values()) for r in b['rows']):
                bad.append(f'boards: {b["id"]} has a ragged row or an unknown letter')
            if b['role'] != role(b['rows']):
                bad.append(f'boards: {b["id"]} is recorded as {b["role"]}, its rows say {role(b["rows"])}')
        pages.append({'key': p['key'], 'boards': [{k: b[k] for k in ('heading', 'table', 'rows')} for b in mine]})
    if bad:
        return bad
    try:
        _, setups = derive(pages)
    except Bad as e:
        return [f'{e}']
    if setups != data['setups']:
        bad.append('setups: re-derived from the recorded boards, they differ from the recorded setups')
    return bad


def synthetic_page(data: dict, key: str) -> str:
    """A page from the recorded boards alone, for selftests (the real bytes are not committed): headings,
    tables and boards in order, parsing back to the recorded boards."""
    rev = {v: k for k, v in TOKENS.items() if k not in ('',)}
    out, heads, table = [], [], 0
    for b in [b for b in data['boards'] if b['page'] == key]:
        if b['heading'] != heads:
            common = 0
            while common < min(len(heads), len(b['heading'])) and heads[common] == b['heading'][common]:
                common += 1
            for lvl, h in enumerate(b['heading'][common:], start=common + 2):
                out.append(f'{"=" * lvl}{h}{"=" * lvl}')
            heads = b['heading']
        while table < b['table']:
            out.append('{|')
            table += 1
        rows = ['{{pfrowblank}}' if r == '.' * W else '{{pfrow|' + '|'.join(rev[c] for c in r) + '}}'
                for r in b['rows']]
        out.append('|{{pfstart}}\n' + '\n'.join(rows) + '\n{{pfend}}')
    return '\n'.join(out) + '\n'


def write(d: Path) -> int:
    data = json.loads(OUT.read_text())
    pages = []
    for pg in data['pages']:
        raw = (d / pg['snapshot_file']).read_bytes()
        if hashlib.sha1(raw).hexdigest() != pg['revision_sha1']:
            print(f'FAIL {pg["key"]}: hash: the bytes in {d} are not the pinned revision')
            return 1
        pg['snapshot_sha256'] = hashlib.sha256(raw).hexdigest()
        pg['snapshot_bytes'] = len(raw)
        pages.append({'key': pg['key'], 'boards': parse_page(raw.decode('utf8'))})
    data['boards'], data['setups'] = derive(pages)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
    print(f'wrote {OUT.relative_to(HERE.parent.parent)}: {len(data["boards"])} boards, {len(data["setups"])} setups')
    return 0


def report(bad: list[str], what: str) -> int:
    for x in bad:
        print(f'FAIL {x}')
    if not bad:
        print(f'ok  {what}')
    return 1 if bad else 0


def selftest() -> int:
    data = json.loads(OUT.read_text())
    survived = killed = 0

    def expect(label, bad, want):
        nonlocal survived, killed
        if bool(bad) == want:
            killed += want
            print(f'  {"killed" if want else "passed"}: {label}')
        else:
            survived += 1
            print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

    expect('the committed file (control)', offline_checks(data), False)
    s0 = data['setups'][0]
    b0 = next(b for b in data['boards'] if b['id'] == s0['id'])

    def with_board(fn):
        d = copy.deepcopy(data)
        b = next(b for b in d['boards'] if b['id'] == s0['id'])
        b['rows'] = fn(b['rows'])
        return d
    # a P cell moved to an empty cell: no longer a T
    r, c = next((r, c) for r, row in enumerate(b0['rows']) for c, ch in enumerate(row) if ch == 'P')
    fr, fc = next((i, j) for i, row in enumerate(b0['rows']) for j, ch in enumerate(row) if ch == '.')

    def move_p(rows):
        g = [list(x) for x in rows]
        g[r][c], g[fr][fc] = '.', 'P'
        return [''.join(x) for x in g]
    expect('a P cell moved (not a T tetromino)', offline_checks(with_board(move_p)), True)
    # a base cell emptied: the recorded setup no longer re-derives
    br, bc = next((i, j) for i, row in enumerate(b0['rows']) for j, ch in enumerate(row) if ch in PIECES)
    expect('a base cell emptied', offline_checks(with_board(
        lambda rows: [row[:bc] + '.' + row[bc + 1:] if i == br else row for i, row in enumerate(rows)])), True)
    d = copy.deepcopy(data)
    d['setups'][0]['lines'] += 1
    expect('a recorded line count edited', offline_checks(d), True)
    d = copy.deepcopy(data)
    d['setups'][0]['same_as'] = []
    expect('a recorded same_as group emptied', offline_checks(d) if data['setups'][0]['same_as'] else ['n/a'], True)
    d = copy.deepcopy(data)
    d['boards'][0]['role'] = 'solution' if d['boards'][0]['role'] != 'solution' else 'board'
    expect('a board role edited', offline_checks(d), True)
    d = copy.deepcopy(data)
    del d['pages'][0]['revision_sha1']
    expect('a page with no revision_sha1', offline_checks(d), True)
    # the re-parse: faithful synthetic pages pass except their hashes; an edited board fails
    with tempfile.TemporaryDirectory() as td:
        for p in data['pages']:
            (Path(td) / p['snapshot_file']).write_text(synthetic_page(data, p['key']))
        res = snapshot_checks(data, Path(td))
        expect('synthetic pages re-parse to the recorded boards (hash lines aside) (control)',
               [x for x in res if ': hash: ' not in x], False)
        expect('...and the synthetic bytes are not the pinned ones', [x for x in res if ': hash: ' in x], True)
        f = Path(td) / data['pages'][0]['snapshot_file']
        t = f.read_text()
        m = re.search(r'\{\{pfrow\|([^}]*)\}\}', t)
        cells = m.group(1).split('|')
        j = next(i for i, x in enumerate(cells) if x.strip())
        cells[j] = ' '
        f.write_text(t[:m.start(1)] + '|'.join(cells) + t[m.end(1):])
        expect('a board cell blanked in a page', [x for x in snapshot_checks(data, Path(td)) if ': hash: ' not in x],
               True)
        f.write_text(t.replace('{{pfrow|', '{{pfrow|Q|', 1))
        expect('a row with an unknown token', [x for x in snapshot_checks(data, Path(td)) if ': hash: ' not in x],
               True)
        f.unlink()
        expect('a missing snapshot', snapshot_checks(data, Path(td)), True)
    print(f'selftest: {killed} killed, {survived} survived')
    return 1 if survived else 0


#: what `check_wikitext_sources` reads: one synthetic page per pinned revision, and the --wikitext-dir checks
SPEC = SimpleNamespace(
    synthetic_wikitext=lambda d: {p['snapshot_file']: synthetic_page(d, p['key']) for p in d['pages']},
    wikitext_checks=snapshot_checks,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--wikitext-dir', type=Path)
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.write:
        if not a.wikitext_dir:
            print('FAIL --write needs --wikitext-dir')
            return 1
        return write(a.wikitext_dir)
    data = json.loads(OUT.read_text())
    if a.wikitext_dir:
        return report(snapshot_checks(data, a.wikitext_dir), f'{len(data["pages"])} pinned revisions re-parse '
                      f'to the {len(data["boards"])} recorded boards and {len(data["setups"])} setups')
    return report(offline_checks(data), f'{len(data["boards"])} boards, {len(data["setups"])} setups re-derive')


if __name__ == '__main__':
    raise SystemExit(main())
