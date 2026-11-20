"""Transcribe harddrop's Hamburger page into `hamburger-technique.json`.

    python3 -m pipeline.openers.extract_hamburger_shapes                  # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_hamburger_shapes --selftest       # prove the verifier has teeth
    python3 -m pipeline.openers.extract_hamburger_shapes --html-dir <dir> # re-check the pinned revision
    python3 -m pipeline.openers.extract_hamburger_shapes --wikitext-dir <dir>  # the same, as the weekly job runs it
    python3 -m pipeline.openers.extract_hamburger_shapes --html-dir <dir> --write  # ...and rewrite

ハンバーガー (Hamburger): sustainable T-spin Single stacking. harddrop's page (「popularized by top Japanese player,
Amemiyataiyou」) is the primary source; shiwehi.com draws no such page.

DECISION: the spin is a FULL TSS and the anchor is the T's cells — the T laid flat, nub down. Two columns from the
nub, on the side away from the roof, is a WELL: the cell under the cleared row there is an empty hole, the T's own
row and the row above it are empty, and the cleared-row cells at the well and between the well and the nub (the
COVER: a Z on the page's own build) sit over the hole. The other side of the T is the roof. The TSS clears the
cover's row, so the well column opens from the top to the floor; the payoff harddrop names is a Tetris into it
(「After a few iterations, use an I piece to clear the excess.」) — so the variant carries a `well_quad` payoff, as
欄干's does, and the prose words a well filled by anything but a Tetris-clearing I as 「再疊多層」 (another cycle),
never as a failure.

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`). The page draws the shape on its own basic board,
on two opener boards (its Usages board with the T in, and Sailboat's), and SDPC Spin's and stick spin's bag 1
draw it too (another page and another site). The box every one of them agrees on is four rows by five columns: the
row above the T (the roof over the end away from the well, open over the well), the T's row, the cleared row (the
cover, the nub, the stack beyond), the row under it (the hole at the well, filled beyond). Above that row board 8
fills the well side; below the hole row the basic board ends; beyond column 4 the drawings disagree.

THE PAGE ORDER IS THE PAGE'S FIRST THREE TABLES (six boards); every later board is `boards_not_transcribed` and
recorded instead in `cross_source.page`, measured and complete both ways: every board whose drawn T (P) the window
fires on (`drawings`, the agreement set's page drawings), every OTHER drawn T with why the window misses it
(`drawn_t_not_fired`), and every board with no T drawn on which some resting T placement fires
(`fires_without_slot`). So the window does not choose its own evidence.

READINGS: `SG` grey (read c), `SP` the T placed (U), `ST` a T drawn grey-ish as a residue or the soft-dropped T
(read t), `SZ`/`SI`/`SJ`/`SL`/`SO`/`SS` a piece of that letter. harddrop never mutes a cleared row, so the spin
board is a named `:muting` discrepancy. The board after the TSS is not drawn; `spin.after` is DERIVED (`after_of`),
checked exactly by the after rule.
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
OUT = HERE / 'hamburger-technique.json'

ALPHABET = frozenset('-cUtzi')
MAX_ROWS = 8
#: boards on the page (every {{pfstart}}), 0-based; the first six are transcribed as nodes
N_BOARDS = 27
N_NODES = 6


def _b(text: str) -> list[str]:
    return text.split()


READINGS = {'SG': 'c', 'SP': 'U', 'ST': 't', 'SZ': 'z', 'SI': 'i', 'SJ': 'j', 'SL': 'l', 'SO': 'o', 'SS': 's'}

SOURCE = {
    'url': 'https://harddrop.com/wiki/Hamburger',
    'edit_url': 'https://harddrop.com/w/index.php?title=Hamburger&action=edit',
    'title': 'Hamburger',
    'site': 'harddrop.com (Hard Drop Tetris Wiki, MediaWiki)',
    'author_note': 'the page is harddrop\'s, edited by its wiki editors; it says the method was 「popularized by top '
                   'Japanese player, Amemiyataiyou」',
    'oldid': 40054,
    'parentid': 37877,
    'revision_sha1': '0d76bcfb514b59fa815a99b83cee6d45b31b2a38',
    'revision_timestamp': '2024-07-24T13:11:30Z',
    'updated': '2024-07-24',
    'revision_note': 'MediaWiki\'s own sha1 of revision 40054 (read from the API), equal to sha1 of the saved bytes: a '
                     'second authority beside snapshot_sha256, which is ours; the page\'s latest revision when fetched',
    'fetched': '2026-11-20',
    'fetch_method': 'the pinned revision\'s own bytes from the MediaWiki API (api.php?action=query&prop=revisions&'
                    'titles=Hamburger&rvprop=ids|sha1|content|timestamp&rvslots=main&format=json&formatversion=2), with '
                    'Python\'s urllib and a descriptive User-Agent (NOT curl). Boards are {{pfstart}} … {{pfend}} '
                    'templates, read by route_transcription.wikitext_boards with `wikitext_readings`',
    'snapshot_file': 'Hamburger.wikitext',
    'snapshot_sha256': 'cdd891932856d563798d4cc521852a3c044de834e225c6be61924b6490ff37eb',
    'snapshot_bytes': 7797,
    'snapshot_note': 'sha256 of the revision\'s bytes as the API serves them. The page is not committed; the weekly '
                     '`wikitext-sources` job refetches the pinned revision, checks both hashes and re-runs '
                     '--wikitext-dir, and fails when the page has a newer revision.',
    'wikitext_readings': READINGS,
    'wikitext_readings_note': 'this page draws every cell with an S-prefixed code: SG grey (read c), SP the T placed '
                              '(read U), ST a T drawn as a residue or as the soft-dropped T (read t), and SZ, SI, SJ, '
                              'SL, SO, SS a piece of that letter',
    'boards_not_transcribed': [
        {'boards': [N_NODES, N_BOARDS - 1], 'heading': 'Usages, Opening Setup, Mid Game Conversion',
         'reason': 'opener and conversion boards; recorded in cross_source.page (the window measured on each), not '
                   'transcribed as nodes'},
    ],
    'shiwehi': {'checked': '2026-11-20',
                'index': 'https://shiwehi.com/tetris/template/ (its 中盤テンプレ・ドネイト list names no Hamburger)',
                'note': 'no shiwehi.com page draws this setup, so harddrop\'s page is the primary source'},
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
    'c': 'a cell drawn grey (harddrop SG): placed before this diagram, any piece or garbage',
    'U': 'a cell of the T the spin places (harddrop SP)',
    't': 'a cell drawn as a T (harddrop ST): the soft-dropped T on the second board, a TSS\'s residue on the repeat '
         'and Tetris boards (OUR READING)',
    'z': 'a cell of the Z (the cover on the page\'s Z build)',
    'i': 'a cell of the I (the Tetris)',
    'muting': 'harddrop never draws the row a spin clears muted, so the spin board is a named `:muting` discrepancy',
}

QUOTES = [
    {'id': 'intro', 'verbatim': "'''Hamburger''' is a form of sustainable [[T-Spin Single]] stacking"},
    {'id': 'basic', 'verbatim': 'The basic idea of Hamburger is to create this basic shape:'},
    {'id': 'initial', 'verbatim': 'Initial build'},
    {'id': 'softdrop', 'verbatim': 'Soft Drop T'},
    {'id': 'rotate', 'verbatim': 'Rotate T, for <br> T-Spin Single'},
    {'id': 'zpiece', 'verbatim': 'The obvious way to make a Hamburger is to use a Z piece.'},
    {'id': 'excess', 'verbatim': 'After a few iterations, use an I piece to clear the excess.'},
    {'id': 'repeat', 'verbatim': 'Repeat'},
    {'id': 'tetris', 'verbatim': 'Tetris'},
]

NODES = [
    {'id': 'terrain', 'table': 0, 'board': 0, 'kind': 'base', 'caption_quote': 'initial',
     'label': 'the basic shape: a roof over the T\'s right end, a cover over a hole two columns left of the nub',
     'rows': _b('---------- ---cc----- ----c----- cc-ccccccc -ccccccccc')},
    {'id': 'softdrop', 'table': 0, 'board': 1, 'kind': 'illustration', 'caption_quote': 'softdrop',
     'label': 'the T soft-dropped stood up into the slot, before it rotates',
     'rows': _b('---------- --tcc----- -tt-c----- cctccccccc -ccccccccc')},
    {'id': 'spin', 'table': 0, 'board': 2, 'kind': 'spin', 'caption_quote': 'rotate',
     'label': 'the T rotated flat, nub down: a T-spin Single clearing the cover\'s row',
     'rows': _b('---------- ---cc----- -UUUc----- ccUccccccc -ccccccccc'),
     'spin_of': 'terrain', 'spin_piece': 'U', 'spin': 'TSS', 'lines': 1},
    {'id': 'zbuild', 'table': 1, 'board': 0, 'kind': 'base', 'caption_quote': 'zpiece',
     'label': 'the same shape built with a Z: the Z is the cover and the row under it',
     'rows': _b('---------- ---cc----- ----c----- zz-ccccccc -zzccccccc'), 'same_occupancy_as': 'terrain'},
    {'id': 'repeat', 'table': 2, 'board': 0, 'kind': 'illustration', 'caption_quote': 'repeat',
     'label': 'the shape again on top of the last cycle\'s residue: the well under it is deeper',
     'rows': _b('---------- ---------- ---cc----- ----c----- cc-ccccccc -ccccccccc -tttcccccc -ccccccccc')},
    {'id': 'tetris', 'table': 2, 'board': 1, 'kind': 'illustration', 'caption_quote': 'tetris',
     'label': 'a few cycles later: an I into the well clears the excess',
     'rows': _b('---------- ---cc-cccc -tttcccccc -ccccccccc itttcccccc iccccccccc itttcccccc iccccccccc')},
    {'id': 'spin.after', 'kind': 'derived', 'derived': True, 'caption_quote': 'rotate',
     'label': 'what the TSS leaves (the page does not draw it): the well column open from the top to the floor',
     'rows': _b('---------- ---------- ---cc----- -tttc----- -ccccccccc'), 'after_of': 'spin'},
]

_SLOT = [[2, 1], [2, 2], [2, 3], [3, 2]]

VARIANTS = [{
    'id': 'hamburger', 'board': 'spin', 'spin': 'TSS', 'lines': 1,
    'window_basis': 'agreement',
    'window': {'rows': [1, 4], 'cols': [0, 4]},
    't_cells': _SLOT,
    'roof_cells': [[1, 3], [1, 4]],
    'window_note': 'in spin\'s frame, row 0 the top: the AGREEMENT BOX of the page\'s basic board, its two opener '
                   'drawings with the T in (cross_source.page.drawings) and SDPC Spin\'s and stick spin\'s bag 1. Row 1 '
                   'is the roof over the T\'s right end, open over the well; row 2 the T\'s row (the well cell left of '
                   'it empty, the stack right of it filled); row 3 the row the TSS clears (the cover at the well and '
                   'next to the nub, entailed by the clear at a full TSS, NaiveClauseForced); row 4 the hole under the '
                   'cover at the well, filled beyond it. Occupancy only, never colour; garbage is filled, so a hole '
                   'that is a garbage row\'s hole counts.',
    'agreement': [{'board': 'terrain', 't_cells': _SLOT, 'mirrored': False},
                  {'board': 'zbuild', 't_cells': _SLOT, 'mirrored': False},
                  {'board': 'repeat', 't_cells': [[3, 1], [3, 2], [3, 3], [4, 2]], 'mirrored': False}],
    'untested_drawn': {'cells': [], 'reason': ''},
    'payoff': {'kind': 'well_quad', 'board': 'spin.after', 'piece': 'I', 'lines': 4,
               'well_cell_pre_clear': [4, 0], 'well_cell_after': [4, 0],
               'note': 'a Tetris into the well, the step the page names (「After a few iterations, use an I piece to '
                       'clear the excess.」) and draws (its Tetris board). A well that the next piece into its column '
                       'fills without a Tetris is another cycle of the stacking (the page\'s Repeat board), not a '
                       'failure; the matcher carries the well cell to the first later lock that puts a cell in its '
                       'column and asks whether that lock is an I the engine credits with four lines'},
    'fires_on': ['terrain', 'zbuild', 'repeat'],
    'misses': ['softdrop', 'tetris', 'spin.after'],
}]

#: the page's other boards, measured: the window at every drawn T, and at every resting T on a board with none
PAGE = {
    'note': 'every board of the pinned revision after the six transcribed ones, read with `wikitext_readings`. A '
            'board whose drawn T (SP) the window fires on is a `drawing` (an agreement drawing); a board with a drawn '
            'T the window misses is in `drawn_t_not_fired` with how the T lies and why; a board with no T drawn on '
            'which a resting T placement fires is in `fires_without_slot`, one entry per hand. Complete both ways, '
            'measured by the gate on every --wikitext-dir run.',
    'drawings': [
        {'board': 8, 'section': 'Usages',
         'rows': _b('---------- ---ccccccc ---ccccccc -UUUcccccc zzUccccccc -zzccccccc'),
         't_cells': [[3, 1], [3, 2], [3, 3], [4, 2]], 'mirrored': False,
         'note': 'the Usages board drawn with the T in, on a Z cover and a full stack'},
        {'board': 20, 'section': 'Opening Setup',
         'rows': _b('---------- ---------- ---------- ---ll----i -UUUloo--i zzUjloossi -zzjjjss-i'),
         't_cells': [[4, 1], [4, 2], [4, 3], [5, 2]], 'mirrored': False,
         'note': 'the Sailboat opener\'s first T-spin, a Hamburger on its Z'},
    ],
    'drawn_t_not_fired': [
        {'board': 6, 'section': 'Usages', 
         'rows': _b('---------- ---ccccccc --Uccccccc --UUcccccc zzUccccccc -zzccccccc'),
         'lie': 'stood up', 'reason': 'not the window\'s T',
         'note': 'the T stood up into the slot, for a Tetris (「rotate the T piece once or twice」)'},
        {'board': 22, 'section': 'Opening Setup', 
         'rows': _b('---------- --i-z---ll ooizz----l ooizUUUssl jjiccUss-c jcccccc--c jccccccc-c'),
         'lie': 'flat, nub down', 'reason': 'disagrees',
         'note': 'the Sailboat example\'s T-spin Single on its right; the cell over the well side is filled'},
        {'board': 24, 'section': 'Opening Setup', 
         'rows': _b('---------- ---------- --c-c---cc ccccc----c ccccccccUc cccccccUUc ccccccccUc'),
         'lie': 'stood up', 'reason': 'not the window\'s T',
         'note': 'the T-spin Triple the Sailboat example ends with'},
    ],
    'fires_without_slot': [
        {'board': 6, 'mirrored': False, 'note': 'beside its drawn stood T, the flat T fires at the same slot'},
        {'board': 11, 'mirrored': False, 'note': 'Requires J before L'},
        {'board': 12, 'mirrored': False, 'note': 'Hamburger completed'},
        {'board': 13, 'mirrored': True, 'note': 'Mirrored version (L before J)'},
        {'board': 15, 'mirrored': False, 'note': 'Get creative'},
        {'board': 16, 'mirrored': False, 'note': 'ST Stacking start'},
        {'board': 17, 'mirrored': False, 'note': 'ST Stacking start'},
        {'board': 18, 'mirrored': False, 'note': 'ST Stacking start'},
        {'board': 19, 'mirrored': False, 'note': 'ST Stacking start'},
        {'board': 25, 'mirrored': False, 'note': 'Opener'},
        {'board': 26, 'mirrored': False, 'note': '2nd Bag Conversion'},
    ],
}

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'hamburger',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of '
            'every committed *-routes.json, with the U cells as the T: it fires on SDPC Spin\'s two bag-1 TSS boards '
            '(harddrop\'s SDPC_Spin page, another page) and on stick spin\'s bag-1 TSS board mirrored (shiwehi.com, '
            'another site). Those three are also the window\'s external agreement drawings, beside the page\'s own '
            'two opener drawings (`page`).',
    'fires': [
        {'file': 'sdpcspin-routes.json', 'node': 'bag1.lj', 'variant': 'hamburger', 'mirrored': False,
         'note': 'SDPC Spin\'s bag-1 T-spin Single, the L under the J'},
        {'file': 'sdpcspin-routes.json', 'node': 'bag1.jl', 'variant': 'hamburger', 'mirrored': False,
         'note': 'SDPC Spin\'s bag-1 T-spin Single, the J under the L'},
        {'file': 'stickspin-routes.json', 'node': 'bag1.pc', 'variant': 'hamburger', 'mirrored': True,
         'note': 'stick spin\'s bag-1 T-spin Single laid flat (パフェ派生), mirrored'},
    ],
    'also': [],
    'labelled_not_fired': [],
    'page': PAGE,
    #: every board of every OTHER committed technique transcription on which the window fires
    'other_techniques': [
        {'file': 'basicdonating-technique.json', 'node': 'tonbo.burger', 'mirrored': True,
         'note': 'とんぼ\'s video\'s ハンバーガー積み template (another author), as 基本的なドネイト\'s file transcribes it, mirrored'},
        {'file': 'basicdonating-technique.json', 'node': 'tonbo.burger_play', 'mirrored': True,
         'note': 'the same board with the T played'},
    ],
}

KNOWN_DISCREPANCIES = [
    {'id': 'spin:muting', 'note': 'harddrop draws the row the TSS clears in the same letters as the rest (it never '
                                  'mutes a cleared row)'},
    {'id': 'repeat:colour', 'note': 'the last cycle\'s T is three cells after its TSS (the fourth was in the cleared '
                                    'row): a piece cut by a line clear, not a whole T'},
    {'id': 'tetris:colour', 'note': 'three cycles\' T residues, three cells each, drawn as harddrop draws them (ST)'},
]

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'hamburger',
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


def _occ(rows: list[str]) -> list[str]:
    return [''.join(EMPTY if ch in (EMPTY, 'U') else 'c' for ch in row) for row in rows]


def external_drawings(data: dict | None = None) -> list[dict]:
    """The page's two opener drawings and the three routes boards the window fires on, slot read empty."""
    d = data or build()
    out = [{'name': f'Hamburger board {e["board"]}', 'rows': _occ(e['rows']), 't_cells': e['t_cells'],
            'mirrored': e['mirrored']} for e in d['cross_source']['page']['drawings']]
    want = {(e['file'], e['node']): e['mirrored'] for e in d['cross_source']['fires']}
    for fn, n, rows, u in TT.route_u_boards(SPEC):
        if (fn, n['id']) in want:
            out.append({'name': f'{fn} {n["id"]}', 'rows': _occ(rows), 't_cells': sorted(list(x) for x in u),
                        'mirrored': want[(fn, n['id'])]})
    return out


