"""The shared gate for a transcribed shiwehi.com MID-GAME TECHNIQUE page (STSD, …).

A route page (`route_transcription.py`) draws an opener from an EMPTY board, so its boards are whole
boards, bottom-aligned, matched at a fixed lock. A technique page draws a LOCAL SHAPE on a partial
stack: the cells around one spin, with everything else grey. So the thing a technique transcription
must carry, and this gate must check, is a WINDOW — the part of a drawing the matcher compares — and
the T cells it is anchored on. Each technique keeps its own transcription, a hand-checked literal in
`extract_<technique>_shapes.py` written to `<technique>-technique.json` (deliberately NOT
`*-routes.json`, so no route glob and no wikitext refetch job picks it up), and hands this module a
`TechniqueSpec`. Every rule two techniques share lives here, once.

THE RULES (each problem starts with its rule's tag; each technique's `--selftest` plants a defect
per rule and requires that tag):

  provenance: — the source block carries the url, the fetch, the snapshot hash and size; the terms
        block carries the page it was read from.
  grammar:  — ids unique; every cell in the alphabet; a board is 10 wide and at most `max_rows` tall;
        `kind` is one of KINDS; every reference (`spin_of`, `after_of`, `on`, `same_occupancy_as`,
        `extends`, a variant's boards) names a node; `page_order` lists every DRAWN board exactly
        once and no derived one.
  spin:     — a spin board's spin piece, read off its spin letters, is one tetromino; its upper-case
        cells are exactly the cells of the rows that are full with the piece in (cell by cell, so one
        unmuted cell in a cleared row fails); the spin's named line count is the number of those rows;
        a spin board with `spin_of` equals that board by occupancy once the piece is taken out (the
        base's reading letters, e.g. a highlighted hole, read as empty).
  after:    — an after board equals `after_spin(its spin board)` by occupancy, or the difference is
        a named discrepancy `<id>:after`.
  build:    — a build board less its `adds` letters equals its `on` board by occupancy, bottom-
        aligned; a DERIVED board equals what that subtraction leaves, exactly; `same_occupancy_as`
        and `extends` (this board is that one plus rows at the bottom) hold.
  window:   — per variant: (a) the window holds every spin cell; (b) it is exactly the bounding box
        of the spin cells, the roof cells (the filled cells above the spin's top row, which the
        variant lists and the gate re-reads) and the follow-up slot; (c) outside it, every cell of a
        row the spin does not clear is empty or `c`, so nothing the matcher ignores carries a piece
        letter; (d) the follow-up slot is empty on the after board, is one T, and fills exactly
        `followup.lines` rows of the DRAWN after board; (e) the window, evaluated the way the matcher
        evaluates it, fires on every board the variant lists in `fires_on` at exactly one RESTING
        placement, as drawn, and never mirrored; (f) it does not fire on any board in `misses`, at
        the spin the page draws there, or (for a board with no spin drawn) at any resting placement.
        A variant with `window_basis: agreement` takes (b*), (c*), (g) and (h) of `agreement_window`
        in place of (b) and (c): its window is the box every drawing of the shape agrees on.
  colour:   — every letter is whole pieces (`route_transcription.piece_groups_ok`, with the spec's
        `upper_groups`); a board that breaks it is a named discrepancy `<id>:colour`.
  cross:    — the variant, evaluated by the same predicate on every U-slot board of every committed
        `*-routes.json` (the U cells as the spin's cells), fires on exactly the boards the
        transcription records in `cross_source.fires`, plus the named `cross_source.also`; and every
        board those routes files LABEL as this technique is either one of them or named, with a
        reason, in `cross_source.labelled_not_fired`.
  quote:    — quote ids are unique, every `caption_quote` names one.
  discrepancy: — the measured discrepancies equal `known_discrepancies`, both ways.

The window PREDICATE is written twice, here (`window_fires`) and in `pipeline/sim/technique-facts.ts`
(`windowMatch`), and that is deliberate: the facts test runs the TS one over the same routes files and
must reproduce `cross_source.fires` + `cross_source.also` exactly. Two implementations, one answer.

`--html-dir` re-checks a refetched raw-HTML snapshot with `route_transcription.check_snapshot`,
unchanged: the file keeps its boards under `nodes` and carries an empty `basic_form` for that reason.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from pipeline.openers import route_transcription as RT
from pipeline.openers.route_transcription import EMPTY, WIDTH, after_spin, bottom, piece_groups_ok

HERE = Path(__file__).resolve().parent
KINDS = frozenset({'base', 'spin', 'after', 'build', 'illustration', 'derived'})
#: a technique page's boards are local, never compared whole, but still drawn short
MAX_ROWS = 8


@dataclass
class TechniqueSpec:
    """One technique's half of the gate. Everything else is shared."""
    out: Path
    build: Callable[[], dict]
    alphabet: frozenset
    #: letters that are EMPTY cells drawn highlighted (STSD's `B`, the garbage hole)
    empty_letters: str = ''
    #: rule 7: upper-case letter -> 'merge' (a cleared-row cell of its lower-case piece),
    #: 'separate', or absent (shading, skipped)
    upper_groups: dict = field(default_factory=dict)
    max_rows: int = MAX_ROWS
    #: the routes files the `cross:` rule scans (all of them by default)
    routes_glob: str = '*-routes.json'
    #: technique-only rules: fn(data) -> (problems, measured discrepancy ids)
    extra_checks: Callable | None = None
    #: drawings from OTHER committed transcriptions an `agreement` window is checked against:
    #: fn() -> [{'name', 'rows' ('-' empty), 't_cells' [[row, col]], 'mirrored'}]
    external_drawings: Callable | None = None


