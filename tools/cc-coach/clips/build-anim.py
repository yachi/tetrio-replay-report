import json, collections, html
clips = json.load(open('clips-chosen.json'))
caps = json.load(open('captions-final.json'))            # verified by the round-2 workflow
pr = [json.loads(l) for l in open('rollouts-40k.priced.jsonl')]
y = [r for r in pr if r['user'] == 'yachi']
# percentile of each window's single-run gap within ALL 593 windows (topped-out ones included), mid-rank
diffs = [r['diff'] for r in y]
def pctile(dv): return round(100 * (sum(x < dv for x in diffs) + 0.5 * sum(x == dv for x in diffs)) / len(diffs))
pct = {r['id']: pctile(r['diff']) for r in y}
import re
PFX = re.compile(r'^(human|cc|both)?\s*(step|steps)\s*\d+[^:]*:\s*', re.I)
def clean(t): t = PFX.sub('', t.strip()); return t[0].upper() + t[1:] if t else t

# histogram of cc - human attack per window, drawn to scale
d = collections.Counter(max(-8, min(20, r['diff'])) for r in y)
W, H, L, B = 640, 170, 34, 26
bins = list(range(-8, 21)); bw = (W - L - 8) / len(bins); top = max(d.values())
bars = []
for i, b in enumerate(bins):
    n = d.get(b, 0); h = (H - B - 10) * n / top; x = L + i * bw
    col = 'var(--you)' if b <= 0 else 'var(--cc)'
    bars.append(f'<rect x="{x+1:.1f}" y="{H-B-h:.1f}" width="{bw-2:.1f}" height="{h:.1f}" fill="{col}"><title>{b if -8 < b < 20 else ("≤-8" if b == -8 else "≥20")}: {n} windows</title></rect>')
ticks = []
for b in (-5, 0, 5, 10, 15):
    x = L + (bins.index(b) + .5) * bw
    ticks.append(f'<text x="{x:.1f}" y="{H-8}" text-anchor="middle">{"+" if b > 0 else ""}{b}</text>')
for v in (0, 25, 50):
    yy = H - B - (H - B - 10) * v / top
    ticks.append(f'<line x1="{L}" x2="{W-8}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="var(--line)"/><text x="{L-6}" y="{yy+3:.1f}" text-anchor="end">{v}</text>')
zx = L + bins.index(0) * bw + bw
hist = (f'<svg class="hist" viewBox="0 0 {W} {H}" role="img" aria-label="histogram of Cold Clear minus your attack per window">'
        + ''.join(ticks) + ''.join(bars)
        + f'<line x1="{zx:.1f}" x2="{zx:.1f}" y1="6" y2="{H-B}" stroke="var(--muted)" stroke-dasharray="3 3"/>'
        + f'<text x="{W-8}" y="16" text-anchor="end">Cold Clear ahead →</text><text x="{zx-6:.1f}" y="16" text-anchor="end">← you ahead or level</text><text x="{L}" y="{H-B+12}">≤-8</text></svg>')

out = []
for i, c in enumerate(clips):
    cp = caps[str(i)]
    m = c['id'].split('/')
    where = f"match {int(m[0][-2:])} · round {int(m[1][1:]) + 1} · from piece {int(m[3]) + 1}"
    tag = (f"biggest miss · {where}" if c['source'] == 'example' else f"typical · percentile {pct[c['id']]} · {where}")
    st = sorted(c['seedTotals'])
    nov = [j + 1 for j, h in enumerate(c['human']) if not h['verified']]
    note = (f"Cold Clear searches at random, so it was run 8 times from this position. Its 14-piece attack across the 8 runs: "
            f"{', '.join(map(str, st))}. Shown: the lower median ({c['totals']['cc']}).")
    if c['source'] == 'percentile':
        r0 = next(r for r in y if r['id'] == c['id'])
        note += (f" This window was picked from the chart above by its first run (Cold Clear {r0['cc']['attack']}, you {r0['human']['attack']}),"
                 f" which sits at percentile {pct[c['id']]}; the median-of-8 run shown here can land elsewhere.")
    if nov:
        note += f" Your moves {nov[0]}–{nov[-1]} here fall after the replay's attack-verified stretch; their boards still rebuild exactly from the recorded drops and garbage."
    def slim(s):
        if s.get('dead'): return {'dead': True}
        o = {k: s[k] for k in ('piece', 'hold', 'cells', 'lines', 'spin', 'attack', 'b2b', 'combo', 'garbage', 'before', 'after')}
        for k in ('current', 'holdPiece', 'next', 'verified', 'loss'):
            if k in s: o[k] = s[k]
        return o
    out.append({'id': c['id'], 'source': c['source'], 'title': cp['title'], 'summary': cp['summary'], 'claims': sorted([dict(x, text=clean(x['text'])) for x in cp['claims']], key=lambda x: x['step']),
                'tag': tag, 'where': where, 'seedNote': note, 'totals': c['totals'], 'start': c['start'],
                'human': [slim(s) for s in c['human']], 'cc': [slim(s) for s in c['cc']]})

foot = """<h3>What is and isn't shown</h3><ul>
<li><b>Every frame was rebuilt independently.</b> Four agents wrote their own checkers from the raw replay data and re-derived all 336 placements: piece shape, empty cells, piece resting on something, cleared rows, garbage rows and hole column, and TETR.IO attack, B2B and combo. No frame disagreed. Every caption claim then survived two skeptics, one checking numbers and one checking wording.</li>
<li><b>Garbage:</b> Cold Clear receives exactly the rows you received, on the same piece, with the same hole. If its piece there clears lines, the rows wait for its next piece that clears nothing, which is TETR.IO's own rule. It gets no credit for cancelling with its attack, and the incoming meter it sees is your meter at that moment.</li>
<li><b>Preview:</b> Cold Clear never sees more than you did: hold plus the 5-piece preview, with one new piece revealed per placement.</li>
<li><b>Not modelled:</b> speed and key inputs. You played in real time; Cold Clear thought about 0.2 s per piece with no clock. The drop is drawn straight down for clarity, so tucks and spins are shown by where the piece ends up, not how it got there.</li>
<li><b>Cold Clear is a strong bot's line, not "the correct play".</b> It is tuned for Puyo Puyo Tetris scoring, has no 180° spins, and does not know TETR.IO's B2B chain bonus. The bar under your field is each move's graded loss against it (taller is worse; orange marks a clear miss of 600 or more; hatched means not graded).</li>
</ul>"""
page = open('anim-template.html').read().replace('{{DATA}}', json.dumps(out, separators=(',', ':'))).replace('{{HIST}}', hist).replace('{{FOOT}}', foot)
open('replays.html', 'w').write(page)
print('ok', len(page))
