import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
# Detector for Y6 = TS2 (yachi locks the T sideways = TSS in a ready TSD slot), copied VERBATIM from the
# surviving skeptic scripts verify-tspins-TS2-yachi-tss-in-tsd-slot-{stats,misdrop}.py.
import json, os
CORPUS = CC_WORK + '/corpus'
HAB = CC_WORK + '/scen/habits'
SESS = sorted(f[:-6] for f in os.listdir(CORPUS) if f.endswith('.jsonl') and f[:4] == '2026')
def occ(field): return [[c != '.' for c in row] for row in field]
def F(g, x, r): return x < 0 or x > 9 or r > 39 or (r >= 0 and g[r][x])
def slots(g):
    out = []
    for r in range(1, 39):
        emp_r = [c for c in range(10) if not g[r][c]]
        if len(emp_r) != 3: continue
        emp_r1 = [c for c in range(10) if not g[r+1][c]]
        if len(emp_r1) != 1: continue
        x = emp_r1[0]
        if emp_r != [x-1, x, x+1]: continue
        tl, tr = F(g, x-1, r-1), F(g, x+1, r-1)
        if tl == tr: continue
        side = x+1 if tl else x-1
        if any(g[k][x] for k in range(r)) or any(g[k][side] for k in range(r)): continue
        out.append((x, r, 'R' if tl else 'L'))
    return out
def mh(g):
    for r in range(40):
        if any(g[r]): return 40 - r
    return 0
def classify(cells, spin, lines, sl):
    pc = set(map(tuple, cells))
    for x, r, side in sl:
        D = {(x-1, r), (x, r), (x+1, r), (x, r+1)}
        if (x, r+1) in pc and len(pc & D) >= 3:
            if pc == D and lines >= 2: return 'TSD', (x, r, side), D
            if spin != 'none' and lines == 1: return 'TSS', (x, r, side), D
            return 'other', (x, r, side), D
    return None, None, None
def pick_out(gr, sl):
    pk = gr.get('pick') if gr else None
    if not pk or pk['piece'] != 'T': return None
    k = pk['kind']
    return classify(pk['cells'], 'normal' if k in ('tsd', 'tss', 'tst') else ('mini' if 'mini' in k else 'none'),
                    2 if k == 'tsd' else 1 if k in ('tss', 'mini_tss') else 0, sl)[0]
def keysig(rot):
    n = len(rot)
    if n == 0: return '0 rot'
    if 'rotate180' in rot: return 'uses 180'
    if n >= 2 and rot[-1] != rot[-2]: return 'last two opposite (correction)'
    if n == 1: return '1 rot'
    if n == 2: return '2 same rot'
    return '3+ same rot'
def in_slot_positions(user=None):
    """every verified decision where the player locked a T into a static TSD slot as TSD or TSS (the skeptic's recs)"""
    for s in SESS:
        for l in open(f'{CORPUS}/{s}.jsonl'):
            d = json.loads(l)
            if not d['verified'] or d['played']['piece'] != 'T': continue
            if user and d['user'] != user: continue
            g = occ(d['field']); sl = slots(g)
            if not sl: continue
            pl = d['played']
            out, slot, D = classify(pl['cells'], pl['spin'], pl['lines'], sl)
            if out not in ('TSD', 'TSS'): continue
            yield s, d, g, sl, out, slot, D
