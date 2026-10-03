import json, statistics as st
def load(n): return {g['id']: g for g in map(json.loads, open(f'calib-{n}.jsonl')) if 'error' not in g}
ref = load(640000)
def key(piece, cells): return piece + json.dumps(sorted(cells))
def vmap(g): return {key(a[0], a[1]): a[2] for a in g['all']}
def q(xs, f): xs = sorted(xs); return xs[min(len(xs)-1, int(f*len(xs)))]
R = {i: vmap(g) for i, g in ref.items()}
best = {i: max(v.values()) for i, v in R.items()}
for n in (10000, 40000, 160000, 640000):
    G = load(n)
    reg = []; same = 0; preg = []; pl_loss_n = []
    for i, g in G.items():
        v = R[i]; k = key(g['pick']['piece'], g['pick']['cells'])
        if k not in v: continue
        reg.append(best[i] - v[k]); same += (k == key(ref[i]['pick']['piece'], ref[i]['pick']['cells']))
        if g['player'].get('found'): pl_loss_n.append(g['best']['value'] - g['player']['value'])
    print(f'N={n:>6}: CC-pick regret vs 640k  median {st.median(reg):5.0f}  p75 {q(reg,.75):5.0f}  p90 {q(reg,.9):5.0f}  p95 {q(reg,.95):5.0f}  same-pick {same}/{len(reg)}')
# the player's regret measured by the 640k reference
pl = []
for i, g in ref.items():
    p = g['player']
    if p.get('found'): pl.append(best[i] - p['value'])
print('player regret @640k: median', st.median(pl), 'p75', q(pl,.75), 'p90', q(pl,.9), 'zero', sum(x==0 for x in pl), '/', len(pl))
# stability of the player's loss across budgets
import itertools
for a in (10000, 40000, 160000):
    A = load(a)
    xs = []; ys = []
    for i in ref:
        if A[i]['player'].get('found') and ref[i]['player'].get('found'):
            xs.append(A[i]['best']['value'] - A[i]['player']['value']); ys.append(best[i] - ref[i]['player']['value'])
    mx, my = st.mean(xs), st.mean(ys)
    cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys)); r = cov / (sum((x-mx)**2 for x in xs)**.5 * sum((y-my)**2 for y in ys)**.5)
    big_ref = [y >= 100 for y in ys]; big_a = [x >= 100 for x in xs]
    agree = sum(1 for p, q_ in zip(big_ref, big_a) if p == q_)
    print(f'player-loss @{a} vs @640k: pearson r={r:.3f}; ">=100 loss" classification agrees {agree}/{len(xs)}')
