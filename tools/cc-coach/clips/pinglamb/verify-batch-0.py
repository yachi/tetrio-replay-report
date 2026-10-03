#!/usr/bin/env python3
"""Independent verifier for clips 0,1,2 of clips-chosen.json. Written from scratch;
reads only raw sources (positions.jsonl, clips-in.jsonl, clips-cc-s<seed>.jsonl) and the artefact."""
import json, math, sys, os

D = os.path.dirname(os.path.abspath(__file__))
CLIPS = [int(a) for a in sys.argv[1:]] or [0, 1, 2]
W, H = 10, 40

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
    mx = min(c[0] for c in cells); my = min(c[1] for c in cells)
    return frozenset((x - mx, y - my) for x, y in cells)


ROTS = {}
for p, s in SHAPES.items():
    forms = set(); cur = s
    for _ in range(4):
        forms.add(norm(cur)); cur = [(-y, x) for x, y in cur]
    ROTS[p] = forms


def shape_of(cells):
    n = norm(cells)
    return [p for p, f in ROTS.items() if n in f]


def filled(ch):
    return ch != '.'


def b2s(b):
    return [''.join(r) for r in b]


def s2b(s):
    return [list(r) for r in s]


def canon(b):  # compare occupancy + letters exactly; also offer occupancy-only
    return [''.join(r) for r in b]


def occ(b):
    return [''.join('#' if filled(c) else '.' for c in r) for r in b]


def place(board, piece, cells, errs, tag):
    b = [r[:] for r in board]
    if len(cells) != 4:
        errs.append(f"{tag}: {len(cells)} cells")
    sh = shape_of(cells)
    if piece not in sh:
        errs.append(f"{tag}: cells {cells} form {sh} not {piece}")
    cs = set(map(tuple, cells))
    for c, r in cells:
        if not (0 <= c < W and 0 <= r < H):
            errs.append(f"{tag}: cell {(c, r)} out of bounds"); continue
        if filled(b[r][c]):
            errs.append(f"{tag}: cell {(c, r)} overlaps '{b[r][c]}'")
    sup = any(r == H - 1 or (r + 1 < H and (c, r + 1) not in cs and filled(board[r + 1][c])) for c, r in cells
              if 0 <= c < W and 0 <= r < H)
    if not sup:
        errs.append(f"{tag}: piece floats (unsupported) {cells}")
    for c, r in cells:
        if 0 <= c < W and 0 <= r < H:
            b[r][c] = piece
    full = [i for i in range(H) if all(filled(x) for x in b[i])]
    rest = [b[i] for i in range(H) if i not in full]
    nb = [['.'] * W for _ in full] + rest
    pc = all(not filled(x) for r in nb for x in r)
    return nb, len(full), pc


def add_garbage(b, amount, hole, errs, tag):
    for _ in range(amount):
        if any(filled(x) for x in b[0]):
            errs.append(f"{tag}: garbage pushes stack out of top")
        row = ['G'] * W; row[hole] = '.'
        b = b[1:] + [row]
    return b


def attack(lines, spin, b2b, combo, pc):
    s = None if spin == 'none' else spin
    if lines == 0: g = 0
    elif lines == 1: g = 0 if s == 'mini' else 2 if s == 'normal' else 0
    elif lines == 2: g = 1 if s == 'mini' else 4 if s == 'normal' else 1
    elif lines == 3: g = 2 if s == 'mini' else 6 if s == 'normal' else 2
    elif lines == 4: g = 10 if s else 4
    elif lines == 5: g = 12 if s else 5
    else: g = (12 + 2 * (lines - 5)) if s else 5 + (lines - 5)
    b = max(b2b, 0); c = max(combo, 0)
    if lines > 0 and b > 0:
        l = math.log1p(b * 0.8)
        g += 1 * (math.floor(1 + l) + (0 if b == 1 else (1 + l % 1) / 3))
    if c > 0:
        g *= 1 + 0.25 * c
        if c > 1:
            g = max(math.log1p(1 * c * 1.25), g)
    return math.floor(g) + (10 if pc else 0)


def counters(lines, spin, b2b, combo):
    if lines > 0:
        combo += 1
        if spin != 'none' or lines >= 4: b2b += 1
        else: b2b = -1
    else:
        combo = -1
    return b2b, combo


