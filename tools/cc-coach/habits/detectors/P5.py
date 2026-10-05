import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
# Habit P5 (pinglamb): skipping an available line clear at a mid-high stack with garbage on board
# (FINDINGS pinglamb #5, 'same as yachi #2'; same detector as Y2.py, player pinglamb).
# Surviving (narrowed) definition = the HS1 core both skeptics re-derived
# (verify-pressure-HS1-stats.py / verify-pressure-HS1-misdrop.py, FINDINGS pinglamb #5 "Frequency": -0.110 lines/move at 12-15 rows):
#   eligible position : graded mid-game position, pre-move max height 12..15, 4..7 rows holding garbage
#   habit occurrence  : cc's pick clears >=1 line, the player's move clears 0 lines
#   rate              : lines cleared per move (player vs cc's pick, same positions); P(clear) also given
# misdrop_shaped = the misdrop skeptic's geometry rule mdA (neargeo): the player's piece equals cc's pick
#   or a top-3 candidate of the same piece shifted 1-2 columns (same shape) or a different rotation
#   within 1 column. mdB (geometry AND (pieceTime < corpus p25 OR keys > piece median+1)) is in detail.
import json, collections, statistics as st, os
SP = CC_WORK + ''
C = SP + '/corpus'; OUT = SP + '/scen/habits'
HMIN, HMAX, GMIN, GMAX = 12, 15, 4, 7
BROAD = (10, 13, 0, 40)  # the habit title's '10-13 rows' band (D1/S3 band, any garbage), context only

def heights(f): return [40 - next((r for r in range(40) if f[r][c] != '.'), 40) for c in range(10)]
def place(f, cells):
    g = [list(r) for r in f]
    for x, y in cells:
        if 0 <= y < 40: g[y][x] = '#'
    full = [i for i, r in enumerate(g) if '.' not in r]
    keep = [r for r in g if '.' in r]; keep = [['.'] * 10 for _ in range(40 - len(keep))] + keep
    return dict(lines=len(full), garbage_lines=sum('G' in f[i] for i in full), rows=full,
                post_maxh=max(heights([''.join(r) for r in keep])))
def norm(cells):
    mx = min(x for x, y in cells); my = min(y for x, y in cells)
    return frozenset((x - mx, y - my) for x, y in cells), mx, my
def neargeo(pp, pc, cands):
    ps, px, py = norm(pc)
    for c in cands:
        if c['piece'] != pp: continue
        if set(map(tuple, c['cells'])) == set(map(tuple, pc)): return 'same'
        cs, cx, cy = norm(c['cells'])
        if cs == ps and abs(cx - px) <= 2: return 'shift'
        if cs != ps and abs(cx - px) <= 1: return 'rot'
    return None
def ready_rows(f):
    """rows with exactly one empty cell that is open to the surface (nothing above it in its column)"""
    out = []
    for r in range(40):
        e = [c for c in range(10) if f[r][c] == '.']
        if len(e) == 1 and all(f[k][e[0]] == '.' for k in range(r)): out.append((r, e[0]))
    return out

M = {}
for l in open(C + '/mid.jsonl'):
    p = json.loads(l); M[p['id']] = p
G = {}
for l in open(C + '/grade.jsonl'):
    g = json.loads(l); G[g['id']] = g
