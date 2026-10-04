# Habit Y3 (yachi): holding back a ready quad.
# Detector = scenario D1 of b2b_hold.py as re-derived by the skeptic
# (verify-b2b-hold-I-hoard-quad-ready-yachi-misdrop.py), verbatim:
#   eligible: graded position (b2b_hold.pkl rows = mid.jsonl lines with a cc duel), 'I' in (current, hold),
#             and the deepest clean well (well() below, the skeptic's loop) >= 4 rows ready.
#   player takes = played lines == 4 ; cc takes = cc seed-0 pick kind == 'quad'.
#   occurrence ("decline") = cc takes and player does not.
#   misdrop_shaped = skeptic's LIBERAL flag: I dropped vertically one column beside the well, OR near-miss
#             geometry vs cc pick/top-3 (same piece, +-1 col shift or centroid within 1), OR fast
#             (pieceTime <= corpus p10 of the scenario pool) with >= 4 keys.
# FINDINGS yachi #3 keeps this definition; its narrowing is "without likely misdrops" (-8.7pp), which
# nights.json reports beside the raw gap.
import json, pickle, os, collections, statistics as st, glob
H = os.path.dirname(os.path.abspath(__file__)); SC = os.path.dirname(H); C = SC + '/../corpus/'
USER = 'yachi'
D = pickle.load(open(SC + '/b2b_hold.pkl', 'rb')); R = D['rows']

def wellinfo(F):
    best = 0; bc = None
    for c in range(10):
        top = next((r for r in range(40) if F[r][c] != '.'), 40); d = 0; r = top - 1
        while r >= 0 and all(F[r][x] != '.' for x in range(10) if x != c) and F[r][c] == '.': d += 1; r -= 1
        if d > best: best, bc = d, c
    return best, bc

MID = {}
for l in open(C + 'mid.jsonl'):
    m = json.loads(l)
    if m['user'] == USER: MID[m['id']] = m
GR = {}
for l in open(C + 'grade.jsonl'):
    g = json.loads(l)
    if g['id'] in MID: GR[g['id']] = g
for r in R:
    if r['user'] != USER: continue
    m = MID[r['id']]; r['well'], r['wcol'] = wellinfo(m['field']); r['keys'] = m['played'].get('keys', [])

