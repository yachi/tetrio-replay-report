#!/usr/bin/env python3
"""Render one player's animated "<player> vs Cold Clear" page.

    python3 build-anim.py --player pinglamb --other yachi \
        --data <work>/pinglamb --rollouts <work>/rollouts-40k.priced.jsonl \
        --captions pinglamb/captions-final.json --rollout-nodes 40000 \
        --verify pinglamb/adjudication.json --refute pinglamb/refute-history.json \
        --out ../pages/cc-pinglamb.html

Every number on the page is derived from the inputs, never typed here: the histogram, the window
count, the topped-out count and the "matched or beat" count come from the 40k rollouts filtered to
--player; the clip / step / seed counts come from clips-chosen.json; the frame count, the number of
checkers, their saved mismatch lines and how each was resolved come from --verify (adjudicate.py's
output over the checkers' saved re-runs); the caption refute history comes from --refute.

Pages are public and third person: the player is named, never addressed.
"""
import argparse, collections, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument('--player', required=True)
ap.add_argument('--other', required=True, help='the other player, linked from the page')
ap.add_argument('--data', required=True, help='directory holding this player\'s clips-chosen.json')
ap.add_argument('--rollouts', required=True, help='rollouts-40k.priced.jsonl (all players)')
ap.add_argument('--captions', required=True)
ap.add_argument('--verify', required=True, help='adjudication.json written by adjudicate.py')
ap.add_argument('--refute', required=True, help='per-round caption refute history (JSON list)')
ap.add_argument('--rollout-nodes', type=int, required=True, help='node budget the rollouts were run at (CC_NODES)')
ap.add_argument('--template', default=os.path.join(HERE, 'anim-template.html'))
ap.add_argument('--out', required=True)
a = ap.parse_args()
P, O = a.player, a.other

clips = json.load(open(os.path.join(a.data, 'clips-chosen.json')))
caps = json.load(open(a.captions))
adj = json.load(open(a.verify))
y = [r for r in map(json.loads, open(a.rollouts)) if r['user'] == P]
assert y, f'no rollouts for {P}'
assert len(caps) == len(clips), (len(caps), len(clips))

K = len(clips[0]['human'])
assert all(len(c['human']) == K and len(c['cc']) == K for c in clips), 'clips differ in length'
n_seeds = len(clips[0]['seedTotals'])
n_ex = sum(c['source'] == 'example' for c in clips)
n_pct = sum(c['source'] == 'percentile' for c in clips)

# --- frame checks: the checkers' saved re-runs, adjudicated -----------------------------------
frames = adj['frames']
expected = len(clips) * 2 * K                       # both sides, every step
assert frames == expected, f'adjudication covers {frames} frames, clips hold {expected}'
assert [c['id'] for c in adj['clips']] == [c['id'] for c in clips], 'adjudication is for other clips'
rebuild_problems = len(adj['problems'])
n_checkers = len(adj['verifier'])
vlines = [r for v in adj['verifier'] for r in v['lines']]
unresolved = sum(r['verdict'] != 'explained' for r in vlines)
hist = [(r['checked'], r['refuted']) for r in json.load(open(a.refute))]
assert hist and hist[-1][1] == 0, f'refute loop did not end dry: {hist}'

# --- the chart: one 40k run per mid-game window ------------------------------------------------
diffs = [r['diff'] for r in y]
N = len(diffs)
def pctile(dv): return round(100 * (sum(x < dv for x in diffs) + 0.5 * sum(x == dv for x in diffs)) / N)
pct = {r['id']: pctile(r['diff']) for r in y}
level = sum(x <= 0 for x in diffs)
dead = sum(1 for r in y if r['cc']['dead'])

PFX = re.compile(r'^(human|cc|both)?\s*(step|steps)\s*\d+[^:]*:\s*', re.I)
def clean(t):
    t = PFX.sub('', t.strip())
    if not t or t.startswith((P, O)): return t   # usernames keep their own (lower) case
    return t[0].upper() + t[1:]

d = collections.Counter(max(-8, min(20, x)) for x in diffs)
W, H, L, B = 640, 170, 34, 26
bins = list(range(-8, 21)); bw = (W - L - 8) / len(bins); top = max(d.values())
bars = []
for i, b in enumerate(bins):
    n = d.get(b, 0); h = (H - B - 10) * n / top; x = L + i * bw
    col = 'var(--human)' if b <= 0 else 'var(--cc)'
    bars.append(f'<rect x="{x+1:.1f}" y="{H-B-h:.1f}" width="{bw-2:.1f}" height="{h:.1f}" fill="{col}"><title>{b if -8 < b < 20 else ("≤-8" if b == -8 else "≥20")}: {n} window{"" if n == 1 else "s"}</title></rect>')
