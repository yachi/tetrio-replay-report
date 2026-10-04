import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
# Habit P6 (pinglamb): holding the current I away from a ready quad at 10+ rows (FINDINGS pinglamb #6).
# Surviving (narrowed) definition = verify-b2b-hold-I-hoard-quad-ready-pinglamb-misdrop.py, last line
# 'maxh>=10 hoard-only gap' (-6.9pp, 14/15 nights, p=0.00098), re-applied here with the SAME code:
#   scenario          : graded mid-game position (b2b_hold.pkl rows = mid.jsonl x grade.jsonl) of pinglamb with
#                       'I' as current or hold piece and a clean well >=4 deep (wellinfo), pre-move max height >=10
#   'hoard-only'      : every decline (cc quads, player does not) that is NOT a hoard decline (kept_I_in_hold /
#                       held_away_current_I) is dropped from the eligible set, exactly as the skeptic did
#   rate              : P(quad) of the player's move vs P(quad) of cc's pick on the eligible positions; gap = player - cc
#   occurrence        : the narrowed habit itself: cc's pick is a quad, the player held the CURRENT I away
#                       (class held_away_current_I). kept_I_in_hold declines (the null half per FINDINGS) are
#                       counted per night but not emitted as occurrences.
#   misdrop_shaped    : the skeptic's STRICT rule (I one column off / in the well but not a quad / near-miss of cc's
#                       quad pick / kept-I-in-hold with pieceTime <= p10). Liberal flag (any fast decline) in detail.
import json, pickle, collections, statistics as st, glob, os
SP = CC_WORK + ''
SC = SP + '/scen'; S = SP + '/corpus'; OUT = SC + '/habits'
U = 'pinglamb'
D = pickle.load(open(SC + '/b2b_hold.pkl', 'rb')); R = D['rows']
def wellinfo(F):
    best = 0; bc = None
    for c in range(10):
        top = next((r for r in range(40) if F[r][c] != '.'), 40); d = 0; r = top - 1
        while r >= 0 and all(F[r][x] != '.' for x in range(10) if x != c) and F[r][c] == '.': d += 1; r -= 1
        if d > best: best, bc = d, c
    return best, bc
M = {}
for l in open(S + '/mid.jsonl'):
    m = json.loads(l)
    if m['user'] != U: continue
    M[m['id']] = m
G = {}
for l in open(S + '/grade.jsonl'):
    g = json.loads(l)
    if g['id'] in M: G[g['id']] = g
R = [r for r in R if r['user'] == U]
for r in R:
    m = M[r['id']]; r['well'], r['wcol'] = wellinfo(m['field']); r['keys'] = m['played'].get('keys', [])
# lookahead (same as skeptic): lines in the next 3 own locks
nxt = collections.defaultdict(dict)
for f in sorted(glob.glob(S + '/2026-*.jsonl')):
    for l in open(f):
        if U not in l[:400]: continue
        m = json.loads(l)
        if m['user'] != U: continue
        nxt[m['file'] + '/' + str(m['round'])][m['lock']] = m['played']['lines']
def next3(r):
    lock = int(r['id'].split('/')[-1]); d = nxt[r['rk']]
    return [d.get(lock + j) for j in (1, 2, 3)]
reg = lambda r: r['dc'] - r['dp']
quad = lambda r: r['lines'] == 4; cq = lambda r: r['ck'] == 'quad'
gap = lambda r: int(quad(r)) - int(cq(r))
def cls(r):
    if r['piece'] == 'I':
        xs = {c[0] for c in r['cells']}
        if len(xs) == 1 and r['wcol'] is not None and abs(next(iter(xs)) - r['wcol']) == 1: return 'I_vertical_adjacent_col'
        if len(xs) == 1 and next(iter(xs)) == r['wcol']: return 'I_in_well_not_quad'
        if len(xs) == 4: return 'I_flat_elsewhere'
        return 'I_vertical_other_col'
    if r['cur'] == 'I' and r['held']: return 'held_away_current_I'
    if r['hold'] == 'I' and not r['held']: return 'kept_I_in_hold'
    return 'other'
def near(cells, pc):
    for dx in (-1, 1):
        if sorted((x + dx, y) for x, y in cells) == pc: return True
    cx = sum(c[0] for c in pc) / 4; cy = sum(c[1] for c in pc) / 4
    qx = sum(c[0] for c in cells) / 4; qy = sum(c[1] for c in cells) / 4
    return abs(qx - cx) <= 1 and abs(qy - cy) <= 1
