import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
# Y6 (yachi): "over-rotating the T into a TSS in a ready TSD slot"  — FINDINGS yachi #6, skeptic TS2.
#
# Detector: verbatim from verify-tspins-TS2-yachi-tss-in-tsd-slot-{stats,misdrop}.py (see Y6_common.py):
#   static TSD slot = row r with exactly the 3 cells x-1,x,x+1 empty, row r+1 with only x empty, exactly one overhang
#   at r-1 over x-1 or x+1, column x and the open side clear to the top. A T locked with its stem in (x,r+1) and >=3 of
#   the 4 down-T cells: exactly the down-T and >=2 lines -> TSD; a spin clearing 1 line -> TSS.
# Narrowed claim (FINDINGS #6 / skeptic): the mechanism is OVER-rotation (3rd rotate press), it runs on ALL verified
#   locks (not only the graded sample), and the cc-regret figure is not to be cited (78% in 10 rounds); the cost is
#   ~2 attack lines per event. So the night rate is over all verified in-slot placements.
# Cold Clear: grade.jsonl covers only every 3rd mid-game lock, so every remaining yachi in-slot position was graded
#   with the identical settings (CC_NODES=20000 COACH_DUEL=20000 COACH_SEED=0) by Y6_prep.py -> Y6.extra-grade.jsonl.
#   A 3-position check reproduced grade.jsonl byte for byte, so the two sources are one measurement.
import json, sys, collections, statistics as st, math
sys.path.insert(0, CC_WORK + '/scen/habits')
from Y6_common import *

G = {}
for f in (f'{CORPUS}/grade.jsonl', f'{HAB}/Y6.extra-grade.jsonl'):
    src = 'grade.jsonl' if f.endswith('/grade.jsonl') else 'Y6.extra-grade.jsonl'
    for l in open(f):
        g = json.loads(l); g['_src'] = src; G.setdefault(g['id'], g)

def apply_lines(field, cells):
    rows = collections.Counter(y for x, y in cells)
    return sum(1 for y, k in rows.items() if field[y].count('.') == k and all(field[y][x] == '.' for x, yy in cells if yy == y))
def shape(cells):
    mx = min(x for x, y in cells); my = min(y for x, y in cells)
    return frozenset((x-mx, y-my) for x, y in cells), mx
def misdrop(pcells, ppiece, g):   # the skeptics' geometry rule (as in verify-holes-*-misdrop / Y5.py)
    ps, px = shape(pcells)
    for c in [g['pick']] + g.get('top', [])[:3]:
        if c['piece'] != ppiece: continue
        cs, cx = shape([tuple(t) for t in c['cells']])
        if cs == ps and abs(cx-px) == 1: return True
        if cs != ps and abs(cx-px) <= 1: return True
    return False

