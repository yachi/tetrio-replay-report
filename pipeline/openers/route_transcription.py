"""The shared gate for a transcribed shiwehi.com opener ROUTE page (迷走砲, はちみつ砲, …).

Each opener keeps its own transcription — a hand-checked literal in `extract_<opener>_routes.py`,
written to `<opener>-routes.json` — and hands this module a `TranscriptionSpec`: what its board
alphabet is, which harddrop field its bag 1 must equal, which of its features are not boards, and
any rule only that page needs. Every rule two openers share lives here, ONCE: a rule kept in two
gates drifts the way a figure kept in two places does (CLAUDE.md, 「Three backends」).

THE RULES (each problem starts with its rule's tag; each opener's `--selftest` plants one defect
per rule and requires that tag):

  1. grammar — ids unique; a node carries a board XOR a non-board kind (a kind the spec lists in
     `board_kinds` carries both); every cell in the alphabet; a `p` cell or a board taller than the
     classifier's ROWS needs an `unmatchable` reason; every reference names a node (a `parent` may
     also name a declared group); a list node's id is `<list>#<index>` and its slot flags are what
     its cells say; a condition names pieces. Every non-board feature is on the spec's named list.
     `page_order` lists every board the page draws exactly once.
  2. harddrop — the spec's bag-1 node equals harddrop's field for the opener cell for cell, as
     drawn or mirrored (`wiki-openers.json`).
  3. internal consistency — a bag-2 board's `c` (and prior-bag letter) cells are exactly its bag-1
     base; a later board's `c` cells are exactly what its base leaves after its T-spin; a Perfect
     Clear pattern clears the spec's `pc_lines`; a 基本形 board equals the node it names, modulo
     a declared recolouring; a board that draws its spin elsewhere (`spin_board`) or is the board
     after another's spin (`after_of`) agrees with it; a board that CONTINUES its base (more pieces,
     then a T into the slot the base leaves in its bottom rows) contains what is left of it.
  4. distinctness — bag-2 boards differ by occupancy (siblings of one group by colour); no
     pattern repeats under one parent; the bag-3 patterns share occupancy, so colour must decide.
  5. discrepancies — list counts against the page's own split; the set of measured source
     discrepancies equals the named `known_discrepancies`, both ways.
  7. piece decomposition — every letter is whole pieces of that letter in the kept-rows frame.

`--html-dir` re-checks a refetched markdown snapshot: every board in page order, every non-board
feature's `page_text`.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
WIKI = HERE / 'wiki-openers.json'

WIDTH = 10
#: `match.ts`'s `ROWS`. A board taller than this cannot be compared by the classifier at all.
ROWS = 8
EMPTY = '-'
PIECES = frozenset('IJLOSTZ')
SWAP = {'l': 'j', 'j': 'l', 's': 'z', 'z': 's', 'Z': 'S', 'J': 'L', 'L': 'J', 'S': 'Z'}


@dataclass
class TranscriptionSpec:
    """One opener's half of the gate. Everything else is shared."""
    out: Path
    build: Callable[[], dict]
    alphabet: frozenset
    #: node id -> the non-board kind it was read as (image_only, text_only)
    non_board: dict
    #: {'key': wiki-openers key, 'node': the bag-1 node that must equal its field}
    harddrop: dict
    #: node kinds that carry a board as well (an illustration of a spin, drawn with shading)
    board_kinds: frozenset = frozenset()
    pc_lines: int = 8
    #: upper-case letters inside a bag-2 board that are bag-1 cells drawn in colour (迷走砲's Z)
    prior_letters: str = ''
    #: rule 7: an upper-case letter that is its own piece ('separate', 迷走砲's Z) or a shaded cell
    #: of the lower-case piece it sits in ('merge'); any other upper-case letter is shading
    upper_groups: dict = field(default_factory=dict)
    #: list-node flags computed from the cells: name -> fn(rows) -> bool
    slot_flags: dict = field(default_factory=dict)
    #: the largest bag-3 occupancy class must span at least this many parents
    occupancy_class_parents: int = 2
    #: opener-only rules: fn(data, ctx) -> (problems, measured discrepancy ids)
    extra_checks: Callable | None = None
    #: placeholder letters: a board holding one is never whole pieces and must be unmatchable
    placeholders: str = 'p'


