import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
# Stage 4: choose the shown Cold Clear run per clip (median of 5 seeds by 4-piece attack, then by
# holes), keep 2 examples per (habit, night) whose frames passed every self-check in all 5 seeds,
# compute caption facts from the data, trim boards, write habit-clips.json.
import json, os, sys, collections, statistics
S = CC_WORK + ''
D = S + '/scen/hclips'; H = S + '/scen/habits'; C = S + '/corpus'
sys.path.insert(0, D); sys.path.insert(0, H)
import meta
from Y6_common import slots as tsd_slots
# copied verbatim from scen/holes_build.py (importing it rebuilds its row cache)
def _hb_covered(g):
    """set of empty cells with a filled cell somewhere above in the same column"""
    s = set()
    for c in range(10):
        seen = False
        for r in range(40):
            if g[r][c] != '.': seen = True
            elif seen: s.add((c, r))
    return s
def classify(g, cov, cells):
    """split covered cells into overhang (4-connected empty region touches an uncovered empty cell) vs sealed"""
    oh = sd = 0
    for cell in cells:
        st_ = [cell]; vis = {cell}; open_ = False
        while st_:
            x, y = st_.pop()
            if (x, y) not in cov: open_ = True; break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 40 and g[ny][nx] == '.' and (nx, ny) not in vis:
                    vis.add((nx, ny)); st_.append((nx, ny))
        if open_: oh += 1
        else: sd += 1
    return oh, sd
def counts(g):
    """covered cells; open = its empty 4-connected component contains an uncovered empty cell (reachable by tuck/spin), else sealed"""
    cov = _hb_covered(g); comp = {}; oh = sd = 0
    for cell in cov:
        if cell in comp: continue
        stack = [cell]; members = [cell]; comp[cell] = None; op = False
        while stack:
            x, y = stack.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 40 and g[ny][nx] == '.':
                    if (nx, ny) not in cov: op = True
                    elif (nx, ny) not in comp:
                        comp[(nx, ny)] = None; members.append((nx, ny)); stack.append((nx, ny))
        for m in members: comp[m] = op
        if op: oh += len(members)
        else: sd += len(members)
    return len(cov), oh, sd
hcounts = counts
SEEDS = [0, 1, 2, 3, 4]; K = 4; MINROWS = 22; KEEP = 2
HABITS = 'Y1 Y2 Y3 Y4 Y5 Y6 P1 P2 P3 P4 P5 P6'.split()
SESS = sorted(f[:-6] for f in os.listdir(C) if f.endswith('.jsonl') and f[:4] == '2026')
cands = json.load(open(f'{D}/candidates.json'))
P = {json.loads(l)['id']: json.loads(l) for l in open(f'{D}/windows.jsonl')}
FR = {s: {c['id']: c for c in json.load(open(f'{D}/frames-s{s}.json'))} for s in SEEDS}
CK = {s: {c['id']: c for c in json.load(open(f'{D}/frames-check-s{s}.json'))} for s in SEEDS}
ids = {c['occ']['id'] for v in cands.values() for c in v}
G = {}
for fn in (f'{C}/grade.jsonl', f'{H}/Y6.extra-grade.jsonl'):
    for l in open(fn):
        i = l[l.index('"id":"') + 6:]; i = i[:i.index('"')]
        if i in ids and i not in G:
            g = json.loads(l)
            if 'error' not in g: G[i] = g

# ---- board helpers (holes_build semantics: covered = empty with a filled cell above, post-clear)
def covered(f):
    n = 0
    for c in range(10):
        seen = False
        for r in range(40):
            if f[r][c] != '.': seen = True
            elif seen: n += 1
    return n
def maxh(f):
    for r in range(40):
        if f[r] != '..........': return 40 - r
    return 0
def garbage_rows(f): return sum(1 for r in f if 'G' in r)
def apply(f, cells):
    g = [list(r) for r in f]
    for x, y in cells: g[y][x] = '#'
    g = [r for r in g if '.' in r]
    g = [['.'] * 10 for _ in range(40 - len(g))] + g
    return [''.join(r) for r in g]
