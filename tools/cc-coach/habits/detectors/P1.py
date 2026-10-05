# Habit P1 (pinglamb): hole placements on 6+ row stacks, one-column-off AND otherwise.
# Source: FINDINGS.md pinglamb #1 + verify-holes-H-MISDROP-{stats,misdrop}.py.
# Narrowed definition (FINDINGS): "same detector as yachi #1. For pinglamb the misdrop shape adds nothing:
# his non-misdrop-shaped hole moves cost about the same (+139). So the habit is 'hole moves under pressure',
# not specifically one-column-off moves" and "absent at 0-5 rows". Hence:
#   occurrence = player's move increases covered cells (post-clear) AND cc's seed-0 pick does not   [the
#   skeptics' "hole-not-cc" selection, before the misdrop-shape filter], at max height >= 6.
# The misdrop-shape filter (H-MISDROP SEL: shift / rot of cc pick or top-3, or own shape one column over is
# clean) is kept as the boolean misdrop_shaped, and MD-only rates are reported beside the main ones.
# Geometry helpers = holes_build.py (as in Y1.py), rows = holes_rows.pkl.
import json, pickle, os, sys, collections, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); SC = os.path.dirname(H); C = SC + '/../corpus/'
src = open(SC + '/holes_build.py').read().split('\nM = [json.loads')[0]
ns = {'__file__': SC + '/holes_build.py'}; exec(src, ns)
hole_delta, misdrop, shift_clean = ns['hole_delta'], ns['misdrop'], ns['shift_clean']

USER = 'pinglamb'; MINH = 6
rows = pickle.load(open(SC + '/holes_rows.pkl', 'rb'))
isMD = lambda r: bool(r['md']) or bool(r['shiftclean'])
HOLE = lambda r: r['pd'][0] > 0 and r['cd'][0] <= 0          # hole-not-cc
SELMD = lambda r: HOLE(r) and isMD(r)                         # misdrop skeptic's SEL, verbatim

A_all = [r for r in rows if r['user'] == USER]
rep = dict(all_heights_graded=len(A_all), all_heights_hole_not_cc=sum(HOLE(r) for r in A_all),
           all_heights_md_sel=sum(SELMD(r) for r in A_all),
           h6_hole_not_cc=sum(HOLE(r) and r['maxh'] >= MINH for r in A_all),
           h6_md_sel=sum(SELMD(r) and r['maxh'] >= MINH for r in A_all),
           h6_eligible=sum(r['maxh'] >= MINH for r in A_all))
print('reproduce:', rep)

need = {r['id'] for r in A_all if r['maxh'] >= MINH}
MID, G = {}, {}
for l in open(C + 'mid.jsonl'):
    p = json.loads(l)
    if p['id'] in need: MID[p['id']] = p
for l in open(C + 'grade.jsonl'):
    g = json.loads(l)
    if g['id'] in need: G[g['id']] = g
# cc-vs-cc (stats skeptic's noise build): sub4000-ccpick.jsonl = the position with `played` replaced by the seed-0
# cc pick, graded by grade-s1-ccpick.jsonl (COACH_SEED=1). "player" = seed-0 pick, "cc" = that grade's seed-1 pick,
# regret = duel.cc - duel.player there (seed-0 pick judged by seed 1).
S1P, CCN = {}, {}
for l in open(C + 'grade-s1-ccpick.jsonl'):
    g = json.loads(l)
    if g['id'] in need and 'pick' in g and g.get('duel') and g['duel']['cc'] is not None and g['duel']['player'] is not None:
        S1P[g['id']] = g['pick']; CCN[g['id']] = g['duel']['cc'] - g['duel']['player']

# Second seed-1 source: grade-s1.jsonl is a separate seed-1 search of the same sub4000 positions (the position with the
# player's own move, so its pick is the same kind of seed-1 pick). The two searches do not always pick the same move, so the
# Cold Clear count on the subsample is reported under both (cc_alt_seed1): one count is one noisy draw.
S1ALT = {}
for l in open(C + 'grade-s1.jsonl'):
    g = json.loads(l)
    if g['id'] in need and 'pick' in g: S1ALT[g['id']] = g['pick']

