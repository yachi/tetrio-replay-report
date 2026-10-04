#!/usr/bin/env python3
"""Independent verifier, batch 2: clips 6, 7, 8 of clips-chosen.json.
Rebuilds every frame of both sides from raw sources only and compares to the artefact."""
import json, math, os, sys

D = os.path.dirname(os.path.abspath(__file__))
CLIPS = [6, 7, 8]
W, H = 10, 40
STRICT = os.environ.get('CC_STRICT_NEXT') == '1'

SHAPES = {
    'I': [(0, 0), (1, 0), (2, 0), (3, 0)],
    'O': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'T': [(1, 0), (0, 1), (1, 1), (2, 1)],
    'S': [(1, 0), (2, 0), (0, 1), (1, 1)],
    'Z': [(0, 0), (1, 0), (1, 1), (2, 1)],
    'J': [(0, 0), (0, 1), (1, 1), (2, 1)],
    'L': [(2, 0), (0, 1), (1, 1), (2, 1)],
}

def norm(cells):
    mx = min(c for c, r in cells); my = min(r for c, r in cells)
    return frozenset((c - mx, r - my) for c, r in cells)

ROTS = {}
for k, base in SHAPES.items():
    s = set(); cur = base
    for _ in range(4):
        s.add(norm(cur)); cur = [(-r, c) for c, r in cur]
    ROTS[k] = s

def shape_of(cells):
    n = norm([tuple(x) for x in cells])
    return [k for k, v in ROTS.items() if n in v]

# ---- TETR.IO attack (own implementation of damageCalc garbageCalcV2) ----
BASE = {(0, None): 0, (0, 'mini'): 0, (0, 'normal'): 0,
        (1, None): 0, (1, 'mini'): 0, (1, 'normal'): 2,
        (2, None): 1, (2, 'mini'): 1, (2, 'normal'): 4,
        (3, None): 2, (3, 'mini'): 2, (3, 'normal'): 6}

def calc(lines, spin, b2b, combo):
    sp = None if spin in (None, 'none') else spin
    if lines <= 3: g = BASE[(lines, sp)]
    elif lines == 4: g = 10 if sp else 4
    elif lines == 5: g = 12 if sp else 5
    else: g = (12 + 2 * (lines - 5)) if sp else (5 + lines - 5)
    if lines > 0 and b2b > 0:
        l = math.log1p(b2b * 0.8)
        g += math.floor(1 + l) + (0 if b2b == 1 else (1 + (l % 1)) / 3)
    if combo > 0:
        g *= 1 + 0.25 * combo
        if combo > 1:
            g = max(math.log1p(combo * 1.25), g)
    return g

class Counters:
    def __init__(s, b2b, combo): s.b2b, s.combo = b2b, combo
    def lock(s, lines, spin, pc):
        if lines > 0:
            s.combo += 1
            if (spin not in (None, 'none')) or lines >= 4: s.b2b += 1
            else: s.b2b = -1
        else:
            s.combo = -1
        g = calc(lines, spin, max(s.b2b, 0), max(s.combo, 0))
        att = math.floor(g)  # round DOWN, gmult 1
        if pc: att += 10
        return att

# ---- board ops ----
def place(board, cells, ch):
    b = [list(r) for r in board]
    for c, r in cells: b[r][c] = ch
    return b

def clear(b):
    full = [i for i, row in enumerate(b) if all(x != '.' for x in row)]
    rest = [row for i, row in enumerate(b) if i not in full]
    return [['.'] * W for _ in full] + rest, full

def add_garbage(b, amount, col):
    out = b[amount:] + [['G' if c != col else '.' for c in range(W)] for _ in range(amount)]
    lost = [row for row in b[:amount] if any(x != '.' for x in row)]
    return out, lost

def S(b): return [''.join(r) for r in b]

def occ(rows):  # filled mask, letters collapsed
    return [''.join('.' if ch == '.' else '#' for ch in r) for r in rows]

