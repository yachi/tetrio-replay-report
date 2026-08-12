"""Transcribe harddrop.com's own opener diagrams into `wiki-openers.json`.

    python3 -m pipeline.openers.extract_wiki_openers            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_wiki_openers --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_wiki_openers --html-dir <dir> --write   # re-transcribe

WHY THIS EXISTS, given `opener-fields.json` already holds 783 catalogue pages.

`opener_db` draws a lot of its pages on a FILLED BASE — two solid rows under the interesting part,
so the reader can see the slot in a stack. 484 of its 783 pages carry at least one full row, and a
full row is a row that would have CLEARED, so such a page can never equal a real no-clear opening
field. It is a teaching diagram, not a board state.

That is not a defect in the catalogue; it is a mismatch with the question this repo asks. Measured:

  TKI-3        12 catalogue pages, 0 of them clean  -> unmeasurable from the catalogue at all
  Honey Cup     absent from the catalogue
  Stray Cannon  absent from the catalogue
  MS2 / MS3     absent from the catalogue

So four of the six openers this file covers cannot be measured against `opener_db`, and the wiki is
where their fields are drawn. The remaining two (Mountainous Stacking 1, Perfect Clear Opener) DO
have clean catalogue pages — and that overlap is the point, because it turns two independently
maintained sources into a CHECK: `cross_check()` requires the wiki transcription and the catalogue
to agree cell-for-cell wherever both draw the same opener. They do, and the gate says so.

WHAT A DIAGRAM LOOKS LIKE. harddrop renders a board as a `<table style="line-height: 10px; ...">`
whose rows are `<div style="height: 12px;">` holding ten 12x12 `<img>` cells:

    Tet.png    empty          {I,J,L,O,S,T,Z}Tet.png   that piece
    GTet.png   grey "any"     PTet.png  the piece being placed (an ANNOTATION, not the field)
    KTet.png   dark checker   {digit}Tet.png  a placement-order number (also an annotation)

`FIELD_CELLS` is the set that may appear in a field. A board holding anything else is an annotated
illustration — the parity checkerboards on the PCO page, the numbered placement orders on the TKI-3
page — and is dropped rather than transcribed, because its cells do not mean "occupied".

WHY THE SOURCE HTML IS NOT COMMITTED. The five pages are 7.7 MB of markup whose every cell is a
separate <img> tag; the transcription is 4 KB. What is committed instead is the transcription plus
each page's sha256 and oldid, so a re-fetch either reproduces the file byte for byte or names the
page that changed. Re-fetching needs network and is therefore NOT a CI gate; what CI runs is
`verify()`, which is offline and checks the two things a bad transcription would break — internal
consistency, and agreement with the catalogue where both sources draw the same opener.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'wiki-openers.json'
CATALOGUE = HERE / 'opener-fields.json'

WIDTH = 10

# ── the markup ─────────────────────────────────────────────────────────────────────────────────
CELL = re.compile(r'cdn\.harddrop\.com/[0-9a-f]/[0-9a-f]{2}/([A-Za-z0-9]*)Tet\.png')
ROW = re.compile(r'<div style="height: 12px;">(.*?)</div>', re.S)
TABLE = re.compile(r'<table style="line-height: 10px;.*?</table>', re.S)
HEADLINE = re.compile(r'<span class="mw-headline" id="[^"]*">(.*?)</span>', re.S)
OLDID = re.compile(r'oldid=(\d+)')

EMPTY = '.'
#: cell codes that carry "this square is part of the field". `G` is the catalogue's own "any piece".
FIELD_CELLS = frozenset('IJLOSTZG')


def _text(html: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html)).strip()


def boards(html: str) -> list[dict]:
    """Every board diagram on a page, in document order, tagged with the heading above it.

    A diagram is kept only if every row is exactly `WIDTH` cells and every non-empty cell is in
    `FIELD_CELLS`. Both halves matter: the width check drops the wiki's narrower legend tables, and
    the cell check drops annotated illustrations whose colours encode something other than
    occupancy. Dropping is silent HERE and loud in `extract()`, which asserts a per-opener count —
    a wiki edit that removes a diagram must fail the re-transcription, not quietly shrink a metric.
    """
    heads = [(m.start(), _text(m.group(1))) for m in HEADLINE.finditer(html)]
    out: list[dict] = []
    for m in TABLE.finditer(html):
        rows = []
        for rm in ROW.finditer(m.group(0)):
            cells = [c or EMPTY for c in CELL.findall(rm.group(1))]
            if cells:
                rows.append(''.join(cells))
        if not rows or any(len(r) != WIDTH for r in rows):
            continue
        if any(c != EMPTY and c not in FIELD_CELLS for r in rows for c in r):
            continue
        heading = ''
        for pos, name in heads:
            if pos < m.start():
                heading = name
        out.append({'heading': heading, 'rows': rows})
    return out


def trim(rows: list[str]) -> list[str]:
    """Drop leading all-empty rows, so a field is stored as drawn rather than as padded."""
    first = next((i for i, r in enumerate(rows) if r != EMPTY * WIDTH), None)
    return [] if first is None else rows[first:]


def cells_of(rows: list[str]) -> int:
    return sum(1 for r in rows for c in r if c != EMPTY)


def has_full_row(rows: list[str]) -> bool:
    return any(all(c != EMPTY for c in r) for r in rows)


def occupancy(rows: list[str]) -> list[str]:
    return [''.join('#' if c != EMPTY else EMPTY for c in r) for r in rows]


# ── what to take from each page ────────────────────────────────────────────────────────────────
# `locks` is the number of pieces ALREADY LOCKED in the drawn field, i.e. cells/4 — and it is
# written out rather than derived because it is the load-bearing number: an opener that keeps a
# piece in hold through bag 1 shows SIX locks, and comparing it against a seven-lock board can only
# ever fail. Four of the six openers here are six-lock openers, which is why the emitter had to
# start sampling the board at more than one lock count.
#
# `expect` is asserted. It is the whole point of pinning a transcription to a specific `oldid`: if
# harddrop redraws a section, this file must fail rather than silently transcribe a different set.
SPEC: list[dict] = [
    {
        'key': 'honey_cup', 'wiki': 'Honey Cup', 'page': 'Honey_Cup', 'jp': 'はちみつ砲',
        'catalogue': None,
        'headings': ['Honey Cup'], 'locks': 7, 'expect': 1,
        'wiki_says': 'a TST to TSD opener; the Perfect Clear rate is 90%',
    },
    {
        'key': 'stray_cannon', 'wiki': 'Stray Cannon', 'page': 'Stray_Cannon', 'jp': '迷走砲',
        'catalogue': None,
        'headings': ['Bag 1'], 'locks': 6, 'expect': 2,
        'wiki_says': 'a TD opener; 75% build rate on bag 1 (90% with mirror) if S/Z is held',
    },
    {
        'key': 'mountainous_1', 'wiki': 'Mountainous Stacking', 'page': 'Mountainous_Stacking',
        'jp': '山岳積み', 'catalogue': 'Mountainous Stacking',
        'headings': ['First Bag'], 'locks': 6, 'expect': 2,
        'wiki_says': 'a Triple Double opener; T-Spin Triple in the second bag, Perfect Clear chance '
                     'in the third; 53.33% setup rate counting the mirror',
    },
    {
        'key': 'mountainous_2', 'wiki': 'Mountainous Stacking 2', 'page': 'Mountainous_Stacking',
        'jp': '山岳積み2', 'catalogue': None,
        'headings': ['Mountainous Stacking 2'], 'locks': 6, 'expect': 2,
        'wiki_says': 'successor to Mountainous Stacking; the L piece (J mirrored) is held until the '
                     'second bag; 100% stack rate counting the mirror',
    },
    {
        'key': 'mountainous_3', 'wiki': 'Mountainous Stacking 3', 'page': 'Mountainous_Stacking',
        'jp': '山岳積み3', 'catalogue': None,
        'headings': ['Mountainous Stacking 3'], 'locks': 6, 'expect': 2,
        'wiki_says': 'successor to Mountainous Stacking 2; the O piece is held; for a J/L start',
    },
    {
        'key': 'tki_3', 'wiki': 'TKI 3 Opening', 'page': 'TKI_3_Opening', 'jp': '開幕TSD',
        'catalogue': 'TKI-3',
        'headings': ['Castle Top variation', 'Fonzie variation', 'Flat Top variation',
                     'Early J setup'],
        'locks': 6, 'expect': 4, 'first_per_heading': True,
        'wiki_says': 'three T-Spin Doubles and a T-Spin Triple to finish; the I piece comes before Z',
    },
    {
        'key': 'pco', 'wiki': 'Perfect Clear Opener', 'page': 'Perfect_Clear_Opener',
        'jp': 'パフェクリテンプレ', 'catalogue': 'Perfect Clear Opener',
        'headings': ['First PC Success Rates'], 'locks': None,
        'expect': 4,
        'wiki_says': 'the standard way to get a Perfect Clear in the first 4 lines (10 dropped '
                     'pieces); 84.6% if the I piece is kept on hold, 61.2% if it is dropped',
    },
]

#: harddrop's own category page. This is the CONTROL for the ordering metric: "a T-spin Triple
#: before a T-spin Double" is the signature of this whole category, not of any one opener in it, so
#: the class has to be published next to the number. Transcribed from the category listing rather
#: than inferred from the six pages above, because a class the repo drew itself would be a class
#: chosen to fit the result.
TRIPLE_DOUBLE_CATEGORY = {
    'name': 'Triple Double openers',
    'url': 'https://harddrop.com/wiki/Category:Triple_Double_openers',
    'says': 'openers that begin with a Triple Double Attack, or any variant thereof',
    #: the page's own count ("The following 38 pages are in this category, out of 38 total").
    #: `verify()` asserts `len(members) == declares`, because the first transcription of this list
    #: silently dropped `PC-Spin (Okey Version)` — its link text and tooltip differ, so a regex
    #: keyed on them agreeing returned 37 and looked complete.
    'declares': 38,
    'members': [
        '1-11th Compromise Cannon', '1-5th End Cannon', 'Aitch Stacking', 'Azyara Spin',
        'Bakery TD', 'C-Spin', 'Desert stacking', 'Donut Stacking', 'Dot Cannon',
        'Gamushiro Stacking', 'Gravity TD', 'Hardtack Stacking', 'Honey Cup', 'Lime Stacking',
        'Loyal TD', 'Magic TD', 'Manhole Stacking', 'Mountainous Stacking', 'OJI Honey Cup',
        'Olive Stacking', 'Operability TD', 'PC-Spin', 'PC-Spin (Okey Version)',
        'Pancake Stacking', 'Plate TD',
        'Pseudo-PC', 'Rabbit Stacking', 'Ruby Stacking', 'SkTD', 'Solitary Moon Stacking',
        'Stray Cannon', 'Tandoori Chicken Stacking', 'Triple Triple PC', 'Tsar Cannon',
        'Waiting Moon Stacking', 'Yamaha Stacking', 'Yuchan Cannon', '：-0 Stacking',
    ],
}


# ── transcription ──────────────────────────────────────────────────────────────────────────────
def extract(html_dir: Path) -> dict:
    pages: dict[str, str] = {}
    for spec in SPEC:
        pages.setdefault(spec['page'], '')
    for name in pages:
        p = html_dir / f'raw-{name}.html'
        if not p.exists():
            raise SystemExit(
                f'missing {p}. Fetch the five pages first, e.g.\n'
                f'  firecrawl scrape "https://harddrop.com/wiki/{name}" '
                f'--format rawHtml -o {html_dir}/raw-{name}.html')
        pages[name] = p.read_text(encoding='utf8', errors='replace')

    openers = []
    for spec in SPEC:
        html = pages[spec['page']]
        found = [b for b in boards(html) if b['heading'] in spec['headings']]
        # A field is a board state, so a row that would have cleared disqualifies it. This is what
        # excludes the TKI-3 "Dingle variation" diagram, which is drawn after its line clears.
        found = [b for b in found if not has_full_row(trim(b['rows']))]
        if spec['locks'] is not None:
            found = [b for b in found if cells_of(trim(b['rows'])) == spec['locks'] * 4]
        if spec.get('first_per_heading'):
            seen: set[str] = set()
            first = []
            for b in found:
                if b['heading'] not in seen:
                    seen.add(b['heading'])
                    first.append(b)
            found = first
        if len(found) != spec['expect']:
            raise SystemExit(
                f'{spec["key"]}: expected {spec["expect"]} diagrams under '
                f'{spec["headings"]}, found {len(found)}. The wiki page changed — read it, then '
                f'update SPEC deliberately rather than relaxing the count.')

        fields = []
        for b in found:
            rows = trim(b['rows'])
            n = cells_of(rows)
            if n % 4:
                raise SystemExit(f'{spec["key"]}: {n} cells is not a whole number of pieces')
            fields.append({'heading': b['heading'], 'locks': n // 4, 'cells': n, 'rows': rows})
        openers.append({
            'key': spec['key'], 'wiki': spec['wiki'], 'jp': spec['jp'],
            'catalogue': spec['catalogue'],
            # the harddrop PAGE, which is what the category listing names. MS1/2/3 share one page,
            # so membership of "Triple Double openers" is a property of the page, not of the title:
            # keying it on `wiki` reported Mountainous Stacking 2 and 3 as outside the category
            # their own article sits in.
            'page': spec['page'].replace('_', ' '),
            'url': f'https://harddrop.com/wiki/{spec["page"]}',
            'wiki_says': spec['wiki_says'],
            'headings': spec['headings'], 'fields': fields,
        })

    provenance = []
    for name, html in sorted(pages.items()):
        ids = OLDID.findall(html)
        provenance.append({
            'page': name,
            'url': f'https://harddrop.com/wiki/{name}',
            'oldid': int(max(ids, key=int)) if ids else None,
            'sha256': hashlib.sha256(html.encode('utf8', 'replace')).hexdigest(),
            'bytes': len(html),
        })

    return {
        'schema': 'wiki-openers/1',
        'source': 'harddrop.com/wiki',
        'why': 'opener_db draws 484 of its 783 pages on a filled base, and a page with a full row '
               'can never equal a no-clear opening field; four of these six openers have no clean '
               'catalogue page at all',
        'cell_legend': {'.': 'empty', '#': 'occupied (occupancy view)',
                        'IJLOSTZ': 'that piece as drawn', 'G': 'grey — any piece'},
        'triple_double_category': TRIPLE_DOUBLE_CATEGORY,
        'provenance': provenance,
        'openers': openers,
    }


# ── verification (offline; this is what CI runs) ───────────────────────────────────────────────
def cross_check(data: dict) -> list[dict]:
    """Every opener drawn by BOTH sources must agree on occupancy, as drawn or mirrored.

    This is the dual-source argument the repo rests on, applied to the opener fields: the wiki and
    opener_db are maintained by different people from different diagrams, so an agreement is
    evidence and a disagreement is a finding.

    `named` and `clean` are reported separately and that separation is the interesting part. TKI-3
    has twelve catalogue pages and NOT ONE of them is clean, so a checker that only counted usable
    pages would print 0 and read as "the catalogue has never heard of TKI-3" — when what is
    actually true is "the catalogue draws TKI-3 twelve times, always on a filled base". Only the
    second sentence explains why this file has to exist.

    The catalogue name is DECLARED per opener (`catalogue` in SPEC), not guessed from the wiki
    title: the wiki calls it `TKI 3 Opening` and opener_db calls it `TKI-3 {Alt: TKI, ...}`, so a
    substring match on the wiki title finds nothing and would have reported a real overlap as an
    absence.
    """
    pages = json.loads(CATALOGUE.read_text())['pages']
    by_key = {s['key']: s.get('catalogue') for s in SPEC}
    results = []
    for op in data['openers']:
        needle = by_key.get(op['key'])
        named = ([] if not needle
                 else [p for p in pages if needle.lower() in p['name'].lower()])
        clean = [p for p in named if not has_full_row(p['rows'])]
        occ_cat = {tuple(occupancy(p['rows'])) for p in clean}
        occ_cat |= {tuple(occupancy(mirror(p['rows']))) for p in clean}
        agreed, missing = [], []
        for f in op['fields']:
            o = tuple(occupancy(f['rows']))
            (agreed if o in occ_cat else missing).append(f['heading'])
        results.append({'key': op['key'], 'catalogue_name': needle,
                        'catalogue_pages_named': len(named), 'catalogue_pages_clean': len(clean),
                        'agreed': len(agreed), 'not_in_catalogue': len(missing)})
    return results


SWAP = {'L': 'J', 'J': 'L', 'S': 'Z', 'Z': 'S'}


def mirror(rows: list[str]) -> list[str]:
    return [''.join(SWAP.get(c, c) for c in reversed(r)) for r in rows]


def verify(data: dict) -> list[str]:
    """Offline consistency. Returns a list of problems; empty means the file is sound."""
    bad: list[str] = []
    keys = [o['key'] for o in data['openers']]
    if len(keys) != len(set(keys)):
        bad.append('duplicate opener keys')
    if {s['key'] for s in SPEC} != set(keys):
        bad.append('openers do not match SPEC')
    for op in data['openers']:
        if not op['fields']:
            bad.append(f'{op["key"]}: no fields')
        for f in op['fields']:
            rows = f['rows']
            if any(len(r) != WIDTH for r in rows):
                bad.append(f'{op["key"]}: a row is not {WIDTH} cells wide')
            if has_full_row(rows):
                bad.append(f'{op["key"]}: a full row would have cleared — not a board state')
            if cells_of(rows) != f['cells'] or f['cells'] != f['locks'] * 4:
                bad.append(f'{op["key"]}: cells/locks disagree with the drawing')
            if rows and rows[0] == EMPTY * WIDTH:
                bad.append(f'{op["key"]}: field is not top-trimmed')
    for r in cross_check(data):
        if r['catalogue_pages_clean'] and r['not_in_catalogue']:
            bad.append(f'{r["key"]}: {r["not_in_catalogue"]} field(s) disagree with the '
                       f'{r["catalogue_pages_clean"]} clean catalogue page(s) drawing the same '
                       f'opener')
    cat = {p['name'] for p in json.loads(CATALOGUE.read_text())['pages']}
    if not cat:
        bad.append('catalogue is empty')

    tdc = data['triple_double_category']
    if len(tdc['members']) != tdc['declares']:
        bad.append(f'Triple Double category lists {len(tdc["members"])} openers but the page '
                   f'declares {tdc["declares"]}')
    if len(set(tdc['members'])) != len(tdc['members']):
        bad.append('Triple Double category has a duplicate member')
    # the control is only a control if the openers it is quoted against are IN it
    for name in ('C-Spin', 'Honey Cup', 'Mountainous Stacking', 'Stray Cannon'):
        if name not in tdc['members']:
            bad.append(f'{name} is missing from the Triple Double category — the ordering '
                       f'metric\'s control no longer covers the openers it is quoted against')
    return bad


def selftest() -> int:
    """A verifier nothing can fail is decorative. Plant each defect it claims to catch."""
    base = json.loads(OUT.read_text())
    if verify(base):
        print('selftest: the committed file does not verify — fix that first', file=sys.stderr)
        return 1

    def mutate(fn, label):
        d = json.loads(OUT.read_text())
        fn(d)
        if not verify(d):
            print(f'selftest FAILED: {label} was not caught', file=sys.stderr)
            return False
        print(f'  killed: {label}')
        return True

    def flip_cell(d):
        # flip one cell of an opener the CATALOGUE also draws, so cross_check is the thing that
        # fires — this is the mutant that proves the dual-source gate, not just the shape checks
        op = next(o for o in d['openers'] if o['key'] == 'pco')
        rows = op['fields'][0]['rows']
        r = rows[0]
        i = r.index('.')
        rows[0] = r[:i] + 'G' + r[i + 1:]
        op['fields'][0]['cells'] += 1

    def fill_row(d):
        d['openers'][0]['fields'][0]['rows'][0] = 'G' * WIDTH

    def drop_opener(d):
        d['openers'] = d['openers'][1:]

    def bad_locks(d):
        d['openers'][0]['fields'][0]['locks'] += 1

    ok = all([
        mutate(flip_cell, 'a cell flipped on an opener the catalogue also draws'),
        mutate(fill_row, 'a full row (a state that would have cleared)'),
        mutate(drop_opener, 'an opener removed'),
        mutate(bad_locks, 'locks disagreeing with the cell count'),
    ])
    print('selftest: all mutants killed' if ok else 'selftest: FAILED')
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    ap.add_argument('--html-dir', type=Path,
                    help='directory of raw-<Page>.html snapshots; required with --write')
    ap.add_argument('--write', action='store_true', help='rewrite wiki-openers.json')
    ap.add_argument('--selftest', action='store_true', help='prove the verifier has teeth')
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if args.write:
        if not args.html_dir:
            ap.error('--write needs --html-dir')
        data = extract(args.html_dir)
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(f'wrote {OUT.relative_to(HERE.parent.parent)}')
    else:
        data = json.loads(OUT.read_text())

    problems = verify(data)
    for op in data['openers']:
        locks = sorted({f['locks'] for f in op['fields']})
        print(f'  {op["key"]:16s} {len(op["fields"])} field(s), {locks} lock(s)  {op["wiki"]}')
    for r in cross_check(data):
        note = ('agrees with the catalogue'
                if r['catalogue_pages_clean'] and not r['not_in_catalogue']
                else 'no clean catalogue page' if not r['catalogue_pages_clean']
                else 'DISAGREES')
        print(f'  cross-check {r["key"]:16s} catalogue named={r["catalogue_pages_named"]:2d} '
              f'clean={r["catalogue_pages_clean"]:2d}  {note}')
    print(f'  Triple Double category: {len(TRIPLE_DOUBLE_CATEGORY["members"])} openers share the '
          f'Triple-then-Double signature')
    if problems:
        for p in problems:
            print(f'FAIL {p}', file=sys.stderr)
        return 1
    print('wiki-openers.json OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