# ── board geometry ─────────────────────────────────────────────────────────────────────────────
def t_slot(rows: list[str], ch: str = 'U') -> str | None:
    """`flat` for the UUU-over-U TSD slot, `other` for any other U, None for none. `ch` reads the
    same shape off another letter (a TSD T drawn as `t`)."""
    cells = [(r, c) for r, row in enumerate(rows) for c, x in enumerate(row) if x == ch]
    if not cells:
        return None
    by_row: dict[int, list[int]] = {}
    for r, c in cells:
        by_row.setdefault(r, []).append(c)
    if len(cells) == 4 and len(by_row) == 2:
        (ra, ca), (rb, cb) = sorted((r, sorted(cs)) for r, cs in by_row.items())
        if rb == ra + 1 and len(ca) == 3 and ca == [ca[0], ca[0] + 1, ca[0] + 2] and cb == [ca[1]]:
            return 'flat'
    return 'other'


def bottom(rows: list[str], height: int) -> list[str]:
    """Strip leading empty rows, then pad (with empty rows on top) to `height`."""
    first = next((i for i, r in enumerate(rows) if r != EMPTY * WIDTH), len(rows))
    rows = rows[first:]
    return [EMPTY * WIDTH] * max(0, height - len(rows)) + rows


def mirror(rows: list[str]) -> list[str]:
    return [''.join(SWAP.get(c, c) for c in reversed(r)) for r in rows]


def occ(rows: list[str]) -> list[str]:
    return [''.join('#' if c != EMPTY else '.' for c in r) for r in rows]


def after_spin(rows: list[str]) -> tuple[list[str], int]:
    """Put the T into every U cell, clear full rows, and return (board, rows cleared)."""
    filled = [r.replace('U', 't') for r in rows]
    keep = [r for r in filled if EMPTY in r]
    cleared = len(filled) - len(keep)
    return [EMPTY * WIDTH] * cleared + keep, cleared


def cells(rows: list[str], pred) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if pred(ch)}


#: One drawing per piece, y-UP (x, y); every rotation is derived, never typed.
_PIECE_BASE = {'i': [(0, 0), (1, 0), (2, 0), (3, 0)], 'o': [(0, 0), (1, 0), (0, 1), (1, 1)],
               't': [(0, 0), (1, 0), (2, 0), (1, 1)], 's': [(0, 0), (1, 0), (1, 1), (2, 1)],
               'z': [(1, 0), (2, 0), (0, 1), (1, 1)], 'j': [(0, 0), (1, 0), (2, 0), (0, 1)],
               'l': [(0, 0), (1, 0), (2, 0), (2, 1)]}


def _norm(cs):
    mx, my = min(x for x, _ in cs), min(y for _, y in cs)
    return tuple(sorted((x - mx, y - my) for x, y in cs))


def _shapes(letter):
    out, cur = set(), _PIECE_BASE[letter]
    for _ in range(4):
        out.add(_norm(cur))
        cur = [(y, -x) for x, y in cur]
    return out


def piece_groups_ok(rows: list[str], upper_groups: dict | None = None) -> list[str]:
    """Rule 7: every letter group of a board is one tetromino of that letter, either as drawn or
    with the rows it straddles (and does not touch) removed — the kept-rows frame a later piece is
    drawn in after rows under it have cleared. Returns the letters that are not. An upper-case
    letter is its own group ('separate') or part of its lower-case piece ('merge'), per the spec."""
    ug = upper_groups if upper_groups is not None else {'Z': 'separate'}
    h = len(rows)
    groups: dict[str, list[tuple[int, int]]] = {}
    for i, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == 'U':
                key = 't'
            elif ch.isupper():
                how = ug.get(ch)
                key = ch if how == 'separate' else ch.lower() if how == 'merge' else None
            else:
                key = ch
            if key is not None and key.lower() in _PIECE_BASE:
                groups.setdefault(key, []).append((x, h - 1 - i))
    bad = []
    for key, cs in sorted(groups.items()):
        letter = key.lower()
        if len(cs) != 4:
            bad.append(key)
            continue
        ys = sorted({y for _, y in cs})
        gap = [y for y in range(ys[0], ys[-1] + 1) if y not in ys]
        kept = [(x, y - sum(1 for g in gap if g < y)) for x, y in cs]
        if _norm(cs) not in _shapes(letter) and _norm(kept) not in _shapes(letter):
            bad.append(key)
    return bad


