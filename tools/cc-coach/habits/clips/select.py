import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
# Stage 1: pick TYPICAL examples per (habit, night) and build the K=4 rollout inputs.
# Typical = regret nearest the median regret of the night's display pool (not the worst).
# Writes: candidates.json (ranked, up to NCAND per habit-night, distinct rounds, valid windows),
#         windows.jsonl (every recorded decision needed for the human side + checks),
#         rollin.jsonl (one rollout input per unique position id), select-log.json
import json, os, statistics, collections
S = CC_WORK + ''
C = S + '/corpus'; H = S + '/scen/habits'; O = S + '/scen/hclips'
HABITS = 'Y1 Y2 Y3 Y4 Y5 Y6 P1 P2 P3 P4 P5 P6'.split()
SESS = sorted(f[:-6] for f in os.listdir(C) if f.endswith('.jsonl') and f[:4] == '2026')
K = 4; NCAND = 3          # keep 2, one backup in case a clip fails its self-checks
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
# soft preferences (applied only if the night still has candidates after them)
PREF = {
    'Y2': ('cc pick without hold (the clear was available with the same piece)', lambda o: not o['cc_move']['hold_used']),
    'P5': ('cc pick without hold (the clear was available with the same piece)', lambda o: not o['cc_move']['hold_used']),
    'Y3': ('decline class held_I_now or kept_I_in_hold', lambda o: o['detail']['decline_class'] in ('held_I_now', 'kept_I_in_hold')),
}
cands = {}; log = {'empty': [], 'short_windows': [], 'notes': [], 'pools': {}}
for h in HABITS:
    for s in SESS:
        allo = [o for o in occ[h] if o['session'] == s]
        rej = collections.Counter(); pool = []
        for o in allo:
            why = pool_filter(h, o)
            if why: rej[why] += 1
            else: pool.append(o)
        pref_used = None
        if h in PREF and pool:
            p2 = [o for o in pool if PREF[h][1](o)]
            if p2: pref_used = PREF[h][0]; rej['not preferred: ' + PREF[h][0]] += len(pool) - len(p2); pool = p2
        info = {'occurrences': len(allo), 'pool': len(pool), 'excluded': dict(rej), 'preference': pref_used}
        if not pool:
            log['empty'].append({'habit': h, 'session': s, 'why': 'no occurrence left after filters', **info}); continue
        med = statistics.median(o['regret'] for o in pool)
        info['pool_regret_median'] = med
        srt = sorted(pool, key=lambda o: (abs(o['regret'] - med), o['regret'], o['id']))
        regs = sorted(o['regret'] for o in pool)
        picked = []; used = set(); short = 0
        for rank, o in enumerate(srt):
            rd = rkey(o['id']).rsplit('/', 1)[0]
            if rd in used: continue
            wf, why = window_ok(o)
            if wf is None:
                short += 1; log['short_windows'].append({'habit': h, 'session': s, 'id': o['id'], 'why': why}); continue
            used.add(rd)
            pct = 100 * (sum(r < o['regret'] for r in regs) + 0.5 * sum(r == o['regret'] for r in regs)) / len(regs)
            picked.append({'occ': o, 'why': {'rule': 'regret nearest the median regret of this night\'s display pool, distinct rounds',
                                            'pool_size': len(pool), 'pool_regret_median': med, 'regret': o['regret'],
                                            'distance_from_median': abs(o['regret'] - med), 'rank_by_distance': rank + 1,
                                            'regret_percentile_in_pool_midrank': round(pct, 1), 'preference': pref_used}})
            if len(picked) == NCAND: break
        info['windows_rejected'] = short
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
        st['garbage_schedule'] = [x['played']['tanks'] for x in w[:K]]
        st['incoming_schedule'] = [x['incoming'] for x in w[:K]]
        fr.write(json.dumps(st) + '\n')
json.dump(log, open(f'{O}/select-log.json', 'w'), indent=1)
print('habit-nights with candidates', len(cands), 'empty', len(log['empty']), 'unique positions', len(ids),
      'short windows skipped', len(log['short_windows']))
for e in log['empty']: print('EMPTY', e['habit'], e['session'], e['why'], e['excluded'])
