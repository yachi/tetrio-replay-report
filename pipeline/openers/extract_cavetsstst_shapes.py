"""Transcribe harddrop's 「Cave TSS to TST」 boards into `cavetsstst-technique.json`.

    python3 -m pipeline.openers.extract_cavetsstst_shapes                  # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_cavetsstst_shapes --selftest       # prove the verifier has teeth
    python3 -m pipeline.openers.extract_cavetsstst_shapes --html-dir <dir> # re-check the pinned revision
    python3 -m pipeline.openers.extract_cavetsstst_shapes --wikitext-dir <dir>  # the same, as the weekly job runs it
    python3 -m pipeline.openers.extract_cavetsstst_shapes --html-dir <dir> --write  # ...and rewrite

A T-spin Single that leaves the slot for a T-spin Triple. yachi asked for it on 2026-11-12 from a YouTube short
(WylieCan'tGame, 「I'm a T-Spin WIZARD」, vr1N137z038, Tetris Effect: Connected): the T stood into a one-column slot
under an overhang, nub toward the open side, clears the bottom row; the T's own remnant and the overhang are then
the walls of a TST slot one column over. shiwehi.com draws no such page (measured 2026-11-12: its template index
names none). harddrop draws it as 「Cave TSS to TST」, three boards on its T-Spin Triple Setups page (the same pinned
revision King Crimson reads), and that is the primary source; every board is checked against it.

DECISION: the spin is a TSS (a full T-spin, 1 line) and the anchor is the T's four cells — the T STOOD UP, nub toward
the open side (right as drawn, left mirrored). The follow-up is the TST the TSS leaves room for: a second T stood up
one column further over, nub back toward the first T's remnant (`followup.lines` 3). Its slot sits partly in the
rows the TSS clears, so the row map joins it, as BT砲's and 千鳥格子's.

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`). harddrop draws the setup on an empty stack and the
short plays it on a full one, so a bounding box of T, roof and follow-up would read cells the two disagree on (the
right-hand stack, built on the short and not yet on harddrop's board). The window is the box on which harddrop's
board and the short's board agree: four rows by four columns, from the overhang down to the cleared row, from the
wall column beside the stem to the column the TST will stand in. Widening it meets a disagreement (above the
overhang the short's left stack is two cells high, harddrop's is empty; right of the window the short's stack is
built) or leaves harddrop's board (its floor, its left wall).

WHAT IS AN INFERENCE, flagged in the JSON (`legend`, `reading`, `cross_source.video`) rather than in prose only:

  * harddrop never mutes a cleared row, so its spin board is a named `:muting` discrepancy.
  * harddrop's `g` (dark grey, under the setup) is read `c`, `G` (the stack built around the TST slot after the TSS)
    `q`, and `T` on the third board, the TSS's T cut by its clear, `t` (not the spin's `U`).
  * the short's board is read by eye off the frame at 5.35 s (palette sampling misread Tetris Effect's lit cells);
    it is recorded six rows tall, the overhang's row and the five around it, one column right of harddrop's.
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_btcannon_shapes import _sections, _tabled
from pipeline.openers.route_transcription import EMPTY, WIDTH
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
OUT = HERE / 'cavetsstst-technique.json'

ALPHABET = frozenset('-cqUlt')
MAX_ROWS = 6
#: the page-order indexes (0-based, every board of the page) of the three Cave TSS to TST boards
FIRST_BOARD = 44


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://harddrop.com/wiki/T-Spin_Triple_Setups',
    'edit_url': 'https://harddrop.com/w/index.php?title=T-Spin_Triple_Setups&action=edit',
    'title': 'T-Spin Triple Setups (Cave TSS to TST)',
    'site': 'harddrop.com (Hard Drop Tetris Wiki, MediaWiki)',
    'author_note': 'the page is harddrop\'s, edited by its wiki editors; it names no inventor for this setup',
    'section': 'Garbage Manipulation',
    'label_text': "'''Cave TSS to TST'''",
    'oldid': 42323,
    'revision_sha1': '0e64836c95d3214bb8c83a5151cbe72763717aef',
    'revision_timestamp': '2025-02-21T13:50:15Z',
    'updated': '2025-02-21',
    'revision_note': 'MediaWiki\'s own sha1 of revision 42323 (read from the API), equal to sha1 of the saved bytes: a '
                     'second authority beside snapshot_sha256, which is ours; the same revision King Crimson pins '
                     '(kingcrimson-technique.json cross_source.pages[0]), the page\'s latest when fetched',
    'fetched': '2026-11-12',
    'fetch_method': 'the pinned revision\'s own bytes from the MediaWiki API (api.php?action=query&prop=revisions&'
                    'titles=T-Spin_Triple_Setups&rvprop=ids|sha1|content|timestamp&rvslots=main&format=json&'
                    'formatversion=2), with Python\'s urllib and a descriptive User-Agent (NOT curl). Boards are '
                    '{{pfstart}} … {{pfend}} templates, read by route_transcription.wikitext_boards with '
                    '`wikitext_readings`; only the three Cave TSS to TST boards are transcribed',
    'snapshot_file': 'T-Spin_Triple_Setups.wikitext',
    'snapshot_sha256': '8ae446b1b7d9b4e8733fd0f4338b1b0279e8fb2609f9c5e612e2e8ee5a0a2042',
    'snapshot_bytes': 48802,
    'snapshot_note': 'sha256 of the revision\'s bytes as the API serves them. The page is not committed; the weekly '
                     '`wikitext-sources` job refetches the pinned revision, checks both hashes and re-runs '
                     '--wikitext-dir, and fails when the page has a newer revision.',
    'wikitext_readings': {'g': 'c', 'G': 'q', 'T': 't', "'L": 'v', '-T': EMPTY, '-': EMPTY, 'Q': 'q'},
    'wikitext_readings_note': 'route_transcription.wikitext_cell reads blank as -, P as U and a piece letter as its '
                              'lower case; this page also draws `g` (dark grey under the setup, read c), `G` (the '
                              'stack built around the TST slot, read q: filled, no piece), `T` (the TSS\'s T cut by its '
                              'clear, read t), and on boards this file does not transcribe `\'L` and `-T`, which are '
                              'given a reading only so the page parses; `Q` (read q) is what the synthetic page writes '
                              'for q, which the real page never draws',
    'boards_not_transcribed': [
        {'boards': [0, FIRST_BOARD - 1], 'heading': 'every setup before Cave TSS to TST',
         'reason': 'other T-spin Triple setups; this file transcribes the three Cave TSS to TST boards only'},
        {'boards': [FIRST_BOARD + 3, 162], 'heading': 'every setup after Cave TSS to TST',
         'reason': 'other T-spin Triple setups; this file transcribes the three Cave TSS to TST boards only'},
    ],
    'shiwehi': {'checked': '2026-11-12',
                'index': 'https://shiwehi.com/tetris/template/ (its 中盤テンプレ・ドネイト list names no TSS into a TST)',
                'note': 'no shiwehi.com page draws this setup, so harddrop\'s boards are the primary source'},
}

TERMS = {
    'url': 'https://harddrop.com/wiki/Hard_Drop_Tetris_Wiki:About',
    'dated': 'not stated: harddrop publishes no licence or terms page for wiki content',
    'read': '2026-10-15, for SDPC Spin (sdpcspin-routes.json): the page footer and the About page it links (no body); '
            'not re-read for this page',
    'allows': 'not stated (no licence is published)',
    'excludes': 'not stated (no licence is published)',
    'requests': 'not stated; credited by link, as this repo credits every harddrop page it reads',
    'how_met': 'source link to the harddrop page in every page header; no ads on GitHub Pages',
}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall',
    '-': 'empty',
    'c': 'a cell drawn dark grey (harddrop g): placed before this diagram, any piece or garbage',
    'q': 'a cell drawn grey (harddrop G): the stack built around the TST slot after the TSS, no piece named (OUR READING)',
    'l': 'a cell of the L (the overhang)',
    'U': 'a cell of the T the spin places (harddrop P)',
    't': 'a cell of the TSS\'s T left by its clear (harddrop T on the third board; OUR READING)',
    'muting': 'harddrop never draws the row a spin clears muted, so the spin board is a named `:muting` discrepancy',
}

QUOTES = [
    {'id': 'h.section', 'verbatim': '=== Garbage Manipulation ==='},
    {'id': 'label', 'verbatim': "'''Cave TSS to TST'''"},
    {'id': 'ez', 'verbatim': 'EZ TSS'},
]

NODES = [
    {'id': 'terrain', 'table': 0, 'board': 0, 'kind': 'base', 'caption_quote': 'label',
     'label': 'the terrain: a single garbage block in the corner, a garbage row with its hole one column in',
     'rows': _b('---------- ---------- ---------- ---------- c--------- c-cccccccc')},
    {'id': 'tss', 'table': 0, 'board': 1, 'kind': 'derived', 'derived': True, 'caption_quote': 'ez',
     'label': 'an L hung over the hole (harddrop draws it only with the T in)',
     'rows': _b('---------- ---------- lll------- l--------- c--------- c-cccccccc'), 'on': 'terrain', 'adds': 'l'},
    {'id': 'tss.spin', 'table': 0, 'board': 1, 'kind': 'spin', 'caption_quote': 'ez',
     'label': 'the T stood up under the L, nub right: a T-spin Single',
     'rows': _b('---------- ---------- lll------- lU-------- cUU------- cUcccccccc'),
     'on': 'tss', 'adds': 'U', 'spin_of': 'tss', 'spin_piece': 'U', 'spin': 'TSS', 'lines': 1},
    {'id': 'tss.after', 'table': 0, 'board': 2, 'kind': 'derived', 'derived': True, 'caption_quote': 'ez',
     'label': 'what the TSS leaves: the L and the T\'s three cells, a row lower',
     'rows': _b('---------- ---------- ---------- lll------- lt-------- ctt-------')},
    {'id': 'tst', 'table': 0, 'board': 2, 'kind': 'build', 'caption_quote': 'label',
     'label': 'the stack built around a TST slot beside the T\'s remnant, roofed one column over',
     'rows': _b('---------- ---qqqqqqq ----qqqqqq lll-qqqqqq lt--qqqqqq ctt-qqqqqq'), 'on': 'tss.after', 'adds': 'q'},
]

_SLOT = [[3, 1], [4, 1], [4, 2], [5, 1]]

VARIANTS = [{
    'id': 'cavetsstst', 'board': 'tss.spin', 'spin': 'TSS', 'lines': 1,
    'credit': 'mini',
    'credit_note': 'the engine credits this TSS as a MINI T-spin Single (probed 2026-11-12 with the demo planner\'s '
                   'reach() on harddrop\'s board and on the short\'s: the only arrival is spin "mini"). Of the four '
                   'corners of the T\'s centre three are filled, but on the nub side only one, so it is a mini under '
                   'TETR.IO\'s rule; the matcher measures the variant at a mini TSS and the follow-up TST at a full one. '
                   'extra_checks re-counts the corners on every drawing.',
    'window_basis': 'agreement',
    'window': {'rows': [2, 5], 'cols': [0, 3]},
    't_cells': _SLOT,
    'roof_cells': [[2, 0], [2, 1], [2, 2]],
    'window_note': 'in tss.spin\'s frame, row 0 the top: the AGREEMENT BOX of harddrop\'s board and the short\'s. Row 2 '
                   'is the overhang (the L over the stem and the wall column, open over the column the TST will stand '
                   'in); rows 3 and 4 the stem\'s wall on the left and the open cells right of the T, where the TST '
                   'goes; row 5 the row the TSS clears (entailed by the clear at a full TSS, NaiveClauseForced). Above '
                   'row 2 the two drawings disagree (the short\'s left stack goes two rows higher); right of column 3 '
                   'they disagree (the short\'s right stack is built, harddrop\'s is not yet); below row 5 and left of '
                   'column 0 harddrop\'s board ends. Occupancy only, never colour; garbage is filled.',
    'agreement': [{'board': 'tss', 't_cells': _SLOT, 'mirrored': False}],
    'untested_drawn': {'cells': [], 'reason': ''},
    'followup': {'board': 'tst', 'spin': 'TST', 'lines': 3,
                 't_cells_pre_clear': [[2, 3], [3, 2], [3, 3], [4, 3]],
                 't_cells_after': [[3, 3], [4, 2], [4, 3], [5, 3]],
                 'note': 'the TST: a second T stood up in the column right of the first, nub left into the cell beside '
                         'the first T\'s remnant, roofed by the stack built over it. The TSS clears the row under it, '
                         'so the row map carries its cells down a row; the matcher checks it fires as a full T-spin '
                         'Triple at the next T.'},
    'fires_on': ['tss'],
    'misses': ['terrain', 'tss.after', 'tst'],
}]

#: the short's board, read by eye off one frame (no colour, occupancy only): the T removed, its slot recorded
VIDEO = {
    'url': 'https://www.youtube.com/shorts/vr1N137z038',
    'id': 'vr1N137z038',
    'title': 'I’m a T-Spin WIZARD',
    'channel': 'WylieCan\'tGame',
    'uploaded': '2024-11-26',
    'game': 'Tetris Effect: Connected',
    'fetched': '2026-11-12',
    'fetch_method': 'yt-dlp, format 299 (1080x1920, 60 fps, video only), through a Tailscale exit node',
    'file_sha256': '81f2a6b0a95840a7a0f05670e952b4d48b6f91f783ee4b3374c9a73c62c719fa',
    'file_bytes': 10428013,
    'file_note': 'the download is not committed and nothing refetches it; its hash is ours alone',
    'frame_s': 5.35,
    'reading': 'read by eye off the frame at 5.35 s (the T resting in its slot before it locks); palette sampling '
               'misread Tetris Effect\'s lit cells. Six rows: the overhang\'s row, the two above it and the three '
               'under it, the bottom one the row the TSS clears; the rows above are higher stack and the rows below '
               'garbage, neither read by the window. One column right of harddrop\'s board.',
    'rows': _b('cc--cccccc cc---ccccc cccc-ccccc cc---ccccc cc---ccccc cc-ccccccc'),
    't_cells': [[3, 2], [4, 2], [4, 3], [5, 2]],
    'mirrored': False,
    'after_s': 10.25,
    'after_note': 'at 10.25 s the short fires the TST into the column right of the first T (its stem rows 3-5 and its '
                  'nub on the row the TSS left beside the remnant, in the frame after the clear), as the follow-up '
                  'slot says',
}

CROSS_SOURCE = {
    'kind': 'video',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of '
            'every committed *-routes.json, with the U cells as the T: it fires on none. The independent drawing is the '
            'short yachi sent (`video`), whose board is the window\'s external `agreement` drawing: rule (g) fires the '
            'window on it, once, at its slot, as drawn.',
    'routes_fire_none': 'no committed routes file draws a TSS under an overhang into a TST (measured: the window fires '
                        'on none of their U-slot boards); the cross-check is the short, below',
    'video': VIDEO,
    #: over the WHOLE pinned page, every board with a drawn T (P) at which the window fires, either hand
    'page_fires': [{'board': FIRST_BOARD + 1, 'mirrored': False}],
    #: every board of every OTHER committed technique transcription on which the window fires
    'other_techniques': [],
    'fires': [],
    'also': [],
    'labelled_not_fired': [],
}

KNOWN_DISCREPANCIES = [
    {'id': 'tss.spin:muting', 'note': 'harddrop draws the row the TSS clears in the same letters as the rest (it never '
                                      'mutes a cleared row)'},
    {'id': 'tss.after:colour', 'note': 'the TSS\'s T is three cells after its clear (the fourth was in the cleared '
                                       'row): a piece cut by a line clear, not a whole T'},
    {'id': 'tst:colour', 'note': 'the same three cells of the TSS\'s T, drawn as harddrop draws them (T)'},
]

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'cavetsstst',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'empty_letters': '',
        'quotes': QUOTES,
        'nodes': NODES,
        'page_order': PAGE_ORDER,
        'basic_form': [],
        'variants': VARIANTS,
        'cross_source': CROSS_SOURCE,
        'known_discrepancies': KNOWN_DISCREPANCIES,
    }


def video_drawings(data: dict | None = None) -> list[dict]:
    """The short's board as an agreement drawing: its slot read as empty."""
    v = (data or build())['cross_source']['video']
    return [{'name': f'video {v["id"]} at {v["frame_s"]} s', 'rows': list(v['rows']),
             't_cells': v['t_cells'], 'mirrored': v['mirrored']}]


