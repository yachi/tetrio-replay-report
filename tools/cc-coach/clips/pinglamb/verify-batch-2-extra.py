import json,re
c=json.load(open('clips-chosen.json'))
pos={}
for l in open('../positions.jsonl'):
    x=json.loads(l); pos[x['id']]=x
def corners(before,cells):
    # T center = cell with 3 neighbours in piece
    s=set(map(tuple,cells))
    ctr=[p for p in s if sum((p[0]+dx,p[1]+dy) in s for dx,dy in((1,0),(-1,0),(0,1),(0,-1)))==3][0]
    n=0
    for dx in(-1,1):
        for dy in(-1,1):
            x,y=ctr[0]+dx,ctr[1]+dy
            if x<0 or x>9 or y>39 or before[y][x]!='.': n+=1
    return n
for ci in (6,7,8):
    cl=c[ci]; mm=[]
    pre,l0=cl['id'].rsplit('/',1); l0=int(l0)
    for side in('human','cc'):
        for j,a in enumerate(cl[side]):
            if a['spin']!='none':
                if a['piece']!='T': mm.append(f'{side} {j} spin on {a["piece"]}')
                elif corners(a['before'],a['cells'])<3: mm.append(f'{side} {j} T-spin with <3 corners')
            if side=='human':
                p=pos[f'{pre}/{l0+j}']
                if a['verified']!=p['verified']: mm.append(f'human {j} verified {a["verified"]} vs {p["verified"]}')
    # clipdump
    txt=open(f'clipdump/{ci:02d}.txt').read()
    blocks=re.split(r'^--- (human|cc|cold clear)\s*step (\d+): (.*)$',txt,flags=re.M|re.I)
    found={'human':0,'cc':0}
    for k in range(1,len(blocks),4):
        side='human' if blocks[k].lower()=='human' else 'cc'; j=int(blocks[k+1])-1; hdr=blocks[k+2]; body=blocks[k+3]
        a=cl[side][j]; found[side]+=1
        fin=None
        if 'board AFTER' in body:
            body,fin=body.split('board AFTER',1)
        if ('(from hold)' in hdr)!=bool(a['hold']): mm.append(f'dump {side} {j} from-hold annot vs hold {a["hold"]}')
        if fin is not None:
            fr=re.findall(r'^\s*(\d+) ([.A-Z]{10})$',fin,flags=re.M)
            for rn,s2 in fr:
                if s2!=a['after'][40-int(rn)]: mm.append(f'dump {side} final row {rn} {s2} vs after {a["after"][40-int(rn)]}')
            nz=[r for r in a['after'] if r!='..........']
            if len([1 for rn,s2 in fr if s2!='..........'])!=len(nz): mm.append(f'dump {side} final nonempty rows count differs')
            found[side+'_final']=1
        m=dict(re.findall(r'(\w+)=(\S+)',hdr))
        if not hdr.startswith(a['piece']): mm.append(f'dump {side} {j} piece hdr {hdr[:2]}')
        for key,v in (('lines',a['lines']),('spin',a['spin']),('attack',a['attack']),('b2b',a['b2b']),('combo',a['combo']),('garbage_in_after',a['garbage'])):
            if key in m and str(v)!=m[key]: mm.append(f'dump {side} {j} {key}={m[key]} vs {v}')
        rows=re.findall(r'^\s*(\d+) ([.A-Z*]{10})$',body,flags=re.M)
        star=set()
        for rn,s in rows:
            r=40-int(rn)
            exp=a['before'][r]
            for x,ch in enumerate(s):
                if ch=='*': star.add((x,r)); ch2='.'
                else: ch2=ch
                if ch2!=exp[x]: mm.append(f'dump {side} {j} row {rn} col {x+1}: {ch} vs before {exp[x]}'); break
        if star!=set(map(tuple,a['cells'])): mm.append(f'dump {side} {j} * cells {sorted(star)} vs {a["cells"]}')
    print(ci,found,mm)