def recolour_equal(basic: list[str], node: list[str], allowed: dict) -> bool:
    """A 基本形 board against its node, bottom-aligned: equal cell for cell, except where the node's
    cell `a` is drawn as `allowed[a]` (a declared recolouring, e.g. the held J drawn grey)."""
    a, b = bottom(basic, ROWS), bottom(node, ROWS)
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        for x, y in zip(ra, rb):
            if x != y and allowed.get(y) != x:
                return False
    return True


# ── the gate ───────────────────────────────────────────────────────────────────────────────────
def verify(data: dict, spec: TranscriptionSpec) -> list[str]:
    """Every shared rule, plus the spec's own. Returns problems; each starts with its rule's tag."""
    bad: list[str] = []
    nodes = data.get('nodes', [])
    ids = [n.get('id') for n in nodes]
    by_id = {n['id']: n for n in nodes if 'id' in n}
    boards = {n['id']: n['rows'] for n in nodes if 'rows' in n}
    boards.update({b['id']: b['rows'] for b in data.get('basic_form', [])})
    groups = {g['id']: g for g in data.get('groups', [])}

    # ── provenance ──
    terms = data.get('terms', {})
    for k in ('url', 'dated', 'read', 'allows', 'excludes', 'requests', 'how_met'):
        if not terms.get(k):
            bad.append(f'terms: provenance field {k!r} is missing')
    for k in ('url', 'updated', 'fetched', 'fetch_method', 'snapshot_sha256'):
        if not data.get('source', {}).get(k):
            bad.append(f'source: provenance field {k!r} is missing')

    # ── rule 1: grammar ──
    all_ids = ids + [b['id'] for b in data.get('basic_form', [])]
    if len(all_ids) != len(set(all_ids)):
        bad.append('grammar: duplicate ids')
    node_kinds = frozenset(spec.non_board.values()) | spec.board_kinds
    for n in nodes:
        nid = n.get('id', '?')
        has_board = 'rows' in n
        kind = n.get('node_kind')
        non_board_kind = kind is not None and kind not in spec.board_kinds
        if has_board == non_board_kind:
            bad.append(f'exclusive-or: {nid} must carry exactly one of a board or a node_kind')
        if kind is not None and kind not in node_kinds:
            bad.append(f'grammar: {nid} has unknown node_kind {kind!r}')
        if 'unmatchable' in n and not n['unmatchable']:
            bad.append(f'grammar: {nid} is unmatchable without a reason')
        if has_board:
            rows = n['rows']
            if any(len(r) != WIDTH for r in rows):
                bad.append(f'grammar: {nid} has a row that is not {WIDTH} wide')
            if any(ch not in spec.alphabet for r in rows for ch in r):
                bad.append(f'grammar: {nid} has a cell outside {"".join(sorted(spec.alphabet))}')
            if 'unmatchable' not in n:
                if any(ph in r for r in rows for ph in spec.placeholders):
                    bad.append(f'placeholder: {nid} has a {spec.placeholders} cell but is not marked '
                               'unmatchable')
                if len(bottom(rows, 0)) > ROWS:
                    bad.append(f'grammar: {nid} is taller than {ROWS} rows but not unmatchable')
        for ref in ('parent', 'base', 'derived_from', 'mirror_of', 'spin_board', 'after_of', 'drawn_as'):
            target = n.get(ref)
            if target is None:
                continue
            ok = target in by_id or (ref == 'parent' and target in groups) or (
                ref == 'drawn_as' and target in boards)
            if not ok:
                bad.append(f'grammar: {nid} {ref} {target!r} names no node')
        if 'group' in n and n['group'] not in groups:
            bad.append(f'grammar: {nid} group {n["group"]!r} is not a declared group')
        if 'list' in n:
            if nid != f'{n["list"]}#{n.get("index")}':
                bad.append(f'id-index: {nid} does not match its list {n["list"]!r} and index '
                           f'{n.get("index")}')
            if any(n.get(k) != fn(n['rows']) for k, fn in spec.slot_flags.items()):
                bad.append(f'grammar: {nid} {" / ".join(reversed(list(spec.slot_flags)))} disagree '
                           f'with its cells')
        cond = n.get('condition')
        if cond is not None:
            pieces = [p for c in cond.get('all', []) for p in c.get('before', [])]
            pieces += [cond['early']] if 'early' in cond else []
            if any(p not in PIECES for p in pieces) or (
                    'bag1' in cond and cond['bag1'] not in by_id):
                bad.append(f'grammar: {nid} condition names something that is not a piece/node')
    for g in groups.values():
        members = [n for n in nodes if n.get('group') == g['id']]
        if g['id'] in by_id or len(members) != g.get('drawn'):
            bad.append(f'grammar: group {g["id"]} is a node id or does not have {g.get("drawn")} '
                       f'members ({len(members)})')

    # every non-board feature of the page is still a node, with the kind it was read as
    for nid, kind in spec.non_board.items():
        if by_id.get(nid, {}).get('node_kind') != kind:
            bad.append(f'non-board: {nid} ({kind}) is missing or changed kind')
    for n in nodes:
        if 'node_kind' in n and n['node_kind'] not in spec.board_kinds and (
                n['id'] not in spec.non_board or not n.get('page_text')):
            bad.append(f'non-board: {n["id"]} is not on the named list or has no page_text')

    # the page order covers every page-drawn board exactly once
    po = data.get('page_order', [])
    drawn = [i for i in all_ids if i in boards and not by_id.get(i, {}).get('derived')
             and not by_id.get(i, {}).get('drawn_as')]
    if sorted(po) != sorted(drawn) or len(po) != len(set(po)):
        bad.append('page_order: does not list every drawn board exactly once')
    for n in nodes:
        if n.get('drawn_as') and boards.get(n['drawn_as']) != n.get('rows'):
            bad.append(f'grammar: {n["id"]} is not the board it is drawn as ({n["drawn_as"]})')
        if n.get('mirror_of') in boards and 'rows' in n and (
                bottom(n['rows'], ROWS) != mirror(bottom(boards[n['mirror_of']], ROWS))):
            bad.append(f'mirror-of: {n["id"]} is not {n["mirror_of"]} mirrored (J<->L, S<->Z)')

    # ── rule 2: cross-source against harddrop ──
    wiki = json.loads(WIKI.read_text())
    key, hnode = spec.harddrop['key'], spec.harddrop['node']
    op = next((o for o in wiki['openers'] if o['key'] == key), None)
    hd = {tuple(f['rows']) for f in op['fields']} if op else set()
    if hnode in boards:
        ours = [r.replace('-', '.').upper() for r in bottom(boards[hnode], 0)]
        mine = {tuple(ours), tuple(r.upper() for r in mirror([x.lower() for x in ours]))}
        if not (mine & hd):
            bad.append(f'harddrop: {hnode} disagrees with wiki-openers.json {key} '
                       'cell for cell, as drawn and mirrored')
    else:
        bad.append(f'harddrop: {hnode} is missing')

    # ── rule 3: internal consistency ──
    def post_spin(base: str) -> tuple[list[str], int, str]:
        """What `base` leaves after its T-spin: from its own U cells, from the board that draws its
        spin (`spin_board`), or — for a board that IS the after-spin board (`after_of`) — itself."""
        b = by_id.get(base, {})
        if b.get('spin_board') in boards:
            after, cl = after_spin(boards[b['spin_board']])
            return after, cl, base
        if b.get('after_of') in boards:
            _, cl = after_spin(boards[b['after_of']])
            return boards[base], cl, base
        after, cl = after_spin(boards[base])
        return after, cl, base

    for n in nodes:
        nid = n.get('id', '?')
        if n.get('spin_board') in boards and 'rows' in n:
            sb = boards[n['spin_board']]
            if occ(bottom([r.replace('U', EMPTY) for r in sb], ROWS)) != occ(bottom(n['rows'], ROWS)) \
                    or 'U' not in ''.join(sb):
                bad.append(f'spin-board: {nid} is not {n["spin_board"]} without its U cells')
        if n.get('after_of') in boards and 'rows' in n:
            after, cl = after_spin(boards[n['after_of']])
            h = max(len(after), len(n['rows']))
            if cl == 0 or occ(bottom(after, h)) != occ(bottom(n['rows'], h)):
                bad.append(f'after-of: {nid} is not what {n["after_of"]} leaves after its spin')
    for n in nodes:
        nid = n.get('id', '?')
        base = n.get('base')
        if 'rows' not in n or base not in boards or n.get('node_kind') in spec.board_kinds:
            continue
        if n.get('bag') == 2:
            # every bag-2 board contains its bag-1 base, reading a prior-bag letter as a bag-1 cell
            h = max(ROWS, len(n['rows']))
            mine = bottom(n['rows'], h)
            theirs = bottom(boards[base], h)
            old = cells(mine, lambda ch: ch == 'c' or ch in spec.prior_letters)
            if old != cells(theirs, lambda ch: ch != EMPTY):
                bad.append(f'bag2-base: {nid} c/{spec.prior_letters} cells are not exactly '
                           f'{base}\'s cells')
            for up in spec.prior_letters:
                if not cells(mine, lambda ch: ch == up) <= cells(theirs, lambda ch: ch == up.lower()):
                    bad.append(f'bag2-base: {nid} draws {up} where {base} has no bag-1 {up.lower()}')
            continue
        if n.get('continues'):
            # the same board built on, then a T into the base's own slot in its bottom
            # `cleared_below` rows clears them: those rows' empty cells are one T, and what is left
            # of the base is still there, cell for cell, under the pieces this node adds
            cut = n['continues'].get('cleared_below', 0)
            src = bottom(boards[base], 0)
            if cut:
                gap = [(x, cut - 1 - y) for y, r in enumerate(src[len(src) - cut:]) for x, ch in enumerate(r)
                       if ch == EMPTY]
                if len(gap) != 4 or _norm(gap) not in _shapes('t'):
                    bad.append(f'continues: {base}\'s bottom {cut} rows do not leave a T slot to clear')
                src = src[:len(src) - cut]
            h = max(len(src), len(bottom(n['rows'], 0)))
            mine, theirs = bottom(n['rows'], h), bottom(src, h)
            if any(t != EMPTY and m != t for rm, rt in zip(mine, theirs) for m, t in zip(rm, rt)):
                bad.append(f'continues: {nid} does not contain {base}')
            added = sum(1 for rm, rt in zip(mine, theirs) for m, t in zip(rm, rt)
                        if t == EMPTY and m != EMPTY)
            if added == 0 or added % 4:
                bad.append(f'continues: {nid} adds {added} cells to {base}, not whole pieces')
            continue
        after, cleared, _ = post_spin(base)
        if cleared == 0:
            bad.append(f'c-cells: {base} clears no row when its T goes in')
        h = max(len(after), len(n['rows']))
        if cells(bottom(n['rows'], h), lambda ch: ch == 'c') != cells(
                bottom(after, h), lambda ch: ch != EMPTY):
            bad.append(f'c-cells: {nid} c cells are not what {base} leaves after its spin')
        placed = cells(n['rows'], lambda ch: ch not in (EMPTY, 'c') and ch not in spec.placeholders)
        if not any(ph in ''.join(n['rows']) for ph in spec.placeholders) and len(placed) % 4:
            bad.append(f'c-cells: {nid} places {len(placed)} cells, not whole pieces')
        if 'list' in n:
            body = bottom(n['rows'], 0)
            if any(EMPTY in r for r in body) or len(body) + cleared != spec.pc_lines:
                bad.append(f'pc: {nid} is not an {spec.pc_lines}-line perfect clear over {base}')
    for b in data.get('basic_form', []):
        tgt = boards.get(b['same_as'])
        if tgt is None or not recolour_equal(b['rows'], tgt, b.get('recolour', {})):
            bad.append(f'basic-form: {b["id"]} is not the board of {b["same_as"]}')

    # ── rule 4: distinctness, derived here and never typed ──
    bag2 = [n for n in nodes if n.get('bag') == 2 and 'rows' in n and 'node_kind' not in n]
    for i, a in enumerate(bag2):
        for b in bag2[i + 1:]:
            ra, rb = bottom(a['rows'], ROWS), bottom(b['rows'], ROWS)
            if a.get('group') is not None and a.get('group') == b.get('group'):
                # siblings of one group may share occupancy; colour must tell them apart
                if ra == rb or ra == mirror(rb):
                    bad.append(f'distinct: bag-2 boards {a["id"]} and {b["id"]} are equal by colour')
                continue
            ga, gb = occ(ra), occ(rb)
            if ga == gb or ga == occ(mirror(rb)):
                bad.append(f'distinct: bag-2 boards {a["id"]} and {b["id"]} are equal')
    pats = [n for n in nodes if 'list' in n]
    seen: dict[tuple, str] = {}
    for n in pats:
        g = tuple(bottom(n['rows'], ROWS))
        for key in (g, tuple(mirror(list(g)))):
            other = seen.get((n['parent'],) + key)
            if other:
                bad.append(f'distinct: duplicate pattern {n["id"]} equals {other} by colour')
        seen[(n['parent'],) + g] = n['id']
    classes: dict[tuple, list[str]] = {}
    for n in pats:
        classes.setdefault(tuple(occ([r.replace('U', EMPTY) for r in n['rows']])), []).append(
            n['parent'])
    largest = max(classes.values(), key=len) if classes else []
    if not classes or max(len(v) for v in classes.values()) < 2 or (
            len(set(largest)) < spec.occupancy_class_parents):
        bad.append('occupancy-classes: bag-3 patterns became distinct by occupancy, so the shape '
                   'that forces a colour comparison no longer holds')

    # ── rule 5: known source discrepancies ──
    found = set()
    for lst in data.get('lists', []):
        n_drawn = sum(1 for n in pats if n['list'] == lst['id'])
        n_rest = sum(1 for n in pats if n['list'] == lst['id'] and n['listed_under'] == 'rest')
        if n_drawn != lst.get('drawn') or n_rest != lst.get('rest_stated') or (
                n_drawn - n_rest != lst.get('shown')):
            bad.append(f'list-count: {lst["id"]} draws {n_drawn} ({n_rest} under 残り), its '
                       f'record says {lst.get("drawn")} ({lst.get("rest_stated")})')
        if lst.get('stated_pattern_count') is not None and lst['stated_pattern_count'] != n_drawn:
            found.add(f'{lst["id"]}:stated_vs_drawn')
        if not lst.get('complete'):
            found.add(f'{lst["id"]}:non_exhaustive')
    # ── rule 7: piece decomposition. Every letter is whole pieces of that letter, in the kept-rows
    # frame; a drawing that colours a piece in another piece's colour is a source discrepancy ──
    for n in nodes:
        if 'rows' in n and not any(ph in ''.join(n['rows']) for ph in spec.placeholders) and \
                piece_groups_ok(n['rows'], spec.upper_groups):
            found.add(f'{n["id"]}:colour')
    for b in data.get('basic_form', []):
        if piece_groups_ok(b['rows'], spec.upper_groups):
            found.add(f'{b["id"]}:colour')
    if spec.extra_checks:
        more, measured = spec.extra_checks(data, {'by_id': by_id, 'boards': boards, 'groups': groups})
        bad += more
        found |= measured
    named = {d['id'] for d in data.get('known_discrepancies', [])}
    for d in sorted(found - named):
        bad.append(f'discrepancy: {d} is not on the named list — read the page, then name it')
    for d in sorted(named - found):
        bad.append(f'discrepancy: {d} is named but no longer measured')
    return bad