def cc_mirror(p, g):
    """looser rule on cc's own seed-0 pick: it makes covered cells while one of its other top-5 candidates is clean."""
    f = p['field']; pc = [tuple(c) for c in g['pick']['cells']]
    if hole_delta(f, pc)[0] <= 0: return False
    return any(hole_delta(f, [tuple(c) for c in t['cells']])[0] <= 0 for t in g['top'][1:5])

E = [r for r in A_all if r['maxh'] >= MINH]
K = ('n', 'pl', 'md', 'cc', 'nsub', 'plsub', 's1', 'nalt', 's1alt', 'regs', 'mdregs', 'nmdregs', 's1regs', 'plsubregs')
def blank(): return {k: ([] if k.endswith('regs') else 0) for k in K}
per = collections.defaultdict(blank); occ = []
for r in E:
    p = MID[r['id']]; g = G[r['id']]; d = per[r['sess']]
    d['n'] += 1
    d['cc'] += cc_mirror(p, g)
    # Cold Clear on the same positions: stats skeptic's noise rule -- the seed-0 cc pick makes covered cells where the
    # seed-1 pick (grade-s1-ccpick) does not; regret = seed-0 pick judged by seed 1
    if r['id'] in S1P:
        d['nsub'] += 1
        if r['cd'][0] > 0 and hole_delta(p['field'], [tuple(c) for c in S1P[r['id']]['cells']])[0] <= 0:
            d['s1'] += 1; d['s1regs'].append(CCN[r['id']])
        if HOLE(r): d['plsub'] += 1; d['plsubregs'].append(r['reg'])
        if r['id'] in S1ALT:   # same rule, the other seed-1 search's pick
            d['nalt'] += 1
            d['s1alt'] += r['cd'][0] > 0 and hole_delta(p['field'], [tuple(c) for c in S1ALT[r['id']]['cells']])[0] <= 0
    if not HOLE(r): continue
    md = isMD(r)
    d['pl'] += 1; d['regs'].append(r['reg'])
    if md: d['md'] += 1; d['mdregs'].append(r['reg'])
    else: d['nmdregs'].append(r['reg'])
    f = p['field']; pl = p['played']; pk = g['pick']
    pcells = [tuple(c) for c in pl['cells']]; ccells = [tuple(c) for c in pk['cells']]
    ps = ns['norm'](pcells); cs = ns['norm'](ccells)
    occ.append(dict(habit='P1', player=USER, session=r['sess'], id=r['id'], lock=r['lock'], regret=r['reg'],
        misdrop_shaped=md, verified=p['verified'],
        player_move=dict(piece=pl['piece'], cells=[list(c) for c in pcells], hold_used=pl['piece'] != p['current'], lines=pl['lines']),
        cc_move=dict(piece=pk['piece'], cells=[list(c) for c in ccells], hold_used=bool(pk['hold']), lines=r['cd'][4]),
        detail=dict(subtype=(r['md'] or ('shiftclean' if r['shiftclean'] else 'other')),
            covered_cells_created=r['pd'][0], sealed_created=r['pd'][3], overhang_created=r['pd'][2],
            cells_left_under_piece=r['pd'][1], cc_covered_delta=r['cd'][0],
            player_cols=sorted({x for x, y in pcells}), cc_cols=sorted({x for x, y in ccells}),
            same_piece_as_cc=pl['piece'] == pk['piece'], same_shape_as_cc=ps[0] == cs[0] and pl['piece'] == pk['piece'],
            col_offset_vs_cc=(ps[1] - cs[1]) if pl['piece'] == pk['piece'] else None,
            max_height=r['maxh'], garbage_rows=r['garb'], covered_cells_before=r['holes0'], incoming=r['inc'],
            player_lines=pl['lines'], cc_lines=r['cd'][4], piece_time_frames=r['pt'], keys=r['keys'])))
occ.sort(key=lambda o: (o['session'], o['id']))
with open(H + '/P1.occ.jsonl', 'w') as fh:
    for o in occ: fh.write(json.dumps(o) + '\n')