# ── the whole page ───────────────────────────────────────────────────────────────────────────────
def _slot(rows: list[str]) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == 'U'}


def page_fires(data: dict, text: str) -> list[dict]:
    """Every board of the page with a drawn four-cell T (P) at which the window fires, either hand."""
    v = data['variants'][0]
    # every board, read with the source's readings plus the page's shaded lower-case pieces read as that piece
    # (only the drawn P decides anything here; the rest is occupancy)
    readings = {**{ch: ch for ch in 'ijlostz'}, **data['source']['wikitext_readings']}
    boards = RT.wikitext_boards(text, readings=readings)
    out = []
    for k, rows in enumerate(boards):
        s = _slot(rows)
        if len(s) != 4:
            continue
        pre = [row.replace('U', EMPTY) for row in rows]
        for m in (False, True):
            if TT.window_fires(data, v, SPEC, pre, s, m):
                out.append({'board': k, 'mirrored': m})
    return out


def page_problems(data: dict, text: str) -> list[str]:
    """The page around the three boards: the label sits under its section heading and directly before the table
    holding them, and the window fires at the drawn T of no board but the recorded ones."""
    bad = []
    text = _tabled(text)
    src = data['source']
    k = text.find(src['label_text'])
    if k < 0:
        return [f'source: the label {src["label_text"]!r} is not on the page']
    secs = _sections(text)
    t = text[:k].count('{|')
    if t >= len(secs) or secs[t] != src['section']:
        bad.append(f'source: the table after the label sits under {secs[t] if t < len(secs) else None!r}, '
                   f'not {src["section"]!r}')
    if text[:k].count('{{pfstart}}') != FIRST_BOARD:
        bad.append(f'source: the label precedes board {text[:k].count("{{pfstart}}")}, the record says {FIRST_BOARD}')
    try:
        got = page_fires(data, text)
    except ValueError as e:
        return bad + [f'source: the page does not parse: {e}']
    key = lambda e: (e['board'], e['mirrored'])
    if sorted(map(key, got)) != sorted(map(key, data['cross_source']['page_fires'])):
        bad.append(f'source: the window fires at the drawn T of boards {sorted(map(key, got))}, the record names '
                   f'{sorted(map(key, data["cross_source"]["page_fires"]))}')
    return bad


