#!/usr/bin/env python3
"""Independent verifier for clips 9, 10, 11 of clips-chosen.json.
Rebuilds both sides from raw sources only (positions.jsonl, clips-in.jsonl,
clips-cc-s<seed>.jsonl). Written from scratch; no project builder code read."""
import json, math, sys, os
from collections import deque

D = os.path.dirname(os.path.abspath(__file__))
CLIPS = [9, 10, 11]
W, H = 10, 40

SHAPES = {  # rotation-0 cells (x, y) with y downwards
    'I': [(0, 1), (1, 1), (2, 1), (3, 1)],
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
for p, cs in SHAPES.items():
    s = set(); cur = cs
    for _ in range(4):
        s.add(norm(cur)); cur = [(-y, x) for x, y in cur]
    ROTS[p] = s

def shape_of(cells):
    n = norm(cells)
    return [p for p, rs in ROTS.items() if n in rs]

# ---------------- attack (own port of damageCalc garbageCalcV2) -------------
BASE = {(0, None): 0, (0, 'mini'): 0, (0, 'normal'): 0,
        (1, None): 0, (1, 'mini'): 0, (1, 'normal'): 2,
        (2, None): 1, (2, 'mini'): 1, (2, 'normal'): 4,
        (3, None): 2, (3, 'mini'): 2, (3, 'normal'): 6}

def garbage_calc(lines, spin, b2b, combo):
    spin = None if spin == 'none' else spin
    if lines <= 3: g = BASE[(lines, spin)]
    elif lines == 4: g = 10 if spin else 4
    elif lines == 5: g = 12 if spin else 5
    else: g = (12 + 2 * (lines - 5)) if spin else (5 + lines - 5)
    if lines > 0 and b2b > 0:
        l = math.log1p(b2b * 0.8)
        g += 1 * (math.floor(1 + l) + (0 if b2b == 1 else (1 + (l % 1)) / 3))
    if combo > 0:
        g *= 1 + 0.25 * combo
        if combo > 1:
            g = max(math.log1p(1 * combo * 1.25), g)
    return g

class Stats:
    def __init__(s, b2b, combo): s.b2b, s.combo = b2b, combo
    def lock(s, lines, spin, pc, gmult=1):
        if lines > 0:
            s.combo += 1
            if spin != 'none' or lines >= 4: s.b2b += 1
            else: s.b2b = -1
        else:
            s.combo = -1
        g = garbage_calc(lines, spin, max(s.b2b, 0), max(s.combo, 0))
        atk = math.floor(g * gmult) if g > 0 else 0
        if pc: atk += 10
        return atk

# ---------------- board ops --------------------------------------------------
def grid(rows): return [list(r) for r in rows]
def rows_of(g): return [''.join(r) for r in g]

def place(rows, cells, letter, tag):
    errs = []
    g = grid(rows)
    for x, y in cells:
        if not (0 <= x < W and 0 <= y < H):
            errs.append(f'{tag}: cell {(x, y)} out of bounds'); continue
        if g[y][x] != '.':
            errs.append(f'{tag}: cell {(x, y)} not empty on before board ({g[y][x]!r})')
    cs = set(map(tuple, cells))
    sup = any(y == H - 1 or (0 <= y + 1 < H and (x, y + 1) not in cs and g[y + 1][x] != '.') for x, y in cells)
    if not sup: errs.append(f'{tag}: piece floating (no cell on floor or above filled)')
    for x, y in cells:
        if 0 <= x < W and 0 <= y < H: g[y][x] = letter
    full = [y for y in range(H) if all(c != '.' for c in g[y])]
    keep = [g[y] for y in range(H) if y not in full]
    g = [['.'] * W for _ in full] + keep
    pc = all(c == '.' for r in g for c in r)
    return g, len(full), pc, errs

def add_garbage(g, amount, col, tag):
    errs = []
    for _ in range(amount):
        top = g.pop(0)
        if any(c != '.' for c in top): errs.append(f'{tag}: garbage pushed filled row off top')
        g.append(['G' if x != col else '.' for x in range(W)])
    return g, errs

def eqboard(a, b, filled_only=False):
    if filled_only:
        a = [''.join('#' if c != '.' else '.' for c in r) for r in a]
        b = [''.join('#' if c != '.' else '.' for c in r) for r in b]
    return list(a) == list(b)

def diffrows(a, b):
    return [(i, a[i], b[i]) for i in range(min(len(a), len(b))) if a[i] != b[i]][:6]

# ---------------- load ------------------------------------------------------
chosen = json.load(open(os.environ.get('CHOSEN', os.path.join(D, 'clips-chosen.json'))))
clips_in = {}
for l in open(os.path.join(D, 'clips-in.jsonl')):
    d = json.loads(l); clips_in[d['id']] = d
pos = {}
for l in open(os.path.join(D, '..', 'positions.jsonl')):
    d = json.loads(l); pos[d['id']] = d

def pid(cid, k):
    a, b, c, lock = cid.split('/')
    return f'{a}/{b}/{c}/{int(lock) + k}'

results = []
for ci in CLIPS:
    clip = chosen[ci]
    cid = clip['id']; seed = clip['seed']
    mism, checks = [], []
    cin = clips_in[cid]
    p0 = pos[cid]
    if p0['field'] != cin['field']: mism.append('start: clips-in field != positions field')
    if clip['start']['field'] != p0['field']: mism.append('artefact start.field != positions field')
    for k in ('current', 'hold', 'next', 'b2b', 'combo'):
        if clip['start'][k] != p0[k]: mism.append(f'artefact start.{k} {clip["start"][k]} != positions {p0[k]}')
    if clip['future'] != cin['future']: mism.append('artefact future != clips-in future')
    K = cin['k']
    sched = cin['garbage_schedule']
    frames = 0

    # ---------------- HUMAN ----------------
    hs = clip['human']
    if len(hs) != K: mism.append(f'human: {len(hs)} steps, expected {K}')
    st = Stats(p0['b2b'], p0['combo'])
    board = list(p0['field'])
    htotal = 0
    for j in range(K):
        tag = f'clip{ci} human step{j}'
        p = pos.get(pid(cid, j))
        if p is None: mism.append(f'{tag}: positions id {pid(cid, j)} missing'); break
        if p['field'] != board: mism.append(f'{tag}: positions field != rebuilt board; rows {diffrows(p["field"], board)}')
        pl = p['played']; a = hs[j] if j < len(hs) else None
        piece = pl['piece']
        # 8: hold usage
        hp = p['hold'] or (p['next'][0] if p['next'] else None)
        if piece != p['current'] and piece != hp:
            mism.append(f'{tag}: piece {piece} not current {p["current"]} nor hold/next {hp}')
        used_hold = piece != p['current']
        # 1
        if piece not in shape_of(pl['cells']): mism.append(f'{tag}: cells {pl["cells"]} are not a {piece} (match {shape_of(pl["cells"])})')
        g, lines, pc, errs = place(board, pl['cells'], piece, tag)
        mism += errs
        if lines != pl['lines']: mism.append(f'{tag}: rebuilt lines {lines} != played.lines {pl["lines"]}')
        atk = st.lock(lines, pl['spin'], pc, p.get('gmult', 1))
        htotal += atk
        if atk != pl['raw']: mism.append(f'{tag}: my attack {atk} != played.raw {pl["raw"]}')
        # tanks vs schedule
        if [ (t['amount'], t['column']) for t in pl['tanks']] != [(t['amount'], t['column']) for t in sched[j]]:
            mism.append(f'{tag}: played.tanks {pl["tanks"]} != garbage_schedule[{j}] {sched[j]}')
        gin = 0
        for t in pl['tanks']:
            g, e = add_garbage(g, t['amount'], t['column'], tag); mism += e; gin += t['amount']
        after = rows_of(g)
        if a is not None:
            if a['before'] != board: mism.append(f'{tag}: artefact before != rebuilt; {diffrows(a["before"], board)}')
            if a['after'] != after: mism.append(f'{tag}: artefact after != rebuilt; {diffrows(a["after"], after)}')
            exp = dict(piece=piece, hold=used_hold, cells=pl['cells'], lines=lines, spin=pl['spin'], attack=atk,
                       b2b=st.b2b, combo=st.combo, garbage=gin, current=p['current'], holdPiece=p['hold'], next=p['next'])
            for k, v in exp.items():
                if a.get(k) != v: mism.append(f'{tag}: artefact {k}={a.get(k)!r}, rebuilt {v!r}')
            if j + 1 < len(hs) and hs[j + 1]['before'] != a['after']: mism.append(f'{tag}: after != next before')
        board = after; frames += 1
    pn = pos.get(pid(cid, K))
    if pn is None: mism.append(f'clip{ci} human: positions {pid(cid, K)} (after last step) missing, final board unchecked vs replay')
    elif pn['field'] != board: mism.append(f'clip{ci} human: final rebuilt board != positions {pid(cid, K)} field; {diffrows(pn["field"], board)}')
    if clip['totals']['human'] != htotal: mism.append(f'clip{ci} human: totals {clip["totals"]["human"]} != rebuilt {htotal}')

    # ---------------- COLD CLEAR ----------------
    ccsrc = None
    for l in open(os.path.join(D, f'clips-cc-s{seed}.jsonl')):
        d = json.loads(l)
        if d['id'] == cid: ccsrc = d; break
    if ccsrc is None:
        mism.append(f'clip{ci} cc: no rollout in clips-cc-s{seed}.jsonl')
    else:
        cs = clip['cc']
        if len(cs) != len(ccsrc['steps']) or len(cs) != K: mism.append(f'clip{ci} cc: step count artefact {len(cs)} src {len(ccsrc["steps"])} k {K}')
        st = Stats(p0['b2b'], p0['combo'])
        board = list(p0['field'])
        cur, hold = p0['current'], p0['hold']
        q = deque(p0['next']); fut = deque(cin['future'])
        pending = []
        ctotal = 0
        for j, s in enumerate(ccsrc['steps']):
            tag = f'clip{ci} cc step{j}'
            a = cs[j] if j < len(cs) else None
            piece = s['piece']
            # 9: availability
            if piece == cur and not s['hold']:
                used_hold = False
                cur = q.popleft() if q else None
            elif s['hold'] and hold is not None and piece == hold:
                used_hold = True
                hold = cur; cur = q.popleft() if q else None
            elif s['hold'] and hold is None and q and piece == q[0]:
                used_hold = True
                hold = cur; q.popleft(); cur = q.popleft() if q else None
            else:
                used_hold = s['hold']
                mism.append(f'{tag}: piece {piece} (hold flag {s["hold"]}) not available: current {cur}, hold {hold}')
                cur = q.popleft() if q else None
            if fut: q.append(fut.popleft())  # one reveal per placement
            if piece not in shape_of(s['cells']): mism.append(f'{tag}: cells {s["cells"]} are not a {piece}')
            g, lines, pc, errs = place(board, s['cells'], piece, tag)
            mism += errs
            if lines != s['lines']: mism.append(f'{tag}: rebuilt lines {lines} != src lines {s["lines"]}')
            if pc != s['pc']: mism.append(f'{tag}: rebuilt pc {pc} != src pc {s["pc"]}')
            spin = {'Full': 'normal', 'Mini': 'mini', 'None': 'none'}[s['tspin']]
            if spin != 'none' and piece != 'T': mism.append(f'{tag}: spin on non-T')
            atk = st.lock(lines, spin, pc)
            ctotal += atk
            # garbage
            pending += [(t['amount'], t['column']) for t in sched[j]]
            if sum(t['amount'] for t in sched[j]) != s['garbage_in']:
                mism.append(f'{tag}: src garbage_in {s["garbage_in"]} != schedule sum {sum(t["amount"] for t in sched[j])}')
            gin = 0
            if lines == 0:
                for amt, col in pending:
                    g, e = add_garbage(g, amt, col, tag); mism += e; gin += amt
                pending = []
            after = rows_of(g)
            if a is not None:
                if a['before'] != board: mism.append(f'{tag}: artefact before != rebuilt; {diffrows(a["before"], board)}')
                if a['after'] != after: mism.append(f'{tag}: artefact after != rebuilt; {diffrows(a["after"], after)}')
                exp = dict(piece=piece, hold=used_hold, cells=s['cells'], lines=lines, spin=spin, attack=atk,
                           b2b=st.b2b, combo=st.combo, garbage=gin)
                for k, v in exp.items():
                    if a.get(k) != v: mism.append(f'{tag}: artefact {k}={a.get(k)!r}, rebuilt {v!r}')
                if j + 1 < len(cs) and cs[j + 1]['before'] != a['after']: mism.append(f'{tag}: after != next before')
            board = after; frames += 1
        if pending: checks.append(f'clip{ci} cc: {sum(a for a,_ in pending)} garbage rows still pending at end (not inserted)')
        if not eqboard(board, ccsrc['final_field'], True):
            mism.append(f'clip{ci} cc: rebuilt final board != src final_field; {diffrows(["".join("#" if c!="." else "." for c in r) for r in board], ccsrc["final_field"])}')
        if clip['totals']['cc'] != ctotal: mism.append(f'clip{ci} cc: totals {clip["totals"]["cc"]} != rebuilt {ctotal}')
        sv = clip.get('seedTotals')
        if sv and sv[seed] != ctotal: mism.append(f'clip{ci} cc: seedTotals[{seed}]={sv[seed]} != rebuilt {ctotal}')
        checks.append(f'clip{ci}: human total {htotal}, cc total {ctotal}')
    results.append(dict(clip=ci, framesChecked=frames, mismatches=mism, checks=checks))

for r in results:
    print(f"== clip {r['clip']}: frames {r['framesChecked']}, mismatches {len(r['mismatches'])}")
    for m in r['mismatches']: print('  MISMATCH', m)
    for c in r['checks']: print('  note', c)
json.dump(results, open(os.path.join(D, 'verify-batch-3.out.json'), 'w'), indent=1)
