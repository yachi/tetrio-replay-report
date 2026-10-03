import json, collections, sys
W = {o['id']: o for o in map(json.loads, open('rollouts.jsonl'))}
R = [json.loads(l) for l in open(sys.argv[1])]
for u in ('yachi', 'pinglamb'):
    H = collections.Counter(); C = collections.Counter()
    for r in R:
        w = W[r['id']]
        if w['user'] != u: continue
        for p in w['player_window']:
            H[p['piece']] += 1
            if p['piece'] == 'I' and p['lines'] == 4: H['I_quad'] += 1
            if p['piece'] == 'I' and 0 < p['lines'] < 4: H['I_burn'] += 1
            if p['piece'] == 'T' and p['spin'] == 'normal' and p['lines'] > 0: H['T_spin'] += 1
            if p['piece'] == 'T' and p['lines'] > 0 and p['spin'] == 'none': H['T_plainclear'] += 1
            if p['lines'] > 0 and p['lines'] < 4 and p['spin'] == 'none': H['plain_clear'] += 1
        for s in r['steps']:
            if s.get('dead'): break
            C[s['piece']] += 1
            if s['piece'] == 'I' and s['lines'] == 4: C['I_quad'] += 1
            if s['piece'] == 'I' and 0 < s['lines'] < 4: C['I_burn'] += 1
            if s['piece'] == 'T' and s['tspin'] == 'Full' and s['lines'] > 0: C['T_spin'] += 1
            if s['piece'] == 'T' and s['lines'] > 0 and s['tspin'] == 'None': C['T_plainclear'] += 1
            if 0 < s['lines'] < 4 and not (s['piece'] == 'T' and s['tspin'] != 'None'): C['plain_clear'] += 1
    for name, X in (('human', H), ('cc', C)):
        n = sum(X[p] for p in 'IOTSZLJ')
        print(f'{u:8s} {name:5s}: I->quad {X["I_quad"]/X["I"]:.1%}  I burned on 1-3 lines {X["I_burn"]/X["I"]:.1%}  T->spin clear {X["T_spin"]/X["T"]:.1%}  T plain clear {X["T_plainclear"]/X["T"]:.1%}  plain 1-3 line clears per 100 pieces {100*X["plain_clear"]/n:.1f}')
