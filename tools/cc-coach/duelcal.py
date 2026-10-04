import json, statistics as st
def load(f): return {g['id']: g for g in map(json.loads, open(f)) if 'error' not in g and g.get('duel')}
def q(xs, f): xs = sorted(xs); return xs[min(len(xs)-1, int(f*len(xs)))]
def reg(g):
    d = g['duel']
    if d['player'] is None or d['cc'] is None: return None
    return d['cc'] - d['player']
A = {m: load(f'duel-40k-{m}.jsonl') for m in (20000, 80000, 320000)}
ids = set.intersection(*[set(a) for a in A.values()])
for m, a in A.items():
    r = [reg(a[i]) for i in ids if reg(a[i]) is not None]
    print(f'duel M={m}: player regret median {st.median(r):.0f} p75 {q(r,.75):.0f} p90 {q(r,.9):.0f}  negative(player better) {sum(x<0 for x in r)}  zero {sum(x==0 for x in r)} n {len(r)}')
# stability across M
for lo in (20000, 80000):
    xs=[];ys=[]
    for i in ids:
        a, b = reg(A[lo][i]), reg(A[320000][i])
        if a is None or b is None: continue
        xs.append(a); ys.append(b)
    mx,my=st.mean(xs),st.mean(ys)
    r=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/(sum((x-mx)**2 for x in xs)**.5*sum((y-my)**2 for y in ys)**.5)
    for T in (100, 200, 300, 500):
        hit=[(x>=T) for x in xs]; ref=[(y>=T/2) for y in ys]
        prec = sum(1 for h,f in zip(hit,ref) if h and f)/max(1,sum(hit))
        print(f'  M={lo} vs 320k: r={r:.3f}  T={T}: flagged {sum(hit)}, of which still >= T/2 at 320k: {prec:.2%}')
# noise floor: how does a WEAKER cold-clear (10k main search) fare under the same duel judge (80k)?
W = load('duel-10000-80000.jsonl'); S = load('duel-160000-80000.jsonl'); M = A[80000]
for name, X in (('cc@10k', W), ('cc@40k', M), ('cc@160k', S)):
    # regret of X's pick relative to the 160k pick, both judged by the 80k duel
    r = [S[i]['duel']['cc'] - X[i]['duel']['cc'] for i in ids if i in X and i in S and X[i]['duel']['cc'] is not None and S[i]['duel']['cc'] is not None]
    print(f'{name} pick vs cc@160k pick (duel 80k): median {st.median(r):.0f} p75 {q(r,.75):.0f} p90 {q(r,.9):.0f} p95 {q(r,.95):.0f} n {len(r)}')
r = [S[i]['duel']['cc'] - S[i]['duel']['player'] for i in ids if i in S and S[i]['duel']['player'] is not None and S[i]['duel']['cc'] is not None]
print(f'human vs cc@160k pick (duel 80k): median {st.median(r):.0f} p75 {q(r,.75):.0f} p90 {q(r,.9):.0f} p95 {q(r,.95):.0f} n {len(r)}')
