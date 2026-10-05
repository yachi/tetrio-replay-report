# Habit Y1 (yachi): one-column-off placement that leaves a hole, on a 6+ row stack.
# Detector = the misdrop skeptic's H-MISDROP selection (verify-holes-H-MISDROP-misdrop.py, n=410 for
# yachi at all heights), reusing holes_build.py's hole_delta / misdrop / shift_clean exactly, then
# narrowed per FINDINGS yachi #1 to start-of-move max height >= 6 ("the cost exists only when the stack
# is 6+ rows").
import json, pickle, os, sys, collections, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); SC = os.path.dirname(H); C = SC + '/../corpus/'
sys.argv = [sys.argv[0]]
# import helpers from holes_build without running its build (it runs at import) -> exec the defs only
src = open(SC + '/holes_build.py').read().split('\nM = [json.loads')[0]
ns = {'__file__': SC + '/holes_build.py'}; exec(src, ns)
hole_delta, misdrop, shift_clean, heights = ns['hole_delta'], ns['misdrop'], ns['shift_clean'], ns['heights']

USER = 'yachi'; MINH = 6
rows = pickle.load(open(SC + '/holes_rows.pkl', 'rb'))
isMD = lambda r: bool(r['md']) or bool(r['shiftclean'])
SEL = lambda r: r['pd'][0] > 0 and r['cd'][0] <= 0 and isMD(r)   # skeptic's SEL, verbatim

# sanity: skeptic pooled (all heights) must reproduce 410 / 25348
A_all = [r for r in rows if r['user'] == USER]
n_all_sel = sum(SEL(r) for r in A_all)
print('reproduce skeptic all-heights:', n_all_sel, '/', len(A_all))

need = {r['id'] for r in A_all if r['maxh'] >= MINH}
MID, G = {}, {}
for l in open(C + 'mid.jsonl'):
    p = json.loads(l)
    if p['id'] in need: MID[p['id']] = p
for l in open(C + 'grade.jsonl'):
    g = json.loads(l)
    if g['id'] in need: G[g['id']] = g
S1 = {}
for l in open(C + 'grade-s1.jsonl'):
    g = json.loads(l)
    if g['id'] in need and 'pick' in g: S1[g['id']] = g['pick']
SUB = {json.loads(l)['id'] for l in open(C + 'sub4000.jsonl')}
CCN, CCP = {}, {}   # cost of cc's seed-1 pick against its seed-0 pick (grade-s1-ccpick)
# grade-s1-ccpick grades the SEED-0 pick as the "player" move under seed 1, so its duel.cc is the seed-1
# pick's value and duel.player the seed-0 pick's. Here the seed-1 pick is the hole move and the seed-0 pick
# the clean one, so the hole move's cost is duel.player - duel.cc (the opposite sign to P1/Y4/P2, where the
# seed-0 pick is the bad move). CCP keeps that file's seed-1 pick so an event is only valued when it is the
# same move as the seed-1 hole move found in grade-s1 (the two seed-1 searches do not always agree).
for l in open(C + 'grade-s1-ccpick.jsonl'):
    g = json.loads(l)
    if g.get('duel') and g['duel']['cc'] is not None and g['duel']['player'] is not None:
        CCN[g['id']] = g['duel']['player'] - g['duel']['cc']
        CCP[g['id']] = sorted(map(tuple, g['pick']['cells'])) if g.get('pick') else None

def cc_mirror(p, g):
    """Same rule applied to cc's own (seed-0) pick: it makes covered cells, a clean alternative exists among
    cc's other top-5 candidates, and the pick is a 1-column shift / rotation-neighbour of one of cc's
    next three candidates (same piece), or its own shape one column over is clean."""
    f = p['field']; pk = g['pick']; pc = [tuple(c) for c in pk['cells']]
    if hole_delta(f, pc)[0] <= 0: return False
    alts = g['top'][1:5]
    if not any(hole_delta(f, [tuple(c) for c in t['cells']])[0] <= 0 for t in alts): return False
    return bool(misdrop(pk['piece'], pc, g['top'][1:4])) or bool(shift_clean(f, pc))

CCPF = {}   # grade-s1-ccpick's full seed-1 pick (piece + cells), for the second seed-1 source
for l in open(C + 'grade-s1-ccpick.jsonl'):
    g = json.loads(l)
    if g['id'] in need and g.get('pick'): CCPF[g['id']] = g['pick']

