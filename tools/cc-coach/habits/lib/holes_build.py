import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
# Lens: HOLES, OVERHANGS AND MISDROPS — row builder (cached to holes_rows.pkl)
import json, pickle, os, collections
C = CC_WORK + '/corpus'
H = os.path.dirname(os.path.abspath(__file__))

def heights(f):
    return [40 - next((r for r in range(40) if f[r][c] != '.'), 40) for c in range(10)]
def apply(f, cells):
    g = [list(r) for r in f]
    for x, y in cells:
        if 0 <= y < 40: g[y][x] = '#'
    nl = sum(1 for r in g if '.' not in r)
    g = [r for r in g if '.' in r]
    g = [['.'] * 10 for _ in range(40 - len(g))] + g
    return g, nl
def covered(g):
    """set of empty cells with a filled cell somewhere above in the same column"""
    s = set()
    for c in range(10):
        seen = False
        for r in range(40):
            if g[r][c] != '.': seen = True
            elif seen: s.add((c, r))
    return s
def classify(g, cov, cells):
    """split covered cells into overhang (4-connected empty region touches an uncovered empty cell) vs sealed"""
    oh = sd = 0
    for cell in cells:
        st_ = [cell]; vis = {cell}; open_ = False
        while st_:
            x, y = st_.pop()
            if (x, y) not in cov: open_ = True; break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 40 and g[ny][nx] == '.' and (nx, ny) not in vis:
                    vis.add((nx, ny)); st_.append((nx, ny))
        if open_: oh += 1
        else: sd += 1
    return oh, sd
def counts(g):
    """covered cells; open = its empty 4-connected component contains an uncovered empty cell (reachable by tuck/spin), else sealed"""
    cov = covered(g); comp = {}; oh = sd = 0
    for cell in cov:
        if cell in comp: continue
        stack = [cell]; members = [cell]; comp[cell] = None; op = False
        while stack:
            x, y = stack.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 40 and g[ny][nx] == '.':
                    if (nx, ny) not in cov: op = True
                    elif (nx, ny) not in comp:
                        comp[(nx, ny)] = None; members.append((nx, ny)); stack.append((nx, ny))
        for m in members: comp[m] = op
        if op: oh += len(members)
        else: sd += len(members)
    return len(cov), oh, sd
def hole_delta(f, cells):
    """POST-CLEAR deltas vs the start board: (covered cells, of which open-overhang, sealed), plus pre-clear cells left
    empty directly under the piece, and lines.  Returned as (dcov, under, doh, dsealed, lines)."""
    g0 = [list(r) for r in f]; a = counts(g0)
    g1, nl = apply(f, cells); b = counts(g1)
    pre = [list(r) for r in f]
    for x, y in cells:
        if 0 <= y < 40: pre[y][x] = '#'
    under = 0
    for x in {x for x, y in cells}:
        y = max(yy for xx, yy in cells if xx == x) + 1
        while y < 40 and pre[y][x] == '.': under += 1; y += 1
    return b[0] - a[0], under, b[1] - a[1], b[2] - a[2], nl
_cache = {}
# hard-drop placements (no tucks/spins) for clean-fit counting
SH = {'I': [[(0,0),(1,0),(2,0),(3,0)], [(0,0),(0,1),(0,2),(0,3)]],
      'O': [[(0,0),(1,0),(0,1),(1,1)]],
      'T': [[(0,0),(1,0),(2,0),(1,1)], [(1,0),(0,1),(1,1),(2,1)], [(0,0),(0,1),(0,2),(1,1)], [(1,0),(1,1),(1,2),(0,1)]],
      'S': [[(1,0),(2,0),(0,1),(1,1)], [(0,0),(0,1),(1,1),(1,2)]],
      'Z': [[(0,0),(1,0),(1,1),(2,1)], [(1,0),(1,1),(0,1),(0,2)]],
      'J': [[(0,0),(0,1),(1,1),(2,1)], [(0,0),(1,0),(0,1),(0,2)], [(0,0),(1,0),(2,0),(2,1)], [(1,0),(1,1),(1,2),(0,2)]],
      'L': [[(2,0),(0,1),(1,1),(2,1)], [(0,0),(0,1),(0,2),(1,2)], [(0,0),(1,0),(2,0),(0,1)], [(0,0),(1,0),(1,1),(1,2)]]}
def drops(f, piece):
    h = heights(f); out = []
    for sh in SH[piece]:
        w = max(x for x, y in sh) + 1; hh = max(y for x, y in sh) + 1
        for x0 in range(10 - w + 1):
            # lowest y offset: piece cell (x0+dx, top+dy); need all rows below free; land where any cell rests
            top = 0
            while True:
                ok = all(top + dy + 1 < 40 and f[top + dy + 1][x0 + dx] == '.' for dx, dy in sh)
                if not ok: break
                top += 1
            cells = [(x0 + dx, top + dy) for dx, dy in sh]
            if any(f[y][x] != '.' for x, y in cells): continue
            out.append(cells)
    return out
