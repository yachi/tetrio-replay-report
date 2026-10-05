import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
# Writes the yachi in-slot T positions that grade.jsonl does not already hold, for an extra cc-coach run with the
# SAME settings (CC_NODES=20000 COACH_DUEL=20000 COACH_SEED=0); identical input + seed is byte-identical output.
import json, sys
sys.path.insert(0, CC_WORK + '/scen/habits')
from Y6_common import *
have = {json.loads(l)['id'] for l in open(f'{CORPUS}/grade.jsonl')}
n = m = 0
with open(f'{HAB}/Y6.extra-in.jsonl', 'w') as o:
    for s, d, *_ in in_slot_positions('yachi'):
        n += 1
        if d['id'] in have: continue
        m += 1; o.write(json.dumps(d) + '\n')
print('yachi in-slot positions', n, 'to grade', m)
