# Habit P2 (pinglamb): sealing a hole when a clean placement exists, on garbage boards.
# Source: FINDINGS.md pinglamb #2 ("same detector as yachi #4") + verify-holes-H-DECISION-{misdrop,stats}.py.
# Surviving definition (misdrop skeptic, SEAL): r['pd'][3] > 0 and r['cd'][3] <= 0 and not isMD(r), over holes_rows.pkl
#   pd/cd = holes_build.hole_delta(field, cells) = (dcovered, under, doverhang, dSEALED, lines), post-clear;
#   SEALED = covered empty cell whose empty 4-connected component holds no uncovered empty cell (no tuck/spin reaches it)
#   isMD = misdrop geometry: shift/rot of cc pick or its top-3 (holes_build.misdrop) OR own shape one column over is
#          clean (shift_clean).
# Narrowing (FINDINGS pinglamb #2): "his covering cost appears only on boards with garbage (+149, against -15 with none)",
# practice "on a garbage board ...". Hence eligible = graded positions with >= 1 garbage row on the board.
# Occurrences written = player seals AND cc's seed-0 pick does not AND moves differ, INCLUDING misdrop-shaped ones
# (flagged misdrop_shaped); the habit count (skeptic's) is the non-misdrop-shaped subset.
import json, pickle, os, collections, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); SC = os.path.dirname(H); C = SC + '/../corpus/'
src = open(SC + '/holes_build.py').read().split('\nM = [json.loads')[0]
ns = {'__file__': SC + '/holes_build.py'}; exec(src, ns)
hole_delta, covered, misdrop, shift_clean = ns['hole_delta'], ns['covered'], ns['misdrop'], ns['shift_clean']

USER = 'pinglamb'
rows = pickle.load(open(SC + '/holes_rows.pkl', 'rb'))
isMD = lambda r: bool(r['md']) or bool(r['shiftclean'])
SEALX = lambda r: r['pd'][3] > 0 and r['cd'][3] <= 0 and not r['same']     # incl. misdrop-shaped
SEAL = lambda r: r['pd'][3] > 0 and r['cd'][3] <= 0 and not isMD(r)         # skeptic's SEAL, verbatim
GB = lambda r: r['garb'] > 0

A_all = [r for r in rows if r['user'] == USER]
rep = dict(all_boards_graded=len(A_all), all_boards_seal=sum(SEAL(r) for r in A_all),
           all_boards_seal_incl_md=sum(SEALX(r) for r in A_all),
           garbage_graded=sum(GB(r) for r in A_all), garbage_seal=sum(SEAL(r) and GB(r) for r in A_all),
           garbage_seal_incl_md=sum(SEALX(r) and GB(r) for r in A_all),
           no_garbage_seal=sum(SEAL(r) and not GB(r) for r in A_all))
print('reproduce:', rep)

E = [r for r in A_all if GB(r)]
need = {r['id'] for r in E}
MID, G = {}, {}
for l in open(C + 'mid.jsonl'):
    p = json.loads(l)
    if p['id'] in need: MID[p['id']] = p
for l in open(C + 'grade.jsonl'):
    g = json.loads(l)
    if g['id'] in need: G[g['id']] = g
S1P, CCN = {}, {}
for l in open(C + 'grade-s1-ccpick.jsonl'):
    g = json.loads(l)
    if g['id'] in need and 'pick' in g and g.get('duel') and g['duel']['cc'] is not None and g['duel']['player'] is not None:
        S1P[g['id']] = g; CCN[g['id']] = g['duel']['cc'] - g['duel']['player']

def reach(g):
    vis = set(); stk = [(c, 0) for c in range(10) if g[0][c] == '.']; vis.update(stk)
    while stk:
        x, y = stk.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < 10 and 0 <= ny < 40 and g[ny][nx] == '.' and (nx, ny) not in vis:
                vis.add((nx, ny)); stk.append((nx, ny))
    return vis
