# Habit Y5 (yachi): burying an open garbage hole.
# Detector = H-GARBAGE-COVER as re-derived by the statistics skeptic
# (verify-holes-H-GARBAGE-COVER-stats.py), copied verbatim:
#   eligible ("scenario"): graded position (mid.jsonl line with a cc seed-0 grade carrying a pick) where some column's
#             SURFACE cell (first empty cell above the column's top block) sits in a garbage row that has exactly one
#             empty cell -- i.e. a garbage hole open to the surface, ready to dig (exposed()).
#   covers(move) = some placed cell lies in an exposed-hole column ABOVE that hole, AND the board's total covered-cell
#             count (empty cells with a block anywhere above them), measured after the move's line clears, rises.
#   player rate = P(player move covers); Cold Clear rate = P(cc seed-0 pick covers), same positions.
#   occurrence = player covers and cc does not.
#   misdrop_shaped = that skeptic's geometry rule misdrop(): same piece as cc pick/top-3 with the same shape one column
#             over, or a different rotation within one column.
# Narrowing (FINDINGS yachi #5, "without misdrops"): the stats skeptic drops every row whose player move is
#   misdrop-shaped (+0.99 pp, 14/0 nights); reported per night as excl_misdrop_rows. The misdrop skeptic's stricter
#   variant (+0.45 pp, garbage_seal def + isMD) uses a different cover definition and is cross-checked in notes only.
# HS2 cross-reference (verify-pressure-HS2-*): max height >= 12, the TOP garbage row has one hole, open straight up
#   (garb()), and the move adds a covered cell in that column (covers()). Reported per night as hs2_12plus, and each
#   occurrence carries in_hs2 = HS2 would also count it.
import json, os, collections, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(H) + '/../corpus/'
USER = 'yachi'

# ---- stats skeptic, verbatim ----
def heights(f): return [40-next((y for y in range(40) if f[y][c]!='.'),40) for c in range(10)]
def covered(f):
    n=0
    for c in range(10):
        seen=False
        for y in range(40):
            if f[y][c]!='.': seen=True
            elif seen: n+=1
    return n
def apply(f,cells):
    g=[list(r) for r in f]
    for x,y in cells: g[y][x]='X'
    rows=[r for r in g if '.' in r]
    k=40-len(rows)
    return [ '.'*10 ]*k+[''.join(r) for r in rows], k
def exposed(f):
    h=heights(f); out=[]
    for c in range(10):
        y=39-h[c]
        if 0<=y<40 and 'G' in f[y] and f[y].count('.')==1: out.append((c,y))
    return out
def covers(f,cells,cov0):
    ex=exposed(f)
    if not ex: return False
    hit=any(x==c and y<hy for x,y in cells for c,hy in ex)
    if not hit: return False
    g,_=apply(f,cells)
    return covered(g)>cov0
def shape(cells):
    mx=min(x for x,y in cells); my=min(y for x,y in cells)
    return frozenset((x-mx,y-my) for x,y in cells), mx
def misdrop(pcells,ppiece,g):
    ps,px=shape(pcells)
    cands=[g['pick']]+g.get('top',[])[:3]
    for c in cands:
        if c['piece']!=ppiece: continue
        cs,cx=shape([tuple(t) for t in c['cells']])
        if cs==ps and abs(cx-px)==1: return True
        if cs!=ps and abs(cx-px)<=1: return True
    return False
# ---- HS2 skeptic, verbatim ----
def place(f,cells):
    g=[list(r) for r in f]
    for x,y in cells:
        if 0<=y<40: g[y][x]='#'
    full=[r for r in g if '.' not in r]; keep=[r for r in g if '.' in r]
    keep=[['.']*10 for _ in range(40-len(keep))]+keep
    return [''.join(r) for r in keep],len(full)
def colholes(ff):
    h=heights(ff); return [sum(1 for r in range(40-h[c],40) if ff[r][c]=='.') for c in range(10)]