def wikitext_checks(data: dict, html_dir: Path) -> list[str]:
    """`--wikitext-dir`: the pinned revision through the shared snapshot reader (its hash line tagged `source: hash:`,
    the line the weekly selftest excuses offline), MediaWiki's sha1, and the page around the boards."""
    src = data['source']
    p = Path(html_dir) / src['snapshot_file']
    if not p.exists():
        return [f'source: {src["snapshot_file"]} is not in {html_dir}']
    bad = [('source: hash: ' + x[len('snapshot: '):]) if x.startswith('snapshot: sha256') else x
           for x in RT.check_snapshot(data, Path(html_dir))]
    raw = p.read_bytes()
    if hashlib.sha1(raw).hexdigest() != src['revision_sha1'] or len(raw) != src['snapshot_bytes']:
        bad.append(f'source: hash: sha1/bytes {hashlib.sha1(raw).hexdigest()} / {len(raw)} are not the recorded ones')
    return bad + page_problems(data, raw.decode('utf8'))


def html_checks(data: dict, html_dir: Path) -> list[str]:
    """`--html-dir` already runs the shared snapshot reader; this adds MediaWiki's sha1 and the page around it."""
    p = Path(html_dir) / data['source']['snapshot_file']
    raw = p.read_bytes()
    bad = []
    if hashlib.sha1(raw).hexdigest() != data['source']['revision_sha1']:
        bad.append(f'source: hash: sha1 {hashlib.sha1(raw).hexdigest()} is not MediaWiki\'s revision sha1')
    return bad + page_problems(data, raw.decode('utf8'))


