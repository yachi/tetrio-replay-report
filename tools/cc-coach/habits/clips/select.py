import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
# Stage 1: rank example candidates per (habit, night) and build the K=4 rollout inputs.
# Candidates are every usable occurrence of the night (no cost band), in order of graded cost nearest the
# median graded cost of the night's display pool ("typical" is only the ORDER now). finalize.py keeps the
# first two, from different rounds and match files, on which Cold Clear's line is clearly better over
# the K pieces (its rule MUCH, in at least 3 of the 5 seeds). At most NCAND candidates per habit-night are
# rolled out; the log records every habit-night where that cap left candidates untried.
# Writes: candidates.json (ranked, up to NCAND per habit-night, valid windows),
#         windows.jsonl (every recorded decision needed for the human side + checks),
#         rollin.jsonl (one rollout input per unique position id), select-log.json
import json, os, statistics, collections
S = CC_WORK + ''
C = S + '/corpus'; H = S + '/scen/habits'; O = S + '/scen/hclips'
HABITS = 'Y1 Y2 Y3 Y4 Y5 Y6 P1 P2 P3 P4 P5 P6'.split()
SESS = sorted(f[:-6] for f in os.listdir(C) if f.endswith('.jsonl') and f[:4] == '2026')
K = 4; NCAND = 12         # rollout cap per habit-night: finalize.py keeps the first 2 that qualify; the rest are
                          # backups for clips that fail a self-check, are not clearly worse than Cold Clear's line,
                          # or repeat a match file / a round already shown
# extend.json (optional; the union of finalize.py's log.capped_short over the earlier passes): habit-nights whose cap is lifted,
# because after NCAND they still had fewer than 2 examples. Rerun until log.capped_short is empty, so a night is
# short only when its candidates ran out.
EXTEND = set(json.load(open(f'{O}/extend.json'))) if os.path.exists(f'{O}/extend.json') else set()
# Habits whose definition IS misdrop-shaped (Y1 by definition; P1 deliberately includes them per
# FINDINGS pinglamb #1; Y6's TSS is cc's TSD one rotation off, misdrop-shaped by construction)
MISDROP_OK = {'Y1', 'P1', 'Y6'}
occ = {h: [json.loads(l) for l in open(f'{H}/{h}.occ.jsonl')] for h in HABITS}

def rkey(i):  # file/round/user
    return i.rsplit('/', 1)[0]

# 1. load every decision needed: for each occurrence, locks l0..l0+K
need = collections.defaultdict(set)
for h in HABITS:
    for o in occ[h]:
        need[o['session']].add(rkey(o['id']))
dec = {}
for s in SESS:
    ks = need[s]
    for l in open(f'{C}/{s}.jsonl'):
        i = l[7:l.index('"', 7)]
        if rkey(i) in ks: dec[i] = json.loads(l)
rounds = {}
for s in SESS:
    for r in json.load(open(f'{C}/{s}.jsonl.rounds.json')):
        rounds[(s, r['file'], r['round'], r['user'])] = r

def window_ok(o):
    k, l0 = o['id'].rsplit('/', 1); l0 = int(l0)
    w = [dec.get(f'{k}/{l0 + j}') for j in range(K + 1)]
    if any(x is None for x in w): return None, f'fewer than {K} following recorded locks in the round'
    if not all(x['verified'] for x in w[:K]): return None, f'one of the {K} shown human locks is outside the verified prefix'
    st = w[0]; r = rounds[(st['session'], st['file'], st['round'], st['user'])]
    cur = st['seqIndex']; nn = len(st['next'])
    fut = list(r['seq'][cur + 1 + nn: cur + 1 + nn + K + 2])
    if len(fut) < K: return None, 'piece sequence too short for the future reveal'
    return (w, fut), None

def pool_filter(h, o):
    if not o['verified']: return 'not verified'
    if o['regret'] is None: return 'no regret'
    if o['misdrop_shaped'] and h not in MISDROP_OK: return 'misdrop_shaped'
    return None
# The night's pool (above) is what "typical" is measured against: its median graded cost, with no
# narrowing. Examples are then drawn from that pool, nearest its median, under two restrictions that
# never move the median:
#  * graded cost > 0: a move the duel rates at least as good as Cold Clear's own pick does not
#    illustrate a costly habit;
#  * P3 only: single-line follow-up clears, the habit's own modal case (FINDINGS pinglamb #3: 478 of
#    683 are singles); if a night has none, any line count.
EXAMPLE_OK = {'P3': ('single-line clears', lambda o: o['player_move']['lines'] == 1)}
# Hard example restrictions (no fallback): occurrences that meet the code definition but would show a
# different scene from the one the card describes. They stay in the pool, so the median does not move.
QUAD_IDS = {o['id'] for h in ('Y3', 'P6') for o in occ[h]}
EXAMPLE_ONLY = {
    # the card describes playing another piece first (I held away, or left in hold); spending the I
    # itself away from the well is a decline by the code but not that scene
    'Y3': ('the I was kept in hold or held away, not played elsewhere itself', lambda o: o['detail']['decline_class'] != 'I_elsewhere'),
    # a plain line clear on offer, not a ready quad declined (that is Y3/P6, a separate card)
    'Y2': ("Cold Clear's pick is a 1–3 line clear, not a ready quad",
           lambda o: o['detail']['cc_lines'] in (1, 2, 3) and o['id'] not in QUAD_IDS),
    # FINDINGS pinglamb #5: use the 10-13 band for pinglamb, so examples sit where both bands meet
    'P5': ("Cold Clear's pick is a 1–3 line clear, not a ready quad, and the stack is 12–13 rows",
           lambda o: o['detail']['cc_lines'] in (1, 2, 3) and o['id'] not in QUAD_IDS and o['detail']['max_height'] <= 13),
    # a piece whose centroid sits exactly on the midline (4.5) is in neither half; P4.py counts it as right
    'P4': ('the piece sits clearly on one half, not on the midline', lambda o: o['detail']['player_centroid_x'] != 4.5),
}
def midrank_pct(v, regs):
    return round(100 * (sum(r < v for r in regs) + 0.5 * sum(r == v for r in regs)) / len(regs), 1)