# ── the whole page ───────────────────────────────────────────────────────────────────────────────
def _slot(rows: list[str]) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == 'U'}


def _lie(cells) -> str:
    rs = sorted(r for r, _ in cells)
    if len({r for r, _ in cells}) == 3:
        return 'stood up'
    top = [r for r, _ in cells].count(rs[0])
    return 'flat, nub down' if top == 3 else 'flat, nub up'


def page_record(data: dict, text: str) -> dict:
    """The window over every board after the transcribed ones, as `PAGE` records it (no notes, no sections)."""
    v = data['variants'][0]
    boards = RT.wikitext_boards(text, readings=data['source']['wikitext_readings'])
    rec = {'drawings': [], 'drawn_t_not_fired': [], 'fires_without_slot': [], 'n_boards': len(boards)}
    for k, rows in enumerate(boards):
        if k < N_NODES:
            continue
        s = _slot(rows)
        pre = [row.replace('U', EMPTY) for row in rows]
        if s:
            got = {m: TT.window_fires(data, v, SPEC, pre, s, m) for m in (False, True)}
            fired = [m for m, g in got.items() if g]
            if fired:
                rec['drawings'] += [{'board': k, 'rows': rows, 't_cells': sorted(list(x) for x in s), 'mirrored': m}
                                    for m in fired]
            else:
                lie = _lie(s)
                reason = ('not the window\'s T' if lie != 'flat, nub down'
                          else 'leaves the board' if all(g is None for g in got.values()) else 'disagrees')
                rec['drawn_t_not_fired'].append({'board': k, 'rows': rows, 'lie': lie, 'reason': reason})
        for m in (False, True):
            if any(cs != s and TT.window_fires(data, v, SPEC, pre, cs, m) for cs in TT.t_placements(pre, SPEC)):
                rec['fires_without_slot'].append({'board': k, 'mirrored': m})
    return rec


