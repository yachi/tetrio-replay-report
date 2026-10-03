# Independent check of the extraction: start field + played cells -> clear -> insert the tanked
# garbage (bottom, hole at the recorded column) must reproduce the NEXT decision's field exactly.
import json, collections
P = [json.loads(l) for l in open('positions.jsonl')]
by = collections.defaultdict(list)
for p in P: by[(p['file'], p['round'], p['user'])].append(p)
def step(field, cells, tanks):
    g = [list(r) for r in field]
    for c, r in cells: g[r][c] = 'X'
    g = [r for r in g if not all(ch != '.' for ch in r)]
    g = [['.'] * 10 for _ in range(40 - len(g))] + g
    for t in tanks:
        for _ in range(t['amount']):
            g = g[1:] + [['G' if x != t['column'] else '.' for x in range(10)]]
    return [''.join('#' if ch != '.' else '.' for ch in r) for r in g]
norm = lambda f: [''.join('#' if ch != '.' else '.' for ch in r) for r in f]
ok = bad = 0; ex = []
for k, ps in by.items():
    ps.sort(key=lambda p: p['lock'])
    for a, b in zip(ps, ps[1:]):
        if step(a['field'], a['played']['cells'], a['played']['tanks']) == norm(b['field']): ok += 1
        else:
            bad += 1
            if len(ex) < 5: ex.append(a['id'])
print('board transitions reproduced', ok, 'mismatch', bad, ex)