def well_ready(F):  # b2b_hold.py qr: rows directly above a column's top that are full except that column
    best, bc = 0, None
    for c in range(10):
        top = next((r for r in range(40) if F[r][c] != '.'), 40); d = 0; r = top - 1
        while r >= 0 and all(F[r][x] != '.' for x in range(10) if x != c) and F[r][c] == '.': d += 1; r -= 1
        if d > best: best, bc = d, c
    return best, bc
def cols1(cells): return sorted({x + 1 for x, y in cells})
def mv_key(m): return (m['piece'], bool(m['hold']), tuple(sorted(map(tuple, m['cells']))))

def outcome(fr, side):
    steps = [s for s in fr[side] if not s.get('dead')]
    dead = any(s.get('dead') for s in fr[side])
    last = steps[-1]['after'] if steps else None
    return {'attack': sum(s['attack'] for s in steps), 'lines': sum(s['lines'] for s in steps),
            'pieces_played': len(steps), 'topped_out': dead,
            'covered_cells_end': covered(last) if last else None, 'max_height_end': maxh(last) if last else None,
            'garbage_received': sum(s['garbage'] for s in steps)}

def first_move_facts(start, m, lines):
    after = apply(start, m['cells'])
    return {'piece': m['piece'], 'from_hold': bool(m['hold']), 'columns': cols1(m['cells']), 'lines': lines,
            'covered_cells_created': covered(after) - covered(start)}