def page_problems(data: dict, text: str) -> list[str]:
    """The page around the boards: the basic section heads the first table, the page holds the recorded number of
    boards, and the window's record over every other board is exactly `cross_source.page`."""
    bad = []
    secs = _sections(_tabled(text))
    if not secs or secs[0] != 'Basic Setup':
        bad.append(f'source: the first table sits under {secs[0] if secs else None!r}, not \'Basic Setup\'')
    try:
        got = page_record(data, text)
    except ValueError as e:
        return bad + [f'source: the page does not parse: {e}']
    if got['n_boards'] != N_BOARDS:
        bad.append(f'source: the page draws {got["n_boards"]} boards, the record says {N_BOARDS}')
    rec = data['cross_source']['page']
    for key, f in (('drawings', lambda e: (e['board'], tuple(e['rows']), str(e['t_cells']), e['mirrored'])),
                   ('drawn_t_not_fired', lambda e: (e['board'], tuple(e['rows']), e['lie'], e['reason'])),
                   ('fires_without_slot', lambda e: (e['board'], e['mirrored']))):
        a, b = sorted(map(f, got[key])), sorted(map(f, rec[key]))
        if a != b:
            bad.append(f'source: page {key} measured {[x[0] for x in a]}, the record names {[x[0] for x in b]}'
                       + ('' if [x[0] for x in a] != [x[0] for x in b] else ' (same boards, a field differs)'))
    return bad


