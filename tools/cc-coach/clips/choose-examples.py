# Stage 2: keep candidates still >= 600 when re-judged at 160k main / 320k duel, then take the
# highest confirmed miss per category (distinct rounds, a full 14-piece window after it).
import json, sys
OUT = sys.argv[1]; K = 14
P = {json.loads(l)['id'] for l in open('positions.jsonl')}
cats = json.load(open(f'{OUT}/candidate-cats.json'))
V = [json.loads(l) for l in open(f'{OUT}/verify-out.jsonl')]
ok = [v for v in V if v.get('duel') and v['duel']['player'] is not None and v['duel']['cc'] is not None and v['duel']['cc'] - v['duel']['player'] >= 600]
ok.sort(key=lambda v: -(v['duel']['cc'] - v['duel']['player']))
ORDER = ['missed a quad cc took', 'made a hole / overhang', 'burned 1-3 lines cc kept', 'missed a T-spin cc took',
         'spent T without a spin (cc saved it)', "didn't clear when cc cleaned up", 'setup/sequence (only shows with look-ahead)',
         'bumpy surface', 'stacked higher']
chosen, rounds = [], set()
for c in ORDER:
    for v in ok:
        k, l = v['id'].rsplit('/', 1)
        if cats[v['id']] != c or k in rounds: continue
        if not all(f'{k}/{int(l) + j}' in P for j in range(K + 1)): continue
        chosen.append({'id': v['id'], 'category': c, 'regret160': v['duel']['cc'] - v['duel']['player']}); rounds.add(k); break
    if len(chosen) == 7: break
json.dump(chosen, open(f'{OUT}/examples.json', 'w'), indent=1)
print('confirmed', len(ok), 'of', len(V), '| chosen', [(e['category'], e['regret160']) for e in chosen])
