# Habit P4 (pinglamb): adding to the tall half of a lopsided board at 10-13 rows (with garbage).
# Source: FINDINGS.md pinglamb #4 + verify-discovery-D2-stats.py / verify-discovery-D2-misdrop.py (+ .out).
# Surviving definition = the skeptic's "S1b" (verify-discovery-D2-stats.py, copied verbatim below):
#   rows = mid.jsonl positions with a cc seed-0 grade carrying pick and duel, duel.player and duel.cc not None;
#   max column height <= 13; neither the player's move kind nor cc's pick kind in STRONG (T-spins, quad);
#   not (player cleared lines with a spin); player's hold use == cc pick's hold use;
#   |mean height cols 0-4 - mean height cols 5-9| >= 2 ("lopsided"); S1b narrows to max height 10-13 AND
#   >= 4 rows containing garbage. A move is "on the taller half" when its 4-cell centroid x is on that side
#   (x < 4.5 = left). Rate = share of eligible positions whose move is on the taller half; gap = player - cc.
#   Occurrence = player on the taller half AND cc's pick not ("taller/cc-lower" in the skeptic's script).
#   misdrop_shaped = the stats script's md(): some of cc's pick or its top-3 (by cells) is the player's exact
#   shape shifted one column, or a different shape whose min-x is within 1 column and bottom row within 1 row.
import json, os, collections, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(os.path.dirname(H)) + '/corpus/'
USER = 'pinglamb'
STRONG = {'tsd','tst','tss','mini_tss','tspin0','mini_tspin0','quad'}
G = {}
for l in open(C + 'grade.jsonl'):
    g = json.loads(l)
    if g.get('pick') and g.get('duel'): G[g['id']] = g
def heights(f): return [40 - next((r for r in range(40) if f[r][c] != '.'), 40) for c in range(10)]
def halves(h): return sum(h[:5]) / 5, sum(h[5:]) / 5
def side_centroid(cells): return 'L' if sum(x for x, _ in cells) / 4 < 4.5 else 'R'
def norm(cs):
    mx = min(x for x, _ in cs); my = min(y for _, y in cs); return frozenset((x - mx, y - my) for x, y in cs), mx, max(y for _, y in cs)
def md(pcs, cands):
    ps, px, pb = norm(pcs)
    for c in cands:
        if c == pcs: return False
        cs, cx, cb = norm(c)
        if cs == ps and abs(cx - px) == 1: return True
        if cs != ps and abs(cx - px) <= 1 and abs(cb - pb) <= 1: return True
    return False
def place(F, cells):
    g = [list(r) for r in F]
    for x, y in cells: g[y][x] = '#'
    return g
def covered(g):  # empty cells with a filled cell somewhere above in the same column
    n = 0
    for c in range(10):
        seen = False
        for r in range(40):
            if g[r][c] != '.': seen = True
            elif seen: n += 1
    return n
def after(F, cells):
    g = place(F, cells); full = [r for r in range(40) if '.' not in g[r]]
    g2 = [['.'] * 10 for _ in full] + [g[r] for r in range(40) if r not in full]
    return len(full), g2
occ = []; per = collections.defaultdict(lambda: dict(n=0, pl=0, cc=0, occ=0, rev=0, md=0, regs=[], regs_nomd=[], n_x=0, pl_x=0, cc_x=0))
for l in open(C + 'mid.jsonl'):
    p = json.loads(l)
    if p['user'] != USER: continue
    g = G.get(p['id'])
    if not g or g['duel']['player'] is None or g['duel']['cc'] is None: continue
    f = p['field']; h0 = heights(f); mh = max(h0)
    if mh > 13: continue
    pk = g['player'].get('kind'); ck = g['pick'].get('kind')
    if pk in STRONG or ck in STRONG: continue
    pl = p['played']
    if pl['lines'] > 0 and pl['spin'] != 'none': continue
    phold = pl['piece'] != p['current']
    if phold != bool(g['pick']['hold']): continue
    L, R = halves(h0); d = L - R
    if abs(d) < 2: continue
    hi = 'L' if d > 0 else 'R'
    ngr = sum('G' in r for r in f)
    if not (10 <= mh <= 13 and ngr >= 4): continue   # S1b
    pc = [tuple(c) for c in pl['cells']]; cc = [tuple(c) for c in g['pick']['cells']]
    P = side_centroid(pc) == hi; Cc = side_centroid(cc) == hi
    cands = [sorted(map(tuple, t['cells'])) for t in g.get('top', [])[:3]] + [sorted(cc)]
    m = md(sorted(pc), cands)
    reg = g['duel']['cc'] - g['duel']['player']
    s = p['session']; D = per[s]
    D['n'] += 1; D['pl'] += P; D['cc'] += Cc
    if P and not Cc:
        D['occ'] += 1; D['regs'].append(reg); D['md'] += m
        if not m: D['regs_nomd'].append(reg)
    if Cc and not P: D['rev'] += 1
    if not m: D['n_x'] += 1; D['pl_x'] += P; D['cc_x'] += Cc
    if not (P and not Cc): continue
    cov0 = covered(f)
    pln, pg = after(f, pc); cln, cg = after(f, cc)
    ph = heights(pg); chh = heights(cg)
    tall = range(0, 5) if hi == 'L' else range(5, 10)
    occ.append(dict(habit='P4', player=USER, session=s, id=p['id'], lock=p['lock'], regret=reg,
        misdrop_shaped=m, verified=p['verified'],
        player_move=dict(piece=pl['piece'], cells=[list(c) for c in sorted(pc)], hold_used=phold, lines=pl['lines']),
        cc_move=dict(piece=g['pick']['piece'], cells=[list(c) for c in sorted(cc)], hold_used=bool(g['pick']['hold']), lines=cln),
        detail=dict(tall_half='left (cols 0-4)' if hi == 'L' else 'right (cols 5-9)',
            half_mean_heights=dict(left=round(L, 2), right=round(R, 2)), lopsidedness_rows=round(abs(d), 2),
            heights=h0, max_height=mh, garbage_rows=ngr, incoming=p['incoming'],
            player_centroid_x=sum(x for x, _ in pc) / 4, cc_centroid_x=sum(x for x, _ in cc) / 4,
            player_cols=sorted({x for x, _ in pc}), cc_cols=sorted({x for x, _ in cc}),
            player_kind=pk, cc_kind=ck, player_lines=pl['lines'], cc_lines=cln,
            player_rank_in_cc_list=g['player'].get('rank'),
            tall_half_mean_after_player=round(sum(ph[c] for c in tall) / 5, 2),
            tall_half_mean_after_cc=round(sum(chh[c] for c in tall) / 5, 2),
            max_height_after_player=max(ph), max_height_after_cc=max(chh),
            covered_cells_created_player=covered(pg) - cov0 + 0 if pln == 0 else None,
            covered_cells_created_cc=covered(cg) - cov0 if cln == 0 else None,
            current=p['current'], hold=p['hold'], next=p['next'][:3],
            piece_time_frames=pl.get('pieceTime'), keys=pl.get('keys'))))