def wikitext_checks(data: dict, html_dir: Path) -> list[str]:
    """`--wikitext-dir`: the pinned revision through the shared snapshot reader (its hash line tagged `source: hash:`),
    MediaWiki's sha1, and the window over every other board of the page."""
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
    acc = [v['board'], v['payoff']['board'], *(a['board'] for a in v.get('agreement', [])),
           *v.get('fires_on', []), *v.get('misses', [])]
    left = [n['id'] for n in data['nodes'] if n['id'] not in acc]
    if left:
        bad.append(f'window: boards neither a drawing, fired on nor missed: {left}')
    if sorted(a['board'] for a in v.get('agreement', []) if not a['mirrored']) != sorted(v.get('fires_on', [])):
        bad.append('window: the page\'s as-drawn drawings of the shape (agreement) are not fires_on')
    # the drawn nodes' (table, board): tables 0, 1, 2 holding 3, 1, 2 boards, in page order
    drawn = [(by[i]['table'], by[i]['board']) for i in data['page_order']]
    if drawn != [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)]:
        bad.append(f'page: the drawn nodes\' (table, board) are {drawn}, not the page\'s first three tables')
    # the shape: the well two columns from the nub on the side away from the roof, the cover over it, a hole under it
    tc = sorted(tuple(x) for x in v['t_cells'])
    arms = [x for x in tc if x[0] == tc[0][0]]
    nub = [x for x in tc if x[0] != tc[0][0]]
    if len(arms) != 3 or len(nub) != 1 or nub[0][0] != arms[0][0] + 1:
        bad.append('shape: the T is not flat, nub down')
    else:
        (nr, nc) = nub[0]
        roof = sorted(tuple(x) for x in v['roof_cells'])
        side = -1 if all(c > nc for _, c in roof) else (1 if all(c < nc for _, c in roof) else 0)
        w = nc + 2 * side
        wc = TT.window_cells(data, v, TT.TechniqueSpec(out=OUT, build=None, alphabet=ALPHABET), False)
        want = {(nr, w): '#', (nr, nc + side): '#', (nr + 1, w): '.', (nr - 1, w): '.', (nr - 2, w): '.'}
        if side == 0 or any(wc.get(k) != x for k, x in want.items()):
            bad.append(f'shape: the well two columns from the nub away from the roof is not covered over a hole '
                       f'with its T row and the row above empty ({ {k: wc.get(k) for k in want} })')
        if list(v['payoff']['well_cell_pre_clear']) != [nr + 1, w]:
            bad.append('shape: the payoff\'s well cell is not the hole under the cover')
    # the page record's drawings carry rows from the page: the slot is a flat T, nub down, in the recorded hand
    for e in xs['page']['drawings']:
        if sorted(tuple(x) for x in e['t_cells']) != sorted(_slot(e['rows'])) or _lie(_slot(e['rows'])) != 'flat, nub down':
            bad.append(f'page: drawing {e["board"]}\'s t_cells are not its drawn flat T')
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
    external_drawings=lambda: external_drawings(),
    html_checks=html_checks,
    wikitext_checks=wikitext_checks,
    synthetic_wikitext=lambda d: {d['source']['snapshot_file']: _synthetic_page(d)},
    synthetic_snapshot=lambda d: _synthetic_page(d),
)