PT = sorted(p['played']['pieceTime'] for p in M.values()); PT25 = PT[len(PT) // 4]
NK = collections.defaultdict(list)
for p in M.values(): NK[p['played']['piece']].append(len(p['played']['keys']))
NKmed = {k: sorted(v)[len(v) // 2] for k, v in NK.items()}

# per-night decision files: to say what the player did on the following own locks
NEXT = {}
sess = sorted({p['session'] for p in M.values()})
want = set()
for p in M.values(): want.add((p['session'], p['file'], p['round'], p['user']))
for s in sess:
    for l in open(f'{C}/{s}.jsonl'):
        d = json.loads(l)
        k = (s, d['file'], d['round'], d['user'])
        if k in want: NEXT[k + (d['lock'],)] = d['played']['lines']

rows = []
for pid, p in M.items():
    g = G.get(pid)
    if not g or 'error' in g or not g.get('pick'): continue
    f = p['field']; hs = heights(f); mh = max(hs); ngr = sum('G' in r for r in f)
    pl = p['played']; pc = [tuple(c) for c in pl['cells']]
    po = place(f, pc); co = place(f, [tuple(c) for c in g['pick']['cells']])
    reg = None
    if g.get('duel') and g['duel'].get('player') is not None and g['duel'].get('cc') is not None:
        reg = g['duel']['cc'] - g['duel']['player']
    rows.append(dict(id=pid, p=p, g=g, u=p['user'], s=p['session'], mh=mh, ngr=ngr, po=po, co=co, reg=reg,
                     geo=neargeo(pl['piece'], pc, [g['pick']] + g.get('top', [])[:3])))

core = lambda r: HMIN <= r['mh'] <= HMAX and GMIN <= r['ngr'] <= GMAX
broad = lambda r: BROAD[0] <= r['mh'] <= BROAD[1] and BROAD[2] <= r['ngr'] <= BROAD[3]
occ_f = lambda r: r['co']['lines'] > 0 and r['po']['lines'] == 0
U = 'pinglamb'

def summ(rs):
    n = len(rs)
    if not n: return None
    oc = [r for r in rs if occ_f(r)]
    regs = [r['reg'] for r in oc if r['reg'] is not None]
    ccl = [r for r in rs if r['co']['lines'] > 0]
    pl = sum(r['po']['lines'] for r in rs) / n; cl = sum(r['co']['lines'] for r in rs) / n
    pp = sum(r['po']['lines'] > 0 for r in rs) / n; cp = sum(r['co']['lines'] > 0 for r in rs) / n
    return dict(n=n, player_lines_per_move=round(pl, 4), cc_lines_per_move=round(cl, 4), gap_lines_per_move=round(pl - cl, 4),
                player_p_clear=round(pp, 4), cc_p_clear=round(cp, 4), gap_p_clear=round(pp - cp, 4),
                cc_clear_positions=len(ccl), occurrences=len(oc),
                stack_share_where_cc_clears=round(len(oc) / len(ccl), 4) if ccl else None,
                occurrences_per_100_eligible=round(100 * len(oc) / n, 2),
                occ_misdrop_shaped=sum(r['geo'] in ('shift', 'rot') for r in oc),
                regret_n=len(regs), regret_mean=round(st.mean(regs), 1) if regs else None,
                regret_median=st.median(regs) if regs else None,
                gap_excl_misdrop=(round(sum(r['po']['lines'] - r['co']['lines'] for r in nm) / len(nm), 4) if (nm := [r for r in rs if r['geo'] not in ('shift', 'rot')]) else None))

ys = [r for r in rows if r['u'] == U]
os.makedirs(OUT, exist_ok=True)
with open(OUT + '/P5.occ.jsonl', 'w') as fo:
    for r in sorted((r for r in ys if core(r) and occ_f(r)), key=lambda r: (r['s'], r['id'])):
        p, g, pl = r['p'], r['g'], r['p']['played']
        pk = g['pick']
        hold_used_p = pl['piece'] != p['current']
        fast = pl['pieceTime'] < PT25; extra = len(pl['keys']) > NKmed[pl['piece']] + 1
        xs = [x for x, y in pl['cells']]
        rr = ready_rows(p['field'])
        key = (p['session'], p['file'], p['round'], p['user'])
        nxt = [NEXT.get(key + (p['lock'] + k,)) for k in (1, 2, 3)]
        first_clear = next((k for k, v in zip((1, 2, 3), nxt) if v), None)
        cc_cols = sorted({x for x, y in pk['cells']})
        fo.write(json.dumps(dict(
            habit='P5', player=U, session=r['s'], id=r['id'], lock=p['lock'], regret=r['reg'],
            misdrop_shaped=r['geo'] in ('shift', 'rot'), verified=p['verified'],
            player_move=dict(piece=pl['piece'], cells=pl['cells'], hold_used=hold_used_p, lines=r['po']['lines']),
            cc_move=dict(piece=pk['piece'], cells=pk['cells'], hold_used=bool(pk.get('hold')), lines=r['co']['lines']),
            detail=dict(max_height=r['mh'], garbage_rows=r['ngr'], incoming=p['incoming'], combo=p['combo'], b2b=p['b2b'],
                        cc_lines=r['co']['lines'], cc_garbage_lines=r['co']['garbage_lines'], cc_kind=pk.get('kind'),
                        cc_tspin=pk.get('tspin'), cc_columns=cc_cols,
                        ready_rows=len(rr), ready_columns=sorted({c for _, c in rr}),
                        player_post_max_height=r['po']['post_maxh'], cc_post_max_height=r['co']['post_maxh'],
                        player_against_wall=min(xs) == 0 or max(xs) == 9,
                        player_columns=sorted(set(xs)), in_title_band_10_13=10 <= r['mh'] <= 13,
                        geometry=r['geo'], fast=fast, extra_keys=extra, misdrop_fast_or_keys=bool(r['geo'] in ('shift', 'rot') and (fast or extra)),
                        piece_time_frames=pl['pieceTime'], keys=len(pl['keys']),
                        player_lines_next3=nxt, player_first_clear_within3=first_clear,
                        duel_same=(g.get('duel') or {}).get('same'))), separators=(',', ':')) + '\n')

nights = {}
for s in sess:
    rs = [r for r in ys if r['s'] == s and core(r)]
    nights[s] = summ(rs)
    b = summ([r for r in ys if r['s'] == s and broad(r)])
    nights[s]['band_10_13_any_garbage'] = {k: b[k] for k in ('n', 'player_lines_per_move', 'cc_lines_per_move', 'gap_lines_per_move', 'occurrences')} if b else None
pooled = summ([r for r in ys if core(r)])
bp = summ([r for r in ys if broad(r)])
pooled['band_10_13_any_garbage'] = {k: bp[k] for k in ('n', 'player_lines_per_move', 'cc_lines_per_move', 'gap_lines_per_move', 'occurrences')}
neg = sum(v['gap_lines_per_move'] < 0 for v in nights.values()); pos = sum(v['gap_lines_per_move'] > 0 for v in nights.values())
res = dict(habit='P5', player=U,
           definition=(f'Eligible: graded mid-game position (corpus/mid.jsonl x grade.jsonl, every 3rd verified lock>=21) of {U} with pre-move max height '
                       f'{HMIN}-{HMAX} and {GMIN}-{GMAX} rows containing garbage (the HS1 core both skeptics re-derived). Rate = lines cleared per move '
                       '(player\'s actual move vs Cold Clear\'s pick on the same position); P(clear) given too. Occurrence = Cold Clear\'s pick clears '
                       '>=1 line and the player\'s move clears 0. regret = duel.cc - duel.player. misdrop_shaped = skeptic geometry rule (same piece as '
                       'cc pick/top-3, same shape shifted 1-2 columns or other rotation within 1 column). band_10_13_any_garbage = the habit title\'s wider band, context only.'),
           nights=nights, pooled=pooled, nights_gap_negative=neg, nights_gap_positive=pos)
json.dump(res, open(OUT + '/P5.nights.json', 'w'), indent=1)
print(json.dumps(pooled))
for s, v in nights.items(): print(s, v['n'], v['player_lines_per_move'], v['cc_lines_per_move'], v['gap_lines_per_move'], v['occurrences'], v['regret_mean'], v['regret_median'])
print('nights neg/pos', neg, pos)