# ── other technique transcriptions ───────────────────────────────────────────────────────────────
def other_technique_fires(data: dict) -> list[dict]:
    """The window over every board of every other committed `*-technique.json`: a spin board at its drawn spin
    (the T only), any other board at every resting placement of a T, both hands, read with that file's empty letters."""
    v = data['variants'][0]
    out = []
    for f in sorted(HERE.glob('*-technique.json')):
        if f == OUT:
            continue
        od = json.loads(f.read_text())
        sp = copy.copy(SPEC)
        sp.empty_letters = od.get('empty_letters', '')
        for n in od.get('nodes', []):
            rows = n.get('rows')
            if not rows or len(rows) < 4:
                continue
            if n.get('kind') == 'spin':
                if n.get('spin_piece', 'T').lower() not in ('t', 'u'):
                    continue
                sc = TT.spin_cells(n)
                pre = [''.join(EMPTY if (r, c) in sc else ch for c, ch in enumerate(row)) for r, row in enumerate(rows)]
                cands = [sc]
            else:
                pre = [row.replace('U', EMPTY) for row in rows]
                cands = TT.t_placements(pre, sp)
            filled = (lambda R, C, pre=pre, sp=sp: not TT.is_empty(pre[R][C], sp))
            for m in (False, True):
                if any(TT.window_fires(data, v, sp, pre, cs, m, filled) for cs in cands):
                    out.append({'file': f.name, 'node': n['id'], 'mirrored': m})
    return out