def garb(f):
    rows=[r for r in range(40) if 'G' in f[r]]
    if not rows: return None
    top=rows[0]; hs=[c for c in range(10) if f[top][c]=='.']
    if len(hs)!=1: return None
    c=hs[0]
    return c if all(f[r][c]=='.' for r in range(top)) else None
def hs2_covers(f,cells,gc):
    nf,_=place(f,cells); return int(colholes(nf)[gc]>colholes(f)[gc])

# ---- load ----
G={}
for l in open(C+'grade.jsonl'):
    g=json.loads(l)
    if 'pick' in g: G[g['id']]=g
rows=[]
for l in open(C+'mid.jsonl'):
    p=json.loads(l)
    if p['user']!=USER: continue
    g=G.get(p['id'])
    if not g: continue
    f=p['field']; ex=exposed(f)
    if not ex: continue
    cov0=covered(f)
    pc=[tuple(c) for c in p['played']['cells']]; cc=[tuple(c) for c in g['pick']['cells']]
    pv=covers(f,pc,cov0); cv=covers(f,cc,cov0)
    gp,_=apply(f,pc); gcc,ccl=apply(f,cc)
    mh=max(heights(f)); gc=garb(f)
    hs2=mh>=12 and gc is not None
    r=dict(p=p,g=g,pv=pv,cv=cv,ex=ex,cov0=cov0,dcov_p=covered(gp)-cov0,dcov_c=covered(gcc)-cov0,cc_lines=ccl,
           reg=g['duel']['cc']-g['duel']['player'] if g.get('duel') and g['duel'].get('cc') is not None and g['duel'].get('player') is not None else None,
           md=misdrop(pc,p['played']['piece'],g),h=mh,garb=sum(1 for rr in f if 'G' in rr),hs2=hs2,
           hs2p=hs2_covers(f,pc,gc) if hs2 else None,hs2c=hs2_covers(f,cc,gc) if hs2 else None,s=p['session'])
    rows.append(r)
print('eligible', len(rows))

occ=[]
for r in sorted((r for r in rows if r['pv'] and not r['cv']), key=lambda r:(r['s'],r['p']['id'])):
    p=r['p']; g=r['g']; pl=p['played']; pk=g['pick']; f=p['field']
    pc=[tuple(c) for c in pl['cells']]
    hit=sorted({(c,hy) for x,y in pc for c,hy in r['ex'] if x==c and y<hy})
    occ.append(dict(habit='Y5', player=USER, session=r['s'], id=p['id'], lock=p['lock'], regret=r['reg'],
        misdrop_shaped=bool(r['md']), verified=p['verified'],
        player_move=dict(piece=pl['piece'], cells=[list(c) for c in pl['cells']], hold_used=pl['piece']!=p['current'], lines=pl['lines']),
        cc_move=dict(piece=pk['piece'], cells=[list(c) for c in pk['cells']], hold_used=bool(pk['hold']), lines=r['cc_lines']),
        detail=dict(
            open_holes=[dict(column=c, row=hy) for c,hy in r['ex']],          # every exposed garbage hole on the board
            buried_holes=[dict(column=c, row=hy) for c,hy in hit],           # the ones the player's piece sits above
            covered_cells_created=r['dcov_p'],                               # board covered-cell delta after line clears
            cc_covered_cells_delta=r['dcov_c'],
            player_lines=pl['lines'], cc_lines=r['cc_lines'], cc_kind=pk['kind'],
            max_height=r['h'], garbage_rows=r['garb'], incoming=p['incoming'],
            current=p['current'], hold=p['hold'], next=p['next'][:5], b2b=p['b2b'], combo=p['combo'],
            in_hs2=bool(r['hs2'] and r['hs2p'] and not r['hs2c']),
            piece_time_frames=pl.get('pieceTime'), keys=pl.get('keys'), n_keys=len(pl.get('keys') or []))))
with open(H+'/Y5.occ.jsonl','w') as fh:
    for o in occ: fh.write(json.dumps(o)+'\n')