# ── geometry ─────────────────────────────────────────────────────────────────────────────────────
def is_empty(ch: str, spec: TechniqueSpec) -> bool:
    return ch == EMPTY or ch in spec.empty_letters


def filled_set(rows: list[str], spec: TechniqueSpec, skip: str = '') -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row)
            if not is_empty(ch, spec) and ch not in skip}


def occ_of(rows: list[str], spec: TechniqueSpec, drop: set | None = None) -> list[str]:
    """Occupancy ('#' / '-', so `bottom()` can trim it), with `drop` cells read as empty."""
    drop = drop or set()
    return [''.join(EMPTY if is_empty(ch, spec) or (r, c) in drop else '#' for c, ch in enumerate(row))
            for r, row in enumerate(rows)]


def spin_cells(n: dict) -> set[tuple[int, int]]:
    """The spin piece's cells off a spin board: its letter in either case."""
    p = n.get('spin_piece', 'T')
    return {(r, c) for r, row in enumerate(n['rows']) for c, ch in enumerate(row) if ch in (p, p.lower())}


def full_rows(occ_rows: list[str]) -> list[int]:
    return [r for r, row in enumerate(occ_rows) if EMPTY not in row]


def mirror_cells(cs, c0: int, c1: int):
    return {(r, c0 + (c1 - c)) for r, c in cs}


def window_cells(data: dict, var: dict, spec: TechniqueSpec, mirrored: bool) -> dict:
    """The variant's window in its board's frame: (row, col) -> 'T' (a spin cell), '#' (must be
    filled) or '.' (must be empty). Mirrored, columns reflect inside the window."""
    rows = node_rows(data, var['board'])
    (r0, r1), (c0, c1) = var['window']['rows'], var['window']['cols']
    tc = {tuple(x) for x in var['t_cells']}
    out = {}
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            v = 'T' if (r, c) in tc else ('.' if is_empty(rows[r][c], spec) else '#')
            out[(r, c0 + (c1 - c)) if mirrored else (r, c)] = v
    return out


def window_fires(data: dict, var: dict, spec: TechniqueSpec, board: list[str], lock: set,
                 mirrored: bool, filled=None) -> bool | None:
    """THE PREDICATE (the Python twin of `windowMatch` in technique-facts.ts). `board` is the board
    the piece went into (rows top to bottom), `lock` the piece's cells. Anchored on the spin cells:
    the lock must equal them under exactly one translation; then every non-spin window cell must
    agree (filled / empty) with the board. Off the board -> None. Colour is never compared."""
    W = window_cells(data, var, spec, mirrored)
    D = {k for k, v in W.items() if v == 'T'}
    if len(lock) != len(D):
        return False
    dr = min(r for r, _ in lock) - min(r for r, _ in D)
    dc = min(c for _, c in lock) - min(c for _, c in D)
    if {(r + dr, c + dc) for r, c in D} != set(lock):
        return False
    filled = filled or (lambda R, C: not is_empty(board[R][C], spec))
    for (r, c), v in W.items():
        R, C = r + dr, c + dc
        if R < 0 or R >= len(board) or C < 0 or C >= WIDTH:
            return None
        if v == 'T':
            continue
        if (v == '#') != filled(R, C):
            return False
    return True