# ── technique-only rules ─────────────────────────────────────────────────────────────────────────
def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    v = data['variants'][0]
    xs = data['cross_source']
    # every board is accounted for: the variant's board, a drawing of the shape, its follow-up board, or a miss
    acc = [v['board'], v['followup']['board'], *(a['board'] for a in v.get('agreement', [])),
           *v.get('fires_on', []), *v.get('misses', [])]
    left = [n['id'] for n in data['nodes'] if n['id'] not in acc]
    if left:
        bad.append(f'window: boards neither a drawing, fired on nor missed: {left}')
    if sorted(a['board'] for a in v.get('agreement', []) if not a['mirrored']) != sorted(v.get('fires_on', [])):
        bad.append('window: the page\'s as-drawn drawings of the shape (agreement) are not fires_on')
    # the derived after board is what the TSS leaves, letter for letter (the T's cells read t)
    sp = by[v['board']]
    got, n = RT.after_spin(sp['rows'])
    if n != v['lines'] or RT.bottom(got, MAX_ROWS) != RT.bottom(by['tss.after']['rows'], MAX_ROWS):
        bad.append('after: tss.after is not what tss.spin leaves')
    # the (table, board) of the drawn nodes: one table, boards 0, 1, 2 in page order; a derived node shares a drawn
    # board's index (it is that board less a piece, or what it leaves)
    drawn = [(by[i]['table'], by[i]['board']) for i in data['page_order']]
    if drawn != [(0, k) for k in range(len(drawn))]:
        bad.append(f'page: the drawn nodes\' (table, board) are {drawn}, not one table numbered from 0')
    # the follow-up: one column right of the T's stem, nub left, its top a row above the TSS's T
    st = sorted(tuple(x) for x in v['t_cells'])
    fu = sorted(tuple(x) for x in v['followup']['t_cells_pre_clear'])
    stem = min(c for _, c in st)
    want = sorted([(st[0][0] - 1, stem + 2), (st[0][0], stem + 1), (st[0][0], stem + 2), (st[0][0] + 1, stem + 2)])
    if fu != want:
        bad.append(f'window: the follow-up slot {fu} is not the TST slot beside the T ({want})')
    # the credit: on every drawing of the shape, the T's centre has three filled corners and one filled on the nub
    # side (a mini under TETR.IO's rule); a full credit would need both nub-side corners filled
    def corners(rows, tc):
        tc = sorted(tuple(x) for x in tc)
        cols = [c for _, c in tc]
        stem = max(set(cols), key=cols.count)
        nub = [c for c in cols if c != stem][0]
        cr = sorted(r for r, c in tc if c == stem)[1]
        def filled(r, c):
            return not (0 <= c < WIDTH) or r >= len(rows) or (r >= 0 and rows[r][c] != EMPTY)
        cs = {(dr, dc): filled(cr + dr, stem + dc) for dr in (-1, 1) for dc in (-1, 1)}
        side = 1 if nub > stem else -1
        return sum(cs.values()), sum(v2 for (dr, dc), v2 in cs.items() if dc == side)
    want = (3, 1) if v.get('credit') == 'mini' else None
    draws = [(by[v['board']]['rows'], v['t_cells'], True)] + [(xs['video']['rows'], xs['video']['t_cells'], False)]
    for rows, tc, spin_board in draws:
        pre = [''.join(EMPTY if (r, c) in {tuple(x) for x in tc} else ch for c, ch in enumerate(row))
               for r, row in enumerate(rows)] if spin_board else rows
        got_c = corners(pre, tc)
        if want is None or got_c != want:
            bad.append(f'credit: the T\'s corners {got_c} (filled, filled on the nub side) do not make the '
                       f'{v.get("credit", "full")} credit the variant names')
    # the short
    vid = xs.get('video', {})
    for k in ('url', 'id', 'fetched', 'fetch_method', 'file_sha256', 'file_bytes', 'frame_s', 'reading', 'rows',
              't_cells'):
        if not vid.get(k) and vid.get(k) != 0:
            bad.append(f'video: {k} missing')
    if vid.get('rows') and (any(len(r) != WIDTH for r in vid['rows']) or set(''.join(vid['rows'])) - {'c', EMPTY}):
        bad.append('video: the short\'s board is not ten wide in c and -')
    elif vid.get('rows'):
        # the T fits its slot and clears exactly the TSS's row
        tc = {tuple(x) for x in vid['t_cells']}
        o = [''.join('#' if (r, c) in tc else ch for c, ch in enumerate(row)) for r, row in enumerate(vid['rows'])]
        if any(vid['rows'][r][c] != EMPTY for r, c in tc) or len(TT.full_rows(o)) != v['lines']:
            bad.append('video: the short\'s T is not an empty slot that clears one row')
    # other techniques: the window fires on exactly the recorded boards
    key = lambda e: (e['file'], e['node'], e['mirrored'])
    got2 = sorted(map(key, other_technique_fires(data)))
    want2 = sorted(map(key, xs.get('other_techniques', [])))
    if got2 != want2:
        bad.append(f'other: the window fires on {got2} of the other technique transcriptions, the record names {want2}')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    upper_groups={}, max_rows=MAX_ROWS, muting_slips=True,
    extra_checks=extra_checks,
    external_drawings=lambda: video_drawings(),
    html_checks=html_checks,
    wikitext_checks=wikitext_checks,
    synthetic_wikitext=lambda d: {d['source']['snapshot_file']: _synthetic_page(d)},
    synthetic_snapshot=lambda d: _synthetic_page(d),
)


