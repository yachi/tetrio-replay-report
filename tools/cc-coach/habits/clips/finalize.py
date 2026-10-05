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
def hb_sealed_set(g):
    """holes_build semantics (P2): covered cells whose empty 4-connected component holds no uncovered empty cell"""
    cov = _hb_covered(g); out = set(); comp = {}
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
        if not op: out.update(members)
    return out
def reach_sealed_set(g):
    """Y4 semantics (verify-holes-H-DECISION-stats.py stats()): empty cells not reachable from the top row"""
    vis = set(); st_ = [(c, 0) for c in range(10) if g[0][c] == '.']; vis.update(st_)
    while st_:
        x, y = st_.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < 10 and 0 <= ny < 40 and g[ny][nx] == '.' and (nx, ny) not in vis:
                vis.add((nx, ny)); st_.append((nx, ny))
    return {(x, y) for y in range(40) for x in range(10) if g[y][x] == '.' and (x, y) not in vis}
SEALED_SET = {'Y4': reach_sealed_set, 'P2': hb_sealed_set}   # each sealing habit's own detector semantics
def new_sealed(hab, f, cells):
    """cells sealed off by this move: sealed after (post-clear) minus the cells already sealed before, mapped through the clear"""
    fn = SEALED_SET[hab]
    g = [list(r) for r in f]
    for x, y in cells: g[y][x] = '#'
    clr = [y for y in range(40) if '.' not in g[y]]
    pre = {(x, y + sum(1 for c in clr if c > y)) for x, y in fn([list(r) for r in f]) if y not in clr}
    return sorted(fn([list(r) for r in apply(f, cells)]) - pre)
# SRS orientations, cells (x right, y down) normalised to their bounding box
_SH = {
 'T': {'spawn': [(1,0),(0,1),(1,1),(2,1)], 'cw': [(0,0),(0,1),(1,1),(0,2)], '180': [(0,0),(1,0),(2,0),(1,1)], 'ccw': [(1,0),(0,1),(1,1),(1,2)]},
 'L': {'spawn': [(2,0),(0,1),(1,1),(2,1)], 'cw': [(0,0),(0,1),(0,2),(1,2)], '180': [(0,0),(1,0),(2,0),(0,1)], 'ccw': [(0,0),(1,0),(1,1),(1,2)]},
 'J': {'spawn': [(0,0),(0,1),(1,1),(2,1)], 'cw': [(0,0),(1,0),(0,1),(0,2)], '180': [(0,0),(1,0),(2,0),(2,1)], 'ccw': [(1,0),(1,1),(0,2),(1,2)]},
 'S': {'flat': [(1,0),(2,0),(0,1),(1,1)], 'upright': [(0,0),(0,1),(1,1),(1,2)]},
 'Z': {'flat': [(0,0),(1,0),(1,1),(2,1)], 'upright': [(1,0),(0,1),(1,1),(0,2)]},
 'I': {'flat': [(0,0),(1,0),(2,0),(3,0)], 'upright': [(0,0),(0,1),(0,2),(0,3)]},
 'O': {'': [(0,0),(1,0),(0,1),(1,1)]},
}
def orientation(piece, cells):
    mx = min(x for x, y in cells); my = min(y for x, y in cells)
    n = sorted((x - mx, y - my) for x, y in cells)
    hit = [k for k, v in _SH[piece].items() if sorted(v) == n]
    assert len(hit) == 1, (piece, cells)
    return hit[0]
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

def first_move_facts(start, m, lines, hab):
    after = apply(start, m['cells'])
    d = {'piece': m['piece'], 'from_hold': bool(m['hold']), 'columns': cols1(m['cells']), 'lines': lines,
         'orientation': orientation(m['piece'], m['cells']), 'covered_cells_created': covered(after) - covered(start)}
    if hab in SEALED_SET:   # the sealing habits caption sealed cells, by the habit's own detector semantics
        ns = new_sealed(hab, start, m['cells'])
        d['sealed_cells_new'] = [[x + 1, 40 - y] for x, y in ns]   # [column from 1, row from the bottom from 1], board after the move
    return d

