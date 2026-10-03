import json, collections
K = 14
P = [json.loads(l) for l in open('positions.jsonl')]
R = {(r['file'], r['round'], r['user']): r for r in json.load(open('positions.jsonl.rounds.json'))}
by = collections.defaultdict(list)
for p in P: by[(p['file'], p['round'], p['user'])].append(p)
out = []
for key, ps in by.items():
    ps.sort(key=lambda p: p['lock'])
    seq = R[key]['seq']
    n = len(ps)
    for s in range(21, n - K - 1, 7):
        w = ps[s:s + K + 1]                     # K decisions + the start state after them
        if len(w) < K + 1: break
        dec = w[:K]
        if not all(p['verified'] for p in w): continue
        if any(abs(p['gmult'] - 1) > 1e-9 for p in dec): continue
        st = dict(dec[0])
        cur = st['seqIndex']; nn = len(st['next'])
        st['future'] = list(seq[cur + 1 + nn: cur + 1 + nn + K + 2])
        st['k'] = K
        st['garbage_schedule'] = [p['played']['tanks'] for p in dec]
        st['incoming_schedule'] = [p['incoming'] for p in dec]
        st['player_window'] = [{'piece': p['played']['piece'], 'lines': p['played']['lines'], 'spin': p['played']['spin'],
                                'raw': p['played']['raw'], 'cells': p['played']['cells'], 'b2b': p['b2b'], 'combo': p['combo']} for p in dec]
        st['player_end'] = {'field': w[K]['field'], 'b2b': w[K]['b2b'], 'combo': w[K]['combo'], 'hold': w[K]['hold']}
        out.append(st)
open('rollouts.jsonl', 'w').write('\n'.join(json.dumps(o) for o in out) + '\n')
print('windows', len(out), collections.Counter(o['user'] for o in out))