def pct(a,n): return round(100*a/n,2) if n else None
def row(label, rs):
    n=len(rs); pv=sum(r['pv'] for r in rs); cv=sum(r['cv'] for r in rs)
    d=[r for r in rs if r['pv'] and not r['cv']]; rv=sum((not r['pv']) and r['cv'] for r in rs)
    dm=[r for r in d if r['md']]; dd=[r for r in d if not r['md']]
    regs=[r['reg'] for r in d if r['reg'] is not None]; regd=[r['reg'] for r in dd if r['reg'] is not None]
    nm=[r for r in rs if not r['md']]; n2=len(nm)
    h2=[r for r in rs if r['hs2']]; n3=len(h2)
    return dict(session=label, eligible=n, player_covers=pv, cc_covers=cv,
        player_rate_pct=pct(pv,n), cc_rate_pct=pct(cv,n), gap_pp=round(100*(pv-cv)/n,2) if n else None,
        occurrences=len(d), occurrences_misdrop_shaped=len(dm), occurrences_deliberate=len(dd), reverse_cc_covers_player_not=rv,
        regret_mean=round(st.mean(regs),1) if regs else None, regret_median=st.median(regs) if regs else None,
        regret_mean_deliberate=round(st.mean(regd),1) if regd else None, regret_median_deliberate=st.median(regd) if regd else None,
        occurrences_player_cleared_lines=sum(r['p']['played']['lines']>0 for r in d),
        excl_misdrop_rows=dict(eligible=n2, player_rate_pct=pct(sum(r['pv'] for r in nm),n2), cc_rate_pct=pct(sum(r['cv'] for r in nm),n2),
            gap_pp=round(100*(sum(r['pv'] for r in nm)-sum(r['cv'] for r in nm))/n2,2) if n2 else None),
        hs2_12plus=dict(eligible=n3, player_rate_pct=pct(sum(r['hs2p'] for r in h2),n3), cc_rate_pct=pct(sum(r['hs2c'] for r in h2),n3),
            gap_pp=round(100*(sum(r['hs2p'] for r in h2)-sum(r['hs2c'] for r in h2))/n3,2) if n3 else None,
            note='HS2 scenario rows (n=5791 pooled) are all inside this eligible set'))
by=collections.defaultdict(list)
for r in rows: by[r['s']].append(r)
nights=[row(s,by[s]) for s in sorted(by)]
pooled=row('pooled',rows)
out=dict(habit='Y5', player=USER,
    definition=('Eligible: graded yachi position (mid.jsonl sample: verified locks >= 21, every 3rd; cc seed-0 grade with a pick) '
        'where some column\'s surface cell lies in a garbage row with exactly one empty cell, i.e. a garbage hole open to the '
        'surface (skeptic verify-holes-H-GARBAGE-COVER-stats.py, exposed()). A move "buries" it when one of its cells sits in '
        'that column above the hole AND the board\'s count of covered empty cells, after the move\'s line clears, goes up. '
        'Player rate = share of eligible positions where the player\'s move buries; Cold Clear rate = share where cc\'s '
        'seed-0 pick buries, same positions; gap = player - cc (pp). Occurrence = player buries and cc does not. '
        'misdrop_shaped = that skeptic\'s rule: same piece as cc pick/top-3, same shape one column over or another rotation '
        'within one column. excl_misdrop_rows = the skeptic\'s narrowed variant: positions where the player\'s move is '
        'misdrop-shaped dropped from the eligible set. hs2_12plus = the HS2 detector (max height >= 12, top garbage row\'s '
        'single hole open straight up, move adds a covered cell in that column) on the eligible rows that meet it. '
        'Regret = duel.cc - duel.player.'),
    nights=nights, pooled=pooled)
json.dump(out, open(H+'/Y5.nights.json','w'), indent=1)
print(json.dumps({k:v for k,v in pooled.items()}))
for n in nights: print(n['session'], n['eligible'], n['player_rate_pct'], n['cc_rate_pct'], n['gap_pp'], n['occurrences'], n['occurrences_misdrop_shaped'], n['regret_mean'], n['regret_median'], n['excl_misdrop_rows']['gap_pp'], n['hs2_12plus']['gap_pp'])
