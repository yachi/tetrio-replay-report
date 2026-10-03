# Stage 1 of a player's clip set: the per-move clear misses (>= 600) at mid stack heights, top 10
# per category — the same rule for every player. Reads positions.jsonl, grade-mid.jsonl and mid.jsonl
# from the work directory (the cwd), as the top-level pipeline in ../README.md leaves them.
import json, sys, collections, os
HERE = os.path.dirname(os.path.abspath(__file__))
PLAYER, OUT = sys.argv[1], sys.argv[2]
sys.argv = sys.argv[:1]  # grade-analyze reads argv[1] as its grade file; keep its default
exec(open(os.path.join(HERE, '..', 'grade-analyze.py')).read().split("by = collections.defaultdict(list)")[0])
M = {json.loads(l)['id']: l for l in open('mid.jsonl')}
c = [r for r in rows if r['user'] == PLAYER and r['reg'] >= 600 and 5 <= r['maxh'] <= 15]
byc = collections.defaultdict(list)
for r in c: byc[cat(r)].append(r)
pick = []
for k, v in byc.items(): v.sort(key=lambda r: -r['reg']); pick += v[:10]
open(f'{OUT}/verify.jsonl', 'w').write(''.join(M[r['id']] if M[r['id']].endswith('\n') else M[r['id']] + '\n' for r in pick))
json.dump({r['id']: cat(r) for r in pick}, open(f'{OUT}/candidate-cats.json', 'w'))
print(PLAYER, len(pick), {k: len(v) for k, v in byc.items()})