def frame_map(data: dict, var: dict, spec: TechniqueSpec, lock: set, mirrored: bool):
    """The map `window_fires` applies, from the variant board's frame to a board where the spin went
    into `lock`: columns reflected inside the window when mirrored, then the one translation that puts
    the window's T on `lock`. Defined for cells outside the window too (the agreement rule extends it)."""
    (c0, c1) = var['window']['cols']
    tc = [tuple(x) for x in var['t_cells']]
    mc = (lambda c: c0 + (c1 - c)) if mirrored else (lambda c: c)
    dr = min(r for r, _ in lock) - min(r for r, _ in tc)
    dc = min(c for _, c in lock) - min(mc(c) for _, c in tc)
    return lambda r, c: (r + dr, mc(c) + dc)


def agreement_drawings(data: dict, var: dict, spec: TechniqueSpec) -> list[dict]:
    """The drawings an `agreement` window is checked on: the variant's own `agreement` boards (each a
    node of this transcription with its slot's T cells and orientation), then the spec's external ones."""
    out = [{'name': a['board'], 'rows': node_rows(data, a['board']),
            't_cells': a['t_cells'], 'mirrored': a['mirrored']} for a in var.get('agreement', [])]
    return out + (spec.external_drawings() if spec.external_drawings else [])


def agreement_window(data, v, spec, rows, sc, top, inwin, fr) -> list[str]:
    """The window rule for a variant whose window is the AGREEMENT BOX (`window_basis: agreement`), the
    opt-in alternative to the bounding box of T, roof and follow-up. A page that draws its technique
    once as a whole stacked board (pieces above the spin that are no part of the shape) and once more
    as local sketches cannot take the bounding-box rule: the stacked pieces would all be in the
    window. So the window is the box on which every drawing of the shape AGREES, cell for cell, and it
    is checked from both sides:

      (b*) the window lies on its board; its roof cells are the filled cells above the spin INSIDE it;
           the follow-up slot may lie outside it (the matcher carries it either way);
      (c*) every piece letter drawn outside the window in a row the spin does not clear is NAMED in
           `untested_drawn` (exactly those, both ways), so nothing the matcher ignores is silent;
      (g)  agreement: anchored at each drawing's declared slot, in its declared orientation, the window
           fires — and at no other resting placement, either orientation; at least two drawings, at
           least one from another transcription (the spec's `external_drawings`);
      (h)  maximality: widened by one row or column on any side, the new cells hold one on which the
           drawings disagree or which leaves one of them. The window is DERIVED from the drawings,
           never chosen: a cell every drawing agrees on cannot be left out of it at its edge.
    """
    bad = []
    (r0, r1), (c0, c1) = v['window']['rows'], v['window']['cols']
    if r0 < 0 or c0 < 0 or r1 >= len(rows) or c1 >= WIDTH:
        bad.append(f'window: {v["id"]}\'s window leaves its board')
        return bad
    roof = {(r, c) for (r, c) in filled_set(rows, spec) if r < top and (r, c) in inwin}
    if roof != {tuple(x) for x in v['roof_cells']}:
        bad.append(f'window: {v["id"]}.roof_cells are not the filled cells above the T inside the window: {sorted(roof)}')
    outside = {(r, c) for r, row in enumerate(rows) if r not in fr for c, ch in enumerate(row)
               if (r, c) not in inwin and ch not in (EMPTY, 'c') and not is_empty(ch, spec)}
    named = {tuple(x) for x in v.get('untested_drawn', {}).get('cells', [])}
    if outside != named:
        bad.append(f'window: {v["id"]}.untested_drawn {sorted(named)} is not the piece letters outside the window '
                   f'{sorted(outside)}')
    if outside and not v.get('untested_drawn', {}).get('reason'):
        bad.append(f'window: {v["id"]}.untested_drawn carries no reason')
    ds = agreement_drawings(data, v, spec)
    if len(ds) < 2 or not (spec.external_drawings and spec.external_drawings()):
        bad.append(f'window: {v["id"]}: an agreement window needs two drawings, one from another transcription')
        return bad
    W = window_cells(data, v, spec, False)
    for d in ds:
        lock = {tuple(x) for x in d['t_cells']}
        if any(not is_empty(d['rows'][r][c], spec) for r, c in lock):
            bad.append(f'window: {v["id"]}: {d["name"]}\'s slot is not empty')
            continue
        hits = [(frozenset(cs), m) for cs in t_placements(d['rows'], spec) for m in (False, True)
                if window_fires(data, v, spec, d['rows'], cs, m)]
        if hits != [(frozenset(lock), d['mirrored'])]:
            bad.append(f'window: {v["id"]} fires {len(hits)} time(s) on {d["name"]}, not once at its slot '
                       f'({"mirrored" if d["mirrored"] else "as drawn"})')
    maps = [(d, frame_map(data, v, spec, {tuple(x) for x in d['t_cells']}, d['mirrored'])) for d in ds]

    def agrees(r, c):
        vals = set()
        for d, f in maps:
            R, C = f(r, c)
            if R < 0 or R >= len(d['rows']) or C < 0 or C >= WIDTH:
                return False
            vals.add(not is_empty(d['rows'][R][C], spec))
        return len(vals) == 1
    for (r, c) in W:
        if W[(r, c)] != 'T' and not agrees(r, c):
            bad.append(f'window: {v["id"]}: the drawings disagree at ({r},{c}), inside the window')
    for side, strip in (('up', [(r0 - 1, c) for c in range(c0, c1 + 1)]),
                        ('down', [(r1 + 1, c) for c in range(c0, c1 + 1)]),
                        ('left', [(r, c0 - 1) for r in range(r0, r1 + 1)]),
                        ('right', [(r, c1 + 1) for r in range(r0, r1 + 1)])):
        if all(agrees(r, c) for r, c in strip):
            bad.append(f'window: {v["id"]}: every drawing agrees one {side} of the window — it is not the agreement box')
    return bad


