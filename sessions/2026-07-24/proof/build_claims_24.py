#!/usr/bin/env python3
"""build_claims_24.py — assemble claims-24.json.

Extracts id / category / 廣東話 / english-gloss for the 20 claims VERBATIM from
report-2026-07-24.html's appendix table, and attaches an integer-only
python_check per id that faithfully expresses the same statement over
facts-24.json with the concrete values the report renders. Displayed rounded
numbers (~21.0s, 1.32 PPS) are pinned via integer bounds / integer-scaled
rounding, never floats.
"""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "..", "report-2026-07-24.html")

# python_check per claim id — single expression over dict `facts`, must eval True.
CHECKS = {
    "C001": "sum(1 for m in facts['matches'] if m['winner']=='pinglamb')==4 and sum(1 for m in facts['matches'] if m['winner']=='yachi')==3",
    "C002": "sum(len(m['rounds']) for m in facts['matches'])==50 and sum(1 for m in facts['matches'] for r in m['rounds'] if r['winner']=='pinglamb')==29 and sum(1 for m in facts['matches'] for r in m['rounds'] if r['winner']=='yachi')==21",
    "C003": "sum(r['players']['pinglamb']['pieces'] for m in facts['matches'] for r in m['rounds'])==4439 and sum(r['players']['yachi']['pieces'] for m in facts['matches'] for r in m['rounds'])==4748",
    # aggregate PPS = pieces/(ms/1000); 2-dp display = floor(pieces*100000/ms + 0.5) = (2*P*1e5 + M)//(2*M)
    "C004": "(lambda P,M,Y,N: (2*P*100000+M)//(2*M)==132 and (2*Y*100000+N)//(2*N)==141)(sum(r['players']['pinglamb']['pieces'] for m in facts['matches'] for r in m['rounds']), sum(r['players']['pinglamb']['lifetime'] for m in facts['matches'] for r in m['rounds']), sum(r['players']['yachi']['pieces'] for m in facts['matches'] for r in m['rounds']), sum(r['players']['yachi']['lifetime'] for m in facts['matches'] for r in m['rounds']))",
    "C005": "sum(d['clears']['allclear'] for m in facts['matches'] for r in m['rounds'] for d in r['players'].values())==10 and sum(r['players']['pinglamb']['clears']['allclear'] for m in facts['matches'] for r in m['rounds'])==4 and sum(r['players']['yachi']['clears']['allclear'] for m in facts['matches'] for r in m['rounds'])==6",
    # shortest round overall = m5 (idx5) round-index1, duration = max of both lifetimes; ~21.0s
    "C006": "min(max(d['lifetime'] for d in r['players'].values()) for m in facts['matches'] for r in m['rounds'])==21023 and facts['matches'][4]['index']==5 and max(d['lifetime'] for d in facts['matches'][4]['rounds'][1]['players'].values())==21023 and 20950<=21023<21050",
    # longest round overall = m3 (idx3) round-index2; ~240.1s
    "C007": "max(max(d['lifetime'] for d in r['players'].values()) for m in facts['matches'] for r in m['rounds'])==240131 and facts['matches'][2]['index']==3 and max(d['lifetime'] for d in facts['matches'][2]['rounds'][2]['players'].values())==240131 and 240050<=240131<240150",
    # per-match longest round: value, winner, ~display
    "C008": "facts['matches'][0]['index']==1 and max(max(d['lifetime'] for d in r['players'].values()) for r in facts['matches'][0]['rounds'])==116222 and max(d['lifetime'] for d in facts['matches'][0]['rounds'][4]['players'].values())==116222 and facts['matches'][0]['rounds'][4]['winner']=='pinglamb' and 116150<=116222<116250",
    "C009": "facts['matches'][1]['index']==2 and max(max(d['lifetime'] for d in r['players'].values()) for r in facts['matches'][1]['rounds'])==179950 and max(d['lifetime'] for d in facts['matches'][1]['rounds'][2]['players'].values())==179950 and facts['matches'][1]['rounds'][2]['winner']=='yachi' and 179950<=179950<180050",
    "C010": "facts['matches'][2]['index']==3 and max(max(d['lifetime'] for d in r['players'].values()) for r in facts['matches'][2]['rounds'])==240131 and max(d['lifetime'] for d in facts['matches'][2]['rounds'][2]['players'].values())==240131 and facts['matches'][2]['rounds'][2]['winner']=='yachi' and 240050<=240131<240150",
    "C011": "facts['matches'][3]['index']==4 and max(max(d['lifetime'] for d in r['players'].values()) for r in facts['matches'][3]['rounds'])==83945 and max(d['lifetime'] for d in facts['matches'][3]['rounds'][4]['players'].values())==83945 and facts['matches'][3]['rounds'][4]['winner']=='pinglamb' and 83850<=83945<83950",
    "C012": "facts['matches'][4]['index']==5 and max(max(d['lifetime'] for d in r['players'].values()) for r in facts['matches'][4]['rounds'])==140000 and max(d['lifetime'] for d in facts['matches'][4]['rounds'][0]['players'].values())==140000 and facts['matches'][4]['rounds'][0]['winner']=='yachi' and 139950<=140000<140050",
    "C013": "facts['matches'][5]['index']==6 and max(max(d['lifetime'] for d in r['players'].values()) for r in facts['matches'][5]['rounds'])==95111 and max(d['lifetime'] for d in facts['matches'][5]['rounds'][4]['players'].values())==95111 and facts['matches'][5]['rounds'][4]['winner']=='pinglamb' and 95050<=95111<95150",
    "C014": "facts['matches'][6]['index']==7 and max(max(d['lifetime'] for d in r['players'].values()) for r in facts['matches'][6]['rounds'])==101797 and max(d['lifetime'] for d in facts['matches'][6]['rounds'][2]['players'].values())==101797 and facts['matches'][6]['rounds'][2]['winner']=='pinglamb' and 101750<=101797<101850",
    "C015": "max(max(d['lifetime'] for d in r['players'].values()) for m in facts['matches'] for r in m['rounds'])==240131 and facts['matches'][2]['index']==3 and max(d['lifetime'] for d in facts['matches'][2]['rounds'][2]['players'].values())==240131 and 240050<=240131<240150",
    "C016": "min(max(d['lifetime'] for d in r['players'].values()) for m in facts['matches'] for r in m['rounds'])==21023 and facts['matches'][4]['index']==5 and max(d['lifetime'] for d in facts['matches'][4]['rounds'][1]['players'].values())==21023 and 20950<=21023<21050",
    "C017": "max(d['maxspike'] for m in facts['matches'] for r in m['rounds'] for d in r['players'].values())==17 and sum(1 for m in facts['matches'] for r in m['rounds'] for d in r['players'].values() if d['maxspike']==17)==1 and facts['matches'][4]['index']==5 and facts['matches'][4]['rounds'][7]['players']['pinglamb']['maxspike']==17",
    # biggest comeback = max (winnerQueued - loserQueued) over rounds; m7(idx7) round-index2, 67 vs 47, diff 20
    "C018": "(lambda Q: facts['matches'][6]['index']==7 and facts['matches'][6]['rounds'][2]['winner']=='pinglamb' and Q(facts['matches'][6]['rounds'][2],'pinglamb')==67 and Q(facts['matches'][6]['rounds'][2],'yachi')==47 and max(Q(r,r['winner'])-Q(r,'yachi' if r['winner']=='pinglamb' else 'pinglamb') for m in facts['matches'] for r in m['rounds'])==20)(lambda r,pl: sum(e['amt'] for e in r['players'][pl]['garbage_events']))",
    "C019": "all(r['players'][r['winner']]['vs_x1000'] > [d for p,d in r['players'].items() if p!=r['winner']][0]['vs_x1000'] for m in facts['matches'] for r in m['rounds'])",
    "C020": "(lambda P,M,Y,N: P*N < Y*M and (2*P*100000+M)//(2*M)==132 and (2*Y*100000+N)//(2*N)==141)(sum(r['players']['pinglamb']['pieces'] for m in facts['matches'] for r in m['rounds']), sum(r['players']['pinglamb']['lifetime'] for m in facts['matches'] for r in m['rounds']), sum(r['players']['yachi']['pieces'] for m in facts['matches'] for r in m['rounds']), sum(r['players']['yachi']['lifetime'] for m in facts['matches'] for r in m['rounds']))",
}


def main():
    s = open(HTML, encoding="utf-8").read()
    i = s.find('<table class="appendix')
    tbl = s[i:s.find("</table>", i) + 8]
    rows = re.findall(r"<tr.*?</tr>", tbl[tbl.find("<tbody"):], re.S)

    def celltext(t):
        return html.unescape(re.sub(r"\s+", " ", re.sub("<[^>]+>", "", t))).strip()

    claims = []
    for r in rows:
        tds = re.findall(r"<td.*?</td>", r, re.S)
        cid = celltext(tds[0])
        cat = celltext(tds[1])
        canto = celltext(tds[2])
        gloss = celltext(tds[3])
        assert cid in CHECKS, f"no python_check for {cid}"
        claims.append({
            "id": cid, "canto": canto, "english_gloss": gloss,
            "category": cat, "python_check": CHECKS[cid],
        })
    assert len(claims) == 20, f"expected 20 claims, got {len(claims)}"
    with open(os.path.join(HERE, "claims-24.json"), "w") as f:
        json.dump(claims, f, ensure_ascii=False, indent=2)
    print(f"wrote claims-24.json with {len(claims)} claims")


if __name__ == "__main__":
    main()