STRONG = {'tsd', 'tst', 'tss', 'mini_tss', 'tspin0', 'mini_tspin0', 'quad'}   # P4.py's STRONG kinds
def contrast(hab, o, start, cm0, hm0, st):
    """Does a Cold Clear first move contrast with the habit, by the habit's own test? -> (bool, rule text)"""
    def sealed_delta(m): return len(new_sealed(hab, start, m['cells']))
    def cov_delta(m): return covered(apply(start, m['cells'])) - covered(start)
    det = o['detail']
    if hab in ('Y1', 'P1'): return cov_delta(cm0) <= 0, 'cc first move creates no covered cell'
    if hab in ('Y4', 'P2'): return sealed_delta(cm0) == 0, 'cc first move seals off no cell'
    if hab in ('Y2', 'P5'): return cm0['lines'] >= 1, 'cc first move clears at least one line'
    if hab in ('Y3', 'P6'): return cm0['lines'] == 4, 'cc first move is a quad'
    if hab == 'Y6': return cm0['kind'] == 'tsd', 'cc first move is a TSD'
    if hab == 'P3': return cm0['lines'] == 0, 'cc first move clears no line'
    if hab == 'P4':
        # P4 eligibility compares like with like: same hold use as the player, no T-spin or quad
        cx = sum(x for x, y in cm0['cells']) / 4
        same_hold = bool(cm0['hold']) == (hm0['piece'] != st['current'])
        return ((cx < 4.5) != det['tall_half'].startswith('left')) and same_hold and cm0.get('kind') not in STRONG, \
            'cc first move uses hold exactly when the player did, is not a T-spin or quad, and its centroid is not on the taller half'
    if hab == 'Y5':
        bur = any(x == h_['column'] and y < h_['row'] for h_ in det['open_holes'] for x, y in cm0['cells']) and cov_delta(cm0) > 0
        return not bur, 'cc first move does not bury an open garbage hole (a cell in that column above the hole and covered cells rise)'
    raise KeyError(hab)

def build_clip(hab, night, cand):
    o = cand['occ']; i = o['id']
    fails = [s for s in SEEDS if not FR[s][i]['ok']]
    if fails: return None, {'id': i, 'why': 'self-check failed', 'seeds': fails, 'detail': [CK[s][i]['why'] for s in fails]}
    st = P[i]; start = st['field']
    hm0x = FR[0][i]['human'][0]
    runs = []
    for s in SEEDS:
        fr = FR[s][i]; oc = outcome(fr, 'cc')
        m0 = fr['cc'][0] if fr['cc'] and not fr['cc'][0].get('dead') else None
        con = contrast(hab, o, start, m0, hm0x, st)[0] if m0 else False
        sortkey = (oc['attack'], -(oc['covered_cells_end'] if oc['covered_cells_end'] is not None else 999), -s)
        runs.append((sortkey, s, oc, con))
    ncon = sum(r[3] for r in runs)
    if 2 * ncon <= len(SEEDS):
        return None, {'id': i, 'why': 'Cold Clear does not contrast', 'detail': f'{ncon} of {len(SEEDS)} seeds made a first move that contrasts with the habit (a majority is required)'}
    ok_runs = sorted([r for r in runs if r[3] and not r[2]['topped_out']], key=lambda r: r[0])
    if not ok_runs:
        return None, {'id': i, 'why': 'every contrasting Cold Clear run topped out in the harness', 'detail': f'{ncon} contrasting'}
    # shown = the median contrasting run that the harness did not declare dead (its topout rule is stricter
    # than TETR.IO's), ordered worst-to-best by 4-piece attack then covered cells; even count -> lower middle
    shown = ok_runs[(len(ok_runs) - 1) // 2][1]
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
        if human: d.update({'keys': s.get('keys'), 'tanks': s['tanks'], 'verified': s['verified'], 'queue': {'current': s['current'], 'hold': s['holdPiece'], 'next': s['next']}})
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
        'player_first': first_move_facts(start, {'piece': hm0['piece'], 'hold': hm0['hold'], 'cells': hm0['cells']}, hm0['lines'], hab),
        'cc_first': first_move_facts(start, cm0, cm0['lines'], hab) if cm0 else None,
        'player_4': outcome(fr, 'human'), 'cc_4': outcome(fr, 'cc'),
        'columns_note': 'columns are 1-based from the left; covered cells = empty cells with a filled cell above in the same column, counted after line clears',
    }
    ct, crule = contrast(hab, o, start, cm0, hm0, st) if cm0 else (None, None)
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
                   'rule': 'among the seeds whose first move contrasts with the habit and whose run the harness did not declare dead, the median by 4-piece attack, then by covered cells at the end (more = worse), ties broken by seed (even count: the lower middle); a clip needs a majority of seeds contrasting',
                   'seeds_contrasting': ncon, 'seeds_shown_from': len(ok_runs),
                   'per_seed': [{'seed': s, 'attack': oc['attack'], 'covered_cells_end': oc['covered_cells_end'], 'topped_out': oc['topped_out'], 'contrasts': con,
                                 'first_move': ({'piece': first[s]['piece'], 'hold': bool(first[s]['hold']), 'cells': tc(first[s]['cells'])} if first[s] else None)}
                                for _, s, oc, con in sorted(runs, key=lambda r: r[1])],
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
       'selection_rule': 'per habit and night: the pool is every verified occurrence, misdrop-shaped excluded unless the habit is misdrop-shaped by definition (Y1, P1, Y6); examples are taken nearest the pool median graded cost, from positive graded cost only and only inside the 25th-75th percentile of the pool (P3: single-line clears only, its modal case, when the night has one); window of 4 verified recorded locks plus the next decision; a majority of the 5 Cold Clear seeds must make a first move that contrasts with the habit, and the shown run is the median contrasting run the harness did not declare dead; the two examples come from different match files; no position or piece is shown under two habits, and a round another habit already uses is taken only when a night would otherwise have fewer than two (habits taken in page order)',
       'habits': []}
