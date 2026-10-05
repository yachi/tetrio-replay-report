# Habit P3 (pinglamb): follow-up line clear to keep a short combo while the B2B chain is dead.
# Source: FINDINGS.md pinglamb #3 + verify-b2b-hold-combo-singles-pinglamb-{stats,misdrop}.py (+ .out).
# Surviving definition (misdrop skeptic, verbatim): rows = mid.jsonl positions with a cc grade carrying pick and a
#   complete duel (duel.cc, duel.player not None). Scenario (eligible) = combo >= 0 (a line was cleared by the previous
#   piece, combo counter live) AND b2b == -1 (no B2B chain). Player clears = played.lines > 0; cc clears = cc seed-0
#   pick kind in CLEAR. Rate gap = mean(player clears) - mean(cc clears) over the same positions.
#   Occurrence = player clears AND cc's pick does not ("player-only clear").
#   misdrop_shaped = the skeptic's strict geometry rule geo(): same piece as cc's pick or its top-3, either that exact
#   shape shifted one column, or its centroid within 1 column and 1 row of the player's (shift1 / rot/near).
#   Narrowing kept from FINDINGS: the reported gap is also given excluding misdrop-shaped player-only clears (rows
#   dropped), and the combo-specific control (same rule on b2b-dead positions with NO prior clear, combo == -1) per
#   night, since ~3pp of the gap is a general tendency to clear more.
import json, os, collections, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(os.path.dirname(H)) + '/corpus/'
USER = 'pinglamb'
CLEAR = {'single','double','triple','quad','tss','tsd','tst','mini_tss','mini_tsd','mini','pc'}
MID = {}
for l in open(C + 'mid.jsonl'):
    m = json.loads(l)
    if m['user'] == USER: MID[m['id']] = m
R = []
for l in open(C + 'grade.jsonl'):
    g = json.loads(l)
    if g['id'] not in MID or g.get('pick') is None or g.get('duel') is None or g['duel']['cc'] is None or g['duel']['player'] is None: continue
    R.append(g)
def heights(F): return [next((40 - r for r in range(40) if F[r][c] != '.'), 0) for c in range(10)]
def lines_after(F, cells):
    g = [list(r) for r in F]
    for x, y in cells: g[y][x] = '#'
    return sum(1 for r in g if '.' not in r)
def geo(pp, pc, cand):
    cx = sum(c[0] for c in pc) / 4; cy = sum(c[1] for c in pc) / 4
    for piece, cells in cand:
        if piece != pp or cells == pc: continue
        for dx in (-1, 1):
            if sorted((x + dx, y) for x, y in cells) == pc: return 'shift1'
        qx = sum(c[0] for c in cells) / 4; qy = sum(c[1] for c in cells) / 4
        if abs(qx - cx) <= 1 and abs(qy - cy) <= 1: return 'rot/near'
    return None
S1 = {}; 
for l in open(C + 'grade-s1.jsonl'):
    g = json.loads(l)
    if g['id'] in MID and g.get('pick'): S1[g['id']] = g

K = ('n', 'pl', 'cc', 'occ', 'md', 'n_x', 'pl_x', 'cc_x', 'n0', 'pl0', 'cc0', 'ns1', 'cc_s0', 'cc_s1', 'pl_s')
def blank():
    d = {k: 0 for k in K}; d['regs'] = []; d['occregs_nomd'] = []; d['mdregs'] = []; d['lines'] = collections.Counter(); return d
per = collections.defaultdict(blank); occ = []; kindcheck = collections.Counter()
for g in R:
    m = MID[g['id']]; p = m['played']; F = m['field']; s = m['session']; d = per[s]
    if m['b2b'] != -1: continue
    pk = g['pick']; PC = p['lines'] > 0; CCc = pk['kind'] in CLEAR
    if m['combo'] == -1:
        d['n0'] += 1; d['pl0'] += PC; d['cc0'] += CCc; continue
    if m['combo'] < 0: continue
    d['n'] += 1; d['pl'] += PC; d['cc'] += CCc
    pc = sorted(map(tuple, p['cells'])); ccells = sorted(map(tuple, pk['cells']))
    cand = [(pk['piece'], ccells)] + [(t['piece'], sorted(map(tuple, t['cells']))) for t in (g.get('top') or [])[:3]]
    md = None
    if PC and not CCc: md = geo(p['piece'], pc, cand)
    if g['id'] in S1:
        d['ns1'] += 1; d['cc_s0'] += CCc; d['cc_s1'] += S1[g['id']]['pick']['kind'] in CLEAR; d['pl_s'] += PC
    if not (PC and not CCc and md):   # rows kept by the skeptic's "excl strict(geometry)" view
        d['n_x'] += 1; d['pl_x'] += PC; d['cc_x'] += CCc
    if not (PC and not CCc): continue
    reg = g['duel']['cc'] - g['duel']['player']
    cl = lines_after(F, ccells); kindcheck[(pk['kind'], cl)] += 1
    d['regs'].append(reg); d['lines'][p['lines']] += 1
    if md: d['md'] += 1; d['mdregs'].append(reg)
    else: d['occ'] += 1; d['occregs_nomd'].append(reg)
    hs = heights(F); grows = sum(1 for r in F if 'G' in r)
    ready = sum(1 for r in F if r.count('.') == 1 and any(ch != '.' for ch in r))
    pr = g['player'].get('rank')
    occ.append(dict(habit='P3', player=USER, session=s, id=g['id'], lock=m['lock'], regret=reg,
        misdrop_shaped=bool(md), verified=m['verified'],
        player_move=dict(piece=p['piece'], cells=[list(c) for c in pc], hold_used=p['piece'] != m['current'], lines=p['lines']),
        cc_move=dict(piece=pk['piece'], cells=[list(c) for c in ccells], hold_used=bool(pk['hold']), lines=cl),
        detail=dict(misdrop_subtype=md, combo_before=m['combo'], b2b_before=m['b2b'], player_lines=p['lines'],
            player_spin=p['spin'], player_raw_attack=p['raw'], player_sent=p['sent'], cc_kind=pk['kind'], cc_lines=cl,
            player_rank_in_cc_list=pr, player_in_cc_top3=(pr is not None and pr <= 3),
            rows_one_cell_from_full=ready, max_height=max(hs), heights=hs, garbage_rows=grows,
            incoming=m['incoming'], current=m['current'], hold=m['hold'], next=m['next'][:3],
            player_cols=sorted({x for x, y in pc}), cc_cols=sorted({x for x, y in ccells}),
            piece_time_frames=p.get('pieceTime'), keys=p.get('keys'))))