def drift(data: dict, spec: TranscriptionSpec) -> list[str]:
    return [] if data == spec.build() else [f'drift: {spec.out.name} differs from SPEC — rerun --write']


# ── the page snapshot (offline re-check after a refetch) ─────────────────────────────────────────
BOARD_ROW = re.compile(r'^[-a-zA-Z]{10}$')


def page_boards(md: str) -> list[list[str]]:
    """Every board in a markdown snapshot, in page order: runs of 10-wide board rows."""
    out, cur = [], []
    for line in md.split('\n'):
        s = line.replace('\\-', '-').rstrip()
        if BOARD_ROW.match(s):
            cur.append(s)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def check_snapshot(data: dict, html_dir: Path) -> list[str]:
    p = html_dir / data['source']['snapshot_file']
    raw = p.read_bytes()
    bad = []
    sha = hashlib.sha256(raw).hexdigest()
    if sha != data['source']['snapshot_sha256']:
        bad.append(f'snapshot: sha256 {sha} is not the recorded one (read the board diff below)')
    rows = {n['id']: n['rows'] for n in data['nodes'] if 'rows' in n}
    rows.update({b['id']: b['rows'] for b in data['basic_form']})
    text = raw.decode('utf8')
    for n in data['nodes']:
        if 'page_text' in n and n['page_text'] not in text:
            bad.append(f'snapshot: {n["id"]}\'s page_text {n["page_text"]!r} is not on the page')
    # a markdown link is rendered as ` [text](url) ` where the page has `text` run into its sentence
    plain = re.sub(r'\s*\[([^\]]*)\]\([^)]*\)\s*', r'\1', text)
    for q in data.get('quotes', []):
        if q.get('rendered', True) and q['verbatim'] not in text and q['verbatim'] not in plain:
            bad.append(f'snapshot: quote {q["id"]} is not verbatim on the page')
    want = [rows[i] for i in data['page_order']]
    got = page_boards(text)
    if got != want:
        bad.append(f'snapshot: the page draws {len(got)} boards, page_order has {len(want)}')
        for k, (a, b) in enumerate(zip(got, want)):
            if a != b:
                bad.append(f'snapshot: board {k + 1} ({data["page_order"][k]}) differs: '
                           f'page {a} vs transcription {b}')
                break
    return bad