def node_rows(data: dict, nid: str) -> list[str]:
    return next(n for n in data['nodes'] if n['id'] == nid)['rows']


def t_placements(board: list[str], spec: TechniqueSpec) -> list[set]:
    """Every resting placement of a T on a drawn board: four empty cells in a T shape, one of them
    on a filled cell or the floor."""
    shapes = {RT._norm(s) for s in RT._shapes('t')}
    occupied = filled_set(board, spec)
    h = len(board)
    out = []
    for sh in shapes:
        for r0 in range(-3, h):
            for c0 in range(-3, WIDTH):
                # RT shapes are (x, y-up); place them y-down from (r0, c0)
                cs = {(r0 + (3 - y), c0 + x) for x, y in sh}
                if any(r < 0 or r >= h or c < 0 or c >= WIDTH or (r, c) in occupied for r, c in cs):
                    continue
                if any(r + 1 == h or (r + 1, c) in occupied for r, c in cs):
                    out.append(cs)
    uniq = []
    for cs in out:
        if cs not in uniq:
            uniq.append(cs)
    return uniq


# ── the gate ─────────────────────────────────────────────────────────────────────────────────────
def verify(data: dict, spec: TechniqueSpec) -> list[str]:
    bad: list[str] = []
    measured: set[str] = set()
    nodes = data.get('nodes', [])
    byid = {n['id']: n for n in nodes}

    # provenance
    src, terms = data.get('source', {}), data.get('terms', {})
    for k in ('url', 'title', 'fetched', 'fetch_method', 'snapshot_file', 'snapshot_sha256', 'snapshot_bytes'):
        if not src.get(k):
            bad.append(f'provenance: source.{k} missing')
    if not terms.get('url'):
        bad.append('provenance: terms.url missing')

    # grammar
    if len(byid) != len(nodes):
        bad.append('grammar: duplicate node ids')
    if data.get('empty_letters', '') != spec.empty_letters:
        bad.append(f'grammar: empty_letters {data.get("empty_letters")!r} is not the spec\'s {spec.empty_letters!r} '
                   f'(the matcher reads the JSON\'s)')
    for n in nodes:
        if n.get('kind') not in KINDS:
            bad.append(f'grammar: {n["id"]} kind {n.get("kind")!r}')
        rows = n.get('rows')
        if not rows:
            bad.append(f'grammar: {n["id"]} has no rows')
            continue
        if len(rows) > spec.max_rows or any(len(r) != WIDTH for r in rows):
            bad.append(f'grammar: {n["id"]} is not a ≤{spec.max_rows}-row, {WIDTH}-wide board')
        for r in rows:
            for ch in r:
                if ch not in spec.alphabet:
                    bad.append(f'grammar: {n["id"]} cell {ch!r} not in the alphabet')
        for ref in ('spin_of', 'after_of', 'on', 'same_occupancy_as', 'extends'):
            if ref in n and n[ref] not in byid:
                bad.append(f'grammar: {n["id"]}.{ref} names no node ({n[ref]!r})')
        if (n['kind'] == 'derived') != bool(n.get('derived')):
            bad.append(f'grammar: {n["id"]} kind derived iff derived: true')
    drawn = [n['id'] for n in nodes if not n.get('derived')]
    if data.get('page_order') != drawn:
        bad.append(f'grammar: page_order {data.get("page_order")} is not the drawn boards in order {drawn}')
    for v in data.get('variants', []):
        for ref in [v['board'], v['followup']['board'], *v.get('fires_on', []), *v.get('misses', [])]:
            if ref not in byid:
                bad.append(f'grammar: variant {v["id"]} names no node {ref!r}')
    if any(b.startswith('grammar:') for b in bad):
        return bad

    # quotes
    qids = [q['id'] for q in data.get('quotes', [])]
    if len(set(qids)) != len(qids):
        bad.append('quote: duplicate quote ids')
    for n in nodes:
        if 'caption_quote' in n and n['caption_quote'] not in qids:
            bad.append(f'quote: {n["id"]}.caption_quote names no quote')

    # spin
    for n in nodes:
        if n['kind'] != 'spin':
            continue
        sc = spin_cells(n)
        piece = n.get('spin_piece', 'T').lower()
        ys = {(c, len(n['rows']) - 1 - r) for r, c in sc}
        if len(sc) != 4 or RT._norm(ys) not in RT._shapes(piece):
            bad.append(f'spin: {n["id"]}\'s {piece} cells are not one {piece}')
            continue
        o = occ_of(n['rows'], spec)
        fr = full_rows(o)
        # cell by cell: every cell of a full row is drawn muted (upper case), no other cell is
        wrong = [(r, c) for r, row in enumerate(n['rows']) for c, ch in enumerate(row)
                 if ch not in spec.empty_letters and ch != EMPTY and ch.isupper() != (r in fr)]
        if wrong:
            bad.append(f'spin: {n["id"]}: cells {wrong[:4]} are muted off, or unmuted in, the full rows {fr}')
        if n.get('lines') != len(fr):
            bad.append(f'spin: {n["id"]}: lines {n.get("lines")} but {len(fr)} rows clear')
        if 'spin_of' in n:
            base = byid[n['spin_of']]['rows']
            if bottom(occ_of(n['rows'], spec, sc), MAX_ROWS) != bottom(occ_of(base, spec), MAX_ROWS):
                bad.append(f'spin: {n["id"]} less its {piece} is not {n["spin_of"]} by occupancy')

    # after
    for n in nodes:
        if n['kind'] != 'after':
            continue
        sp = byid[n['after_of']]
        got, _ = after_spin([''.join('t' if (r, c) in spin_cells(sp) else ('-' if is_empty(ch, spec) else 'c')
                                     for c, ch in enumerate(row)) for r, row in enumerate(sp['rows'])])
        if bottom(occ_of(got, spec), MAX_ROWS) != bottom(occ_of(n['rows'], spec), MAX_ROWS):
            measured.add(f'{n["id"]}:after')

    # build / derived
    for n in nodes:
        if 'on' in n:
            adds = set(n.get('adds', ''))
            less = [''.join('-' if ch in adds else ch for ch in row) for row in n['rows']]
            on = byid[n['on']]
            if on.get('derived'):
                if bottom(less, MAX_ROWS) != bottom(on['rows'], MAX_ROWS):
                    bad.append(f'build: derived {on["id"]} is not {n["id"]} less {sorted(adds)}')
            elif bottom(occ_of(less, spec), MAX_ROWS) != bottom(occ_of(on['rows'], spec), MAX_ROWS):
                bad.append(f'build: {n["id"]} less {sorted(adds)} is not {n["on"]} by occupancy')
        if 'same_occupancy_as' in n:
            o = byid[n['same_occupancy_as']]['rows']
            if bottom(occ_of(n['rows'], spec), MAX_ROWS) != bottom(occ_of(o, spec), MAX_ROWS):
                bad.append(f'build: {n["id"]} is not {n["same_occupancy_as"]} by occupancy')
        if 'extends' in n:
            e = byid[n['extends']]['rows']
            k = n.get('extra_bottom_rows', 0)
            if bottom(occ_of(n['rows'][:len(n['rows']) - k], spec), MAX_ROWS) != bottom(occ_of(e, spec), MAX_ROWS):
                bad.append(f'build: {n["id"]} less its bottom {k} row(s) is not {n["extends"]} by occupancy')
        if n.get('derived') and not any(m.get('on') == n['id'] for m in nodes):
            bad.append(f'build: derived {n["id"]} is no board\'s `on`')

    # window
    for v in data.get('variants', []):
        sp = byid[v['board']]
        rows = sp['rows']
        tc = {tuple(x) for x in v['t_cells']}
        sc = spin_cells(sp)
        (r0, r1), (c0, c1) = v['window']['rows'], v['window']['cols']
        inwin = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        if tc != sc:
            bad.append(f'window: {v["id"]}.t_cells {sorted(tc)} are not {v["board"]}\'s T cells {sorted(sc)}')
        if not tc <= inwin:
            bad.append(f'window: {v["id"]}\'s window does not hold every T cell')
        top = min(r for r, _ in sc)
        fu = {tuple(x) for x in v['followup']['t_cells_pre_clear']}
        fr = set(full_rows(occ_of(rows, spec)))
        if v.get('window_basis') == 'agreement':
            bad += agreement_window(data, v, spec, rows, sc, top, inwin, fr)
        else:
            roof = {(r, c) for (r, c) in filled_set(rows, spec) if r < top}
            if roof != {tuple(x) for x in v['roof_cells']}:
                bad.append(f'window: {v["id"]}.roof_cells are not the filled cells above the T: {sorted(roof)}')
            basis = sc | roof | fu
            box = ([min(r for r, _ in basis), max(r for r, _ in basis)], [min(c for _, c in basis), max(c for _, c in basis)])
            if [v['window']['rows'], v['window']['cols']] != [box[0], box[1]]:
                bad.append(f'window: {v["id"]}\'s window {v["window"]} is not the bounding box {box} of T, roof and follow-up')
            for r, row in enumerate(rows):
                if r in fr:
                    continue
                for c, ch in enumerate(row):
                    if (r, c) not in inwin and ch not in (EMPTY, 'c'):
                        bad.append(f'window: {v["id"]}: {v["board"]} draws {ch!r} at ({r},{c}) outside the window')
        # (d) the follow-up slot
        after = byid[v['followup']['board']]['rows']
        fa = {tuple(x) for x in v['followup']['t_cells_after']}
        # the after board is compared bottom-aligned: a page may draw it shorter than the spin board
        # (STSD draws both the same height, so the shift is 0 there)
        shift = len(rows) - len(after)
        mapped = {(r + sum(1 for x in fr if x > r) - shift, c) for r, c in fu}
        if mapped != fa:
            bad.append(f'window: {v["id"]}: the pre-clear follow-up slot maps to {sorted(mapped)}, not t_cells_after')
        ys = {(c, len(after) - 1 - r) for r, c in fa}
        if RT._norm(ys) not in RT._shapes('t') or any(not is_empty(after[r][c], spec) for r, c in fa):
            bad.append(f'window: {v["id"]}: the follow-up slot is not an empty T on {v["followup"]["board"]}')
        else:
            o = occ_of(after, spec)
            o = [''.join('#' if (r, c) in fa else ch for c, ch in enumerate(row)) for r, row in enumerate(o)]
            if len(full_rows(o)) != v['followup']['lines']:
                bad.append(f'window: {v["id"]}: the follow-up T fills {len(full_rows(o))} rows of the drawn '
                           f'after board, not {v["followup"]["lines"]}')
        # (e) fires on every listed build, once, as drawn
        for bid in v.get('fires_on', []):
            b = byid[bid]['rows']
            hits = [(cs, m) for cs in t_placements(b, spec) for m in (False, True)
                    if window_fires(data, v, spec, b, cs, m)]
            if len(hits) != 1 or hits[0][1]:
                bad.append(f'window: {v["id"]} fires {len(hits)} time(s) on {bid} '
                           f'({["drawn", "mirrored"][hits[0][1]] if hits else "-"}), not once as drawn')
            else:
                o = occ_of(b, spec)
                o = [''.join('#' if (r, c) in hits[0][0] else ch for c, ch in enumerate(row)) for r, row in enumerate(o)]
                if len(full_rows(o)) != 2:
                    bad.append(f'window: {v["id"]} fires on {bid} at a placement that clears {len(full_rows(o))} rows')
        # (f) never on a listed miss
        for bid in v.get('misses', []):
            mb = byid[bid]
            if mb['kind'] == 'spin':
                sc2 = spin_cells(mb)
                pre = [''.join('-' if (r, c) in sc2 else ch for c, ch in enumerate(row)) for r, row in enumerate(mb['rows'])]
                cands = [sc2]
                b = pre
            else:
                b = mb['rows']
                cands = t_placements(b, spec)
            if any(window_fires(data, v, spec, b, cs, m) for cs in cands for m in (False, True)):
                bad.append(f'window: {v["id"]} fires on {bid}, which the page draws as no {v["id"]}')

    # colour
    for n in nodes:
        if n['kind'] == 'after':
            continue   # its letters are pieces cut by the clear; the after rule checks it
        if piece_groups_ok(n['rows'], spec.upper_groups):
            measured.add(f'{n["id"]}:colour')

    # cross
    bad += check_cross_routes(data, spec)

    if spec.extra_checks:
        p, m = spec.extra_checks(data)
        bad += p
        measured |= m
    known = {d['id'] for d in data.get('known_discrepancies', [])}
    for m in sorted(measured - known):
        bad.append(f'discrepancy: measured {m} is not named in known_discrepancies')
    for k in sorted(known - measured):
        bad.append(f'discrepancy: named {k} is no longer measured')
    return bad


