# Stage 4: per clip, the LOWER median of 8 seeds; annotate human steps with the verified-prefix flag
# and the graded duel loss; write clips-chosen.json and readable dumps.
import json, sys, os
OUT = sys.argv[1]
S = [json.load(open(f'{OUT}/clips-s{s}.json')) for s in range(8)]
P = {json.loads(l)['id']: json.loads(l) for l in open('positions.jsonl')}
G = {}
for l in open('grade-mid.jsonl'):
    g = json.loads(l)
    if 'error' not in g and g.get('duel') and g['duel']['player'] is not None and g['duel']['cc'] is not None: G[g['id']] = g['duel']['cc'] - g['duel']['player']
chosen = []
for i, c0 in enumerate(S[0]):
    tot = [S[s][i]['totals']['cc'] for s in range(8)]; target = sorted(tot)[3]
    s = min(s for s in range(8) if S[s][i]['totals']['cc'] == target)
    c = dict(S[s][i]); c['seed'] = s; c['seedTotals'] = tot
    k, l0 = c['id'].rsplit('/', 1); l0 = int(l0)
    for j, st in enumerate(c['human']):
        pid = f'{k}/{l0 + j}'; st['verified'] = P[pid]['verified']; st['loss'] = G.get(pid)
    chosen.append(c)
json.dump(chosen, open(f'{OUT}/clips-chosen.json', 'w'))
os.makedirs(f'{OUT}/clipdump', exist_ok=True)
def rows(f, mark=()):
    g = [list(r) for r in f]
    for c, r in mark: g[r][c] = '*'
    top = min([r for r in range(40) if any(ch != '.' for ch in g[r])] + [39])
    return [f'{40-r:2d} ' + ''.join(g[r]) for r in range(max(0, top - 1), 40)]
for n, c in enumerate(chosen):
    L = [f'clip {n}: {c["id"]}  source={c["source"]}  cold-clear seed={c["seed"]} (cc 14-piece attack over 8 seeds: {sorted(c["seedTotals"])}; this run is the LOWER median)',
         f'start: current {c["start"]["current"]} hold {c["start"]["hold"]} next {c["start"]["next"]} b2b {c["start"]["b2b"]} combo {c["start"]["combo"]}  future reveal {"".join(c["future"])}',
         'Board rows: row number counts from the bottom (1 = floor). Letters = stack, G = garbage, * = the piece placed this step. The board shown is BEFORE the step (pre-clear).', '']
    for side in ('human', 'cc'):
        L.append(f'===== {side.upper()} =====  total attack {c["totals"][side]}')
        for j, s in enumerate(c[side]):
            if s.get('dead'): L.append(f'step {j+1}: TOPPED OUT'); break
            ex = f' verified_prefix={s["verified"]} duel_loss={s["loss"]}' if side == 'human' else ''
            L.append(f'--- {side} step {j+1}: {s["piece"]}{" (from hold)" if s["hold"] else ""} lines={s["lines"]} spin={s["spin"]} attack={s["attack"]} b2b={s["b2b"]} combo={s["combo"]} garbage_in_after={s["garbage"]}{ex}')
            L += rows(s['before'], s['cells'])
        last = [s for s in c[side] if not s.get('dead')][-1]
        L.append(f'--- {side} board AFTER its last step:'); L += rows(last['after'])
    open(f'{OUT}/clipdump/{n:02d}.txt', 'w').write('\n'.join(L) + '\n')
print('clips', len(chosen), [(c['id'], c['source'], c['seed'], c['totals']) for c in chosen])
