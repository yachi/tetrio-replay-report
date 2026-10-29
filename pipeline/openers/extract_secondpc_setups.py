"""Transcribe harddrop's Second Perfect Clear page into `secondpc-setups.json`, and gate the transcription.

    python3 -m pipeline.openers.extract_secondpc_setups                    # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_secondpc_setups --selftest         # prove the verifier has teeth
    python3 -m pipeline.openers.extract_secondpc_setups --wikitext-dir <d> # re-parse the pinned revision
    python3 -m pipeline.openers.extract_secondpc_setups --wikitext-dir <d> --write  # ...and rewrite the file

WHAT A SECOND PC IS, in the page's own words (quoted in the JSON's `source.definition`): the first Perfect
Clear takes three pieces of the second bag, and four are left over; the second Perfect Clear is a four-line
Perfect Clear from the empty board using those four pieces and six of the third bag. So every board on the
page is drawn from EMPTY, in a four-row frame.

THE SOURCE is one harddrop wiki page, `Second Perfect Clear` (`2nd PC` and `Second PC` redirect to it),
pinned as a MediaWiki revision exactly as the DPC pages are (`oldid`, MediaWiki's own `revision_sha1`, our
`snapshot_sha256` and `snapshot_bytes`); `check_wikitext_sources` discovers it (`*-setups.json`) and refetches
it weekly, re-running this module with `--wikitext-dir`. harddrop publishes no licence for wiki content, so
the page credits by link. Its sibling `Second perfect clear queuebased setups` is recorded in `source.declined`
and NOT transcribed: it draws next-bag pieces in lower case and some solutions after a line clear, which the
rule below does not read, and folding it in would be a second reading for one page.

THE TRANSCRIPTION IS A PARSE, NOT A HAND COPY. The board parser is `parse_page` below (one
reader of harddrop's `{{pfrow}}` templates; it was the DPC module's until that page moved to a video), so every token is mapped by the same table; a token this page's
rules do not read (anything but a piece letter, `G` or blank) is a failure here, never a guess.

THE ROLES, derived and checked here. A board is read with a lower-case
letter as its piece (the page shades a second piece of one letter, `'L`, where two touch). A board is
  * a SETUP when it holds no `G`: pieces placed from empty (the page's 「setup」), bottom-aligned in the
    four-row frame, no full row, each letter's cell count a multiple of four (rule `setup:`);
  * a SOLUTION when it holds `G`: every non-empty row full, four rows, its `G` cells EXACTLY the occupancy of
    the setup drawn before it in the same section (rule `solution:`), and its other letters whole pieces by count
    (a piece placed after a row under it cleared is drawn split, in the four-row frame).
    `G` is the page's grey: the setup's cells, drawn without their colours.
A board of neither kind fails. Each setup lists the solutions under it (`solutions`, in page order) and
`same_as`: the other setups with the identical letters, so a shape drawn twice is one shape.
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
OUT = HERE / 'secondpc-setups.json'
_W = 10

#: wikitext cell token -> transcription letter (harddrop's `{{pfrow}}` reader; it lived in the DPC module
#: until the DPC page moved to a video source on 2026-10-29, and moved here unchanged)
TOKENS = {'': '.', ' ': '.', 'G': 'G', 'P': 'P', 'N': 'N', 'F': 'F', 'Y': 'Y', '+': '+',
          **{x: x for x in 'IJLOSTZ'}, **{"'" + x: x.lower() for x in 'IJLOSTZ'}}
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
                rows.append('.' * _W)
                continue
            toks = [c.strip() if c.strip() else c for c in cells.split('|')]
            if len(toks) != _W:
                raise Bad(f'board {len(out)}: a pfrow with {len(toks)} cells: {cells!r}')
            bad = [t for t in toks if t not in TOKENS]
            if bad:
                raise Bad(f'board {len(out)}: unknown cell token(s) {bad}')
            rows.append(''.join(TOKENS[t] for t in toks))
        if not rows:
            raise Bad(f'board {len(out)}: no rows')
        out.append({'heading': [h for _, h in heads], 'table': table, 'rows': rows})
    return out


def _dpc_synthetic(data: dict, key: str) -> str:
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
        rows = ['{{pfrowblank}}' if r == '.' * _W else '{{pfrow|' + '|'.join(rev[c] for c in r) + '}}'
                for r in b['rows']]
        out.append('|{{pfstart}}\n' + '\n'.join(rows) + '\n{{pfend}}')
    return '\n'.join(out) + '\n'


W = 10
ROWS = 4
PIECES = set('IJLOSTZ')
#: a lower-case letter is the page's second piece of one letter, shaded so two touching pieces can be told
#: apart (`'L` in the wikitext); it is read as that piece
SHADED = {x.lower() for x in PIECES}
READ = PIECES | SHADED | {'.', 'G'}


def frame(rows: list[str]) -> list[str]:
    """The board's non-empty rows, bottom-aligned in the four-row frame; raises when it is taller."""
    body = [r for r in rows]
    while body and body[0] == '.' * W:
        body.pop(0)
    if len(body) > ROWS:
        raise Bad(f'frame: {len(body)} non-empty rows, the frame is {ROWS}')
    return ['.' * W] * (ROWS - len(body)) + body