def newly_cut(f, cells):
    """PRE-clear board: empty cells reachable from the top before the move and not after (the cells this piece cut off).
    Coordinates are in the decision's field (row 0 = top)."""
    g0 = [list(r) for r in f]; g1 = [list(r) for r in f]
    for x, y in cells: g1[y][x] = '#'
    r0, r1 = reach(g0), reach(g1)
    return sorted((x, y) for (x, y) in r0 - r1 if g1[y][x] == '.')

K = ('n', 'plany', 'ccany', 'occ', 'md', 'nsub', 'plsub', 's1', 'regs', 'mdregs', 'occregs', 's1regs', 'plsubregs')
def blank(): return {k: ([] if k.endswith('regs') else 0) for k in K}
per = collections.defaultdict(blank); occ = []
for r in E:
    p = MID[r['id']]; g = G[r['id']]; d = per[r['sess']]; f = p['field']
    d['n'] += 1
    d['plany'] += r['pd'][3] > 0
    d['ccany'] += r['cd'][3] > 0
    if r['id'] in S1P:
        d['nsub'] += 1
        s1 = S1P[r['id']]; c0 = [tuple(c) for c in g['pick']['cells']]
        # the player side's misdrop rule applied to cc's seed-0 pick, judged against seed 1: a shift/rot of
        # the seed-1 pick or its top-3 (holes_build.misdrop), or its own shape one column over is clean
        cc_md = bool(misdrop(g['pick']['piece'], c0, [s1['pick']] + s1.get('top', [])[:3])) or bool(shift_clean(f, c0))
        if r['cd'][3] > 0 and hole_delta(f, [tuple(c) for c in s1['pick']['cells']])[3] <= 0 and not cc_md:
            d['s1'] += 1; d['s1regs'].append(CCN[r['id']])
        if SEAL(r): d['plsub'] += 1; d['plsubregs'].append(r['reg'])
    if not SEALX(r): continue
    md = isMD(r)
    d['regs'].append(r['reg'])
    if md: d['md'] += 1; d['mdregs'].append(r['reg'])
    else: d['occ'] += 1; d['occregs'].append(r['reg'])
    pl = p['played']; pk = g['pick']
    pcells = [tuple(c) for c in pl['cells']]; ccells = [tuple(c) for c in pk['cells']]
    cut = newly_cut(f, pcells)
    occ.append(dict(habit='P2', player=USER, session=r['sess'], id=r['id'], lock=r['lock'], regret=r['reg'],
        misdrop_shaped=md, verified=p['verified'],
        player_move=dict(piece=pl['piece'], cells=[list(c) for c in pcells], hold_used=pl['piece'] != p['current'], lines=pl['lines']),
        cc_move=dict(piece=pk['piece'], cells=[list(c) for c in ccells], hold_used=bool(pk['hold']), lines=r['cd'][4]),
        detail=dict(misdrop_subtype=(r['md'] or ('shiftclean' if r['shiftclean'] else None)),
            sealed_cells_created=r['pd'][3], covered_cells_created=r['pd'][0], overhang_cells_created=r['pd'][2],
            cc_sealed_delta=r['cd'][3], cc_covered_delta=r['cd'][0],
            cut_off_cells_preclear=[list(c) for c in cut],
            cut_off_cells_in_garbage_rows=sum(1 for x, y in cut if 'G' in f[y]),
            player_cols=sorted({x for x, y in pcells}), cc_cols=sorted({x for x, y in ccells}),
            current=p['current'], hold=p['hold'], next0=(p['next'][0] if p['next'] else None),
            clean_hard_drops_current=r['fits_cur'], clean_hard_drops_hold_or_next=r['fits_alt'],
            max_height=r['maxh'], garbage_rows=r['garb'], covered_cells_before=r['holes0'], incoming=r['inc'],
            player_lines=pl['lines'], cc_lines=r['cd'][4], piece_time_frames=r['pt'], keys=r['keys'])))
occ.sort(key=lambda o: (o['session'], o['id']))
with open(H + '/P2.occ.jsonl', 'w') as fh:
    for o in occ: fh.write(json.dumps(o) + '\n')