def seed1_lookalike_alt(r, p):
    """the same bot-noise rule with the OTHER seed-1 search's pick (grade-s1-ccpick, a separate seed-1 search of the same
    position); one count is one noisy draw, so the page shows both."""
    s = CCPF.get(r['id']); g = G[r['id']]
    if s is None: return None
    sc = [tuple(c) for c in s['cells']]
    return hole_delta(p['field'], sc)[0] > 0 and r['cd'][0] <= 0 and bool(misdrop(s['piece'], sc, [g['pick']] + g['top'][:3]))

def seed1_lookalike(r):
    """skeptic's bot-noise rule (verify-holes-H-MISDROP-misdrop.py): seed-0 pick clean, seed-1 pick makes
    covered cells and is a shift/rot of seed-0's pick or top-3."""
    s = S1.get(r['id']); g = G[r['id']]
    if s is None or 's1' not in r['extra'] or r['id'] not in CCN: return None
    return r['extra']['s1'][0] > 0 and r['cd'][0] <= 0 and bool(misdrop(s['piece'], [tuple(c) for c in s['cells']], [g['pick']] + g['top'][:3]))

E = [r for r in A_all if r['maxh'] >= MINH]
occ = []; per = collections.defaultdict(lambda: dict(n=0, pl=0, cc=0, nsub=0, plsub=0, s1=0, s1unval=0, nalt=0, s1alt=0, regs=[], s1regs=[], plsubregs=[]))
for r in E:
    p = MID[r['id']]; g = G[r['id']]; d = per[r['sess']]
    d['n'] += 1
    ccm = cc_mirror(p, g); d['cc'] += ccm
    if r['id'] in SUB:
        lk = seed1_lookalike(r)
        if lk is not None:
            d['nsub'] += 1
            if lk:
                d['s1'] += 1
                if CCP.get(r['id']) == sorted(map(tuple, S1[r['id']]['cells'])): d['s1regs'].append(CCN[r['id']])
                else: d['s1unval'] += 1
            if SEL(r) and r['md']: d['plsub'] += 1; d['plsubregs'].append(r['reg'])
            la = seed1_lookalike_alt(r, p)
            if la is not None: d['nalt'] += 1; d['s1alt'] += la
    if not SEL(r): continue
    d['pl'] += 1; d['regs'].append(r['reg'])
    f = p['field']; pl = p['played']; pk = g['pick']
    pcells = [tuple(c) for c in pl['cells']]; ccells = [tuple(c) for c in pk['cells']]
    sub = r['md'] or 'shiftclean'
    ps = ns['norm'](pcells); cs = ns['norm'](ccells)
    occ.append(dict(habit='Y1', player=USER, session=r['sess'], id=r['id'], lock=r['lock'], regret=r['reg'],
        misdrop_shaped=True, verified=p['verified'],
        player_move=dict(piece=pl['piece'], cells=[list(c) for c in pcells], hold_used=pl['piece'] != p['current'], lines=pl['lines']),
        cc_move=dict(piece=pk['piece'], cells=[list(c) for c in ccells], hold_used=bool(pk['hold']), lines=r['cd'][4]),
        detail=dict(subtype=sub,                     # shift = cc's pick (or a top-3 candidate) moved one column; rot = rotation neighbour; shiftclean = own shape one column over is clean
            covered_cells_created=r['pd'][0], sealed_created=r['pd'][3], overhang_created=r['pd'][2],
            cells_left_under_piece=r['pd'][1], cc_covered_delta=r['cd'][0],
            player_cols=sorted({x for x, y in pcells}), cc_cols=sorted({x for x, y in ccells}),
            same_piece_as_cc=pl['piece'] == pk['piece'], same_shape_as_cc=ps[0] == cs[0] and pl['piece'] == pk['piece'],
            col_offset_vs_cc=(ps[1] - cs[1]) if pl['piece'] == pk['piece'] else None,
            max_height=r['maxh'], garbage_rows=r['garb'], covered_cells_before=r['holes0'], incoming=r['inc'],
            player_lines=pl['lines'], cc_lines=r['cd'][4], piece_time_frames=r['pt'], keys=r['keys'])))
occ.sort(key=lambda o: (o['session'], o['id']))
with open(H + '/Y1.occ.jsonl', 'w') as fh:
    for o in occ: fh.write(json.dumps(o) + '\n')

