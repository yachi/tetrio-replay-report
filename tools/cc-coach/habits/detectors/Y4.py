# Habit Y4 (yachi): sealing a hole when a clean placement exists.
# Detector = the stats skeptic's SEALS selection, verbatim (verify-holes-H-DECISION-stats.py, own board code,
# n=297 for yachi): H(r,1) = player's move increases SEALED cells (empty cells not 4-connected through empties
# to the top row, measured after line clears), cc's seed-0 pick does not, the moves differ, and the move is
# NOT misdrop-shaped (md_geo shift/rot vs cc pick + top-3, nor shift_clean). FINDINGS yachi #4 keeps only this
# sealing subtype ("Do not generalize to covering").
import json, os, sys, collections, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); SC = os.path.dirname(H); C = SC + '/../corpus'
src = open(SC + '/verify-holes-H-DECISION-stats.py').read().split("\ndef load(fn):")[0]
ns = {}; exec(src, ns)
apply, stats, heights, delta, md_geo, shift_clean, clean_fit, norm = (ns[k] for k in
    ('apply', 'stats', 'heights', 'delta', 'md_geo', 'shift_clean', 'clean_fit', 'norm'))
USER = 'yachi'

def load(fn):
    d = {}
    for l in open(C + '/' + fn):
        g = json.loads(l); d[g['id']] = g
    return d
G = load('grade.jsonl'); S1C = load('grade-s1-ccpick.jsonl')

def sealed_set(g):
    vis = set(); stck = [(c, 0) for c in range(10) if g[0][c] == '.']; vis.update(stck)
    while stck:
        x, y = stck.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < 10 and 0 <= ny < 40 and g[ny][nx] == '.' and (nx, ny) not in vis:
                vis.add((nx, ny)); stck.append((nx, ny))
    return {(x, y) for y in range(40) for x in range(10) if g[y][x] == '.' and (x, y) not in vis}

def lines_of(field, cells):
    g = [list(r) for r in field]
    for x, y in cells: g[y][x] = '#'
    return sum(1 for r in g if '.' not in r)