def build_clip(hab, night, cand):
    o = cand['occ']; i = o['id']
    fails = [s for s in SEEDS if not FR[s][i]['ok']]
    if fails: return None, {'id': i, 'why': 'self-check failed', 'seeds': fails, 'detail': [CK[s][i]['why'] for s in fails]}
    st = P[i]; start = st['field']
    runs = []
    for s in SEEDS:
        fr = FR[s][i]; oc = outcome(fr, 'cc')
        sortkey = (-1 if oc['topped_out'] else 0, oc['attack'], -(oc['covered_cells_end'] if oc['covered_cells_end'] is not None else 999), -s)
        runs.append((sortkey, s, oc))
    order = sorted(runs, key=lambda r: r[0])
    shown = order[2][1]                     # median of 5: index 2, worst-to-best order; ties -> lower seed sorts later
    fr = FR[shown][i]
    first = {s: (FR[s][i]['cc'][0] if FR[s][i]['cc'] and not FR[s][i]['cc'][0].get('dead') else None) for s in SEEDS}
    fk = {s: (mv_key(m) if m else None) for s, m in first.items()}
    same_first = [s for s in SEEDS if fk[s] == fk[shown]]
    g = G.get(i); gp = g['pick'] if g else None
    graded_eq = (mv_key(gp) == fk[shown]) if gp else None
    hum = fr['human']; cc = fr['cc']
    # trimming: one row count for every board in this clip
    boards = [start] + [s['after'] for s in hum] + [s['after'] for s in cc if not s.get('dead')]
    top = max([maxh(b) for b in boards] + [40 - min(y for s in hum + [x for x in cc if not x.get('dead')] for x_, y in s['cells'])])
    R = max(MINROWS, top + 1); off = 40 - R
    tb = lambda f: f[off:]
    tc = lambda cells: [[x, y - off] for x, y in cells]
    def tstep(s, human):
        if s.get('dead'): return {'dead': True, 'why': s.get('why')}
        d = {'piece': s['piece'], 'hold': bool(s['hold']), 'cells': tc(s['cells']), 'lines': s['lines'],
             'cleared_rows': [r - off for r in s['cleared']], 'spin': s['spin'], 'attack': s['attack'],
             'b2b': s['b2b'], 'combo': s['combo'], 'garbage_in': s['garbage'], 'after': tb(s['after'])}
        if human: d.update({'tanks': s['tanks'], 'verified': s['verified'], 'queue': {'current': s['current'], 'hold': s['holdPiece'], 'next': s['next']}})
        else: d['kind'] = s['kind']
        return d
    wr, wc = well_ready(start); sl = tsd_slots([[c != '.' for c in row] for row in start])
    hm0, cm0 = hum[0], (cc[0] if cc and not cc[0].get('dead') else None)
    facts = {
        'max_height_before': maxh(start), 'garbage_rows_before': garbage_rows(start), 'covered_cells_before': covered(start),
        'incoming_before': st['incoming'], 'b2b_before': st['b2b'], 'combo_before': st['combo'],
        'current': st['current'], 'hold': st['hold'], 'next': st['next'],
        'well_rows_ready': wr, 'well_column': (wc + 1) if wc is not None else None,
        'quad_available': wr >= 4 and 'I' in (st['current'], st['hold']),
        'tsd_slot_ready': len(sl) > 0, 'tsd_available': len(sl) > 0 and 'T' in (st['current'], st['hold']),
        'player_first': first_move_facts(start, {'piece': hm0['piece'], 'hold': hm0['hold'], 'cells': hm0['cells']}, hm0['lines']),
        'cc_first': first_move_facts(start, cm0, cm0['lines']) if cm0 else None,
        'player_4': outcome(fr, 'human'), 'cc_4': outcome(fr, 'cc'),
        'columns_note': 'columns are 1-based from the left; covered cells = empty cells with a filled cell above in the same column, counted after line clears',
    }
    # does the SHOWN Cold Clear first move contrast with the habit, by the habit's own test?
    def sealed_delta(m): return hcounts([list(r) for r in apply(start, m['cells'])])[2] - hcounts([list(r) for r in start])[2]
    def cov_delta(m): return covered(apply(start, m['cells'])) - covered(start)
    det = o['detail']; ct, crule = None, None
    if cm0:
        if hab in ('Y1', 'P1'): crule = 'cc first move creates no covered cell'; ct = cov_delta(cm0) <= 0
        elif hab in ('Y4', 'P2'): crule = 'cc first move creates no sealed cell'; ct = sealed_delta(cm0) <= 0
        elif hab in ('Y2', 'P5'): crule = 'cc first move clears at least one line'; ct = cm0['lines'] >= 1
        elif hab in ('Y3', 'P6'): crule = 'cc first move is a quad'; ct = cm0['lines'] == 4
        elif hab == 'Y6': crule = 'cc first move is a TSD'; ct = cm0['kind'] == 'tsd'
        elif hab == 'P3': crule = 'cc first move clears no line'; ct = cm0['lines'] == 0
        elif hab == 'P4':
            crule = 'cc first move centroid is not on the taller half'; cx = sum(x for x, y in cm0['cells']) / 4
            ct = (cx < 4.5) != det['tall_half'].startswith('left')
        elif hab == 'Y5':
            crule = 'cc first move does not bury an open garbage hole (a cell in that column above the hole and covered cells rise)'
            bur = any(x == h_['column'] and y < h_['row'] for h_ in det['open_holes'] for x, y in cm0['cells']) and cov_delta(cm0) > 0
            ct = not bur
    facts['cc_first_contrasts_with_habit'] = ct; facts['contrast_rule'] = crule
    clip = {
        'id': i, 'habit': hab, 'night': night, 'player': o['player'], 'file': st['file'], 'round': st['round'], 'lock': st['lock'],
        'regret': o['regret'], 'misdrop_shaped': o['misdrop_shaped'], 'why_picked': cand['why'],
        'detector_detail': o['detail'], 'rows': R,
        'start': {'field': tb(start), 'current': st['current'], 'hold': st['hold'], 'next': st['next'], 'b2b': st['b2b'],
                  'combo': st['combo'], 'incoming': st['incoming']},
        'human': [tstep(s, True) for s in hum],
        'cc': [tstep(s, False) for s in cc],
        'cc_run': {'nodes': 40000, 'seeds': SEEDS, 'shown_seed': shown,
                   'rule': 'median of the 5 seeds ordered by 4-piece attack, then by covered cells at the end (more = worse), topped-out runs lowest; ties broken by seed',
                   'per_seed': [{'seed': s, 'attack': oc['attack'], 'covered_cells_end': oc['covered_cells_end'], 'topped_out': oc['topped_out'],
                                 'first_move': ({'piece': first[s]['piece'], 'hold': bool(first[s]['hold']), 'cells': tc(first[s]['cells'])} if first[s] else None)}
                                for _, s, oc in sorted(runs, key=lambda r: r[1])],
                   'first_move_same_as_shown': len(same_first), 'first_move_same_seeds': same_first,
                   'first_move_equals_graded_pick': graded_eq,
                   'graded_pick_note': 'graded pick = cc seed-0 pick at 20000 nodes in grade.jsonl (Y6 extra positions: Y6.extra-grade.jsonl, same settings); the rollout searches 40000 nodes'},
        'facts': facts,
    }
    clip['future_revealed'] = ROLL[i]['future']
    return clip, None