def route_u_boards(spec: TechniqueSpec):
    """Every board of every committed routes file that draws a 4-cell U slot: (file, node, rows, U)."""
    for f in sorted(HERE.glob(spec.routes_glob)):
        d = json.loads(f.read_text())
        for n in d['nodes']:
            rows = n.get('rows')
            if not rows:
                continue
            u = {(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == 'U'}
            if len(u) == 4:
                yield f.name, n, rows, u


def cross_fires(data: dict, spec: TechniqueSpec) -> list[dict]:
    """The variant, by THE predicate, over every U-slot routes board: `U` is the spin cell, every
    other non-`-` letter filled. Returned in file, then page, order."""
    out = []
    for fname, n, rows, u in route_u_boards(spec):
        filled = (lambda R, C, rows=rows: rows[R][C] not in (EMPTY, 'U'))
        for v in data.get('variants', []):
            for m in (False, True):
                if window_fires(data, v, spec, rows, u, m, filled):
                    out.append({'file': fname, 'node': n['id'], 'variant': v['id'], 'mirrored': m})
    return out


def check_cross_routes(data: dict, spec: TechniqueSpec) -> list[str]:
    xs = data.get('cross_source', {})
    if not xs.get('fires'):
        return ['cross: the transcription records no routes board the technique fires on — '
                'a technique gate needs an independent drawing to check its window against']
    want = xs['fires'] + xs.get('also', [])
    key = lambda e: (e['file'], e['node'], e['variant'], e['mirrored'])
    got = cross_fires(data, spec)
    bad = []
    if sorted(map(key, got)) != sorted(map(key, [{k: e[k] for k in ('file', 'node', 'variant', 'mirrored')}
                                                 for e in want])):
        bad.append(f'cross: the window fires on {sorted(map(key, got))}, the transcription records '
                   f'{sorted(map(key, want))}')
    fired = {(e['file'], e['node']) for e in got}
    named = {(e['file'], e['node']) for e in xs.get('labelled_not_fired', [])}
    tag = xs.get('label_pattern', '').lower()
    for f in sorted(HERE.glob(spec.routes_glob)):
        for n in json.loads(f.read_text())['nodes']:
            text = (n['id'] + ' ' + n.get('label_jp', '') + ' ' + n.get('label', '')).lower()
            if tag and tag in text and (f.name, n['id']) not in fired and (f.name, n['id']) not in named:
                # a node whose own label calls it this technique, which the window does not fire on
                if 'rows' in n:
                    bad.append(f'cross: {f.name} {n["id"]} is labelled {tag} and neither fires nor is named')
    for f, nid in sorted(named & fired):
        bad.append(f'cross: {f} {nid} is named in labelled_not_fired but fires')
    return bad


def drift(data: dict, spec: TechniqueSpec) -> list[str]:
    return [] if data == spec.build() else [f'drift: {spec.out.name} differs from SPEC — rerun --write']


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def node(d: dict, nid: str) -> dict:
    return next(n for n in d['nodes'] if n['id'] == nid)


def run_selftest(spec: TechniqueSpec, mutants: list, snapshot_edits: dict, spec_mutants: list = ()) -> int:
    """A gate nothing can fail is decorative. `mutants` is [(fn(d), label, tag)]; `spec_mutants` is
    [(fn(spec) -> spec, label, tag)]; `snapshot_edits` is {'board': (old, new), 'text': (old, new)}
    applied to a synthetic raw-HTML snapshot rebuilt from the transcription."""
    base = spec.build()
    if verify(base, spec) or drift(json.loads(spec.out.read_text()), spec):
        print('selftest: the committed file does not verify — fix that first', file=sys.stderr)
        return 1
    ok = True

    def expect(problems, label, tag):
        nonlocal ok
        if any(p.startswith(tag) for p in problems):
            print(f'  killed: {label}  [{tag}]')
        else:
            print(f'selftest FAILED: {label} was not caught by {tag!r} (got {problems[:3]})', file=sys.stderr)
            ok = False

    for fn, label, tag in mutants:
        d = copy.deepcopy(base)
        fn(d)
        expect(verify(d, spec), label, tag)
    for fn, label, tag in spec_mutants:
        expect(verify(copy.deepcopy(base), fn(spec)), label, tag)
    d = copy.deepcopy(base)
    node(d, base['page_order'][0])['label'] = 'edited by hand'
    expect(drift(d, spec), 'a hand edit to the committed JSON', 'drift:')
    # the snapshot locator, unchanged from the route gate: a raw-HTML page rebuilt from the boards
    html = '\n'.join('<div class="ttt">\n' + '\n'.join(node(base, i)['rows']) + '\n</div>' for i in base['page_order'])
    html += '\n' + '\n'.join(f'<p>{q["verbatim"]}</p>' for q in base['quotes'])
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / base['source']['snapshot_file']
        p.write_text(html)
        clean = [x for x in RT.check_snapshot(base, Path(td)) if 'sha256' not in x]
        p.write_text(html.replace(*snapshot_edits['board'], 1))
        dirty = RT.check_snapshot(base, Path(td))
        p.write_text(html.replace(*snapshot_edits['text'], 1))
        lost = RT.check_snapshot(base, Path(td))
    if clean or not any('differs' in x for x in dirty) or not any('quote' in x for x in lost):
        print(f'selftest FAILED: snapshot re-check (clean={clean}, dirty={dirty[:2]}, lost={lost[:2]})',
              file=sys.stderr)
        ok = False
    else:
        print('  killed: a redrawn board / an edited sentence in the page snapshot  [snapshot:]')
    print('selftest: all mutants killed' if ok else 'selftest: FAILED')
    return 0 if ok else 1


def main(spec: TechniqueSpec, selftest: Callable[[], int], doc: str | None) -> int:
    ap = argparse.ArgumentParser(description=(doc or '').split('\n')[0])
    ap.add_argument('--html-dir', type=Path, help='directory holding the page snapshot of a refetch')
    ap.add_argument('--write', action='store_true', help=f'rewrite {spec.out.name} from SPEC')
    ap.add_argument('--selftest', action='store_true', help='prove the verifier has teeth')
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    data = spec.build()
    problems = verify(data, spec)
    if args.html_dir:
        problems += RT.check_snapshot(data, args.html_dir)
    if args.write and not problems:
        spec.out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(f'wrote {spec.out.relative_to(HERE.parent.parent)}')
    if not args.write:
        problems += drift(json.loads(spec.out.read_text()), spec)
    kinds: dict[str, int] = {}
    for n in data['nodes']:
        kinds[n['kind']] = kinds.get(n['kind'], 0) + 1
    print(f'  {len(data["nodes"])} boards: ' + ', '.join(f'{v} {k}' for k, v in sorted(kinds.items()))
          + f'; {len(data["page_order"])} drawn in page order')
    for f in cross_fires(data, spec):
        print(f'  cross: {f["variant"]} fires on {f["file"]} {f["node"]}'
              f'{" (mirrored)" if f["mirrored"] else ""}')
    if problems:
        for p in problems:
            print(f'FAIL {p}', file=sys.stderr)
        return 1
    print(f'{spec.out.name} OK')
    return 0