# ── synthetic page (selftests) ───────────────────────────────────────────────────────────────────
def _page_cell(ch: str) -> str:
    """The source readings backwards: the code this page draws for a cell of the alphabet."""
    return {EMPTY: ' ', 'c': 'g', 'q': 'G', 't': 'T', 'U': 'P'}.get(ch, ch.upper())


def _wikitext(tables: list[list[list[str]]]) -> str:
    return ' '.join('{| ' + ' '.join('|{{pfstart}} ' + ' '.join(
        '{{pfrow|' + '|'.join(_page_cell(ch) for ch in r) + '}}' for r in b) + ' {{pfend}}' for b in t) + ' |}'
        for t in tables)


def _synthetic_page(data: dict) -> str:
    """The page rebuilt: blank one-board tables for every board before and after, the heading, the label and the
    table of the three boards in page order, the quotes as text."""
    blank = [EMPTY * WIDTH] * 4
    boards = [node(data, i)['rows'] for i in data['page_order']]
    before = _wikitext([[blank]] * FIRST_BOARD)
    after = _wikitext([[blank]] * (163 - FIRST_BOARD - len(boards)))
    return (before + '\n=== Garbage Manipulation ===\n' + data['source']['label_text'] + '\n'
            + _wikitext([boards]).replace(' |}', ' EZ TSS |}') + '\n' + after)


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d):
    return d['variants'][0]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'terrain')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'tss.spin').__setitem__('spin_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _set(node(d, 'tss')['rows'], 2, 3, 'l'), 'the derived board not the spin board less its T', 'build:'),
    (lambda d: _set(node(d, 'tst')['rows'], 5, 0, '-'), 'the TST board not what the TSS leaves plus its stack', 'build:'),
    (lambda d: node(d, 'tss.spin').__setitem__('lines', 2), 'the TSS\'s line count', 'spin:'),
    (lambda d: _set(node(d, 'tss.after')['rows'], 4, 1, '-'), 'the after board not what the TSS leaves', 'after:'),
    (lambda d: _var(d).pop('credit'), 'the TSS read as a full T-spin', 'credit:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [0, 4]), 'the window widened by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [0, 2]), 'the window without the TST\'s column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [3, 5]), 'the window without the overhang', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _var(d)['agreement'][0].__setitem__('mirrored', True), 'the drawing read mirrored', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('t_cells_pre_clear', [[1, 3], [2, 2], [2, 3], [3, 3]]),
     'the follow-up slot a row higher', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('lines', 2), 'the follow-up read as a TSD', 'window:'),
    (lambda d: _var(d)['misses'].append('tss'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _var(d)['misses'].remove('terrain'), 'a page board accounted nowhere', 'window:'),
    (lambda d: d['known_discrepancies'].pop(0), 'the spin board\'s unmuted row unnamed', 'discrepancy:'),
    (lambda d: d['known_discrepancies'].append({'id': 'terrain:colour', 'note': 'x'}), 'a stale discrepancy',
     'discrepancy:'),
    (lambda d: node(d, 'tst').__setitem__('board', 3), 'a node\'s board index', 'page:'),
    (lambda d: node(d, 'tst').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['cross_source']['video'].pop('file_sha256'), 'the short\'s hash dropped', 'video:'),
    (lambda d: _set(d['cross_source']['video']['rows'], 4, 3, 'c'), 'the short\'s slot filled', 'video:'),
    (lambda d: d['cross_source']['other_techniques'].append({'file': 'stsd-technique.json', 'node': 'basic',
                                                             'mirrored': False}),
     'an other technique board recorded that does not fire', 'other:'),
    (lambda d: d['cross_source'].pop('routes_fire_none'), 'no routes board and no reason', 'cross:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _video_moved(spec):
    """The short's board one row down from its slot: the agreement rule must refuse it."""
    s = copy.copy(spec)
    d = video_drawings()[0]
    s.external_drawings = lambda: [{**d, 't_cells': [[r + 1, c] for r, c in d['t_cells']]}]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against harddrop alone)', 'window:'),
    (_video_moved, 'the short\'s slot read a row lower', 'window:'),
]