def mm(v): return (round(st.mean(v), 1) if v else None), (st.median(v) if v else None)
def pc(a, b): return round(100 * a / b, 3) if b else None
def row(label, d):
    n = d['n']; ns_ = d['nsub']
    return dict(session=label, eligible=n, occurrences=d['pl'], player_rate_per100=pc(d['pl'], n),
        regret_mean=mm(d['regs'])[0], regret_median=mm(d['regs'])[1], regret_ge600=sum(x >= 600 for x in d['regs']),
        misdrop_shaped=dict(count=d['md'], rate_per100=pc(d['md'], n), regret_mean=mm(d['mdregs'])[0], regret_median=mm(d['mdregs'])[1]),
        not_misdrop_shaped=dict(count=d['pl'] - d['md'], regret_mean=mm(d['nmdregs'])[0], regret_median=mm(d['nmdregs'])[1]),
        cc_same_positions=dict(eligible=ns_, cc_count=d['s1'], player_count=d['plsub'],
            cc_rate_per100=pc(d['s1'], ns_), player_rate_per100=pc(d['plsub'], ns_),
            gap_per100=round(100 * (d['plsub'] - d['s1']) / ns_, 3) if ns_ else None,
            cc_regret_mean=mm(d['s1regs'])[0], cc_regret_median=mm(d['s1regs'])[1],
            player_regret_mean=mm(d['plsubregs'])[0], player_regret_median=mm(d['plsubregs'])[1],
            cc_alt_seed1=dict(source='grade-s1.jsonl', eligible=d['nalt'], cc_count=d['s1alt'], cc_rate_per100=pc(d['s1alt'], d['nalt']))),
        cc_top5_mirror=dict(count=d['cc'], rate_per100=pc(d['cc'], n)))
nights = [row(s, per[s]) for s in sorted(per)]
P = blank()
for d in per.values():
    for k in P: P[k] = P[k] + d[k]
pooled = row('pooled', P)
out = dict(habit='P1', player=USER,
    definition=('Eligible: every graded pinglamb position (mid.jsonl sample = verified locks >=21, every 3rd; cc grade with a duel) '
        'whose max column height before the move is >= 6. Occurrence (the holes skeptics\' "hole-not-cc" selection, holes_build.py '
        'hole_delta): the player\'s move increases covered (empty cell with a filled cell above in its column) cells after line '
        'clears, and Cold Clear\'s seed-0 pick at the same position does not. Per FINDINGS pinglamb #1 the misdrop shape adds nothing '
        'for him, so both misdrop-shaped and other hole moves count; misdrop_shaped = H-MISDROP SEL (same piece as cc\'s pick or one '
        'of its top-3, same orientation one column over (shift) or other orientation within one column (rot), or its own shape '
        'hard-dropped one column left/right would not increase covered cells (shiftclean)). Player rate = occurrences / eligible x100; '
        'regret = duel.cc - duel.player. Cold Clear rate on the same positions (cc_same_positions) = the stats skeptic\'s noise rule: '
        'on eligible ids of the sub4000 subsample that have a cc-vs-cc grade (grade-s1-ccpick: position with the seed-0 cc pick '
        'as the played move, graded with COACH_SEED=1), Cold Clear\'s seed-0 pick increases covered cells where the seed-1 pick does '
        'not (cc judged by its own other seed, exactly as the player is judged by seed 0); player rate on the same ids by the '
        'occurrence rule; cc regret = duel.cc - duel.player of grade-s1-ccpick (seed-0 pick judged by seed 1). gap = player - cc per 100 on that subsample. cc_top5_mirror (cc seed-0 pick makes '
        'covered cells while one of its other top-5 candidates is clean) is a looser rule and NOT comparable to the player rate.'),
    min_height=MINH, nights=nights, pooled=pooled, reproduce=rep)
json.dump(out, open(H + '/P1.nights.json', 'w'), indent=1)
print(json.dumps(pooled))
for n in nights: print(n['session'], n['eligible'], n['occurrences'], n['player_rate_per100'], n['regret_mean'], n['regret_median'], n['misdrop_shaped']['count'], n['cc_same_positions'])