ROLL = {json.loads(l)['id']: json.loads(l) for l in open(f'{D}/rollin.jsonl')}
def nights_of(h):
    d = json.load(open(f'{H}/{h}.nights.json'))
    n = d['nights']
    if isinstance(n, list): n = {e['session']: e for e in n}
    return d, n
out = {'generated_by': 'scen/hclips/{select.py,frames.ts,finalize.py}', 'window_pieces': K,
       'cc_settings': {'mode': 'rollout', 'nodes': 40000, 'seeds': SEEDS},
       'board_rows_note': 'every board keeps its bottom `rows` rows (row 0 = top of the kept area); cells use the same trimmed row index',
       'selection_rule': 'per habit and night: verified occurrences, misdrop-shaped excluded unless the habit is misdrop-shaped by definition (Y1, P1, Y6), soft preferences for Y2/P5 (Cold Clear clear without hold) and Y3 (the two main decline classes); regret nearest the median regret of that pool; distinct rounds; window of 4 verified recorded locks plus the next decision',
       'habits': []}
dropped = []; log = json.load(open(f'{D}/select-log.json'))
counts = {}
for h in HABITS:
    nd, nights = nights_of(h)
    hab = {'id': h, 'player': nd['player'], 'name': meta.NAMES[h], 'definition': nd['definition'].replace('adds nothing for him', 'adds nothing for pinglamb'), 'cc_comparison': meta.CC[h],
           'pooled': nd.get('pooled'), 'nights': {}}
    for k in ('nights_gap_negative', 'nights_gap_positive', 'night_sign_test', 'p10_piece_time', 'reproduce', 'min_height', 'title'):
        if k in nd: hab.setdefault('extra', {})[k] = nd[k]
    for s in SESS:
        ex = []
        for cand in cands.get(f'{h}/{s}', []):
            if len(ex) == KEEP: break
            c, err = build_clip(h, s, cand)
            if err: dropped.append({'habit': h, 'night': s, **err}); continue
            ex.append(c)
        rates = dict(nights[s]); rates.pop('session', None)
        hab['nights'][s] = {'rates': rates, 'pool': log['pools'].get(f'{h}/{s}'), 'examples': ex}
        counts[f'{h}/{s}'] = len(ex)
    out['habits'].append(hab)
out['log'] = {'dropped_clips': dropped, 'habit_nights_without_examples': [k for k, v in counts.items() if v == 0],
              'habit_nights_with_one_example': [k for k, v in counts.items() if v == 1],
              'selection_empty': log['empty'], 'windows_skipped': log['short_windows']}
json.dump(out, open(f'{S}/scen/habit-clips.json', 'w'), separators=(',', ':'))
print('clips', sum(counts.values()), 'dropped', len(dropped), 'zero', out['log']['habit_nights_without_examples'],
      'one', out['log']['habit_nights_with_one_example'], 'size', os.path.getsize(f'{S}/scen/habit-clips.json'))