def selftest() -> int:
    rc = TT.run_selftest(SPEC, MUTANTS,
                         {'board': ('{{pfrow|L|P| | | | | | | | }}', '{{pfrow|L|L| | | | | | | | }}'),
                          'text': ('EZ TSS', 'Easy TSS')},
                         SPEC_MUTANTS)
    ok = rc == 0
    base = build()
    text = _synthetic_page(base)
    clean = page_problems(base, text)
    if clean:
        print(f'selftest FAILED: the synthetic page does not verify ({clean[:2]})')
        ok = False
    else:
        spin = node(base, 'tss.spin')['rows']
        loose = RT.synthetic_wikitext([[spin]])
        plants = {
            'the label moved off the page': text.replace(base['source']['label_text'], 'Cave TSS elsewhere', 1),
            'a heading renamed': text.replace('=== Garbage Manipulation ===', '=== Renamed ===', 1),
            'a board added before the label': loose + '\n' + text,
            'a firing drawing elsewhere on the page left unrecorded': text + '\n' + loose,
        }
        for label, page in plants.items():
            got = page_problems(base, page)
            if page == text or not any(x.startswith('source:') for x in got):
                print(f'selftest FAILED: {label} was not caught ({got[:2]})')
                ok = False
            else:
                print(f'  killed: {label}  [source:]')
    with tempfile.TemporaryDirectory() as td:
        missing = wikitext_checks(base, Path(td))
        (Path(td) / base['source']['snapshot_file']).write_text(text)
        hashed = wikitext_checks(base, Path(td))
    if not any('is not in' in x for x in missing) or not any(': hash: ' in x for x in hashed) \
            or any(': hash: ' not in x for x in hashed):
        print(f'selftest FAILED: the pinned revision (missing={missing[:1]}, hashed={hashed[:3]})')
        ok = False
    else:
        print('  killed: the pinned revision missing / its bytes not the pinned revision (and nothing else)  [hash:]')
    print('selftest: Cave TSS to TST checks all caught' if ok else 'selftest: FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))
