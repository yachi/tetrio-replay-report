import json, sys, random, collections, statistics as st
f = sys.argv[1]
W = {o['id']: o for o in map(json.loads, open('rollouts.jsonl'))}
R = [json.loads(l) for l in open(f)]
def boot(xs_by_cluster, B=2000):
    keys = list(xs_by_cluster); random.seed(1); out = []
    for _ in range(B):
        s = [k for k in (random.choice(keys) for _ in keys)]
        h = sum(xs_by_cluster[k][0] for k in s); c = sum(xs_by_cluster[k][1] for k in s); n = sum(xs_by_cluster[k][2] for k in s)
        out.append((c - h) / n)
    out.sort(); return out[int(.025*B)], out[int(.975*B)]
for u in ('yachi', 'pinglamb'):
    rs = [r for r in R if r['user'] == u]
    cl = collections.defaultdict(lambda: [0, 0, 0])
    for r in rs:
        k = r['id'].rsplit('/', 1)[0]
        cl[k][0] += r['human']['attack']; cl[k][1] += r['cc']['attack']; cl[k][2] += 14
    lo, hi = boot(cl)
    H = sum(r['human']['attack'] for r in rs) / (14*len(rs)); C = sum(r['cc']['attack'] for r in rs) / (14*len(rs))
    print(f'{u}: APP human {H:.3f} cc {C:.3f}  diff {C-H:+.3f}  95% CI (round-clustered bootstrap) [{lo:+.3f}, {hi:+.3f}]  rounds {len(cl)}')
    # excluding windows where cc topped out (those truncate cc's attack, so the gap is conservative)
    alive = [r for r in rs if not r['cc']['dead']]
    print(f'   cc topped out in {len(rs)-len(alive)} windows; gap over the rest {sum(r["cc"]["attack"]-r["human"]["attack"] for r in alive)/(14*len(alive)):+.3f}')
    for label, keyf in (('start height', lambda r: '0-5' if r['start_height'] <= 5 else '6-9' if r['start_height'] <= 9 else '10-13' if r['start_height'] <= 13 else '14+'),
                        ('b2b live at start', lambda r: str(r['start_b2b'] >= 0)),
                        ('garbage received in window', lambda r: (lambda g: '0' if g == 0 else '1-4' if g <= 4 else '5+')(sum(t['amount'] for ts in W[r['id']]['garbage_schedule'] for t in ts)))):
        g = collections.defaultdict(list)
        for r in rs: g[keyf(r)].append(r)
        print(f'   by {label}: ' + '  '.join(f'{k}: {sum(x["cc"]["attack"]-x["human"]["attack"] for x in v)/(14*len(v)):+.3f} APP (n={len(v)})' for k, v in sorted(g.items())))
print('--- exogenous pressure strata (fixed at window start)')
for u in ('yachi', 'pinglamb'):
    rs = [r for r in R if r['user'] == u]
    for label, keyf in (('garbage rows on board at start', lambda r: (lambda g: '0' if g == 0 else '1-3' if g <= 3 else '4-7' if g <= 7 else '8+')(sum(1 for row in W[r['id']]['field'] if 'G' in row))),
                        ('garbage queued at start', lambda r: (lambda g: '0' if g == 0 else '1-4' if g <= 4 else '5+')(W[r['id']]['incoming']))):
        g = collections.defaultdict(list)
        for r in rs: g[keyf(r)].append(r)
        print(f'{u} by {label}: ' + '  '.join(f'{k}: human {sum(x["human"]["attack"] for x in v)/(14*len(v)):.3f} cc {sum(x["cc"]["attack"] for x in v)/(14*len(v)):.3f} (n={len(v)})' for k, v in sorted(g.items())))