def mm(v): return (round(st.mean(v), 1) if v else None), (st.median(v) if v else None)
def row(label, d):
    rg = d['regs']; n = d['n']; ns_ = d['nsub']
    return dict(session=label, eligible=n, occurrences=d['pl'],
        player_rate_per100=round(100 * d['pl'] / n, 3) if n else None,
        regret_mean=mm(rg)[0], regret_median=mm(rg)[1], regret_ge600=sum(x >= 600 for x in rg),
        # Cold Clear on the SAME positions: the skeptic's rule, only computable where a second cc pick exists (sub4000)
        cc_same_positions=dict(eligible=ns_, cc_count=d['s1'], player_count=d['plsub'],
            cc_rate_per100=round(100 * d['s1'] / ns_, 3) if ns_ else None,
            player_rate_per100=round(100 * d['plsub'] / ns_, 3) if ns_ else None,
            gap_per100=round(100 * (d['plsub'] - d['s1']) / ns_, 3) if ns_ else None,
            cc_regret_mean=mm(d['s1regs'])[0], cc_regret_median=mm(d['s1regs'])[1], cc_regret_n=len(d['s1regs']), cc_events_not_valued=d['s1unval'],
            player_regret_mean=mm(d['plsubregs'])[0], player_regret_median=mm(d['plsubregs'])[1],
            cc_alt_seed1=dict(source='grade-s1-ccpick.jsonl', eligible=d['nalt'], cc_count=d['s1alt'],
                              cc_rate_per100=round(100 * d['s1alt'] / d['nalt'], 3) if d['nalt'] else None)),
        # NOT comparable to the player rate (looser condition, see notes): cc's own seed-0 pick vs its other top-5 candidates
        cc_top5_mirror=dict(count=d['cc'], rate_per100=round(100 * d['cc'] / n, 3) if n else None))
nights = [row(s, per[s]) for s in sorted(per)]
P = dict(n=0, pl=0, cc=0, nsub=0, plsub=0, s1=0, s1unval=0, nalt=0, s1alt=0, regs=[], s1regs=[], plsubregs=[])
for d in per.values():
    for k in P: P[k] = P[k] + d[k]
pooled = row('pooled', P)
out = dict(habit='Y1', player=USER,
    definition=('Eligible: every graded yachi position (mid.jsonl sample = verified locks >=21, every 3rd; cc grade with a duel) '
        'whose max column height before the move is >= 6. Occurrence (skeptic H-MISDROP SEL, verify-holes-H-MISDROP-misdrop.py, '
        'using holes_build.py hole_delta/misdrop/shift_clean): the player\'s move increases covered (empty-under-filled) cells after '
        'line clears, cc\'s seed-0 pick does not, and the move is misdrop-shaped: same piece as cc\'s pick or one of its top-3 '
        'candidates and either the same orientation one column over (shift) or a different orientation within one column (rot), or '
        'its own shape hard-dropped one column left/right would not have increased covered cells (shiftclean). Player rate = '
        'occurrences / eligible x100; regret = duel.cc - duel.player of the occurrences. '
        'Cold Clear rate on the same positions (cc_same_positions) = the skeptic\'s bot-noise rule: on the positions that also have '
        'a seed-1 cc grade (sub4000 subsample, and graded cc-vs-cc in grade-s1-ccpick), Cold Clear\'s seed-1 pick makes covered cells '
        'where the seed-0 pick is clean and is a shift/rot of the seed-0 pick or its top-3; compared with the player\'s shift/rot '
        'occurrences (geometry rule only, shiftclean-only excluded, as the skeptic did) on the same ids; cc cost there = the seed-0 (clean) '
        'pick\'s duel value minus the seed-1 (hole) pick\'s, from grade-s1-ccpick (duel.player - duel.cc in that file, which grades the '
        'seed-0 pick as the "player" move under seed 1), averaged only over the events whose grade-s1-ccpick seed-1 pick is the same '
        'move as the grade-s1 hole move (cc_regret_n; cc_events_not_valued counts the rest). gap = player - cc per 100 on that subsample. cc_top5_mirror is a looser '
        'rule on cc\'s seed-0 pick (hole while any of its other top-5 candidates is clean, geometry vs its own next 3) and is NOT '
        'comparable to the player rate.'),
    min_height=MINH, nights=nights, pooled=pooled,
    reproduce=dict(all_heights_sel=n_all_sel, all_heights_graded=len(A_all)))
json.dump(out, open(H + '/Y1.nights.json', 'w'), indent=1)
print(json.dumps(pooled))
for n in nights: print(n['session'], n['eligible'], n['occurrences'], n['player_rate_per100'], n['regret_mean'], n['regret_median'], n['cc_same_positions'])