# yachi TSD p25 pieceTime: the TS2 misdrop skeptic's "fast" threshold
ytsd_pt = sorted((d['played'].get('pieceTime') or 0) for s, d, g, sl, out, *_ in in_slot_positions('yachi') if out == 'TSD')
Q25 = ytsd_pt[len(ytsd_pt)//4]

rows = []
for s, d, g, sl, out, slot, D in in_slot_positions():
    pl = d['played']; gr = G.get(d['id']) if d['user'] == 'yachi' else None
    graded = bool(gr and 'error' not in gr and gr.get('pick') and gr.get('duel') and gr['duel']['player'] is not None and gr['duel']['cc'] is not None)
    co = pick_out(gr, sl) if graded else None
    rot = [k for k in (pl.get('keys') or []) if k.startswith('rotate')]
    rows.append(dict(s=s, d=d, g=g, sl=sl, out=out, slot=slot, gr=gr if graded else None, graded=graded, co=co, rot=rot,
                     reg=(gr['duel']['cc'] - gr['duel']['player']) if graded else None))

occ_out = []
for r in rows:
    d, gr = r['d'], r['gr']
    if d['user'] != 'yachi' or r['out'] != 'TSS' or not r['graded'] or r['co'] != 'TSD': continue
    pl = d['played']; pk = gr['pick']; x, rr, side = r['slot']
    ks = keysig(r['rot']); pt = pl.get('pieceTime') or 0
    occ_out.append(dict(
        habit='Y6', player='yachi', session=r['s'], id=d['id'], lock=d['lock'], regret=r['reg'],
        misdrop_shaped=misdrop([tuple(c) for c in pl['cells']], 'T', gr), verified=d['verified'],
        player_move=dict(piece=pl['piece'], cells=[list(c) for c in pl['cells']], hold_used=pl['piece'] != d['current'], lines=pl['lines']),
        cc_move=dict(piece=pk['piece'], cells=[list(c) for c in pk['cells']], hold_used=bool(pk['hold']), lines=apply_lines(d['field'], pk['cells'])),
        detail=dict(
            slot_column=x, slot_row_from_bottom=40 - (rr + 1), overhang_over='left' if side == 'R' else 'right',
            rows_ready=2, player_kind='TSS', player_lines=pl['lines'], player_spin=pl['spin'], player_rotation=pl['rotation'],
            player_sent=pl.get('sent'), cc_kind=pk['kind'], cc_lines=apply_lines(d['field'], pk['cells']), cc_rotation=pk.get('rot'),
            rotate_keys=r['rot'], n_rotate_keys=len(r['rot']), key_signature=ks, n_keys=len(pl.get('keys') or []),
            piece_time_frames=pl.get('pieceTime'),
            extra_misdrop_sign=(ks == 'last two opposite (correction)' or len(r['rot']) == 1 or pt <= Q25),
            max_height=mh(r['g']), garbage_rows=sum('G' in row for row in d['field']), incoming=d['incoming'],
            b2b=d['b2b'], combo=d['combo'], current=d['current'], hold=d['hold'], next=d['next'],
            grade_source=gr['_src'])))
with open(f'{HAB}/Y6.occ.jsonl', 'w') as o:
    for e in occ_out: o.write(json.dumps(e) + '\n')

def pct(a, b): return round(100*a/b, 2) if b else None
def summ(rs, label):
    y = [r for r in rs if r['d']['user'] == 'yachi']; p = [r for r in rs if r['d']['user'] == 'pinglamb']
    gy = [r for r in y if r['graded']]
    tss = sum(r['out'] == 'TSS' for r in y)
    g_tss = sum(r['out'] == 'TSS' for r in gy)
    cc = collections.Counter(r['co'] for r in gy)
    oc = [e for e in occ_out if label == 'pooled' or e['session'] == label]
    regs = [e['regret'] for e in oc]
    allreg_tss = [r['reg'] for r in gy if r['out'] == 'TSS']
    return dict(
        session=label,
        eligible=len(y), player_tss=tss, player_tsd=len(y) - tss, player_rate_pct=pct(tss, len(y)),
        graded=len(gy), not_graded_dead=len(y) - len(gy),
        player_tss_graded=g_tss, player_tsd_graded=len(gy) - g_tss,
        player_rate_graded_pct=pct(g_tss, len(gy)),
        cc_tsd=cc['TSD'], cc_tss=cc['TSS'], cc_other_in_slot=cc['other'], cc_not_into_slot=cc[None],
        cc_rate_pct=pct(cc['TSS'], len(gy)),
        cc_rate_of_cc_in_slot_pct=pct(cc['TSS'], cc['TSD'] + cc['TSS']),
        gap_pp=round(100*g_tss/len(gy) - 100*cc['TSS']/len(gy), 2) if gy else None,
        occurrences=len(oc),
        occurrences_misdrop_shaped=sum(e['misdrop_shaped'] for e in oc),
        occurrences_extra_misdrop_sign=sum(e['detail']['extra_misdrop_sign'] for e in oc),
        player_tss_cc_also_tss=sum(1 for r in gy if r['out'] == 'TSS' and r['co'] == 'TSS'),
        player_tss_cc_no_slot=sum(1 for r in gy if r['out'] == 'TSS' and r['co'] is None),
        reverse_player_tsd_cc_tss=sum(1 for r in gy if r['out'] == 'TSD' and r['co'] == 'TSS'),
        reverse_regret_mean=(lambda v: round(st.mean(v), 1) if v else None)([r['reg'] for r in gy if r['out'] == 'TSD' and r['co'] == 'TSS']),
        regret_mean=round(st.mean(regs), 1) if regs else None, regret_median=st.median(regs) if regs else None,
        regret_mean_all_player_tss=round(st.mean(allreg_tss), 1) if allreg_tss else None,
        pinglamb_eligible=len(p), pinglamb_tss=sum(r['out'] == 'TSS' for r in p),
        pinglamb_rate_pct=pct(sum(r['out'] == 'TSS' for r in p), len(p)))
nights = [summ([r for r in rows if r['s'] == s], s) for s in SESS] + [summ(rows, 'pooled')]
k = sum(n['player_rate_graded_pct'] > n['cc_rate_pct'] for n in nights[:-1]); nn = sum(n['player_rate_graded_pct'] != n['cc_rate_pct'] for n in nights[:-1])
def signp(k, n):
    p = lambda i: math.comb(n, i)/2**n; o = p(k)
    return min(1, sum(p(i) for i in range(n+1) if p(i) <= o+1e-12))
out = dict(habit='Y6', player='yachi',
    definition=('Eligible: every verified yachi lock (all locks, not only the graded sample) where the T was locked into a '
        'ready static TSD slot as a TSD or a TSS (skeptic verify-tspins-TS2-*: row r empty exactly at x-1,x,x+1, row r+1 '
        'empty only at x, one overhang at r-1, column x and the open side clear above). Player rate = TSS / (TSD+TSS) over '
        'those placements (the skeptic\'s headline share). Cold Clear rate = share of the SAME positions where cc\'s seed-0 '
        'pick (CC_NODES=20000, COACH_DUEL=20000) is the sideways TSS; its denominator is every graded eligible position, so cc '
        'declining the slot counts as not-TSS (cc_rate_of_cc_in_slot_pct gives the share among cc\'s own in-slot T placements). '
        'gap_pp = player_rate_graded_pct - cc_rate_pct on the identical graded set. Positions outside grade.jsonl were graded '
        'with the same settings (Y6.extra-grade.jsonl); positions cc treats as dead are dropped from the graded set. '
        'Occurrence = player locked the TSS and cc\'s pick at that position is the TSD. misdrop_shaped = the skeptics\' '
        'geometry rule (same piece as cc pick/top-3, same shape one column over or another rotation within one column); '
        'detail.extra_misdrop_sign = the TS2 misdrop skeptic\'s stricter key-trace rule (correction key, one rotate, or '
        f'pieceTime <= yachi TSD p25 = {Q25} f). Regret = duel.cc - duel.player (FINDINGS: do not cite as the cost; the '
        'cost is about 2 attack lines per event).'),
    night_sign_test=dict(player_above_cc_nights=k, nights_differing=nn, sign_p=signp(k, nn)),
    nights=nights)
json.dump(out, open(f'{HAB}/Y6.nights.json', 'w'), indent=1)
print('occurrences', len(occ_out), 'Q25', Q25)
for n in nights:
    print(n['session'], n['eligible'], n['player_tss'], n['player_rate_pct'], '| graded', n['graded'], n['player_rate_graded_pct'],
          'cc', n['cc_tss'], n['cc_rate_pct'], n['cc_rate_of_cc_in_slot_pct'], 'gap', n['gap_pp'], '| occ', n['occurrences'],
          n['occurrences_misdrop_shaped'], n['occurrences_extra_misdrop_sign'], n['regret_mean'], n['regret_median'], '| pl', n['pinglamb_rate_pct'])
print(out['night_sign_test'])