# ── synthetic page (selftests) ───────────────────────────────────────────────────────────────────
_BACK = {v: k for k, v in READINGS.items()}


def _page_cell(ch: str) -> str:
    return ' ' if ch == EMPTY else _BACK[ch]


def _wikitext(tables: list[list[list[str]]]) -> str:
    return ' '.join('{| ' + ' '.join('|{{pfstart}} ' + ' '.join(
        '{{pfrow|' + '|'.join(_page_cell(ch) for ch in r) + '}}' for r in b) + ' {{pfend}}' for b in t) + ' |}'
        for t in tables)


def _synthetic_page(data: dict) -> str:
    """The page rebuilt: its sections, the six transcribed boards in their three tables, the quotes as text, and every
    later board blank except the recorded ones (the drawings and the boards a placement fires on, rebuilt as the
    simplest board that keeps their record: a drawing as recorded, a T-less board as the basic terrain)."""
    q = {x['id']: x['verbatim'] for x in data['quotes']}
    b = {n['id']: n['rows'] for n in data['nodes']}
    rec = data['cross_source']['page']
    blank = [EMPTY * WIDTH] * 4
    later = []
    terrain = b['terrain']
    mirror = [row[::-1] for row in terrain]
    hands = {}
    for e in rec['fires_without_slot']:
        hands.setdefault(e['board'], set()).add(e['mirrored'])
    for k in range(N_NODES, N_BOARDS):
        d = next((e for e in rec['drawings'] if e['board'] == k), None)
        n = next((e for e in rec['drawn_t_not_fired'] if e['board'] == k), None)
        if d:
            later.append(d['rows'])
        elif n:
            later.append(n['rows'])
        elif k in hands:
            later.append(mirror if hands[k] == {True} else terrain)
        else:
            later.append(blank)
    return (q['intro'] + '\n==Basic Setup==\n' + q['basic'] + '\n'
            + _wikitext([[b['terrain'], b['softdrop'], b['spin']]])
            .replace(' |}', f' {q["initial"]} {q["softdrop"]} {q["rotate"]} |}}')
            + '\n' + q['zpiece'] + '\n' + _wikitext([[b['zbuild']]]) + '\n' + q['excess'] + '\n'
            + _wikitext([[b['repeat'], b['tetris']]]).replace(' |}', f' {q["repeat"]} {q["tetris"]} |}}')
            + '\n== Usages ==\n' + _wikitext([[x] for x in later]) + '\n')


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d):
    return d['variants'][0]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'terrain')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'spin').__setitem__('spin_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _set(node(d, 'zbuild')['rows'], 1, 0, 'z'), 'the Z build not the terrain by occupancy', 'build:'),
    (lambda d: node(d, 'spin').__setitem__('lines', 2), 'the TSS\'s line count', 'spin:'),
    (lambda d: _set(node(d, 'spin.after')['rows'], 4, 0, 'c'), 'the derived after board not what the TSS leaves',
     'after:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [0, 5]), 'the window widened by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [2, 4]), 'the window without the roof row', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [1, 3]), 'the window without the hole row', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _var(d)['agreement'][0].__setitem__('mirrored', True), 'a drawing read mirrored', 'window:'),
    (lambda d: _var(d)['payoff'].__setitem__('well_cell_pre_clear', [4, 1]), 'the well a column over', 'window:'),
    (lambda d: _var(d)['payoff'].__setitem__('board', 'spin'), 'the payoff on no after board', 'window:'),
    (lambda d: _var(d)['payoff'].__setitem__('lines', 3), 'the payoff read as a triple', 'window:'),
    (lambda d: _var(d)['misses'].append('terrain'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _var(d)['misses'].remove('softdrop'), 'a page board accounted nowhere', 'window:'),
    (lambda d: d['known_discrepancies'].pop(0), 'the spin board\'s unmuted row unnamed', 'discrepancy:'),
    (lambda d: d['known_discrepancies'].append({'id': 'terrain:colour', 'note': 'x'}), 'a stale discrepancy',
     'discrepancy:'),
    (lambda d: node(d, 'tetris').__setitem__('board', 0), 'a node\'s board index', 'page:'),
    (lambda d: node(d, 'repeat').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['cross_source']['page']['drawings'][0].__setitem__('t_cells', [[2, 1], [2, 2], [2, 3], [3, 2]]),
     'a page drawing\'s slot moved', 'page:'),
    (lambda d: d['cross_source']['other_techniques'].append({'file': 'stsd-technique.json', 'node': 'basic',
                                                             'mirrored': False}),
     'an other technique board recorded that does not fire', 'other:'),
    (lambda d: d['cross_source']['fires'].pop(), 'a routes board it fires on unrecorded', 'cross:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _moved(spec):
    s = copy.copy(spec)
    ds = external_drawings()
    s.external_drawings = lambda: [{**ds[0], 't_cells': [[r - 1, c] for r, c in ds[0]['t_cells']]}] + ds[1:]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against the basic boards alone)', 'window:'),
    (_moved, 'a page drawing\'s slot read a row higher', 'window:'),
]


