#!/usr/bin/env python3
"""Independent verifier for clips 3,4,5 of clips-chosen.json.
Rebuilds every frame of both sides from raw sources only:
  human: positions.jsonl ; Cold Clear: clips-in.jsonl + clips-cc-s<seed>.jsonl
Written from scratch; does not read build-frames.ts / attack.ts / build-clips.py / analyze-rollouts.ts.
"""
import json, math, sys, os

D = os.path.dirname(os.path.abspath(__file__))
CLIPS = [int(a) for a in sys.argv[1:]] or [3, 4, 5]
W, H = 10, 40
EARLY = os.environ.get('CC_GARBAGE_MODE') == 'early'  # default = the rule as stated in the task

# --- tetromino shapes (canonical, all rotations generated) ---
BASE = {
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

SHAPES = {}
for p, cs in BASE.items():
    s = set(); cur = cs
    for _ in range(4):
        s.add(norm(cur))
        cur = [(-y, x) for x, y in cur]   # rotate 90
    SHAPES[p] = s

def shape_of(cells):
    n = norm([tuple(c) for c in cells])
    return [p for p, s in SHAPES.items() if n in s]

# --- attack (re-implementation of damageCalc garbageCalcV2, b2b chaining, multiplier combo, T-spins) ---
def attack(lines, spin, piece, combo, b2b, pc):
    spin = None if spin in ('none', None) else spin
    if lines == 0: g = 0
    elif lines == 1: g = 0 if spin == 'mini' else 2 if spin == 'normal' else 0
    elif lines == 2: g = 1 if spin == 'mini' else 4 if spin == 'normal' else 1
    elif lines == 3: g = 2 if spin == 'mini' else 6 if spin == 'normal' else 2
    elif lines == 4: g = 10 if spin else 4
    elif lines == 5: g = 12 if spin else 5
    else: g = (12 + 2 * (lines - 5)) if spin else (5 + lines - 5)
    if lines > 0 and b2b > 0:
        g += 1 * (math.floor(1 + math.log1p(b2b * 0.8)) + (0 if b2b == 1 else (1 + math.log1p(b2b * 0.8) % 1) / 3))
    if combo > 0:
        g *= 1 + 0.25 * combo
        if combo > 1:
            g = max(math.log1p(1 * combo * 1.25), g)
    out = math.floor(g)
    if pc: out += 10
    return out

def step_counters(b2b, combo, lines, spin):
    """TETR.IO counters: line-clearing lock bumps combo, else combo=-1.
    difficult (quad+ or any spin with lines) bumps b2b; other clear resets b2b to -1; 0 lines keeps."""
    if lines > 0:
        combo += 1
        if lines >= 4 or spin in ('normal', 'mini'):
            b2b += 1
        else:
            b2b = -1
    else:
        combo = -1
    return b2b, combo

# --- board ops ---
def place(board, cells, piece):
    rows = [list(r) for r in board]
    for x, y in cells: rows[y][x] = piece
    return rows

def clear(rows):
    full = [i for i, r in enumerate(rows) if all(c != '.' for c in r)]
    keep = [r for i, r in enumerate(rows) if i not in full]
    out = [['.'] * W for _ in full] + keep
    return out, full

def add_garbage(rows, tanks, problems, tag):
    rows = [list(r) for r in rows]
    for t in tanks:
        a, col = t['amount'], t['column']
        top = rows[:a]
        if any(c != '.' for r in top for c in r):
            problems.append(f'{tag}: garbage of {a} pushed filled cells out of the top')
        rows = rows[a:] + [['G' if x != col else '.' for x in range(W)] for _ in range(a)]
    return rows

def S(rows): return [''.join(r) for r in rows]

def is_filled(c): return c != '.'

def corners_T(board, cells):
    # center of T = the cell with 3 neighbours in the piece
    cs = set(map(tuple, cells))
    for x, y in cs:
        if sum((x + dx, y + dy) in cs for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) == 3:
            n = 0
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                X, Y = x + dx, y + dy
                if X < 0 or X >= W or Y >= H or (Y >= 0 and board[Y][X] != '.'):
                    n += 1
            return n
    return None

def check_cells(side, j, piece, cells, before, mm, checks):
    tag = f'{side} step {j}'
    sh = shape_of(cells)
    if len(cells) != 4 or len(set(map(tuple, cells))) != 4 or piece not in sh:
        mm.append(f'{tag}: cells {cells} do not form a {piece} (shape matches {sh})')
    for x, y in cells:
        if not (0 <= x < W and 0 <= y < H):
            mm.append(f'{tag}: cell {(x, y)} out of bounds'); return
        if before[y][x] != '.':
            mm.append(f'{tag}: cell {(x, y)} already filled ({before[y][x]}) on before board')
    cs = set(map(tuple, cells))
    if not any(y == H - 1 or ((x, y + 1) not in cs and before[y + 1][x] != '.') for x, y in cells):
        mm.append(f'{tag}: piece {piece} at {cells} is floating (unsupported)')

def run_clip(ci, clip, pos, clipin, ccr, mm, checks):
    start_id = clip['id']
    date, rnd, user, lock = start_id.split('/')
    lock = int(lock)
    prefix = f'{date}/{rnd}/{user}/'
    # ---- start state ----
    if clipin['field'] != clip['start']['field']:
        mm.append(f'clip {ci}: start field differs from clips-in')
    p0 = pos[prefix + str(lock)]
    if p0['field'] != clipin['field']:
        mm.append(f'clip {ci}: clips-in field differs from positions.jsonl at lock {lock}')
    for k in ('current', 'hold', 'next', 'b2b', 'combo'):
        if clip['start'][k] != clipin[k] or p0[k] != clipin[k]:
            mm.append(f'clip {ci}: start {k} differs (artefact {clip["start"][k]}, clips-in {clipin[k]}, positions {p0[k]})')
    sched = clipin['garbage_schedule']

    # =============== HUMAN ===============
    board = [list(r) for r in clipin['field']]
    b2b, combo = clipin['b2b'], clipin['combo']
    htot = 0
    for j, st in enumerate(clip['human']):
        tag = f'clip {ci} human step {j}'
        P = pos.get(prefix + str(lock + j))
        if P is None:
            mm.append(f'{tag}: no position {prefix}{lock+j}'); break
        pl = P['played']
        if S(board) != P['field']:
            mm.append(f'{tag}: rebuilt board differs from positions field at lock {lock+j}')
        if st['before'] != S(board):
            mm.append(f'{tag}: artefact before != rebuilt board')
        # state fields
        for ak, pk in (('current', 'current'), ('holdPiece', 'hold'), ('next', 'next')):
            if ak in st and st[ak] != P[pk]:
                mm.append(f'{tag}: artefact {ak}={st[ak]} but positions {pk}={P[pk]}')
        # piece / cells
        if st['piece'] != pl['piece']: mm.append(f'{tag}: piece {st["piece"]} != played {pl["piece"]}')
        if sorted(map(tuple, st['cells'])) != sorted(map(tuple, pl['cells'])):
            mm.append(f'{tag}: cells {st["cells"]} != played {pl["cells"]}')
        cells = pl['cells']
        check_cells(f'clip {ci} human', j, pl['piece'], cells, board, mm, checks)
        # hold usage
        alt = P['hold'] if P['hold'] is not None else (P['next'][0] if P['next'] else None)
        used_hold = pl['piece'] != P['current']
        if pl['piece'] != P['current'] and pl['piece'] != alt:
            mm.append(f'{tag}: placed {pl["piece"]} is neither current {P["current"]} nor hold/next {alt}')
        if bool(st['hold']) != used_hold:
            mm.append(f'{tag}: artefact hold={st["hold"]} but piece {pl["piece"]} vs current {P["current"]} implies {used_hold}')
        # spin plausibility
        if pl['spin'] != st['spin']: mm.append(f'{tag}: spin {st["spin"]} != played {pl["spin"]}')
        if pl['spin'] != 'none':
            if pl['piece'] != 'T': mm.append(f'{tag}: non-T spin {pl["spin"]}')
            elif (corners_T(board, cells) or 0) < 3: mm.append(f'{tag}: T-spin claimed with <3 corners')
        # clear
        rows = place(board, cells, pl['piece'])
        rows, full = clear(rows)
        if len(full) != pl['lines']: mm.append(f'{tag}: rebuilt clears {len(full)} rows, played.lines={pl["lines"]}')
        if st['lines'] != len(full): mm.append(f'{tag}: artefact lines {st["lines"]} != rebuilt {len(full)}')
        pc = len(full) > 0 and all(c == '.' for r in rows for c in r)
        b2b, combo = step_counters(b2b, combo, len(full), pl['spin'])
        atk = attack(len(full), pl['spin'], pl['piece'], combo, b2b, pc)
        htot += atk
        if atk != st['attack']: mm.append(f'{tag}: attack artefact {st["attack"]} != rederived {atk}')
        if atk != pl['raw']: mm.append(f'{tag}: rederived attack {atk} != played.raw {pl["raw"]}')
        if st['b2b'] != b2b or st['combo'] != combo:
            mm.append(f'{tag}: counters artefact b2b/combo {st["b2b"]}/{st["combo"]} != tracked {b2b}/{combo}')
        # garbage (tanks right after this lock)
        tanks = pl.get('tanks', [])
        if [(t['amount'], t['column']) for t in tanks] != [(t['amount'], t['column']) for t in sched[j]]:
            mm.append(f'{tag}: played.tanks {tanks} != clips-in garbage_schedule[{j}] {sched[j]}')
        amt = sum(t['amount'] for t in tanks)
        if st['garbage'] != amt: mm.append(f'{tag}: artefact garbage {st["garbage"]} != tanks total {amt}')
        rows = add_garbage(rows, tanks, mm, tag)
        if st['after'] != S(rows): mm.append(f'{tag}: artefact after != rebuilt after')
        if j + 1 < len(clip['human']) and clip['human'][j + 1]['before'] != st['after']:
            mm.append(f'{tag}: after != next step before')
        Pn = pos.get(prefix + str(lock + j + 1))
        if Pn is None:
            mm.append(f'{tag}: no next position (lock {lock+j+1}) to compare after against')
        elif Pn['field'] != S(rows):
            # try reversed tank order to diagnose
            alt_rows = add_garbage(place(board, cells, pl['piece']) and clear(place(board, cells, pl['piece']))[0], list(reversed(tanks)), [], '')
            mm.append(f'{tag}: rebuilt after != positions field at lock {lock+j+1}'
                      + (' (matches with reversed tank order)' if S(alt_rows) == Pn['field'] else ''))
        board = rows
    if clip['totals']['human'] != htot:
        mm.append(f'clip {ci}: human total artefact {clip["totals"]["human"]} != rederived {htot}')
    checks['human_steps'] += len(clip['human'])

    # =============== COLD CLEAR ===============
    board = [list(r) for r in clipin['field']]
    b2b, combo = clipin['b2b'], clipin['combo']
    cur, hold = clipin['current'], clipin['hold']
    queue = list(clipin['next']) + list(clipin['future'])
    pending = []
    ctot = 0
    ccs = ccr['steps']
    if len(ccs) != len(clip['cc']):
        mm.append(f'clip {ci}: cc step count raw {len(ccs)} != artefact {len(clip["cc"])}')
    for j, (raw, st) in enumerate(zip(ccs, clip['cc'])):
        tag = f'clip {ci} cc step {j}'
        if st['before'] != S(board): mm.append(f'{tag}: artefact before != rebuilt board')
        piece = raw['piece']
        if st['piece'] != piece: mm.append(f'{tag}: artefact piece {st["piece"]} != raw {piece}')
        if sorted(map(tuple, st['cells'])) != sorted(map(tuple, raw['cells'])):
            mm.append(f'{tag}: artefact cells {st["cells"]} != raw {raw["cells"]}')
        # queue / hold
        if piece == cur:
            used = False
            cur = queue.pop(0) if queue else None
        else:
            used = True
            if hold is not None:
                if piece != hold:
                    mm.append(f'{tag}: piece {piece} not available (current {cur}, hold {hold})')
                hold, cur = cur, (queue.pop(0) if queue else None)
            else:
                nx = queue[0] if queue else None
                if piece != nx:
                    mm.append(f'{tag}: piece {piece} not available (current {cur}, hold empty, next {nx})')
                hold = cur; queue.pop(0); cur = queue.pop(0) if queue else None
        if bool(raw['hold']) != used: mm.append(f'{tag}: raw hold flag {raw["hold"]} but queue tracking says {used}')
        if bool(st['hold']) != used: mm.append(f'{tag}: artefact hold flag {st["hold"]} but queue tracking says {used}')
        check_cells(f'clip {ci} cc', j, piece, raw['cells'], board, mm, checks)
        spin = {'Full': 'normal', 'Mini': 'mini', 'None': 'none'}[raw['tspin']]
        if spin != 'none' and piece != 'T': mm.append(f'{tag}: spin on non-T')
        if spin != 'none' and (corners_T(board, raw['cells']) or 0) < 3: mm.append(f'{tag}: T-spin with <3 corners')
        if st['spin'] != spin: mm.append(f'{tag}: artefact spin {st["spin"]} != raw {spin}')
        rows = place(board, raw['cells'], piece)
        rows, full = clear(rows)
        n = len(full)
        if n != raw['lines']: mm.append(f'{tag}: rebuilt clears {n} rows, raw lines={raw["lines"]}')
        if st['lines'] != n: mm.append(f'{tag}: artefact lines {st["lines"]} != rebuilt {n}')
        pc = n > 0 and all(c == '.' for r in rows for c in r)
        if pc != bool(raw['pc']): mm.append(f'{tag}: perfect clear rebuilt {pc} != raw {raw["pc"]}')
        b2b, combo = step_counters(b2b, combo, n, spin)
        atk = attack(n, spin, piece, combo, b2b, pc)
        ctot += atk
        if atk != st['attack']: mm.append(f'{tag}: attack artefact {st["attack"]} != rederived {atk}')
        if st['b2b'] != b2b or st['combo'] != combo:
            mm.append(f'{tag}: counters artefact b2b/combo {st["b2b"]}/{st["combo"]} != tracked {b2b}/{combo}')
        # garbage: inserted only on a 0-line lock, from the pending list (rows received at earlier steps)
        ins = []
        if EARLY: pending += sched[j]   # alternative rule: step-j rows are pending BEFORE CC's step-j lock
        if n == 0 and pending:
            ins, pending = pending, []
        amt = sum(t['amount'] for t in ins)
        if amt != raw['garbage_in']: mm.append(f'{tag}: rebuilt garbage insert {amt} != raw garbage_in {raw["garbage_in"]}')
        if st['garbage'] != amt: mm.append(f'{tag}: artefact garbage {st["garbage"]} != rebuilt {amt}')
        rows = add_garbage(rows, ins, mm, tag)
        if not EARLY: pending += sched[j]   # stated rule: human's step-j rows join after CC's step-j lock
        if st['after'] != S(rows): mm.append(f'{tag}: artefact after != rebuilt after')
        if j + 1 < len(clip['cc']) and clip['cc'][j + 1]['before'] != st['after']:
            mm.append(f'{tag}: after != next step before')
        board = rows
    fin = [''.join('#' if c != '.' else '.' for c in r) for r in board]
    if fin != ccr['final_field']:
        mm.append(f'clip {ci}: rebuilt CC final board != raw final_field')
    if clip['totals']['cc'] != ctot:
        mm.append(f'clip {ci}: cc total artefact {clip["totals"]["cc"]} != rederived {ctot}')
    checks['cc_steps'] += len(ccs)
    if pending:
        checks['notes'].append(f'clip {ci}: {sum(t["amount"] for t in pending)} CC garbage rows still pending at end')

def main():
    clips = json.load(open(os.path.join(D, 'clips-chosen.json')))
    clipins = {}
    for l in open(os.path.join(D, 'clips-in.jsonl')):
        d = json.loads(l); clipins[d['id']] = d
    need = {clips[c]['id'] for c in CLIPS}
    prefixes = set()
    for c in CLIPS:
        a = clips[c]['id'].rsplit('/', 1)[0] + '/'
        prefixes.add(a)
    pos = {}
    for l in open(os.path.join(D, 'positions.jsonl')):
        i = l.find('"id":"'); pid = l[i + 6:l.index('"', i + 6)]
        if pid.rsplit('/', 1)[0] + '/' in prefixes:
            pos[pid] = json.loads(l)
    out = []
    for c in CLIPS:
        clip = clips[c]; seed = clip['seed']
        ccr = None
        for l in open(os.path.join(D, f'clips-cc-s{seed}.jsonl')):
            d = json.loads(l)
            if d['id'] == clip['id']: ccr = d
        mm = []; checks = {'human_steps': 0, 'cc_steps': 0, 'notes': []}
        run_clip(c, clip, pos, clipins[clip['id']], ccr, mm, checks)
        out.append({'clip': c, 'id': clip['id'], 'seed': seed, 'mismatches': mm, **checks})
    print(json.dumps(out, indent=1))

main()