dropped = []; log = json.load(open(f'{D}/select-log.json')); USED_POS = set(); USED_ROUND = set(); USED_PIECES = set()
counts = {}
for h in HABITS:
    nd, nights = nights_of(h)
    hab = {'id': h, 'player': nd['player'], 'name': meta.NAMES[h], 'definition': nd['definition'].replace('adds nothing for him', 'adds nothing for pinglamb'), 'cc_comparison': meta.CC[h],
           'pooled': nd.get('pooled') or nights.get('pooled'), 'nights': {}}
    for k in ('nights_gap_negative', 'nights_gap_positive', 'night_sign_test', 'p10_piece_time', 'reproduce', 'min_height', 'title'):
        if k in nd: hab.setdefault('extra', {})[k] = nd[k]
    for s in SESS:
        ex = []; why_not = collections.Counter(); files = set()
        # pass 1: no round already shown under another habit; pass 2 (only if a slot is still empty): such a
        # round is allowed when none of this window's pieces was shown there. A position is never shown twice.
        for pss in (1, 2):
            for cand in cands.get(f'{h}/{s}', []):
                if len(ex) == KEEP: break
                i = cand['occ']['id']; rk, l0 = i.rsplit('/', 1); l0 = int(l0); fk_ = rk.split('/')[0]
                if any(c['id'] == i for c in ex): continue
                win = {(rk, l0 + j) for j in range(K)}
                if i in USED_POS: why_not['position already shown under another habit'] += pss == 1; continue
                if win & USED_PIECES:
                    why_not['its pieces are already shown under another habit'] += pss == 2; continue
                if pss == 1 and rk in USED_ROUND: why_not['round already shown under another habit'] += 1; continue
                if fk_ in files: why_not['same match file as the other example'] += pss == 1; continue
                c, err = build_clip(h, s, cand)
                if err:
                    if pss == 1: dropped.append({'habit': h, 'night': s, **err}); why_not[err['why']] += 1
                    continue
                assert c['facts']['cc_first_contrasts_with_habit'] and not c['facts']['cc_4']['topped_out'], i
                assert 25 <= c['why_picked']['regret_percentile_in_pool_midrank'] <= 75 and c['regret'] > 0, i
                if h in SEALED_SET: assert c['facts']['player_first']['sealed_cells_new'] and not c['facts']['cc_first']['sealed_cells_new'], i
                ex.append(c); files.add(fk_)
                if pss == 2: why_not['round already shown under another habit'] -= 1
            if len(ex) == KEEP: break
        why_not = +why_not
        for c in ex:
            rk, l0 = c['id'].rsplit('/', 1)
            USED_POS.add(c['id']); USED_ROUND.add(rk); USED_PIECES.update((rk, int(l0) + j) for j in range(K))
        rates = dict(nights[s]); rates.pop('session', None)
        hab['nights'][s] = {'rates': rates, 'pool': log['pools'].get(f'{h}/{s}'), 'examples': ex,
                            'candidates': len(cands.get(f'{h}/{s}', [])), 'not_used': dict(why_not)}
        counts[f'{h}/{s}'] = len(ex)
    out['habits'].append(hab)
out['log'] = {'dropped_clips': dropped, 'habit_nights_without_examples': [k for k, v in counts.items() if v == 0],
              'habit_nights_with_one_example': [k for k, v in counts.items() if v == 1],
              'selection_empty': log['empty'], 'windows_skipped': log['short_windows']}
json.dump(out, open(f'{S}/scen/habit-clips.json', 'w'), separators=(',', ':'))
print('clips', sum(counts.values()), 'dropped', len(dropped), 'zero', out['log']['habit_nights_without_examples'],
      'one', out['log']['habit_nights_with_one_example'], 'size', os.path.getsize(f'{S}/scen/habit-clips.json'))