def selftest() -> int:
    rc = TT.run_selftest(SPEC, MUTANTS,
                         {'board': ('{{pfrow|SG|SG|SP|SG|SG|SG|SG|SG|SG|SG}}', '{{pfrow|SG|SG|SG|SG|SG|SG|SG|SG|SG|SG}}'),
                          'text': ('Soft Drop T', 'Hard Drop T')},
                         SPEC_MUTANTS)
    ok = rc == 0
    base = build()
    text = _synthetic_page(base)
    clean = page_problems(base, text)
    if clean:
        print(f'selftest FAILED: the synthetic page does not verify ({clean[:3]})')
        ok = False
    else:
        terrain = node(base, 'terrain')['rows']
        loose = _wikitext([[terrain]])
        plants = {
            'the basic heading renamed': text.replace('==Basic Setup==', '==Renamed==', 1),
            'a board added': text + '\n' + _wikitext([[[EMPTY * WIDTH] * 4]]),
            'a firing board left unrecorded': text.replace(_wikitext([[[EMPTY * WIDTH] * 4]]), loose, 1),
            'a drawing removed from the page': text.replace(
                _wikitext([[base['cross_source']['page']['drawings'][0]['rows']]]), _wikitext([[[EMPTY * WIDTH] * 4]]), 1),
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
    print('selftest: Hamburger checks all caught' if ok else 'selftest: FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))