def main():
    art = json.load(open(os.path.join(D, 'clips-chosen.json')))
    pos = {}
    for l in open(os.path.join(D, '..', 'positions.jsonl')):
        x = json.loads(l); pos[x['id']] = x
    cin = [json.loads(l) for l in open(os.path.join(D, 'clips-in.jsonl'))]
    cin = {x['id']: x for x in cin}
    ccs = {}
    out = []
    for ci in CLIPS:
        A = art[ci]; mm = []; checks = set(); frames = 0
        cid = A['id']; seed = A['seed']
        if seed not in ccs:
            ccs[seed] = {json.loads(l)['id']: json.loads(l) for l in open(os.path.join(D, f'clips-cc-s{seed}.jsonl'))}
        CI = cin[cid]; CC = ccs[seed][cid]
        pre, rest = cid.split('/r'); rnd, user, lock0 = rest.split('/')
        lock0 = int(lock0)
        P0 = pos[cid]
        # start state agreement
        for k in ('field', 'current', 'hold', 'next', 'b2b', 'combo'):
            if A['start'][k] != P0[k]: mm.append(f"clip{ci} start.{k} != positions")
            if CI[k] != P0[k]: mm.append(f"clip{ci} clips-in.{k} != positions")
        if A.get('future') != CI['future']: mm.append(f"clip{ci} future differs from clips-in")
        checks.add('start state (field/current/hold/next/b2b/combo) equals positions.jsonl and clips-in.jsonl')

        # ---------------- HUMAN ----------------
        board = s2b(P0['field']); b2b, combo = P0['b2b'], P0['combo']; tot = 0
        n = len(A['human'])
        for j in range(n):
            tag = f"clip{ci} human step{j}"
            pid = f"{pre}/r{rnd}/{user}/{lock0 + j}"
            if pid not in pos: mm.append(f"{tag}: position {pid} missing"); break
            P = pos[pid]; pl = P['played']; S = A['human'][j]; frames += 1
            if b2s(board) != P['field']:
                mm.append(f"{tag}: my running board != positions field of {pid}")
            if S['before'] != P['field']:
                mm.append(f"{tag}: artefact before != positions field")
            if S['piece'] != pl['piece'] or sorted(map(tuple, S['cells'])) != sorted(map(tuple, pl['cells'])):
                mm.append(f"{tag}: artefact piece/cells {S['piece']} {S['cells']} != played {pl['piece']} {pl['cells']}")
            for k1,k2 in (('current','current'),('holdPiece','hold'),('next','next')):
                if k1 in S and S[k1] != P[k2]: mm.append(f"{tag}: artefact {k1} {S[k1]} != positions {k2} {P[k2]}")
            if S.get('verified') != P.get('verified'): mm.append(f"{tag}: verified flag {S.get('verified')} != positions {P.get('verified')}")
            # queue continuity: next position's current/hold follow from this one
            nid0 = f"{pre}/r{rnd}/{user}/{lock0 + j + 1}"
            if nid0 in pos:
                Q = pos[nid0]
                if pl['piece'] == P['current']: eh, ec, en = P['hold'], P['next'][0], P['next'][1:]
                elif P['hold']: eh, ec, en = P['current'], P['next'][0], P['next'][1:]
                else: eh, ec, en = P['current'], P['next'][1], P['next'][2:]
                if Q['current'] != ec or Q['hold'] != eh or Q['next'][:len(en)] != en:
                    mm.append(f"{tag}: queue continuity: expected cur {ec} hold {eh} next {en}, next position has {Q['current']} {Q['hold']} {Q['next']}")
            # hold availability
            alt = P['hold'] if P['hold'] else (P['next'][0] if P['next'] else None)
            usedhold = pl['piece'] != P['current']
            if pl['piece'] != P['current'] and pl['piece'] != alt:
                mm.append(f"{tag}: piece {pl['piece']} not current {P['current']} nor hold/next0 {alt}")
            if bool(S['hold']) != usedhold:
                mm.append(f"{tag}: artefact hold flag {S['hold']} but placed-vs-current says {usedhold}")
            board, lines, pc = place(board, pl['piece'], pl['cells'], mm, tag)
            if lines != pl['lines']: mm.append(f"{tag}: my lines {lines} != played.lines {pl['lines']}")
            if lines != S['lines']: mm.append(f"{tag}: my lines {lines} != artefact {S['lines']}")
            if S['spin'] != pl['spin']: mm.append(f"{tag}: artefact spin {S['spin']} != played {pl['spin']}")
            if pl['spin'] != 'none' and pl['piece'] != 'T': mm.append(f"{tag}: spin on non-T")
            b2b, combo = counters(lines, pl['spin'], b2b, combo)
            atk = attack(lines, pl['spin'], b2b, combo, pc) * (P.get('gmult') or 1)
            tot += atk
            if atk != S['attack']: mm.append(f"{tag}: my attack {atk} != artefact {S['attack']}")
            if atk != pl['raw']: mm.append(f"{tag}: my attack {atk} != played.raw {pl['raw']}")
            if (b2b, combo) != (S['b2b'], S['combo']):
                mm.append(f"{tag}: my b2b/combo {(b2b, combo)} != artefact {(S['b2b'], S['combo'])}")
            g = 0
            for t in pl['tanks']:
                board = add_garbage(board, t['amount'], t['column'], mm, tag); g += t['amount']
            if g != S['garbage']: mm.append(f"{tag}: tanks total {g} != artefact garbage {S['garbage']}")
            sched = CI['garbage_schedule'][j] if j < len(CI['garbage_schedule']) else None
            if sched is not None and [(t['amount'], t['column']) for t in sched] != [(t['amount'], t['column']) for t in pl['tanks']]:
                mm.append(f"{tag}: clips-in garbage_schedule[{j}] {sched} != played.tanks {pl['tanks']}")
            if S['after'] != b2s(board): mm.append(f"{tag}: artefact after != my rebuilt board")
            nid = f"{pre}/r{rnd}/{user}/{lock0 + j + 1}"
            if nid in pos:
                if pos[nid]['field'] != b2s(board): mm.append(f"{tag}: rebuilt after != positions field of {nid}")
                if (pos[nid]['b2b'], pos[nid]['combo']) != (b2b, combo):
                    mm.append(f"{tag}: my b2b/combo {(b2b, combo)} != next position {(pos[nid]['b2b'], pos[nid]['combo'])}")
            elif j < n - 1:
                mm.append(f"{tag}: next position {nid} missing")
            if j + 1 < n and A['human'][j + 1]['before'] != S['after']:
                mm.append(f"{tag}: after != before of step {j + 1}")
        if tot != A['totals']['human']: mm.append(f"clip{ci} human total {tot} != artefact {A['totals']['human']}")

        # ---------------- COLD CLEAR ----------------
        board = s2b(CI['field']); b2b, combo = CI['b2b'], CI['combo']; tot = 0
        cur, hold = CI['current'], CI['hold']; queue = list(CI['next']) + list(CI['future'])
        pending = []
        steps = CC['steps']
        if len(steps) != len(A['cc']): mm.append(f"clip{ci} cc: rollout has {len(steps)} steps, artefact {len(A['cc'])}")
        for j, (R, S) in enumerate(zip(steps, A['cc'])):
            tag = f"clip{ci} cc step{j}"; frames += 1
            if S['before'] != b2s(board): mm.append(f"{tag}: artefact before != my rebuilt board")
            if R['piece'] != S['piece'] or sorted(map(tuple, R['cells'])) != sorted(map(tuple, S['cells'])):
                mm.append(f"{tag}: artefact piece/cells != rollout")
            if bool(R['hold']) != bool(S['hold']): mm.append(f"{tag}: hold flag rollout {R['hold']} artefact {S['hold']}")
            if R['hold']:
                if hold is None:
                    hold = cur; cur = queue.pop(0)
                else:
                    hold, cur = cur, hold
            if R['piece'] != cur:
                mm.append(f"{tag}: CC places {R['piece']} but current={cur} hold={hold} (hold flag {R['hold']})")
            cur = queue.pop(0) if queue else None
            spin = {'Full': 'normal', 'Mini': 'mini', 'None': 'none'}[R['tspin']]
            if spin != S['spin']: mm.append(f"{tag}: spin rollout {spin} artefact {S['spin']}")
            board, lines, pc = place(board, R['piece'], R['cells'], mm, tag)
            if lines != R['lines']: mm.append(f"{tag}: my lines {lines} != rollout {R['lines']}")
            if lines != S['lines']: mm.append(f"{tag}: my lines {lines} != artefact {S['lines']}")
            if pc != bool(R['pc']): mm.append(f"{tag}: my pc {pc} != rollout pc {R['pc']}")
            b2b, combo = counters(lines, spin, b2b, combo)
            atk = attack(lines, spin, b2b, combo, pc); tot += atk
            if atk != S['attack']: mm.append(f"{tag}: my attack {atk} != artefact {S['attack']}")
            if (b2b, combo) != (S['b2b'], S['combo']):
                mm.append(f"{tag}: my b2b/combo {(b2b, combo)} != artefact {(S['b2b'], S['combo'])}")
            # garbage: step-j rows join pending after the lock; flushed on a 0-line lock
            # (rows join pending after the lock; that same lock flushes them if it cleared 0 lines --
            #  this is the ordering the rollout's own garbage_in records; the flush-on-a-LATER-lock
            #  reading was tried first and contradicts garbage_in and CC's own placements)
            ins = 0
            pending += [(t['amount'], t['column']) for t in CI['garbage_schedule'][j]]
            if lines == 0 and pending:
                for a, col in pending:
                    board = add_garbage(board, a, col, mm, tag); ins += a
                pending = []
            if ins != R['garbage_in']:
                mm.append(f"{tag}: inserted {ins} != rollout garbage_in {R['garbage_in']}")
            if ins != S['garbage']:
                mm.append(f"{tag}: inserted {ins} != artefact garbage {S['garbage']}")
            if S['after'] != b2s(board): mm.append(f"{tag}: artefact after != my rebuilt board")
            if j + 1 < len(A['cc']) and A['cc'][j + 1]['before'] != S['after']:
                mm.append(f"{tag}: after != before of step {j + 1}")
        if occ(board) != [r.replace('#', '#') for r in CC['final_field']]:
            mm.append(f"clip{ci} cc: rebuilt final board occupancy != rollout final_field")
        if tot != A['totals']['cc']: mm.append(f"clip{ci} cc total {tot} != artefact {A['totals']['cc']}")
        out.append({'clip': ci, 'framesChecked': frames, 'mismatches': mm, 'pending_left': pending})
    print(json.dumps(out, indent=1))


main()