def check_place(tag, before, cells, piece, mm):
    sh = shape_of(cells)
    if len(cells) != 4 or piece not in sh:
        mm.append(f"{tag}: cells {cells} do not form a {piece} (shape matches {sh})")
    for c, r in cells:
        if not (0 <= c < W and 0 <= r < H):
            mm.append(f"{tag}: cell {(c, r)} out of bounds"); return
        if before[r][c] != '.':
            mm.append(f"{tag}: cell {(c, r)} occupied on before board ('{before[r][c]}')")
    cs = set(map(tuple, cells))
    sup = any(r == H - 1 or ((c, r + 1) not in cs and before[r + 1][c] != '.') for c, r in cells)
    if not sup:
        mm.append(f"{tag}: piece floating (no cell on floor or above a filled cell)")

def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y: return f"row {i}: '{x}' vs '{y}'"
    return f"len {len(a)} vs {len(b)}"

def main():
    chosen = json.load(open(os.path.join(D, 'clips-chosen.json')))
    clips_in = {}
    for l in open(os.path.join(D, 'clips-in.jsonl')):
        x = json.loads(l); clips_in[x['id']] = x
    pos = {}
    for l in open(os.path.join(D, '..', 'positions.jsonl')):
        x = json.loads(l); pos[x['id']] = x
    results = []
    for ci in CLIPS:
        clip = chosen[ci]; cid = clip['id']; seed = clip['seed']
        mm = []; checks = set(); frames = 0
        src = clips_in[cid]
        st = clip['start']
        for k in ('field', 'current', 'hold', 'next', 'b2b', 'combo'):
            if st[k] != src[k]: mm.append(f"clip {ci} start.{k} differs from clips-in")
        if clip.get('future') != src['future']: mm.append(f"clip {ci} future differs from clips-in")
        checks.add('start state (field/current/hold/next/b2b/combo/future) == clips-in.jsonl')
        prefix, lock0 = cid.rsplit('/', 1); lock0 = int(lock0)

        # ================= HUMAN =================
        board = [list(r) for r in src['field']]
        ctr = Counters(src['b2b'], src['combo'])
        human_att = 0
        for j, a in enumerate(clip['human']):
            tag = f"clip {ci} human step {j}"
            p = pos.get(f"{prefix}/{lock0 + j}")
            if p is None: mm.append(f"{tag}: position {prefix}/{lock0+j} missing"); break
            pl = p['played']
            if S(board) != p['field']:
                mm.append(f"{tag}: my rebuilt board != positions.jsonl field ({first_diff(S(board), p['field'])})")
            if a['before'] != p['field']:
                mm.append(f"{tag}: artefact before != positions field ({first_diff(a['before'], p['field'])})")
            if a['piece'] != pl['piece']: mm.append(f"{tag}: piece {a['piece']} vs raw {pl['piece']}")
            if [list(x) for x in a['cells']] != [list(x) for x in pl['cells']]:
                mm.append(f"{tag}: cells {a['cells']} vs raw {pl['cells']}")
            # hold usage
            cur, hold, nxt = p['current'], p['hold'], p['next']
            alt = hold if hold else (nxt[0] if nxt else None)
            used_hold = pl['piece'] != cur
            if pl['piece'] != cur and pl['piece'] != alt:
                mm.append(f"{tag}: placed {pl['piece']} not current {cur} nor hold/next0 {alt}")
            if cur == alt: used_hold = a['hold']  # ambiguous, accept either
            if a['hold'] != used_hold: mm.append(f"{tag}: artefact hold flag {a['hold']} but derived {used_hold}")
            for k, v in (('current', cur), ('holdPiece', hold), ('next', nxt)):
                if k in a and a[k] != v: mm.append(f"{tag}: artefact {k}={a[k]} vs positions {v}")
            check_place(tag, board, pl['cells'], pl['piece'], mm)
            b = place(board, pl['cells'], pl['piece'])
            b, full = clear(b)
            pc = all(all(x == '.' for x in r) for r in b)
            if len(full) != pl['lines']: mm.append(f"{tag}: full rows {len(full)} vs raw lines {pl['lines']}")
            if a['lines'] != len(full): mm.append(f"{tag}: artefact lines {a['lines']} vs derived {len(full)}")
            if a['spin'] != pl['spin']: mm.append(f"{tag}: artefact spin {a['spin']} vs raw {pl['spin']}")
            att = ctr.lock(len(full), pl['spin'], pc)
            if att != pl['raw']: mm.append(f"{tag}: derived attack {att} vs played.raw {pl['raw']}")
            if a['attack'] != att: mm.append(f"{tag}: artefact attack {a['attack']} vs derived {att}")
            if a['b2b'] != ctr.b2b or a['combo'] != ctr.combo:
                mm.append(f"{tag}: artefact b2b/combo {a['b2b']}/{a['combo']} vs derived {ctr.b2b}/{ctr.combo}")
            human_att += att
            g = 0
            for t in pl['tanks']:
                b, lost = add_garbage(b, t['amount'], t['column']); g += t['amount']
                if lost: mm.append(f"{tag}: garbage pushed stack above row 0")
            if a['garbage'] != g: mm.append(f"{tag}: artefact garbage {a['garbage']} vs tanks {g}")
            if src['garbage_schedule'][j] and [(t['amount'], t['column']) for t in src['garbage_schedule'][j]] != [(t['amount'], t['column']) for t in pl['tanks']]:
                mm.append(f"{tag}: garbage_schedule[{j}] differs from played.tanks")
            if not src['garbage_schedule'][j] and pl['tanks']:
                mm.append(f"{tag}: garbage_schedule[{j}] empty but played.tanks {pl['tanks']}")
            if a['after'] != S(b): mm.append(f"{tag}: artefact after != derived ({first_diff(a['after'], S(b))})")
            if j + 1 < len(clip['human']) and a['after'] != clip['human'][j + 1]['before']:
                mm.append(f"{tag}: after != next step's before")
            nxtp = pos.get(f"{prefix}/{lock0 + j + 1}")
            if nxtp is not None:
                if S(b) != nxtp['field']:
                    mm.append(f"{tag}: derived after != positions field of lock {lock0+j+1} ({first_diff(S(b), nxtp['field'])})")
                if (nxtp['b2b'], nxtp['combo']) != (ctr.b2b, ctr.combo):
                    mm.append(f"{tag}: tracked b2b/combo {ctr.b2b}/{ctr.combo} vs next position {nxtp['b2b']}/{nxtp['combo']}")
            elif j + 1 < len(clip['human']) or True:
                checks.add(f'(clip {ci}: no position after the last human step; final after checked only by derivation)')
            board = b; frames += 1
        if clip['totals']['human'] != human_att:
            mm.append(f"clip {ci} human total {clip['totals']['human']} vs derived {human_att}")

        # ================= COLD CLEAR =================
        ro = None
        for l in open(os.path.join(D, f'clips-cc-s{seed}.jsonl')):
            x = json.loads(l)
            if x['id'] == cid: ro = x; break
        if ro is None: mm.append(f"clip {ci}: no rollout in clips-cc-s{seed}.jsonl"); results.append((ci, frames, mm, checks)); continue
        if len(ro['steps']) != len(clip['cc']): mm.append(f"clip {ci} cc: {len(ro['steps'])} rollout steps vs {len(clip['cc'])} artefact")
        board = [list(r) for r in src['field']]
        ctr = Counters(src['b2b'], src['combo'])
        cur, hold = src['current'], src['hold']
        queue = list(src['next']) + list(src['future'])
        pending = []
        cc_att = 0
        for j, (r, a) in enumerate(zip(ro['steps'], clip['cc'])):
            tag = f"clip {ci} cc step {j}"
            if a['before'] != S(board): mm.append(f"{tag}: artefact before != derived ({first_diff(a['before'], S(board))})")
            piece = r['piece']
            if a['piece'] != piece: mm.append(f"{tag}: artefact piece {a['piece']} vs rollout {piece}")
            if [list(x) for x in a['cells']] != [list(x) for x in r['cells']]:
                mm.append(f"{tag}: cells {a['cells']} vs rollout {r['cells']}")
            if a['hold'] != r['hold']: mm.append(f"{tag}: artefact hold {a['hold']} vs rollout {r['hold']}")
            # queue
            if not r['hold']:
                if piece != cur: mm.append(f"{tag}: no-hold placement of {piece} but current is {cur}")
                cur = queue.pop(0)
            else:
                if hold is None:
                    if piece != queue[0]: mm.append(f"{tag}: hold (empty) placement of {piece} but next is {queue[0]}")
                    hold = cur; queue.pop(0); cur = queue.pop(0)
                else:
                    if piece != hold: mm.append(f"{tag}: hold placement of {piece} but hold is {hold} (current {cur})")
                    hold = cur; cur = queue.pop(0)
            check_place(tag, board, r['cells'], piece, mm)
            b = place(board, r['cells'], piece)
            b, full = clear(b)
            pc = all(all(x == '.' for x in row) for row in b)
            n = len(full)
            if n != r['lines']: mm.append(f"{tag}: full rows {n} vs rollout lines {r['lines']}")
            if a['lines'] != n: mm.append(f"{tag}: artefact lines {a['lines']} vs derived {n}")
            if bool(r['pc']) != pc: mm.append(f"{tag}: rollout pc {r['pc']} vs derived {pc}")
            spin = {'Full': 'normal', 'Mini': 'mini', 'None': 'none'}[r['tspin']]
            if spin != 'none' and piece != 'T': mm.append(f"{tag}: rollout spin on non-T {piece}")
            if a['spin'] != spin: mm.append(f"{tag}: artefact spin {a['spin']} vs rollout {spin}")
            att = ctr.lock(n, spin, pc)
            if a['attack'] != att: mm.append(f"{tag}: artefact attack {a['attack']} vs derived {att}")
            if a['b2b'] != ctr.b2b or a['combo'] != ctr.combo:
                mm.append(f"{tag}: artefact b2b/combo {a['b2b']}/{a['combo']} vs derived {ctr.b2b}/{ctr.combo}")
            cc_att += att
            g = 0
            # Rule as the raw rollout applies it: step j's received rows join pending as part of
            # resolving step j's lock, so a 0-line step-j lock inserts them immediately.
            # Set CC_STRICT_NEXT=1 for the strict reading (only a LATER 0-line lock inserts them).
            if not STRICT:
                for t in src['garbage_schedule'][j]: pending.append((t['amount'], t['column']))
            if n == 0 and pending:
                for amt, col in pending:
                    b, lost = add_garbage(b, amt, col); g += amt
                    if lost: mm.append(f"{tag}: garbage pushed stack above row 0 (topout)")
                pending = []
            if a['garbage'] != g: mm.append(f"{tag}: artefact garbage {a['garbage']} vs derived {g}")
            if r.get('garbage_in', 0) != g:
                mm.append(f"{tag}: rollout garbage_in {r.get('garbage_in')} vs derived insertion {g}")
            if STRICT:
                for t in src['garbage_schedule'][j]: pending.append((t['amount'], t['column']))
            if a['after'] != S(b): mm.append(f"{tag}: artefact after != derived ({first_diff(a['after'], S(b))})")
            if j + 1 < len(clip['cc']) and a['after'] != clip['cc'][j + 1]['before']:
                mm.append(f"{tag}: after != next step's before")
            board = b; frames += 1
        if occ(S(board)) != occ(ro['final_field']):
            mm.append(f"clip {ci} cc: derived final board != rollout final_field ({first_diff(occ(S(board)), occ(ro['final_field']))})")
        if pending: checks.add(f'(clip {ci}: {sum(a for a,_ in pending)} garbage rows still pending at clip end, never inserted)')
        if clip['totals']['cc'] != cc_att:
            mm.append(f"clip {ci} cc total {clip['totals']['cc']} vs derived {cc_att}")
        results.append((ci, frames, mm, checks))
    out = []
    for ci, frames, mm, checks in results:
        print(f"== clip {ci}: {frames} frames checked, {len(mm)} mismatches")
        for m in mm: print('  MISMATCH', m)
        for c in sorted(checks): print('  note', c)
        out.append({'clip': ci, 'framesChecked': frames, 'mismatches': mm, 'notes': sorted(checks)})
    json.dump(out, open(os.path.join(D, 'verify-batch-2.out.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