occ.sort(key=lambda o: (o['session'], o['id']))
with open(H + '/P4.occ.jsonl', 'w') as fh:
    for o in occ: fh.write(json.dumps(o) + '\n')
def pct(a, b): return round(100 * a / b, 3) if b else None
def row(label, D):
    r = D['regs']
    return dict(session=label, eligible=D['n'], player_rate_pct=pct(D['pl'], D['n']), cc_rate_pct=pct(D['cc'], D['n']),
        gap_pp=pct(D['pl'] - D['cc'], D['n']), occurrences=D['occ'], reverse_cc_tall_player_not=D['rev'],
        occurrences_misdrop_shaped=D['md'],
        regret_mean=round(st.mean(r), 1) if r else None, regret_median=st.median(r) if r else None,
        regret_ge600=sum(x >= 600 for x in r),
        regret_not_misdrop_mean=round(st.mean(D['regs_nomd']), 1) if D['regs_nomd'] else None,
        excl_misdrop_shaped=dict(eligible=D['n_x'], player_rate_pct=pct(D['pl_x'], D['n_x']),
            cc_rate_pct=pct(D['cc_x'], D['n_x']), gap_pp=pct(D['pl_x'] - D['cc_x'], D['n_x'])))
nights = [row(s, per[s]) for s in sorted(per)]
T = dict(n=0, pl=0, cc=0, occ=0, rev=0, md=0, regs=[], regs_nomd=[], n_x=0, pl_x=0, cc_x=0)
for D in per.values():
    for k in T: T[k] += D[k]
pooled = row('pooled', T)
out = dict(habit='P4', player=USER,
    definition=('Eligible (skeptic S1b, verify-discovery-D2-stats.py): graded pinglamb positions (mid.jsonl sample = verified '
        'locks >= 21, every 3rd lock; cc seed-0 grade with pick and complete duel) where the board is lopsided (mean height of '
        'columns 0-4 and of columns 5-9 differ by >= 2 rows), the tallest column is 10-13 rows, >= 4 rows contain garbage, '
        'neither the player\'s move nor Cold Clear\'s pick is a T-spin or quad, the player did not clear lines with a spin, and '
        'the player and Cold Clear made the same hold choice. player_rate = share of eligible positions where the player\'s '
        'piece centroid lies on the taller half; cc_rate = the same for Cold Clear\'s pick at the identical position (board, '
        'queue, hold, garbage); gap_pp = player - cc. Occurrence = player on the taller half and Cold Clear not. '
        'misdrop_shaped = skeptic md(): cc pick or its top-3 is the player\'s shape shifted one column, or another shape '
        'within 1 column (min x) and 1 row (bottom). excl_misdrop_shaped drops those positions and recomputes both rates. '
        'regret = duel.cc - duel.player (20k-node duel).'),
    nights=nights, pooled=pooled)
json.dump(out, open(H + '/P4.nights.json', 'w'), indent=1)
print(json.dumps(pooled))
for n in nights: print(n['session'], n['eligible'], n['player_rate_pct'], n['cc_rate_pct'], n['gap_pp'], n['occurrences'], n['occurrences_misdrop_shaped'], n['regret_mean'], n['regret_median'])