per = collections.defaultdict(lambda: dict(n=0, occ=0, plseal=0, ccseal=0, cconly=0, plall=0, regs=[], nsub=0, hsub=0, s1=0, hsubregs=[], s1regs=[]))
occ = []; seal_all = 0
for l in open(C + '/mid.jsonl'):
    p = json.loads(l)
    if p['user'] != USER: continue
    g = G.get(p['id'])
    if not g or 'error' in g or not g.get('duel') or g['duel']['player'] is None or g['duel']['cc'] is None: continue
    d = per[p['session']]; d['n'] += 1
    f = p['field']; base = stats(f); pl = p['played']
    pc = [tuple(c) for c in pl['cells']]; cc = [tuple(c) for c in g['pick']['cells']]
    pd = delta(f, base, pc); cd = delta(f, base, cc); same = set(pc) == set(cc)
    reg = g['duel']['cc'] - g['duel']['player']
    md = sc = None
    if (pd[0] > 0 or pd[1] > 0) and not same:
        md = md_geo(pl['piece'], pc, [g['pick']] + g['top'][:3]); sc = shift_clean(f, base, pc)
    isMD = bool(md) or bool(sc)
    if pd[1] > 0: seal_all += 1; d['plall'] += 1
    if cd[1] > 0 and pd[1] <= 0 and not same: d['cconly'] += 1
    if pd[1] > 0 and not isMD: d['plseal'] += 1
    if cd[1] > 0: d['ccseal'] += 1
    hit = pd[1] > 0 and cd[1] <= 0 and not same and not isMD
    # skeptic noise rule (sub4000 ids with a seed-1 cc pick graded cc-vs-cc)
    s = S1C.get(p['id'])
    if s and s.get('duel') and s['duel']['player'] is not None and s['duel']['cc'] is not None:
        d['nsub'] += 1
        s1d = delta(f, base, [tuple(c) for c in s['pick']['cells']])
        # n1: "player" = seed-0 pick (delta cd), "cc" = seed-1 pick; same SEALS rule applied cc-vs-cc
        # cc side filtered exactly as the player side is: not md_geo against the seed-1 pick/top-3, and not
        # shift_clean (the seed-0 pick's own shape one column over would be clean)
        if cd[1] > 0 and s1d[1] <= 0 and not md_geo(g['pick']['piece'], cc, [s['pick']] + s['top'][:3]) and not shift_clean(f, base, cc):
            d['s1'] += 1; d['s1regs'].append(s['duel']['cc'] - s['duel']['player'])
        if hit: d['hsub'] += 1; d['hsubregs'].append(reg)
    if not hit: continue
    d['occ'] += 1; d['regs'].append(reg)
    post = apply(f, pc)
    gfull = [list(r) for r in f]
    for x, y in pc: gfull[y][x] = '#'
    clr = [y for y in range(40) if '.' not in gfull[y]]
    pre_mapped = {(x, y + sum(1 for c in clr if c > y)) for x, y in sealed_set(apply(f, [])) if y not in clr}
    sealed_new = sorted(sealed_set(post) - pre_mapped)
    hold_used = pl['piece'] != p['current']
    other = p['hold'] if not hold_used else p['current']
    occ.append(dict(habit='Y4', player=USER, session=p['session'], id=p['id'], lock=p['lock'], regret=reg,
        misdrop_shaped=False, verified=p['verified'],
        player_move=dict(piece=pl['piece'], cells=[list(c) for c in pc], hold_used=hold_used, lines=pl['lines']),
        cc_move=dict(piece=g['pick']['piece'], cells=[list(c) for c in cc], hold_used=bool(g['pick']['hold']), lines=lines_of(f, cc)),
        detail=dict(sealed_cells_created=pd[1], covered_cells_created=pd[0],
            cc_sealed_delta=cd[1], cc_covered_delta=cd[0],
            sealed_cells_after=[list(c) for c in sealed_new],      # coordinates on the board AFTER the player's lock (rows 0..39, 39 = bottom)
            sealed_cols=sorted({x for x, y in sealed_new}),
            sealed_in_garbage_row=sum(1 for x, y in sealed_new if 'G' in post[y]),
            player_cols=sorted({x for x, y in pc}), cc_cols=sorted({x for x, y in cc}),
            same_piece_as_cc=pl['piece'] == g['pick']['piece'],
            clean_fit_current=clean_fit(f, base, p['current']),
            clean_fit_hold_or_next=clean_fit(f, base, p['hold'] or (p['next'][0] if p['next'] else None)),
            max_height=max(heights(f)), garbage_rows=sum(1 for row in f if 'G' in row),
            sealed_cells_before=base[1], covered_cells_before=base[0], incoming=p['incoming'],
            player_lines=pl['lines'], cc_lines=lines_of(f, cc),
            cc_pick_rank_of_player_move=next((i for i, t in enumerate(g['top']) if set(map(tuple, t['cells'])) == set(pc)), None),
            piece_time_frames=pl['pieceTime'], keys=pl['keys'])))
occ.sort(key=lambda o: (o['session'], o['lock'], o['id']))
with open(H + '/Y4.occ.jsonl', 'w') as fh:
    for o in occ: fh.write(json.dumps(o) + '\n')

