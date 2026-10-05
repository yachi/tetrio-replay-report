import os as _os; CC_WORK = _os.environ['CC_WORK']  # the work directory: corpus/, scen/, scen/habits/, scen/hclips/
import json, pickle, os
S=CC_WORK + '/corpus'
PLAIN={'single','double','triple'}
def shape(field):
    hs=[]
    for c in range(10):
        r=next((r for r in range(40) if field[r][c]!='.'),40); hs.append(40-r)
    g=sum(1 for row in field if 'G' in row)
    return max(hs), g
def slim(g):
    if 'error' in g or not g.get('duel') or g['duel']['player'] is None or g['duel']['cc'] is None: return None
    return dict(ck=g['pick']['kind'], chold=g['pick']['hold'], cpiece=g['pick']['piece'], ccells=sorted(map(tuple,g['pick']['cells'])),
        top=[(t['piece'],sorted(map(tuple,t['cells'])),t['hold']) for t in g['top'][:3]], pk=g['player']['kind'], found=g['player']['found'],
        dp=g['duel']['player'], dc=g['duel']['cc'], same=g['duel']['same'])
rows=[]
for m,g in zip(open(S+'/mid.jsonl'),open(S+'/grade.jsonl')):
    m=json.loads(m); g=json.loads(g); assert m['id']==g['id']
    s=slim(g)
    if s is None: continue
    pl=m['played']; mh,gr=shape(m['field'])
    held = pl['piece']!=m['current']
    r=dict(id=m['id'],user=m['user'],session=m['session'],rk=m['file']+'/'+str(m['round']),b2b=m['b2b'],combo=m['combo'],
        cur=m['current'],hold=m['hold'],nxt=m['next'],inc=m['incoming'],maxh=mh,grows=gr,piece=pl['piece'],held=held,
        cells=sorted((c[0],c[1]) for c in pl['cells']),lines=pl['lines'],spin=pl['spin'],pt=pl.get('pieceTime'),nk=len(pl.get('keys',[])),**s)
    rows.append(r)
idx=[int(x) for x in open(S+'/sub4000.idx')]
def load(fn): return [json.loads(l) for l in open(S+'/'+fn)]
mid_ids=[json.loads(l)['id'] for l in open(S+'/mid.jsonl')]
sub=dict(s1=load('grade-s1.jsonl'),weak=load('grade-weak.jsonl'),ccpick=load('grade-s1-ccpick.jsonl'))
out=dict(rows=rows, sub={k:[(x['id'],slim(x)) for x in v] for k,v in sub.items()})
pickle.dump(out,open(CC_WORK + '/scen/b2b_hold.pkl','wb'))
print(len(rows), {k:len(v) for k,v in sub.items()})