pts = sorted(r['pt'] for r in R if r['pt'] is not None); P10 = pts[len(pts) // 10]   # skeptic: over ALL rows, both players

def reg(r): return r['dc'] - r['dp']
quad = lambda r: r['lines'] == 4; cq = lambda r: r['ck'] == 'quad'
def cls(r):
    if r['piece'] == 'I':
        xs = {c[0] for c in r['cells']}
        if len(xs) == 1 and abs(next(iter(xs)) - r['wcol']) == 1: return 'I_adjacent_col'
        if len(xs) == 1 and next(iter(xs)) == r['wcol']: return 'I_in_well_not4'
        return 'I_elsewhere'
    if r['cur'] == 'I' and r['held']: return 'held_I_now'
    if r['hold'] == 'I' and not r['held']: return 'kept_I_in_hold'
    return 'other'
def nearmiss(r):
    pc = r['cells']; cx = sum(c[0] for c in pc) / 4; cy = sum(c[1] for c in pc) / 4
    for piece, cells, _ in [(r['cpiece'], r['ccells'], r['chold'])] + r['top']:
        if piece != r['piece'] or cells == pc: continue
        for dx in (-1, 1):
            if sorted((x + dx, y) for x, y in cells) == pc: return True
        qx = sum(c[0] for c in cells) / 4; qy = sum(c[1] for c in cells) / 4
        if abs(qx - cx) <= 1 and abs(qy - cy) <= 1: return True
    return False
mis = lambda r: cls(r) == 'I_adjacent_col' or nearmiss(r) or (r['pt'] is not None and r['pt'] <= P10 and r['nk'] >= 4)

A = [r for r in R if r['user'] == USER and 'I' in (r['cur'], r['hold']) and r['well'] >= 4]
dec = [r for r in A if cq(r) and not quad(r)]
print('eligible', len(A), 'declines', len(dec), 'P10', P10)

# follow-up: when did the player's quad come (full per-night data, same round)
need = collections.defaultdict(set)
for r in dec:
    p = r['id'].split('/'); need[(p[0], p[1])].add(int(p[3]))
QL = collections.defaultdict(dict)   # (file, 'rN') -> lock -> lines
for fn in sorted(glob.glob(C + '2026-*.jsonl')):
    for l in open(fn):
        if '"user": "yachi"' not in l and '"user":"yachi"' not in l: continue
        m = json.loads(l)
        if m['user'] != USER: continue
        p = m['id'].split('/'); key = (p[0], p[1])
        if key in need: QL[key][m['lock']] = m['played']['lines']
def next_quad(r):
    parts = r['id'].split('/'); key = (parts[0], parts[1]); lk = int(parts[3]); L = QL[key]
    k = 1
    while lk + k in L:
        if L[lk + k] == 4: return k
        k += 1
    return None   # round ended without another quad

occ = []
for r in sorted(dec, key=lambda r: (r['session'], r['id'])):
    m = MID[r['id']]; g = GR[r['id']]; F = m['field']; pk = g['pick']
    c = cls(r); wc = r['wcol']
    occ.append(dict(habit='Y3', player=USER, session=r['session'], id=r['id'], lock=int(r['id'].split('/')[-1]),
        regret=reg(r), misdrop_shaped=bool(mis(r)), verified=m['verified'],
        player_move=dict(piece=m['played']['piece'], cells=[list(x) for x in m['played']['cells']], hold_used=r['held'], lines=r['lines']),
        cc_move=dict(piece=pk['piece'], cells=[list(x) for x in pk['cells']], hold_used=bool(pk['hold']), lines=4),
        detail=dict(decline_class=c,   # held_I_now = pressed hold on a current I; kept_I_in_hold = I stayed in hold; I_* = I played but not a quad
            i_location='current' if r['cur'] == 'I' else 'hold', current=r['cur'], hold=r['hold'], next=r['nxt'][:5],
            well_col=wc, well_rows_ready=r['well'], max_height=r['maxh'], garbage_rows=r['grows'], incoming=r['inc'],
            b2b=r['b2b'], combo=r['combo'], cc_kind=r['ck'], cc_lines=4, player_kind=r['pk'],
            player_cols=sorted({x for x, _ in r['cells']}), player_in_well_col=wc in {x for x, _ in r['cells']},
            pieces_until_player_quad=next_quad(r), near_miss=nearmiss(r),
            piece_time_frames=r['pt'], keys=r['keys'], n_keys=r['nk'])))
with open(H + '/Y3.occ.jsonl', 'w') as fh:
    for o in occ: fh.write(json.dumps(o) + '\n')

def mm(v): return (round(st.mean(v), 1) if v else None), (st.median(v) if v else None)
def row(label, rs):
    n = len(rs); pq = sum(quad(r) for r in rs); cqn = sum(cq(r) for r in rs)
    d = [r for r in rs if cq(r) and not quad(r)]; dm = [r for r in d if mis(r)]; dd = [r for r in d if not mis(r)]
    rs2 = [r for r in rs if not (cq(r) and not quad(r) and mis(r))]   # skeptic: misdrop decline rows dropped
    n2 = len(rs2)
    nq = [o for o in (next_quad(r) for r in d)]
    return dict(session=label, eligible=n, player_quad=pq, cc_quad=cqn,
        player_rate_pct=round(100 * pq / n, 2) if n else None, cc_rate_pct=round(100 * cqn / n, 2) if n else None,
        gap_pp=round(100 * (pq - cqn) / n, 2) if n else None,
        occurrences=len(d), occurrences_misdrop_shaped=len(dm), occurrences_deliberate=len(dd),
        player_only_quads=sum(quad(r) and not cq(r) for r in rs),
        regret_mean=mm([reg(r) for r in d])[0], regret_median=mm([reg(r) for r in d])[1],
        regret_mean_deliberate=mm([reg(r) for r in dd])[0], regret_median_deliberate=mm([reg(r) for r in dd])[1],
        decline_classes=dict(collections.Counter(cls(r) for r in d)),
        quad_next_piece=sum(x == 1 for x in nq), quad_within_2=sum(x is not None and x <= 2 for x in nq), no_later_quad_in_round=sum(x is None for x in nq),
        excl_misdrops=dict(eligible=n2, player_rate_pct=round(100 * sum(quad(r) for r in rs2) / n2, 2) if n2 else None,
            cc_rate_pct=round(100 * sum(cq(r) for r in rs2) / n2, 2) if n2 else None,
            gap_pp=round(100 * (sum(quad(r) for r in rs2) - sum(cq(r) for r in rs2)) / n2, 2) if n2 else None))
by = collections.defaultdict(list)
for r in A: by[r['session']].append(r)
nights = [row(s, by[s]) for s in sorted(by)]
pooled = row('pooled', A)
out = dict(habit='Y3', player=USER,
    definition=('Eligible: graded yachi position (mid.jsonl sample: verified locks >= 21, every 3rd; cc seed-0 grade with a duel) '
        'where I is the current piece or in hold and the deepest clean well is >= 4 rows ready (a "ready" row = every other column '
        'filled, counted down from the well column\'s surface; skeptic verify-b2b-hold-I-hoard-quad-ready-yachi-*.py). Player rate = '
        'share of eligible positions where the player\'s move clears 4 lines; Cold Clear rate = share where cc\'s seed-0 pick is a quad, '
        'on the same positions; gap = player - cc (pp). Occurrence = cc quads and the player does not. misdrop_shaped = the skeptic\'s '
        'LIBERAL rule (I dropped vertically one column beside the well; or same piece as cc pick/top-3 shifted one column or centroid '
        'within 1 cell; or pieceTime <= p10 (%.1f f) with >= 4 keys). excl_misdrops = the skeptic\'s robust variant: misdrop-shaped '
        'decline rows dropped from the eligible set. Regret = duel.cc - duel.player.' % P10),
    nights=nights, pooled=pooled, p10_piece_time=P10)
json.dump(out, open(H + '/Y3.nights.json', 'w'), indent=1)
print(json.dumps(pooled))
for n in nights: print(n['session'], n['eligible'], n['player_rate_pct'], n['cc_rate_pct'], n['gap_pp'], n['occurrences'], n['occurrences_misdrop_shaped'], n['regret_mean'], n['regret_median'], n['excl_misdrops']['gap_pp'])
