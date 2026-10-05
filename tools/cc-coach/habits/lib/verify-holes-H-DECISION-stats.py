import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
# Independent skeptic re-derivation of H-DECISION (deliberate hole/overhang placements cc avoids).
# Own board code (does NOT load holes_rows.pkl); reads mid.jsonl + grade*.jsonl directly.
import json, collections, random, math, os, sys
C = CC_WORK + '/corpus'

def apply(field, cells):
    g = [list(r) for r in field]
    for x, y in cells:
        if 0 <= y < 40: g[y][x] = '#'
    keep = [r for r in g if '.' in r]
    return [['.'] * 10 for _ in range(40 - len(keep))] + keep

def stats(g):
    """covered = empty cells with a block above in the column; sealed = empty cells NOT reachable
    (4-connected through empties) from the top row."""
    cov = 0
    for c in range(10):
        seen = False
        for r in range(40):
            if g[r][c] != '.': seen = True
            elif seen: cov += 1
    vis = set(); st = [(c, 0) for c in range(10) if g[0][c] == '.']; vis.update(st)
    while st:
        x, y = st.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < 10 and 0 <= ny < 40 and g[ny][nx] == '.' and (nx, ny) not in vis:
                vis.add((nx, ny)); st.append((nx, ny))
    empt = sum(1 for r in g for v in r if v == '.')
    return cov, empt - len(vis)

def heights(f): return [40 - next((r for r in range(40) if f[r][c] != '.'), 40) for c in range(10)]

def delta(field, base, cells):
    a = stats(apply(field, cells)); return a[0] - base[0], a[1] - base[1]

def norm(cells):
    mx = min(x for x, y in cells); my = min(y for x, y in cells)
    return frozenset((x - mx, y - my) for x, y in cells), mx

def md_geo(piece, pcells, cands):
    ps, px = norm(pcells); P = set(map(tuple, pcells))
    for c in cands:
        if c['piece'] != piece: continue
        if set(map(tuple, c['cells'])) == P: return None
        cs, cx = norm(c['cells'])
        if cs == ps and abs(cx - px) == 1: return 'shift'
        if cs != ps and abs(cx - px) <= 1: return 'rot'
    return None

def hard_drop(field, shape, x0):
    w = max(x for x, y in shape) + 1
    if x0 < 0 or x0 + w > 10: return None
    top = -min(y for x, y in shape)
    if any(field[top + dy][x0 + dx] != '.' for dx, dy in shape): return None
    while all(top + dy + 1 < 40 and field[top + dy + 1][x0 + dx] == '.' for dx, dy in shape): top += 1
    return [(x0 + dx, top + dy) for dx, dy in shape]

def shift_clean(field, base, pcells):
    ps, px = norm(pcells)
    for d in (-1, 1):
        cells = hard_drop(field, sorted(ps), px + d)
        if cells and delta(field, base, cells)[0] <= 0: return True
    return False

SH = {'I': [[(0,0),(1,0),(2,0),(3,0)], [(0,0),(0,1),(0,2),(0,3)]], 'O': [[(0,0),(1,0),(0,1),(1,1)]],
      'T': [[(0,0),(1,0),(2,0),(1,1)], [(1,0),(0,1),(1,1),(2,1)], [(0,0),(0,1),(0,2),(1,1)], [(1,0),(1,1),(1,2),(0,1)]],
      'S': [[(1,0),(2,0),(0,1),(1,1)], [(0,0),(0,1),(1,1),(1,2)]], 'Z': [[(0,0),(1,0),(1,1),(2,1)], [(1,0),(1,1),(0,1),(0,2)]],
      'J': [[(0,0),(0,1),(1,1),(2,1)], [(0,0),(1,0),(0,1),(0,2)], [(0,0),(1,0),(2,0),(2,1)], [(1,0),(1,1),(1,2),(0,2)]],
      'L': [[(2,0),(0,1),(1,1),(2,1)], [(0,0),(0,1),(0,2),(1,2)], [(0,0),(1,0),(2,0),(0,1)], [(0,0),(1,0),(1,1),(1,2)]]}
def clean_fit(field, base, piece):
    if not piece: return False
    for sh in SH[piece]:
        for x0 in range(10):
            cells = hard_drop(field, sh, x0)
            if cells and delta(field, base, cells)[0] <= 0: return True
    return False

def load(fn):
    d = {}
    for l in open(C + '/' + fn):
        g = json.loads(l); d[g['id']] = g
    return d