occ.sort(key=lambda o: (o['session'], o['id']))
with open(H + '/P3.occ.jsonl', 'w') as fh:
    for o in occ: fh.write(json.dumps(o) + '\n')

def mm(v): return (round(st.mean(v), 1) if v else None), (st.median(v) if v else None)
def pct(a, b): return round(100 * a / b, 3) if b else None
def row(label, d):
    n = d['n']; allocc = d['occ'] + d['md']
    gap = pct(d['pl'] - d['cc'], n); gap0 = pct(d['pl0'] - d['cc0'], d['n0'])
    return dict(session=label, eligible=n,
        player_clear_rate_pct=pct(d['pl'], n), cc_clear_rate_pct=pct(d['cc'], n), gap_pp=gap,
        occurrences=allocc, occurrences_not_misdrop_shaped=d['occ'], occurrences_misdrop_shaped=d['md'],
        occ_rate_per100_eligible=pct(allocc, n),
        regret_mean=mm(d['regs'])[0], regret_median=mm(d['regs'])[1], regret_ge600=sum(x >= 600 for x in d['regs']),
        regret_not_misdrop_mean=mm(d['occregs_nomd'])[0], regret_not_misdrop_median=mm(d['occregs_nomd'])[1],
        occ_lines=dict(sorted(d['lines'].items())),
        excl_misdrop_shaped=dict(eligible=d['n_x'], player_clear_rate_pct=pct(d['pl_x'], d['n_x']),
            cc_clear_rate_pct=pct(d['cc_x'], d['n_x']), gap_pp=pct(d['pl_x'] - d['cc_x'], d['n_x'])),
        control_no_prior_clear=dict(eligible=d['n0'], player_clear_rate_pct=pct(d['pl0'], d['n0']),
            cc_clear_rate_pct=pct(d['cc0'], d['n0']), gap_pp=gap0,
            # from the unrounded gaps (a difference of two 3-dp values drifts in the last digit)
            combo_specific_gap_pp=(round(100 * (d['pl'] - d['cc']) / n - 100 * (d['pl0'] - d['cc0']) / d['n0'], 3) if n and d['n0'] else None)),
        cc_seed1_same_positions=dict(eligible=d['ns1'], cc_seed0_clear_rate_pct=pct(d['cc_s0'], d['ns1']),
            cc_seed1_clear_rate_pct=pct(d['cc_s1'], d['ns1']), player_clear_rate_pct=pct(d['pl_s'], d['ns1'])))
nights = [row(s, per[s]) for s in sorted(per)]
P = blank()
for d in per.values():
    for k in K: P[k] += d[k]
    for k in ('regs', 'occregs_nomd', 'mdregs'): P[k] += d[k]
    P['lines'] += d['lines']
pooled = row('pooled', P)
out = dict(habit='P3', player=USER,
    definition=('Eligible: every graded pinglamb position (mid.jsonl sample = verified locks >= 21, every 3rd lock; cc seed-0 '
        'grade with a pick and a complete duel) where the previous piece cleared a line (combo >= 0) and there is no B2B chain '
        '(b2b == -1). player_clear_rate = share of eligible positions where the player\'s piece clears >= 1 line; cc_clear_rate = '
        'share where Cold Clear\'s pick at the same position (same board, queue, hold, garbage) is a clearing kind; gap_pp = '
        'player - cc, percentage points (the skeptic\'s rate). Occurrence = the player clears and Cold Clear\'s pick does not '
        '(all such positions are written; misdrop_shaped flags the skeptic\'s strict geometry rule: same piece as cc\'s pick or '
        'its top-3, shifted one column or centroid within 1 column and 1 row). excl_misdrop_shaped drops the misdrop-shaped '
        'occurrence rows and recomputes both rates (skeptic\'s "excl strict(geometry)"). control_no_prior_clear applies the same '
        'rule to b2b-dead positions with combo == -1; combo_specific_gap_pp = gap - control gap (FINDINGS: ~3pp of the gap is a '
        'general tendency to clear more). cc_seed1_same_positions: on the eligible ids in sub4000, cc seed-0 vs seed-1 clear '
        'rates (bot noise). regret = duel.cc - duel.player.'),
    nights=nights, pooled=pooled, cc_kind_vs_board_lines=sorted([list(k) + [v] for k, v in kindcheck.items()]))
json.dump(out, open(H + '/P3.nights.json', 'w'), indent=1)
print(json.dumps(pooled, indent=0))
print('kind vs board-computed cc lines (occurrences):', sorted(kindcheck.items()))
for n in nights:
    print(n['session'], n['eligible'], n['player_clear_rate_pct'], n['cc_clear_rate_pct'], n['gap_pp'], n['occurrences'],
          n['occurrences_misdrop_shaped'], n['regret_mean'], n['regret_median'], n['excl_misdrop_shaped']['gap_pp'], n['control_no_prior_clear']['combo_specific_gap_pp'])