def mm(v): return (round(st.mean(v), 1) if v else None), (st.median(v) if v else None)
def r3(x): return round(x, 3)
def row(label, d):
    n = d['n']; ns_ = d['nsub']
    return dict(session=label, eligible=n, occurrences=d['occ'],
        occurrence_rate_per100=r3(100 * d['occ'] / n) if n else None,
        player_rate_per100=r3(100 * d['plseal'] / n) if n else None,
        cc_rate_per100=r3(100 * d['ccseal'] / n) if n else None,
        gap_per100=r3(100 * (d['plseal'] - d['ccseal']) / n) if n else None,
        player_seal_count=d['plseal'], cc_seal_count=d['ccseal'], player_seal_count_incl_misdrop_shaped=d['plall'],
        player_any_seal_rate_per100=r3(100 * d['plall'] / n) if n else None,
        cc_only_seal_count=d['cconly'], cc_only_rate_per100=r3(100 * d['cconly'] / n) if n else None,
        regret_mean=mm(d['regs'])[0], regret_median=mm(d['regs'])[1], regret_ge600=sum(x >= 600 for x in d['regs']),
        cc_vs_cc_noise=dict(eligible=ns_, player_count=d['hsub'], cc_count=d['s1'],
            player_rate_per100=r3(100 * d['hsub'] / ns_) if ns_ else None,
            cc_rate_per100=r3(100 * d['s1'] / ns_) if ns_ else None,
            gap_per100=r3(100 * (d['hsub'] - d['s1']) / ns_) if ns_ else None,
            player_regret_mean=mm(d['hsubregs'])[0], cc_regret_mean=mm(d['s1regs'])[0]))
nights = [row(s, per[s]) for s in sorted(per)]
P = {k: (0 if not isinstance(v, list) else []) for k, v in next(iter(per.values())).items()}
for d in per.values():
    for k in P: P[k] = P[k] + d[k]
pooled = row('pooled', P)
out = dict(habit='Y4', player=USER, title='Sealing a hole when a clean placement exists',
    definition=('Eligible: every graded yachi position (mid.jsonl sample, cc grade with a duel; 25348 pooled). '
        '"Seal" = the move increases the number of SEALED cells: empty cells not 4-connected through empty cells to the top row, '
        'counted on the board after line clears, so no tuck or spin can reach them. Occurrence (stats skeptic SEALS, '
        'verify-holes-H-DECISION-stats.py, verbatim board code): the player seals, Cold Clear\'s seed-0 pick at the same position '
        '(same queue, hold, garbage) does not, the two moves differ, and the move is NOT misdrop-shaped (not a one-column shift or '
        'rotation-neighbour of cc\'s pick/top-3 with the same piece, and its own shape one column over would not be clean). '
        'occurrence_rate_per100 = occurrences / eligible x100 (the skeptic\'s "n/100 graded"). player_rate_per100 = positions where '
        'the player makes a non-misdrop-shaped seal / eligible; cc_rate_per100 = positions where cc\'s own pick seals / eligible '
        '(same positions); gap = player - cc. cc_only = cc seals where the player\'s move does not seal (the mirror of an occurrence, no misdrop filter applies to cc). regret = duel.cc - duel.player (cc-coach, 20000 nodes, seed 0) over occurrences. '
        'cc_vs_cc_noise = the skeptic\'s bot-noise rule on the sub4000 ids: the same SEALS rule applied to cc seed 0 vs cc seed 1 '
        '(seed-0 pick seals, seed-1 pick does not, and the seed-0 pick is not misdrop-shaped by the player side\'s own two tests: '
        'not a shift/rot of the seed-1 pick or its top-3, and its own shape one column over would not be clean), regret from grade-s1-ccpick. '
        'player_any_seal_rate_per100 = positions where the player\'s move seals, any shape (misdrop-shaped included) / eligible: the '
        'like-for-like counterpart of cc_rate_per100.'),
    nights=nights, pooled=pooled, all_seals_including_misdrop_shaped=seal_all)
json.dump(out, open(H + '/Y4.nights.json', 'w'), indent=1)
print(json.dumps(pooled))
for n in nights: print(n['session'], n['eligible'], n['occurrences'], n['occurrence_rate_per100'], n['player_rate_per100'], n['cc_rate_per100'], n['gap_per100'], n['regret_mean'], n['regret_median'], n['cc_vs_cc_noise']['player_count'], n['cc_vs_cc_noise']['cc_count'])