def whole_pieces(bid: str, rows: list[str], rule: str) -> list[str]:
    """The piece letters of a board, one per four cells; raises unless each letter's cells are a multiple of
    four. Contiguity is NOT required: a solution is drawn in the frame of its four rows, so a piece placed
    after a row below it cleared is drawn split across that row (the route pages' kept-rows composite)."""
    out = []
    for letter in sorted(PIECES | SHADED):
        n = sum(row.count(letter) for row in rows)
        if n % 4:
            raise Bad(f'{rule}: {bid}: {n} {letter} cells is not whole pieces')
        out += [letter.upper()] * (n // 4)
    return sorted(out)


def occ(rows: list[str]) -> list[str]:
    return [''.join('.' if c == '.' else 'x' for c in r) for r in rows]


def derive(pages: list[dict]) -> tuple[list[dict], list[dict]]:
    """(boards, setups) from the page's parsed boards. Raises Bad on a rule a board breaks."""
    boards, setups = [], []
    for pg in pages:
        cur = None
        for i, b in enumerate(pg['boards']):
            bid = f'{pg["key"]}.{i:03d}'
            bad = set(''.join(b['rows'])) - READ
            if bad:
                raise Bad(f'token: {bid}: letters {sorted(bad)} are not read by this page\'s rules')
            rows = frame(b['rows'])
            cells = ''.join(rows)
            if 'G' not in cells:
                if any('.' not in r for r in rows):
                    raise Bad(f'setup: {bid}: a full row')
                pieces = whole_pieces(bid, rows, 'setup')
                cur = {'id': bid, 'page': pg['key'], 'heading': b['heading'], 'rows': rows,
                       'pieces': ''.join(pieces), 'solutions': []}
                setups.append(cur)
                kind = 'setup'
            else:
                if cur is None or cur['heading'] != b['heading']:
                    raise Bad(f'solution: {bid}: no setup drawn before it in its section')
                if any('.' in r for r in rows):
                    raise Bad(f'solution: {bid}: a row that is not full')
                g = [''.join('x' if c == 'G' else '.' for c in r) for r in rows]
                if g != occ(cur['rows']):
                    raise Bad(f'solution: {bid}: its G cells are not the occupancy of {cur["id"]}')
                n = whole_pieces(bid, rows, 'solution')
                if len(n) * 4 + sum(r.count('x') for r in g) != ROWS * W:
                    raise Bad(f'solution: {bid}: the pieces and the setup do not fill the frame')
                cur['solutions'].append(bid)
                kind = 'solution'
            boards.append({'id': bid, 'page': pg['key'], 'heading': b['heading'], 'table': b['table'],
                           'role': kind, 'rows': b['rows']})
    key: dict = {}
    for s in setups:
        key.setdefault(tuple(s['rows']), []).append(s['id'])
    for s in setups:
        s['same_as'] = [x for x in key[tuple(s['rows'])] if x != s['id']]
    return boards, setups


def snapshot_checks(data: dict, d: Path) -> list[str]:
    """`--wikitext-dir`: the pinned revision's bytes hashed against the record, re-parsed, and the whole
    transcription re-derived and compared."""
    bad, pages = [], []
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
    """The committed file alone: every setup and solution re-derived from its recorded board."""
    bad = []
    keys = [p['key'] for p in data['pages']]
    if len(set(keys)) != len(keys):
        bad.append(f'pages: duplicate keys {keys}')
    for p in data['pages']:
        for k in ('title', 'url', 'oldid', 'revision_sha1', 'snapshot_sha256', 'snapshot_bytes', 'snapshot_file'):
            if k not in p:
                bad.append(f'pages: {p.get("key")} has no {k}')
    for k in ('definition', 'declined'):
        if not data.get('source', {}).get(k):
            bad.append(f'source: no {k}')
    pages = []
    for p in data['pages']:
        mine = [b for b in data['boards'] if b['page'] == p['key']]
        if [b['id'] for b in mine] != [f'{p["key"]}.{i:03d}' for i in range(len(mine))]:
            bad.append(f'boards: {p["key"]} ids are not consecutive')
        for b in mine:
            if any(len(r) != W for r in b['rows']):
                bad.append(f'boards: {b["id"]} has a ragged row')
        pages.append({'key': p['key'], 'boards': [{k: b[k] for k in ('heading', 'table', 'rows')} for b in mine]})
    if bad:
        return bad
    try:
        boards, setups = derive(pages)
    except Bad as e:
        return [f'{e}']
    if [b['role'] for b in boards] != [b['role'] for b in data['boards']]:
        bad.append('boards: a recorded role differs from the one its rows give')
    if setups != data['setups']:
        bad.append('setups: re-derived from the recorded boards, they differ from the recorded setups')
    return bad


def synthetic_page(data: dict, key: str) -> str:
    """A page from the recorded boards alone, for selftests (the real bytes are not committed)."""
    return _dpc_synthetic(data, key)


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
    s0 = next(s for s in data['setups'] if s['solutions'])
    sol = s0['solutions'][0]

    def with_board(bid, fn):
        d = copy.deepcopy(data)
        b = next(b for b in d['boards'] if b['id'] == bid)
        b['rows'] = fn(b['rows'])
        return d

    def edit(rows, pick, to):
        r, c = next((r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if pick(ch))
        return [row[:c] + to + row[c + 1:] if i == r else row for i, row in enumerate(rows)]
    expect('a setup cell emptied (a piece no longer whole)',
           offline_checks(with_board(s0['id'], lambda rows: edit(rows, lambda ch: ch in PIECES, '.'))), True)
    expect('a solution G cell given a colour (G no longer the setup)',
           offline_checks(with_board(sol, lambda rows: edit(rows, lambda ch: ch == 'G', 'I'))), True)
    expect('a solution cell emptied (a row not full)',
           offline_checks(with_board(sol, lambda rows: edit(rows, lambda ch: ch in PIECES, '.'))), True)
    expect('a setup letter swapped (I to Z)',
           offline_checks(with_board(s0['id'], lambda rows: [r.replace('I', 'Z') for r in rows])
                          if 'I' in s0['pieces'] else with_board(s0['id'], lambda rows: [r.replace('O', 'Z') for r in rows])),
           True)
    d = copy.deepcopy(data)
    d['setups'][0]['solutions'] = d['setups'][0]['solutions'][1:] + ['main.999']
    expect('a recorded solution list edited', offline_checks(d), True)
    d = copy.deepcopy(data)
    d['boards'][0]['role'] = 'solution' if d['boards'][0]['role'] != 'solution' else 'setup'
    expect('a board role edited', offline_checks(d), True)
    d = copy.deepcopy(data)
    del d['pages'][0]['revision_sha1']
    expect('a page with no revision_sha1', offline_checks(d), True)
    d = copy.deepcopy(data)
    d['source']['declined'] = []
    expect('the declined sibling page unrecorded', offline_checks(d), True)
    with tempfile.TemporaryDirectory() as td:
        for p in data['pages']:
            (Path(td) / p['snapshot_file']).write_text(synthetic_page(data, p['key']))
        res = snapshot_checks(data, Path(td))
        expect('a synthetic page re-parses to the recorded boards (hash lines aside) (control)',
               [x for x in res if ': hash: ' not in x], False)
        expect('...and the synthetic bytes are not the pinned ones', [x for x in res if ': hash: ' in x], True)
        f = Path(td) / data['pages'][0]['snapshot_file']
        t = f.read_text()
        m = re.search(r'\{\{pfrow\|([^}]*)\}\}', t)
        cells = m.group(1).split('|')
        j = next(i for i, x in enumerate(cells) if x.strip())
        cells[j] = ' '
        f.write_text(t[:m.start(1)] + '|'.join(cells) + t[m.end(1):])
        expect('a board cell blanked in the page', [x for x in snapshot_checks(data, Path(td)) if ': hash: ' not in x],
               True)
        f.write_text(t[:m.start(1)] + '|'.join(['N'] + cells[1:]) + t[m.end(1):])
        expect('a token the rules do not read (the DPC pages\' N mark)',
               [x for x in snapshot_checks(data, Path(td)) if ': hash: ' not in x], True)
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
        return report(snapshot_checks(data, a.wikitext_dir), f'{len(data["pages"])} pinned revision re-parses '
                      f'to the {len(data["boards"])} recorded boards and {len(data["setups"])} setups')
    return report(offline_checks(data), f'{len(data["boards"])} boards, {len(data["setups"])} setups re-derive')


if __name__ == '__main__':
    raise SystemExit(main())