G = load('grade.jsonl'); S1C = load('grade-s1-ccpick.jsonl'); WK = load('grade-weak.jsonl')
rows = []
for l in open(C + '/mid.jsonl'):
    p = json.loads(l); g = G.get(p['id'])
    if not g or 'error' in g or not g.get('duel') or g['duel']['player'] is None or g['duel']['cc'] is None: continue
    f = p['field']; base = stats(f); pl = p['played']
    pc = [tuple(c) for c in pl['cells']]; cc = [tuple(c) for c in g['pick']['cells']]
    pd = delta(f, base, pc); cd = delta(f, base, cc)
    same = set(pc) == set(cc)
    r = dict(id=p['id'], user=p['user'], sess=p['session'], rnd=(p['session'], p['file'], p['round']),
             reg=g['duel']['cc'] - g['duel']['player'], same=same, maxh=max(heights(f)),
             garb=sum(1 for row in f if 'G' in row), pd=pd, cd=cd, pt=pl['pieceTime'], nk=len(pl['keys']))
    if (pd[0] > 0 or pd[1] > 0) and not same:
        r['geo'] = md_geo(pl['piece'], pc, [g['pick']] + g['top'][:3])
        r['sc'] = shift_clean(f, base, pc)
        # top-5 near: any top-5 candidate sharing >=3 cells (looser misdrop variant)
        r['near'] = any(len(set(map(tuple, t['cells'])) & set(pc)) >= 3 for t in g['top'][:5])
        r['cleanfit'] = clean_fit(f, base, p['current']) or clean_fit(f, base, p['hold'] or (p['next'][0] if p['next'] else None))
    # noise analogs on sub4000 ids
    if p['id'] in S1C and S1C[p['id']].get('duel') and S1C[p['id']]['duel']['player'] is not None:
        s = S1C[p['id']]  # player = seed0 pick, cc = seed1 pick, judged by seed1
        r['n1'] = dict(reg=s['duel']['cc'] - s['duel']['player'], pd=cd,
                       cd=delta(f, base, [tuple(c) for c in s['pick']['cells']]))
        r['n1']['geo'] = md_geo(g['pick']['piece'], cc, [s['pick']] + s['top'][:3]) if (r['n1']['pd'][0] > 0 or r['n1']['pd'][1] > 0) else None
        # same subset, humans judged by seed1
        r['h1'] = dict(reg=s['duel']['cc'] - S1C[p['id']]['duel']['cc'] if False else None)
    if p['id'] in WK and WK[p['id']].get('duel') and WK[p['id']]['duel']['cc'] is not None:
        w = WK[p['id']]
        wc = [tuple(c) for c in w['pick']['cells']]
        r['nw'] = dict(reg=g['duel']['cc'] - w['duel']['cc'], pd=delta(f, base, wc), cd=cd,
                       geo=md_geo(w['pick']['piece'], wc, [g['pick']] + g['top'][:3]))
    rows.append(r)
