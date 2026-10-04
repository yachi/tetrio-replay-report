import json, sys, collections, statistics as st
G = [json.loads(l) for l in open(sys.argv[1] if len(sys.argv) > 1 else 'grade-mid.jsonl')]
P = {p['id']: p for p in map(json.loads, open('positions.jsonl'))}
T = 600   # "clear mistake": beyond cc@10k's p95 (582) under the same 80k duel judge (calibration)
def q(xs, f): xs = sorted(xs); return xs[min(len(xs)-1, int(f*len(xs)))] if xs else None
GROUPS = ['holes', 'surface', 'height', 'tslot', 'well', 'b2b_state', 'clear_reward', 'wasted_t', 'move_time']
rows = []
for g in G:
    if 'error' in g or not g.get('duel'): continue
    d = g['duel']
    if d['player'] is None or d['cc'] is None: continue
    p = P[g['id']]
    r = d['cc'] - d['player']
    pg, cg = g['player_groups'], g['cc_groups']
    delta = {k: (pg[k] - cg[k]) if pg and cg else 0 for k in GROUPS}
    maxh = max(40 - next((r_ for r_ in range(40) if p['field'][r_][c] != '.'), 40) for c in range(10))
    rows.append(dict(id=g['id'], user=p['user'], reg=r, same=d['same'], piece=p['played']['piece'], held=p['played']['piece'] != p['current'],
        cc_held=g['pick']['hold'], pk=g['player'].get('kind'), ck=g['pick']['kind'], delta=delta, maxh=maxh, inc=p['incoming'],
        b2b=p['b2b'] >= 0, found=g['player']['found'], spin=p['played']['spin'], lines=p['played']['lines'],
        cc_piece=g['pick']['piece'], cc_tspin=g['pick']['tspin']))
by = collections.defaultdict(list)
for r in rows: by[r['user']].append(r)
def cat(r):
    # what kind of difference: by the outcome first, then by the largest static-score deficit
    if r['piece'] == 'T' and r['spin'] == 'none' and r['cc_piece'] != 'T' : return 'spent T without a spin (cc kept it)'
    if r['ck'] in ('tsd', 'tst', 'tss') and r['pk'] not in ('tsd', 'tst', 'tss'): return 'missed an available T-spin'
    if r['ck'] == 'quad' and r['pk'] != 'quad': return 'missed an available quad'
    worst = min(r['delta'], key=lambda k: r['delta'][k])
    return {'holes': 'created holes/overhang', 'surface': 'bumpy surface', 'height': 'stacked higher',
            'tslot': 'lost/didn\'t build a T-slot', 'well': 'blocked the well', 'clear_reward': 'cleared lines cc avoided (burned)',
            'wasted_t': 'used T without spin', 'b2b_state': 'broke back-to-back', 'move_time': 'slow finesse'}[worst]
for u, rs in sorted(by.items()):
    regs = [r['reg'] for r in rs]; n = len(rs)
    mist = [r for r in rs if r['reg'] >= T]
    print(f'\n=== {u}: {n} mid-game decisions graded')
    print(f'  same placement as cold-clear: {sum(r["same"] for r in rs)/n:.1%}   duel regret median {st.median(regs):.0f} p75 {q(regs,.75)} p90 {q(regs,.9)} p95 {q(regs,.95)}')
    print(f'  clear mistakes (regret >= {T}): {len(mist)} = {100*len(mist)/n:.2f} per 100 pieces;  player better than cc pick: {sum(x<0 for x in regs)/n:.1%}')
    print(f'  mean regret {st.mean(regs):.0f};  share of total regret from the >= {T} tail: {sum(r["reg"] for r in mist)/sum(max(0,x) for x in regs):.1%}')
    c = collections.Counter(cat(r) for r in mist)
    for k, v in c.most_common(): print(f'    {v:5d} {100*v/len(mist):5.1f}%  {k}')
    # contexts: mistakes per 100 pieces by height / incoming / piece
    for label, keyf in (('stack height', lambda r: '0-5' if r['maxh'] <= 5 else '6-9' if r['maxh'] <= 9 else '10-13' if r['maxh'] <= 13 else '14+'),
                        ('incoming garbage', lambda r: 'none' if r['inc'] == 0 else '1-3' if r['inc'] <= 3 else '4-7' if r['inc'] <= 7 else '8+'),
                        ('piece', lambda r: r['piece']), ('b2b live', lambda r: str(r['b2b'])), ('held', lambda r: str(r['held']))):
        grp = collections.defaultdict(list)
        for r in rs: grp[keyf(r)].append(r)
        print(f'  by {label}: ' + '  '.join(f'{k}: {100*sum(x["reg"]>=T for x in v)/len(v):.1f}/100 (n={len(v)}, med {st.median([x["reg"] for x in v]):.0f})' for k, v in sorted(grp.items())))
    # T-piece usage
    ts = [r for r in rs if r['piece'] == 'T']
    print(f'  T pieces placed: {len(ts)}; with a line-clearing T-spin: {sum(1 for r in ts if r["spin"]=="normal" and r["lines"]>0)/max(1,len(ts)):.1%};'
          f'  cc spent a T on the same decision: {sum(1 for r in rs if r["cc_piece"]=="T")} of which spun: {sum(1 for r in rs if r["cc_piece"]=="T" and r["ck"] in ("tsd","tst","tss"))}')
    print(f'  holds: you {sum(r["held"] for r in rs)/n:.1%}, cc {sum(r["cc_held"] for r in rs)/n:.1%}; your moves outside cc movegen (180/SRS+): {sum(not r["found"] for r in rs)}')
json.dump(rows, open('grade-rows.json', 'w'))