ticks = []
for b in (-5, 0, 5, 10, 15):
    x = L + (bins.index(b) + .5) * bw
    ticks.append(f'<text x="{x:.1f}" y="{H-8}" text-anchor="middle">{"+" if b > 0 else ""}{b}</text>')
step = 25 if top <= 80 else 50
for v in range(0, top + 1, step):
    yy = H - B - (H - B - 10) * v / top
    ticks.append(f'<line x1="{L}" x2="{W-8}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="var(--line)"/><text x="{L-6}" y="{yy+3:.1f}" text-anchor="end">{v}</text>')
zx = L + bins.index(0) * bw + bw
hist_svg = (f'<svg class="hist" viewBox="0 0 {W} {H}" role="img" aria-label="histogram of Cold Clear minus {P}\'s attack per window">'
            + ''.join(ticks) + ''.join(bars)
            + f'<line x1="{zx:.1f}" x2="{zx:.1f}" y1="6" y2="{H-B}" stroke="var(--muted)" stroke-dasharray="3 3"/>'
            + f'<text x="{W-8}" y="16" text-anchor="end">Cold Clear ahead →</text><text x="{zx-6:.1f}" y="16" text-anchor="end">← {P} ahead or level</text><text x="{L}" y="{H-B+12}">≤-8</text></svg>')

typ = sorted(pct[c['id']] for c in clips if c['source'] == 'percentile')
ids = {r['id'] for r in y}
assert all(c['id'] in ids for c in clips if c['source'] == 'percentile'), 'a typical clip is not a charted window'
# The "biggest miss" clips are chosen per MOVE (graded loss, choose-examples.py), not from this chart: their
# windows start at the missed move, which is generally not one of the charted windows. Say so, with their own gaps.
ex_gaps = [c['totals']['cc'] - c['totals']['human'] for c in clips if c['source'] == 'example']
n_ex_charted = sum(c['id'] in ids for c in clips if c['source'] == 'example')
ex_where = ('none of them is one of the windows charted here' if n_ex_charted == 0
            else f'{n_ex_charted} of them happen to be charted windows')
kn = f"{a.rollout_nodes // 1000}k" if a.rollout_nodes % 1000 == 0 else str(a.rollout_nodes)
distnote = (f"Cold Clear's {K}-piece attack minus {P}'s, over all {N} of {P}'s mid-game windows "
            f"(one {kn}-node run each, the {dead} where Cold Clear topped out included). "
            f"{P} matched or beat it in <b>{level} of {N} ({round(100 * level / N)}%)</b>. "
            f"The {n_pct} \"typical\" clips are windows from this chart, at percentiles {typ[0]} to {typ[-1]} "
            f"(mid-rank: windows with the same gap count half; rounded half to even). "
            f"The {n_ex} \"biggest miss\" clips were picked by a different measure, the graded loss of a single move, "
            f"and start at that move, so {ex_where}; their own {K}-piece gaps (the lower-median Cold Clear run shown, minus {P}) "
            f"are {', '.join(map(str, ex_gaps))}.")

out = []
for i, c in enumerate(clips):
    cp = caps[str(i)]
    m = c['id'].split('/')
    assert m[2] == P, c['id']
    where = f"match {int(m[0][-2:])} · round {int(m[1][1:]) + 1} · from piece {int(m[3]) + 1}"
    tag = (f"biggest miss · {where}" if c['source'] == 'example' else f"typical · percentile {pct[c['id']]} · {where}")
    st = sorted(c['seedTotals'])
    nov = [j + 1 for j, h in enumerate(c['human']) if not h['verified']]
    note = (f"Cold Clear searches at random, so it was run {n_seeds} times from this position. Its {K}-piece attack across the {n_seeds} runs: "
            f"{', '.join(map(str, st))}. Shown: the lower median ({c['totals']['cc']}).")
    if c['source'] == 'percentile':
        r0 = next(r for r in y if r['id'] == c['id'])
        note += (f" This window was picked from the chart above by its first run (Cold Clear {r0['cc']['attack']}, {P} {r0['human']['attack']}),"
                 f" which sits at percentile {pct[c['id']]}; the median-of-{n_seeds} run shown here can land elsewhere.")
    if nov:
        note += f" {P}'s moves {nov[0]}–{nov[-1]} here fall after the replay's attack-verified stretch; their boards still rebuild exactly from the recorded drops and garbage."
    def slim(s):
        if s.get('dead'): return {'dead': True}
        o = {k: s[k] for k in ('piece', 'hold', 'cells', 'lines', 'spin', 'attack', 'b2b', 'combo', 'garbage', 'before', 'after')}
        for k in ('current', 'holdPiece', 'next', 'verified', 'loss'):
            if k in s: o[k] = s[k]
        return o
    out.append({'id': c['id'], 'source': c['source'], 'title': cp['title'], 'summary': cp['summary'],
                'claims': sorted([dict(x, text=clean(x['text'])) for x in cp['claims']], key=lambda x: x['step']),
                'tag': tag, 'where': where, 'seedNote': note, 'totals': c['totals'], 'start': c['start'],
                'human': [slim(s) for s in c['human']], 'cc': [slim(s) for s in c['cc']]})