def clean_fits(f, piece):
    if not piece: return 0
    n = 0
    for cells in drops(f, piece):
        d, u, oh, sd, nl = hole_delta(f, cells)
        if d <= 0 and u == 0: n += 1
    return n
def norm(cells):
    mx = min(x for x, y in cells); my = min(y for x, y in cells)
    return frozenset((x - mx, y - my) for x, y in cells), mx
def misdrop(pp, pcells, cands):
    ps, px = norm(pcells)
    for c in cands:
        if c['piece'] != pp: continue
        cs, cx = norm(c['cells'])
        if set(map(tuple, c['cells'])) == set(map(tuple, pcells)): return None
        if cs == ps and abs(cx - px) == 1: return 'shift'
        if cs != ps and abs(cx - px) <= 1: return 'rot'
    return None
def shift_clean(f, pcells):
    """same shape hard-dropped one column left/right: does it make no gap under the piece?"""
    ps, px = norm(pcells)
    shape = sorted(ps)
    for dxs in (-1, 1):
        x0 = px + dxs; w = max(x for x, y in shape) + 1
        if x0 < 0 or x0 + w > 10: continue
        top = 0
        while all(top + dy + 1 < 40 and f[top + dy + 1][x0 + dx] == '.' for dx, dy in shape): top += 1
        cells = [(x0 + dx, top + dy) for dx, dy in shape]
        if any(f[y][x] != '.' for x, y in cells): continue
        if hole_delta(f, cells)[0] <= 0: return True
    return False
def surf(f, cols):
    h = heights(f); b = min(h[c] for c in cols)
    return tuple(min(h[c] - b, 3) for c in cols)

M = [json.loads(l) for l in open(C + '/mid.jsonl')]
G = {}
for l in open(C + '/grade.jsonl'):
    g = json.loads(l); G[g['id']] = g
def loadg(fn):
    d = {}
    for l in open(C + '/' + fn):
        g = json.loads(l); d[g['id']] = g
    return d
S1, WK = loadg('grade-s1.jsonl'), loadg('grade-weak.jsonl')
rows = []
for p in M:
    g = G.get(p['id'])
    if not g or 'error' in g or not g.get('duel') or g['duel']['player'] is None or g['duel']['cc'] is None: continue
    f = p['field']; h = heights(f); pl = p['played']
    pcells = [tuple(c) for c in pl['cells']]; ccells = [tuple(c) for c in g['pick']['cells']]
    pd = hole_delta(f, pcells); cd = hole_delta(f, ccells)
    extra = {}
    if p['id'] in S1 and 'pick' in S1[p['id']]:
        extra['s1'] = hole_delta(f, [tuple(c) for c in S1[p['id']]['pick']['cells']])
    if p['id'] in WK and 'pick' in WK[p['id']]:
        extra['wk'] = hole_delta(f, [tuple(c) for c in WK[p['id']]['pick']['cells']])
    topc = [hole_delta(f, [tuple(c) for c in t['cells']])[0] for t in g['top'][:5]]
    s1sh = S1[p['id']]['cc_shape'] if p['id'] in S1 and 'cc_shape' in S1[p['id']] else None
    holdp = p['hold'] or (p['next'][0] if p['next'] else None)
    pcols = sorted({x for x, y in pcells})
    rows.append(dict(id=p['id'], user=p['user'], sess=p['session'], rnd=(p['session'], p['file'], p['round']),
        lock=p['lock'], reg=g['duel']['cc'] - g['duel']['player'], same=g['duel']['same'], maxh=max(h),
        bump=sum(abs(h[i] - h[i + 1]) for i in range(9)), garb=sum(1 for r in f if 'G' in r), holes0=len(covered([list(r) for r in f])),
        inc=p['incoming'], cur=p['current'], hold=p['hold'], nxt=p['next'], ppiece=pl['piece'], held=pl['piece'] != p['current'],
        spin=pl['spin'], plines=pl['lines'], cpiece=g['pick']['piece'], ckind=g['pick']['kind'], ctspin=g['pick']['tspin'],
        pkind=g['player'].get('kind'), found=g['player']['found'], rank=g['player'].get('rank'),
        pd=pd, cd=cd, extra=extra, topc=topc, pshape=g['player_shape'], cshape=g['cell_shape'] if 'cell_shape' in g else g['cc_shape'],
        s1sh=s1sh, pgrp=g['player_groups'], cgrp=g['cc_groups'],
        md=misdrop(pl['piece'], pcells, [g['pick']] + g['top'][:3]), shiftclean=shift_clean(f, pcells) if pd[0] > 0 else None,
        fits_cur=clean_fits(f, p['current']), fits_alt=clean_fits(f, holdp),
        surf=surf(f, pcols), pcols=pcols, rot=pl['rotation'],
        pt=pl['pieceTime'], nk=len(pl['keys']), keys=pl['keys']))
pickle.dump(rows, open(H + '/holes_rows.pkl', 'wb'))
print('rows', len(rows))