print('graded rows', len(rows))
PT = sorted(r['pt'] for r in rows); PT25 = PT[len(PT) // 4]

def band(r): m = r['maxh']; return '0-5' if m <= 5 else '6-9' if m <= 9 else '10-13' if m <= 13 else '14+'
def isMD(r): return bool(r.get('geo')) or bool(r.get('sc'))
def H(r, k=0): return (r['pd'][k] > 0 and r['cd'][k] <= 0 and not r['same'] and not isMD(r))

def boot(rs, fn, B=1000, seed=7):
    by = collections.defaultdict(lambda: [0.0, 0])
    for r in rs: v = fn(r); by[r['rnd']][0] += v; by[r['rnd']][1] += 1
    v = list(by.values()); tot = sum(a for a, b in v) / max(1, sum(b for a, b in v))
    rng = random.Random(seed); ms = []
    for _ in range(B):
        S = N = 0
        for _ in v: a, b = v[rng.randrange(len(v))]; S += a; N += b
        ms.append(S / max(N, 1))
    ms.sort(); return tot, ms[int(.025 * B)], ms[int(.975 * B)]
def signp(k, n):
    m = min(k, n - k); return min(1.0, 2 * sum(math.comb(n, i) for i in range(m + 1)) / 2 ** n) if n else 1.0
F = lambda t: f'{t[0]:+.0f} [{t[1]:+.0f}, {t[2]:+.0f}]'

for u in ('yachi', 'pinglamb'):
    U = [r for r in rows if r['user'] == u]; N = len(U)
    dev = [r for r in U if not r['same']]
    # baseline: non-H, non-misdrop deviating moves in the same band (the "average deviation")
    ctrl = [r for r in dev if not (r['pd'][0] > 0 and r['cd'][0] <= 0)]
    base = {b: sum(r['reg'] for r in ctrl if band(r) == b) / max(1, sum(1 for r in ctrl if band(r) == b)) for b in ('0-5', '6-9', '10-13', '14+')}
    allb = {b: sum(r['reg'] for r in U if band(r) == b) / max(1, sum(1 for r in U if band(r) == b)) for b in base}
    print(f'\n===== {u}: graded {N}, deviations {len(dev)}; band baseline (non-covering deviations) ' + ' '.join(f'{b}:{v:.0f}' for b, v in base.items()))
    for lab, k in (('COVERS', 0), ('SEALS', 1)):
        sel = [r for r in U if H(r, k)]
        cand = [r for r in U if r['pd'][k] > 0 and r['cd'][k] <= 0 and not r['same']]
        mdsh = sum(isMD(r) for r in cand) / max(1, len(cand))
        print(f' {lab}: n={len(sel)} ({100*len(sel)/N:.2f}/100 graded); raw candidates incl misdrops {len(cand)}, misdrop share {mdsh:.1%}')
        print(f'   mean regret {F(boot(sel, lambda r: r["reg"]))}; excess vs band non-covering deviations {F(boot(sel, lambda r: r["reg"] - base[band(r)]))}; excess vs band ALL moves {F(boot(sel, lambda r: r["reg"] - allb[band(r)]))}')
        print(f'   per100 pieces (excess vs ctrl) {F(boot(U, lambda r: 100*(r["reg"] - base[band(r)]) if H(r, k) else 0))}')
        # within-band
        for b in base:
            s = [r for r in sel if band(r) == b]
            if len(s) >= 10:
                print(f'     band {b:5s} n={len(s):4d} rate {100*len(s)/sum(1 for r in U if band(r)==b):.2f}/100 regret {F(boot(s, lambda r: r["reg"], 400))} ctrl {base[b]:.0f} excess {F(boot(s, lambda r: r["reg"] - base[b], 400))}')
        # session consistency: excess per H move (sessions with >=5 H moves); plus leave-big-out
        bys = collections.defaultdict(list)
        for r in sel: bys[r['sess']].append(r['reg'] - base[band(r)])
        vals = {s: sum(v) / len(v) for s, v in bys.items() if len(v) >= 5}
        pos = sum(v > 0 for v in vals.values())
        print(f'   sessions: {pos}/{len(vals)} positive, sign p={signp(pos, len(vals)):.2g}; per-session mean excess: ' + ' '.join(f'{s[5:]}:{v:+.0f}(n{len(bys[s])})' for s, v in sorted(vals.items())))
        big = ('2026-09-18', '2026-09-19', '2026-10-03')
        s3 = [r for r in sel if r['sess'] not in big]
        print(f'   excluding 09-18/09-19/10-03: n={len(s3)} excess {F(boot(s3, lambda r: r["reg"] - base[band(r)]))}')
        # garbage control
        for gl, gf in (('garb0', lambda r: r['garb'] == 0), ('garb>0', lambda r: r['garb'] > 0)):
            s = [r for r in sel if gf(r)]
            cb = [r for r in ctrl if gf(r)]
            if s: print(f'     {gl}: n={len(s)} excess vs band&garb-matched ctrl {F(boot(s, lambda r: r["reg"] - sum(c["reg"] for c in cb if band(c)==band(r))/max(1,sum(1 for c in cb if band(c)==band(r))), 300))}')
        # stricter misdrop exclusion: also drop near (>=3 shared cells w/ top5), short pieceTime, or extra keys
        strict = [r for r in sel if not r['near'] and r['pt'] > PT25]
        print(f'   strict non-misdrop (no top5 cand sharing >=3 cells, pieceTime>p25={PT25}): n={len(strict)} excess {F(boot(strict, lambda r: r["reg"] - base[band(r)]))}')
        # cc-free detector: player covers AND a clean (no-new-cover) hard-drop existed for current or hold/next
        cf = [r for r in U if r['pd'][k] > 0 and not r['same'] and r.get('cleanfit') and not isMD(r)]
        print(f'   cc-free detector (covers & a clean drop existed, not MD): n={len(cf)} excess {F(boot(cf, lambda r: r["reg"] - base[band(r)]))}')
        # leakage check: same detector where cc ALSO covers -> regret
        both = [r for r in U if r['pd'][k] > 0 and r['cd'][k] > 0 and not r['same'] and not isMD(r)]
        print(f'   leakage check: player covers AND cc covers too (n={len(both)}): excess {F(boot(both, lambda r: r["reg"] - base[band(r)]))}')

    # bot noise on the sub4000 subset (same detector)
    sub = [r for r in U if 'n1' in r and 'nw' in r]
    for k, lab in ((0, 'COVERS'), (1, 'SEALS')):
        hs = [r for r in sub if H(r, k)]
        n1 = [r for r in sub if r['n1']['pd'][k] > 0 and r['n1']['cd'][k] <= 0 and not r['n1']['geo']]
        nw = [r for r in sub if r['nw']['pd'][k] > 0 and r['nw']['cd'][k] <= 0 and not r['nw']['geo']]
        def per100(rs, key):
            return sum((r[key]['reg'] if key else r['reg']) for r in rs) * 100 / len(sub)
        print(f'  NOISE sub4000 {lab} (n={len(sub)}): human n={len(hs)} rate {100*len(hs)/len(sub):.2f}/100 mean regret {F(boot(hs, lambda r: r["reg"], 400))} raw per100 {per100(hs, None):+.0f}')
        print(f'      cc seed0 vs seed1: n={len(n1)} rate {100*len(n1)/len(sub):.2f}/100 mean regret {F(boot(n1, lambda r: r["n1"]["reg"], 400)) if n1 else "-"} raw per100 {per100(n1, "n1"):+.0f}')
        print(f'      weak bot vs cc:    n={len(nw)} rate {100*len(nw)/len(sub):.2f}/100 mean regret {F(boot(nw, lambda r: r["nw"]["reg"], 400)) if nw else "-"} raw per100 {per100(nw, "nw"):+.0f}')