A0 = [r for r in R if 'I' in (r['cur'], r['hold']) and r['well'] >= 4]          # skeptic's scenario (all heights)
dec0 = [r for r in A0 if cq(r) and not quad(r)]
pts = sorted(r['pt'] for r in R if r['pt'] is not None); P10 = pts[len(pts) // 10]
nm_pick = {r['id'] for r in dec0 if r['piece'] == r['cpiece'] and r['cells'] != r['ccells'] and near(r['ccells'], r['cells'])}
STRICT = lambda r: cls(r) in ('I_vertical_adjacent_col', 'I_in_well_not_quad') or r['id'] in nm_pick or (cls(r) == 'kept_I_in_hold' and r['pt'] is not None and r['pt'] <= P10)
LIB = lambda r: STRICT(r) or cls(r).startswith('I_') or (r['pt'] is not None and r['pt'] <= P10)
HOARD = ('kept_I_in_hold', 'held_away_current_I')
isdec = lambda r: cq(r) and not quad(r)
# eligible = maxh>=10 hoard-only (skeptic's last line)
E = [r for r in A0 if r['maxh'] >= 10 and not (isdec(r) and cls(r) not in HOARD)]
occ = lambda r: isdec(r) and cls(r) == 'held_away_current_I'
sess = sorted({m['session'] for m in M.values()})
def summ(rs):
    n = len(rs)
    if not n: return None
    oc = [r for r in rs if occ(r)]; kp = [r for r in rs if isdec(r) and cls(r) == 'kept_I_in_hold']
    hd = [r for r in rs if isdec(r)]
    regs = [reg(r) for r in oc]; hregs = [reg(r) for r in hd]
    cur = [r for r in rs if r['cur'] == 'I']
    pq = sum(map(quad, rs)) / n; cc = sum(map(cq, rs)) / n
    return dict(n=n, player_quad_rate=round(pq, 4), cc_quad_rate=round(cc, 4), gap=round(pq - cc, 4),
                player_quads=sum(map(quad, rs)), cc_quads=sum(map(cq, rs)),
                occurrences=len(oc), occ_misdrop_shaped=sum(map(STRICT, oc)),
                regret_mean=round(st.mean(regs), 1) if regs else None, regret_median=st.median(regs) if regs else None,
                kept_I_in_hold_declines=len(kp), hoard_declines=len(hd),
                hoard_regret_mean=round(st.mean(hregs), 1) if hregs else None,
                player_quads_not_cc=sum(1 for r in rs if quad(r) and not cq(r)),
                current_I_only=dict(n=len(cur), player_quad_rate=round(sum(map(quad, cur)) / len(cur), 4) if cur else None,
                                    cc_quad_rate=round(sum(map(cq, cur)) / len(cur), 4) if cur else None,
                                    gap=round(sum(map(gap, cur)) / len(cur), 4) if cur else None))
os.makedirs(OUT, exist_ok=True)
n_occ = 0
with open(OUT + '/P6.occ.jsonl', 'w') as fo:
    for r in sorted((r for r in E if occ(r)), key=lambda r: (r['session'], r['id'])):
        m = M[r['id']]; g = G[r['id']]; pl = m['played']; pk = g['pick']; n3 = next3(r)
        F = m['field']; wc = r['wcol']
        top = next((y for y in range(40) if F[y][wc] != '.'), 40)
        fo.write(json.dumps(dict(
            habit='P6', player=U, session=r['session'], id=r['id'], lock=m['lock'], regret=reg(r),
            misdrop_shaped=bool(STRICT(r)), verified=m['verified'],
            player_move=dict(piece=pl['piece'], cells=pl['cells'], hold_used=bool(r['held']), lines=pl['lines']),
            cc_move=dict(piece=pk['piece'], cells=pk['cells'], hold_used=bool(pk.get('hold')), lines=4 if pk['kind'] == 'quad' else None),
            detail=dict(decline_class=cls(r), current=m['current'], hold_before=m['hold'], next=m['next'],
                        piece_played_instead=pl['piece'], well_column=wc, well_depth=r['well'], rows_ready=r['well'],
                        well_rows=[top - 1 - k for k in range(r['well'])],
                        max_height=r['maxh'], garbage_rows=r['grows'], incoming=m['incoming'], b2b=m['b2b'], combo=m['combo'],
                        cc_kind=pk['kind'], cc_lines=4, cc_column=sorted({x for x, y in pk['cells']}),
                        player_lines=pl['lines'], player_lines_next3=n3,
                        player_quad_within3=next((j for j, v in zip((1, 2, 3), n3) if v == 4), None),
                        piece_time_frames=r['pt'], keys=len(r['keys']), fast_le_p10=bool(r['pt'] is not None and r['pt'] <= P10),
                        misdrop_liberal=bool(LIB(r)), duel_same=r['same'])), separators=(',', ':')) + '\n')
        n_occ += 1
nights = {s: summ([r for r in E if r['session'] == s]) for s in sess}
pooled = summ(E)
neg = sum(v['gap'] < 0 for v in nights.values()); pos = sum(v['gap'] > 0 for v in nights.values())
oc = [r for r in E if occ(r)]
pooled.update(nights_gap_negative=neg, nights_gap_positive=pos, nights=len(nights),
              occ_quad_within3_share=round(sum(any(v == 4 for v in next3(r)) for r in oc) / len(oc), 4),
              pinglamb_pieceTime_p10=P10)
res = dict(habit='P6', player=U,
  definition=('Eligible: graded mid-game position (corpus/mid.jsonl x grade.jsonl, as loaded into scen/b2b_hold.pkl) of pinglamb where the I is the '
              'current or hold piece, a clean well is ready >=4 deep (a column empty from its stack top down through >=4 rows that are each full '
              'except that column), and the pre-move max height is >=10; then, as in the surviving skeptic line "maxh>=10 hoard-only gap", every '
              'decline (cc quads, player does not) that is not a hold decision (player kept the I in hold, or held the current I away) is dropped. '
              'Rate = share of moves that are quads: player\'s actual move vs Cold Clear\'s pick (seed 0, 20000 nodes) on the same positions; '
              'gap = player - cc. Occurrence = cc\'s pick is a quad and the player pressed hold on the current I (held_away_current_I). '
              'kept_I_in_hold_declines are counted but are not the habit (FINDINGS: the I-in-hold half is not a finding). '
              'current_I_only = the same rate restricted to positions where the I is the current piece. regret = duel.cc - duel.player.'),
  nights=nights, pooled=pooled)
json.dump(res, open(OUT + '/P6.nights.json', 'w'), indent=1)
print(json.dumps(pooled, indent=1)); print('occurrences written', n_occ)
for s in sess: v = nights[s]; print(s, v['n'], v['player_quad_rate'], v['cc_quad_rate'], v['gap'], v['occurrences'], v['kept_I_in_hold_declines'], v['regret_mean'], v['regret_median'], v['current_I_only']['gap'])