def words(n):
    return {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six'}.get(n, str(n))
first = hist[0]
rest = ', '.join(str(r) for _, r in hist[1:-1]) + (' and ' if len(hist) > 2 else '') + str(hist[-1][1]) if len(hist) > 1 else ''
claims_n = sum(len(cp['claims']) for cp in caps.values())
n_garb = sum(r['verdict'] == 'explained' for r in vlines)
if not vlines:
    frame_line = f'Their saved re-runs report no mismatch.'
else:
    frame_line = (f"Their saved re-runs report {len(vlines)} mismatch line{'s' if len(vlines) != 1 else ''}"
                  + (f", all of one kind: the checker compared the garbage rows Cold Clear inserted on a step with the rows {P} received on it, "
                     f"which differ whenever Cold Clear's piece there cleared lines and the rows waited (the rule below)" if n_garb == len(vlines) else '')
                  + '.')
frame_line += (f" A separate script then rebuilt every frame of both sides from the frames alone, Cold Clear's garbage-waiting rule included, "
               f"and found {'nothing wrong' if rebuild_problems == 0 else f'{rebuild_problems} problems'}"
               + (f"; {unresolved} checker line{'s' if unresolved != 1 else ''} remain{'s' if unresolved == 1 else ''} unexplained." if unresolved else '.'))
foot = f"""<h3>What is and isn't shown</h3><ul>
<li><b>Every frame was rebuilt independently.</b> {words(n_checkers)} agents wrote their own checkers from the raw replay data and re-derived all {frames} placements ({len(clips)} clips × {K} pieces × 2 sides): piece shape, empty cells, piece resting on something, cleared rows, garbage rows and hole column, and TETR.IO attack, B2B and combo. {frame_line} Every caption item ({len(clips)} titles, {len(clips)} summaries and {claims_n} step claims) then went through two skeptics, one checking numbers and one checking wording, in a loop until nothing was refuted: {first[1]} of {first[0]} checks refuted in the first round{', then ' + rest if rest else ''}.</li>
<li><b>Garbage:</b> Cold Clear receives exactly the rows {P} received, on the same piece, with the same hole. If its piece there clears lines, the rows wait for its next piece that clears nothing, which is TETR.IO's own rule. It gets no credit for cancelling with its attack, and the incoming meter it sees is {P}'s meter at that moment.</li>
<li><b>Preview:</b> Cold Clear never sees more than {P} did: hold plus the 5-piece preview, with one new piece revealed per placement.</li>
<li><b>Not modelled:</b> speed and key inputs. {P} played in real time; Cold Clear thought about 0.2 s per piece with no clock. The drop is drawn straight down for clarity, so tucks and spins are shown by where the piece ends up, not how it got there.</li>
<li><b>Cold Clear is a strong bot's line, not "the correct play".</b> It is tuned for Puyo Puyo Tetris scoring, has no 180° spins, and does not know TETR.IO's B2B chain bonus. The bar under {P}'s field is each move's graded loss against it (taller is worse; orange marks a clear miss of 600 or more; hatched means not graded).</li>
<li><b>Not in the proof chain.</b> Everything on this page comes from a replay simulator and one bot, not from the two independent parsers and Dafny proofs behind the match reports.</li>
</ul>"""

meta = {'player': P, 'k': K}
subs = {'{{DATA}}': json.dumps(out, separators=(',', ':')), '{{META}}': json.dumps(meta), '{{HIST}}': hist_svg,
        '{{FOOT}}': foot, '{{DISTNOTE}}': distnote, '{{PLAYER_UP}}': P.upper(), '{{PLAYER}}': P,
        '{{OTHER_HREF}}': f'cc-{O}.html', '{{OTHER}}': O, '{{K}}': str(K)}
page = open(a.template, encoding='utf-8').read()
for k, v in subs.items():
    page = page.replace(k, v)
assert '{{' not in page.replace(subs['{{DATA}}'], ''), 'unfilled placeholder'
body = re.sub(r'<script>.*?</script>', '', page, flags=re.S)
text = re.sub(r'<[^>]+>', ' ', body) + ' ' + json.dumps(out, ensure_ascii=False)
bad = re.findall(r"\b(you|your|yours|he|she|his|her|him)\b", text, re.I)
assert not bad, f'second-person / gendered words in the page: {sorted(set(bad))}'
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
open(a.out, 'w', encoding='utf-8').write(page)
print('ok', a.out, len(page), f'windows={N} level={level} dead={dead} frames={frames} refute={hist}')
