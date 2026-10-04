import json, collections
exec(open('grade-analyze.py').read().split("by = collections.defaultdict(list)")[0])   # reuse rows + cat()
G = {g['id']: g for g in map(json.loads, open('grade-mid.jsonl')) if 'error' not in g}
seqs = collections.defaultdict(dict)
for p in P.values(): seqs[p['id'].rsplit('/',1)[0]][p['lock']] = p
def human_next(i, n=6):
    k, l = i.rsplit('/',1); l = int(l); out = []
    for j in range(l, l+n):
        p = seqs[k].get(j)
        if not p: break
        pl = p['played']; out.append('tsd' if pl['spin']=='normal' and pl['lines']==2 else 'tst' if pl['spin']=='normal' and pl['lines']==3 else 'quad' if pl['lines']==4 and pl['spin']=='none' else 'x')
    return out
for u in ('yachi','pinglamb'):
    rs = [r for r in rows if r['user']==u and r['reg']>=600 and cat(r).startswith('setup')]
    cc_pay = sum(1 for r in rs if any(s['kind'] in ('tsd','tst','quad') for s in G[r['id']]['plan'][:6]))
    hu_pay = sum(1 for r in rs if any(k in ('tsd','tst','quad') for k in human_next(r['id'])))
    grp = collections.Counter(min(('tslot','well','surface','holes','height','b2b_state'), key=lambda k: r['delta'][k]) for r in rs)
    print(u, len(rs), f'cc plan reaches TSD/TST/quad within 6 pieces: {cc_pay/len(rs):.0%}; you actually did within 6: {hu_pay/len(rs):.0%}', 'largest 1-ply deficit:', grp.most_common())
    allm = [r for r in rows if r['user']==u]
    cc_pay_all = sum(1 for r in allm if any(s['kind'] in ('tsd','tst','quad') for s in G[r['id']]['plan'][:6]))/len(allm)
    hu_pay_all = sum(1 for r in allm if any(k in ('tsd','tst','quad') for k in human_next(r['id'])))/len(allm)
    print('   baseline over all decisions: cc plan', f'{cc_pay_all:.0%}', 'you', f'{hu_pay_all:.0%}')