def synthetic_snapshot(base: dict) -> str:
    """A markdown snapshot rebuilt from the transcription, the way the fetch renders one."""
    rows = {n['id']: n['rows'] for n in base['nodes'] if 'rows' in n}
    rows.update({b['id']: b['rows'] for b in base['basic_form']})
    md = '\n\n'.join('\n'.join(('\\' + r) if r.startswith('-') else r for r in rows[i])
                     for i in base['page_order']) + '\n'
    md += '\n'.join(n['page_text'] for n in base['nodes'] if 'page_text' in n) + '\n'
    md += '\n'.join(q['verbatim'] for q in base.get('quotes', []) if q.get('rendered', True)) + '\n'
    return md


# ── selftest ───────────────────────────────────────────────────────────────────────────────────
def node(d: dict, nid: str) -> dict:
    return next(n for n in d['nodes'] if n['id'] == nid)


def setcell(rows: list[str], r: int, c: int, ch: str) -> None:
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def run_selftest(spec: TranscriptionSpec, mutants: list, snapshot_edits: dict,
                 spec_mutants: list = ()) -> int:
    """A gate nothing can fail is decorative. Plant one defect per rule, require its own message.
    `mutants` is [(fn(d), label, tag)]; `spec_mutants` is [(fn(spec) -> spec, label, tag)], a defect
    in the opener's half of the gate rather than in its data; `snapshot_edits` names a board row to
    blank and a page_text fragment to change ({'board': (old, new), 'text': (old, new), 'hand_edit':
    node id}, plus optionally 'quote': a quote id whose committed verbatim is edited)."""
    base = spec.build()
    if verify(base, spec) or drift(json.loads(spec.out.read_text()), spec):
        print('selftest: the committed file does not verify — fix that first', file=sys.stderr)
        return 1
    ok = True
    for fn, label, tag in mutants:
        d = copy.deepcopy(base)
        fn(d)
        problems = verify(d, spec)
        if not any(p.startswith(tag) for p in problems):
            print(f'selftest FAILED: {label} was not caught by {tag!r} (got {problems[:3]})',
                  file=sys.stderr)
            ok = False
        else:
            print(f'  killed: {label}  [{tag}]')
    for fn, label, tag in spec_mutants:
        problems = verify(copy.deepcopy(base), fn(spec))
        if not any(p.startswith(tag) for p in problems):
            print(f'selftest FAILED: {label} was not caught by {tag!r} (got {problems[:3]})',
                  file=sys.stderr)
            ok = False
        else:
            print(f'  killed: {label}  [{tag}]')
    # the drift gate itself
    d = copy.deepcopy(base)
    node(d, snapshot_edits['hand_edit'])['label'] = 'edited by hand'
    if drift(d, spec):
        print('  killed: a hand edit to the committed JSON  [drift:]')
    else:
        print('selftest FAILED: a hand edit was not caught by drift', file=sys.stderr)
        ok = False
    # the snapshot locator: one row changed in a synthetic snapshot
    import tempfile
    md = synthetic_snapshot(base)
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / base['source']['snapshot_file']
        p.write_text(md)
        clean = [x for x in check_snapshot(base, Path(td)) if not x.startswith('snapshot: sha256')]
        p.write_text(md.replace(*snapshot_edits['board'], 1))
        dirty = check_snapshot(base, Path(td))
        p.write_text(md.replace(*snapshot_edits['text']))
        lost = check_snapshot(base, Path(td))
        p.write_text(md)
        quoted = None
        if snapshot_edits.get('quote'):
            d = copy.deepcopy(base)
            q = next(x for x in d['quotes'] if x['id'] == snapshot_edits['quote'])
            q['verbatim'] = q['verbatim'][:-1] + '!'
            quoted = check_snapshot(d, Path(td))
    if clean or not any('differs' in x for x in dirty):
        print(f'selftest FAILED: snapshot locator (clean={clean}, dirty={dirty[:2]})',
              file=sys.stderr)
        ok = False
    else:
        print('  killed: a redrawn board in the page snapshot  [snapshot:]')
    if not any("page_text" in x for x in lost):
        print('selftest FAILED: a non-board feature gone from the snapshot was not caught',
              file=sys.stderr)
        ok = False
    else:
        print('  killed: a non-board feature gone from the page snapshot  [snapshot:]')
    if quoted is not None:
        if any('not verbatim' in x for x in quoted):
            print('  killed: a quote edited away from the page\'s words  [snapshot:]')
        else:
            print('selftest FAILED: an edited quote was not caught by the snapshot check', file=sys.stderr)
            ok = False
    print('selftest: all mutants killed' if ok else 'selftest: FAILED')
    return 0 if ok else 1