def mm(v): return (round(st.mean(v), 1) if v else None), (st.median(v) if v else None)
def pc(a, b): return round(100 * a / b, 3) if b else None
def row(label, d):
    n = d['n']; ns_ = d['nsub']
    return dict(session=label, eligible=n,
        player_rate_per100=pc(d['occ'], n), occurrences=d['occ'],
        regret_mean=mm(d['occregs'])[0], regret_median=mm(d['occregs'])[1], regret_ge600=sum(x >= 600 for x in d['occregs']),
        any_seal=dict(player_count=d['plany'], player_rate_per100=pc(d['plany'], n), cc_count=d['ccany'],
                      cc_rate_per100=pc(d['ccany'], n), gap_per100=round(100 * (d['plany'] - d['ccany']) / n, 3) if n else None),
        misdrop_shaped=dict(count=d['md'], rate_per100=pc(d['md'], n), regret_mean=mm(d['mdregs'])[0], regret_median=mm(d['mdregs'])[1]),
        all_occurrence_lines=dict(count=d['occ'] + d['md'], regret_mean=mm(d['regs'])[0], regret_median=mm(d['regs'])[1]),
        cc_same_positions=dict(eligible=ns_, cc_count=d['s1'], player_count=d['plsub'],
            cc_rate_per100=pc(d['s1'], ns_), player_rate_per100=pc(d['plsub'], ns_),
            gap_per100=round(100 * (d['plsub'] - d['s1']) / ns_, 3) if ns_ else None,
            cc_regret_mean=mm(d['s1regs'])[0], cc_regret_median=mm(d['s1regs'])[1],
            player_regret_mean=mm(d['plsubregs'])[0], player_regret_median=mm(d['plsubregs'])[1]))
nights = [row(s, per[s]) for s in sorted(per)]
P = blank()
for d in per.values():
    for k in P: P[k] = P[k] + d[k]
pooled = row('pooled', P)
out = dict(habit='P2', player=USER,
    definition=('Eligible: every graded pinglamb position (mid.jsonl sample = verified locks >=21, every 3rd; cc grade with a duel) '
        'with at least one garbage row on the board before the move (FINDINGS pinglamb #2: the cost exists only on garbage boards). '
        'Habit occurrence = the H-DECISION misdrop skeptic\'s SEAL selection, verbatim (holes_build.hole_delta, post-clear): the '
        'player\'s move increases SEALED cells (covered empty cells whose empty 4-connected region contains no uncovered empty cell, '
        'i.e. no tuck/spin can reach them) while Cold Clear\'s seed-0 pick at the same position does not increase sealed cells (a clean '
        'placement existed), and the move is not misdrop-shaped (same piece as cc\'s pick or its top-3 shifted one column or rotated '
        'within one column, or the player\'s own shape one column over would add no covered cell). player_rate_per100 = occurrences / '
        'eligible x100. Misdrop-shaped seals are written to P2.occ.jsonl too (misdrop_shaped=true) but are not counted in occurrences. '
        'Cold Clear on the same positions, two views: any_seal = share of eligible positions where the player\'s move seals (any shape) '
        'vs where cc\'s seed-0 pick seals; cc_same_positions = the cc-vs-cc noise rule on the eligible ids of sub4000 that have a '
        'grade-s1-ccpick grade: cc\'s seed-0 pick seals where its seed-1 pick does not and is not misdrop-shaped by the player side\'s rule against the '
        'seed-1 pick and its top-3 (cc judged by its own other seed as the player is judged by seed 0), against the player\'s occurrence rule on the same ids; gap = player - cc per 100. regret = duel.cc - duel.player.'),
    nights=nights, pooled=pooled, reproduce=rep)
json.dump(out, open(H + '/P2.nights.json', 'w'), indent=1)
print(json.dumps(pooled))
for n in nights: print(n['session'], n['eligible'], n['occurrences'], n['player_rate_per100'], n['regret_mean'], n['regret_median'], n['any_seal'], n['misdrop_shaped']['count'], n['cc_same_positions']['cc_count'], n['cc_same_positions']['player_count'], n['cc_same_positions']['eligible'])
