# Clip inputs: rollout windows starting at each of the 7 verified example positions, plus 5
# rollout windows from the 40k run chosen near the 75th-90th percentile of yachi's gap
# (representative, not cherry-picked extremes).
import json, collections
K = 14
P = {json.loads(l)['id']: json.loads(l) for l in open('positions.jsonl')}
R = {(r['file'], r['round'], r['user']): r for r in json.load(open('positions.jsonl.rounds.json'))}
ex = [e['id'] for e in json.load(open('examples.json'))]
pr = [json.loads(l) for l in open('rollouts-40k.priced.jsonl')]
y = sorted([r for r in pr if r['user'] == 'yachi' and not r['cc']['dead']], key=lambda r: r['diff'])
n = len(y); picks = [y[int(n * q)]['id'] for q in (0.5, 0.75, 0.8, 0.85, 0.9)]
out = []
for i in ex + picks:
    k, l = i.rsplit('/', 1); l = int(l)
    w = [P.get(f'{k}/{j}') for j in range(l, l + K + 1)]
    if any(x is None for x in w): print('short window', i); continue
    st = dict(w[0]); seq = R[(st['file'], st['round'], st['user'])]['seq']
    cur = st['seqIndex']; nn = len(st['next'])
    st['future'] = list(seq[cur + 1 + nn: cur + 1 + nn + K + 2]); st['k'] = K
    st['garbage_schedule'] = [x['played']['tanks'] for x in w[:K]]
    st['incoming_schedule'] = [x['incoming'] for x in w[:K]]
    st['clip_source'] = 'example' if i in ex else 'percentile'
    out.append(st)
open('clips-in.jsonl', 'w').write('\n'.join(json.dumps(o) for o in out) + '\n')
print(len(out), picks)