def main(spec: TranscriptionSpec, selftest: Callable[[], int], doc: str | None) -> int:
    snap = spec.out.name.replace('-routes.json', '.md')
    ap = argparse.ArgumentParser(description=(doc or '').split('\n')[0])
    ap.add_argument('--html-dir', type=Path,
                    help=f'directory holding the markdown snapshot ({snap}) of a refetch')
    ap.add_argument('--write', action='store_true', help=f'rewrite {spec.out.name} from SPEC')
    ap.add_argument('--selftest', action='store_true', help='prove the verifier has teeth')
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    data = spec.build()
    problems = verify(data, spec)
    if args.html_dir:
        problems += check_snapshot(data, args.html_dir)
    if args.write and not problems:
        spec.out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(f'wrote {spec.out.relative_to(HERE.parent.parent)}')
    if not args.write:
        problems += drift(json.loads(spec.out.read_text()), spec)

    nodes = data['nodes']
    n_boards = sum(1 for n in nodes if 'rows' in n)
    kinds: dict[str, int] = {}
    for n in nodes:
        if 'node_kind' in n:
            kinds[n['node_kind']] = kinds.get(n['node_kind'], 0) + 1
    print(f'  {len(nodes)} nodes: {n_boards} with a board, '
          + ', '.join(f'{v} {k}' for k, v in sorted(kinds.items()))
          + f'; {sum(1 for n in nodes if "unmatchable" in n)} unmatchable')
    print(f'  {len(data["page_order"])} boards in page order '
          f'(+{sum(1 for n in nodes if n.get("derived") or n.get("drawn_as"))} derived)')
    for lst in data['lists']:
        print(f'  {lst["id"]:16s} drawn {lst["drawn"]:2d} (shown {lst["shown"]}, rest '
              f'{lst["rest_stated"]}), stated {lst["stated_pattern_count"]}')
    classes: dict[tuple, int] = {}
    for n in nodes:
        if 'list' in n:
            k = tuple(occ([r.replace('U', EMPTY) for r in n['rows']]))
            classes[k] = classes.get(k, 0) + 1
    print(f'  bag-3 occupancy classes (raw rows, U empty): '
          f'{sorted(classes.values(), reverse=True)} — colour decides, occupancy cannot')
    if problems:
        for p in problems:
            print(f'FAIL {p}', file=sys.stderr)
        return 1
    print(f'{spec.out.name} OK')
    return 0