cands = {}; log = {'empty': [], 'short_windows': [], 'notes': [], 'pools': {}, 'capped': [], 'ncand': NCAND, 'extended': sorted(EXTEND)}
for h in HABITS:
    for s in SESS:
        allo = [o for o in occ[h] if o['session'] == s]
        rej = collections.Counter(); pool = []
        for o in allo:
            why = pool_filter(h, o)
            if why: rej[why] += 1
            else: pool.append(o)
        info = {'occurrences': len(allo), 'pool': len(pool), 'excluded': dict(rej),
                'misdrop_shaped_in_pool': sum(o['misdrop_shaped'] for o in pool), 'misdrop_ok': h in MISDROP_OK}
        if not pool:
            log['empty'].append({'habit': h, 'session': s, 'why': 'no occurrence left after filters', **info}); continue
        med = statistics.median(o['regret'] for o in pool)
        regs = sorted(o['regret'] for o in pool)
        info['pool_regret_median'] = med
        ex = [o for o in pool if o['regret'] > 0]
        info['nonpositive_cost'] = len(pool) - len(ex)
        restr = None
        if h in EXAMPLE_ONLY:
            ex2 = [o for o in ex if EXAMPLE_ONLY[h][1](o)]
            info['example_only_excluded'] = len(ex) - len(ex2); info['example_only'] = EXAMPLE_ONLY[h][0]; ex = ex2
        if h in EXAMPLE_OK and ex:
            ex2 = [o for o in ex if EXAMPLE_OK[h][1](o)]
            if ex2: restr = EXAMPLE_OK[h][0]; info['example_class_excluded'] = len(ex) - len(ex2); ex = ex2
        info['example_restriction'] = restr
        srt = sorted(ex, key=lambda o: (abs(o['regret'] - med), o['regret'], o['id']))
        info['positive_eligible'] = len(ex)
        picked = []; short = 0
        for rank, o in enumerate(srt):
            wf, why = window_ok(o)
            if wf is None:
                short += 1; log['short_windows'].append({'habit': h, 'session': s, 'id': o['id'], 'why': why}); continue
            if len(picked) == NCAND and f'{h}/{s}' not in EXTEND:   # the cap: count what it leaves untried
                info['capped_untried'] = info.get('capped_untried', 0) + 1; continue
            picked.append({'occ': o, 'why': {'rule': 'graded cost nearest the median graded cost of this night\'s pool (every verified occurrence, misdrop-shaped excluded unless the habit is misdrop-shaped by definition); candidates only from positive graded cost' + (', ' + restr if restr else '') + (f'; at most {NCAND} rolled out' if f'{h}/{s}' not in EXTEND else f'; more than {NCAND} rolled out, the night being short after {NCAND}'),
                                            'example_only': EXAMPLE_ONLY.get(h, (None,))[0],
                                            'pool_size': len(pool), 'pool_regret_median': med, 'regret': o['regret'],
                                            'distance_from_median': abs(o['regret'] - med), 'rank_by_distance': rank + 1,
                                            'regret_percentile_in_pool_midrank': midrank_pct(o['regret'], regs),
                                            'misdrop_ok': h in MISDROP_OK, 'example_restriction': restr}})
        info['windows_rejected'] = short; info['candidates'] = len(picked); info['cap_lifted'] = f'{h}/{s}' in EXTEND
        if info.get('capped_untried'): log['capped'].append({'habit': h, 'session': s, 'rolled': len(picked), 'untried': info['capped_untried']})
        log['pools'][f'{h}/{s}'] = info
        if not picked: log['empty'].append({'habit': h, 'session': s, 'why': 'no candidate with a valid 4-lock window in a usable round', **info}); continue
        cands[f'{h}/{s}'] = picked
json.dump(cands, open(f'{O}/candidates.json', 'w'))
# 2. windows + rollout inputs (one per unique position id: the harness seeds by id, so a position
# shared by two habits gets identical runs)
ids = sorted({c['occ']['id'] for v in cands.values() for c in v})
with open(f'{O}/windows.jsonl', 'w') as fw, open(f'{O}/rollin.jsonl', 'w') as fr:
    for i in ids:
        k, l0 = i.rsplit('/', 1); l0 = int(l0)
        (w, fut), _ = window_ok({'id': i})
        for x in w: fw.write(json.dumps(x) + '\n')
        st = dict(w[0]); st['future'] = fut; st['k'] = K
        st['garbage_cap'] = 8   # TETR.IO's garbagecap default; no replay in the corpus sets it (frames.ts checks)
        st['garbage_schedule'] = [x['played']['tanks'] for x in w[:K]]
        st['incoming_schedule'] = [x['incoming'] for x in w[:K]]
        fr.write(json.dumps(st) + '\n')
json.dump(log, open(f'{O}/select-log.json', 'w'), indent=1)
print('habit-nights with candidates', len(cands), 'empty', len(log['empty']), 'unique positions', len(ids),
      'short windows skipped', len(log['short_windows']), 'habit-nights capped', len(log['capped']))
for e in log['empty']: print('EMPTY', e['habit'], e['session'], e['why'], e['excluded'])
