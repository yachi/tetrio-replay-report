#!/usr/bin/env python3
"""Render pages/cc-habits.html: each player's recurring habits, night by night, against Cold Clear.

    python3 build-habits.py --clips <work>/scen/habit-clips.json --out ../pages/cc-habits.html

The input is habit-clips.json, written by tools/cc-coach/habits/clips/finalize.py (see the README's
"Habits page" section). Every figure on the page is read out of that file: each habit-night's rates
are its detector's nights.json entry copied verbatim, the examples carry their own `facts`, and the
few labels this script prints beside a number (which field a row reads) are the only text written
here. The one derived figure is Y6's all-nights row, which the detector did not pool: it is summed
from the per-night counts and asserted against the figures in that habit's own comparison text.

The page addresses yachi as "you" on yachi's view only; pinglamb is always named. Captions are
templated in the page's script from each clip's facts, so no caption is typed.
"""
import argparse, json, os, re

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument('--clips', required=True, help='habit-clips.json')
ap.add_argument('--out', required=True)
a = ap.parse_args()

D = json.load(open(a.clips))
HAB = D['habits']
NIGHTS = sorted({n for h in HAB for n in h['nights']})
PLAYERS = ['yachi', 'pinglamb']
K = D['window_pieces']
SEEDS = D['cc_settings']['seeds']
NODES = D['cc_settings']['nodes']
for h in HAB:
    assert sorted(h['nights']) == NIGHTS, (h['id'], 'night set differs')
    assert h['player'] in PLAYERS


def num(v):
    """A figure exactly as the data file holds it (no rounding here)."""
    if v is None:
        return '–'
    if isinstance(v, float) and v.is_integer() and abs(v) >= 100:
        v = int(v)
    return str(v).replace('-', '−')


def sg(v):
    if v is None:
        return '–'
    s = str(v)
    return ('+' + s if not s.startswith('-') and v != 0 else s).replace('-', '−')


def pct_of_frac(v):        # P6 stores rates as fractions with 4 decimals; x100 at 2 dp is exact
    return None if v is None else float(f'{v * 100:.2f}')


# --- one spec per habit: which fields the card prints -------------------------------------------
# Each returns rows [what, player, cc, n] (strings) and notes (templates with {S}/{s}/{poss}),
# plus the strip value. {S}/{s} = You/you or pinglamb; {poss} = your / pinglamb's.
def spec_Y1(r):
    cs = r['cc_same_positions']
    rows = [['hole moves per 100 positions (6+ rows)', f"{num(r['player_rate_per100'])} ({num(r['occurrences'])})", '—', num(r['eligible'])],
            ['… on positions with a second Cold Clear pick', f"{num(cs['player_rate_per100'])} ({num(cs['player_count'])})",
             f"{num(cs['cc_rate_per100'])} ({num(cs['cc_count'])})", num(cs['eligible'])],
            ['mean graded cost of those moves', num(cs['player_regret_mean']), num(cs['cc_regret_mean']), '']]
    notes = ["Cold Clear makes this shape too, at a similar rate; what separates the two is the cost. "
             "That subsample is small per night, so read the cost line, not a per-night gap.",
             f"All {num(r['occurrences'])} of {{poss}} hole moves this night: mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}."]
    return rows, notes, r['player_rate_per100']


def spec_P1(r):
    rows, _, v = spec_Y1(r)
    notes = ["For pinglamb the one-column-off shape adds nothing: hole moves of every shape cost about the same, so all of them count here. "
             "The Cold Clear subsample is small per night; read the cost line, not a per-night gap.",
             f"All {num(r['occurrences'])} hole moves this night: mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}."]
    return rows, notes, v


def spec_lines(r, gap_key):
    rows = [['lines cleared per move', num(r['player_lines_per_move']), num(r['cc_lines_per_move']), num(r['n'])],
            ['chance the move clears', num(r['player_p_clear']), num(r['cc_p_clear']), num(r['n'])]]
    notes = [f"Cold Clear's pick cleared on {num(r['cc_clear_positions'])} of these positions; "
             f"{{S}} kept stacking on {num(r['occurrences'])} of them (mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])})."]
    return rows, notes, r[gap_key]


def spec_Y2(r): return spec_lines(r, 'gap_lines_per_move')
def spec_P5(r): return spec_lines(r, 'gap_lines_per_move')


def spec_Y3(r):
    x = r['excl_misdrops']
    rows = [['took the ready quad (%)', num(r['player_rate_pct']), num(r['cc_rate_pct']), num(r['eligible'])],
            ['… without misdrop-shaped declines', num(x['player_rate_pct']), num(x['cc_rate_pct']), num(x['eligible'])]]
    notes = [f"{num(r['occurrences'])} declines ({num(r['occurrences_deliberate'])} deliberate). "
             f"The quad came on the very next piece {num(r['quad_next_piece'])} times and within 2 pieces {num(r['quad_within_2'])} times. "
             f"Mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}."]
    return rows, notes, r['gap_pp']


def spec_Y4(r):
    nz = r['cc_vs_cc_noise']
    rows = [['seals where Cold Clear placed cleanly, per 100', f"{num(r['occurrence_rate_per100'])} ({num(r['occurrences'])})", '—', num(r['eligible'])],
            ['same rule, Cold Clear judged by its own second run', f"{num(nz['player_rate_per100'])} ({num(nz['player_count'])})",
             f"{num(nz['cc_rate_per100'])} ({num(nz['cc_count'])})", num(nz['eligible'])],
            ['mean graded cost there', num(nz['player_regret_mean']), num(nz['cc_regret_mean']), '']]
    notes = [f"Careful: Cold Clear's own moves seal a cell more often overall ({num(r['cc_rate_per100'])} against {{poss}} "
             f"{num(r['player_rate_per100'])} per 100 here). The habit is not sealing more; it is sealing where a clean placement existed, "
             f"at a mean graded cost of {num(r['regret_mean'])} (median {num(r['regret_median'])})."]
    return rows, notes, r['occurrence_rate_per100']


def spec_P2(r):
    cs = r['cc_same_positions']; an = r['any_seal']
    rows = [['seals where Cold Clear placed cleanly, per 100 (garbage boards)', f"{num(r['player_rate_per100'])} ({num(r['occurrences'])})", '—', num(r['eligible'])],
            ['same rule, Cold Clear judged by its own second run', f"{num(cs['player_rate_per100'])} ({num(cs['player_count'])})",
             f"{num(cs['cc_rate_per100'])} ({num(cs['cc_count'])})", num(cs['eligible'])],
            ['mean graded cost there', num(cs['player_regret_mean']), num(cs['cc_regret_mean']), '']]
    notes = [f"Careful: counting every seal, Cold Clear seals more often ({num(an['cc_rate_per100'])} against pinglamb's "
             f"{num(an['player_rate_per100'])} per 100 here). The habit is sealing where a clean placement existed, "
             f"at a mean graded cost of {num(r['regret_mean'])} (median {num(r['regret_median'])})."]
    return rows, notes, r['player_rate_per100']


def spec_Y5(r):
    x = r['excl_misdrop_rows']
    rows = [['buried the open garbage hole (%)', num(r['player_rate_pct']), num(r['cc_rate_pct']), num(r['eligible'])],
            ['… without misdrop-shaped moves', num(x['player_rate_pct']), num(x['cc_rate_pct']), num(x['eligible'])]]
    notes = [f"{num(r['occurrences'])} times {{s}} buried it where Cold Clear did not ({num(r['occurrences_deliberate'])} deliberate); "
             f"{num(r['reverse_cc_covers_player_not'])} times the other way round. "
             f"Mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}."]
    return rows, notes, r['gap_pp']


def spec_Y6(r):
    rows = [['T locked sideways (TSS) in a ready TSD slot (%)', num(r['player_rate_graded_pct']), num(r['cc_rate_pct']), num(r['graded'])],
            ["pinglamb on its own ready slots (%)", num(r['pinglamb_rate_pct']), '', num(r['pinglamb_eligible'])]]
    notes = ["Against Cold Clear this habit does not separate: Cold Clear also turns the T sideways in these slots at times. "
             "What makes it a habit is the comparison with pinglamb and how it happens, a third rotate press once the T already points down.",
             f"{num(r['player_tss'])} TSS against {num(r['player_tsd'])} TSD this night."]
    return rows, notes, r['gap_pp']


def spec_P3(r):
    x = r['excl_misdrop_shaped']
    rows = [['cleared again after a clear, no B2B (%)', num(r['player_clear_rate_pct']), num(r['cc_clear_rate_pct']), num(r['eligible'])],
            ['… without misdrop-shaped moves', num(x['player_clear_rate_pct']), num(x['cc_clear_rate_pct']), num(x['eligible'])]]
    c = r['control_no_prior_clear']
    notes = [f"Part of this is a general taste for clearing: with no clear just before, the gap is {sg(c['gap_pp'])} pp "
             f"(n {num(c['eligible'])}), so {sg(c['combo_specific_gap_pp'])} pp is specific to keeping the combo.",
             f"{num(r['occurrences'])} times pinglamb cleared where Cold Clear stacked (mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])})."]
    return rows, notes, r['gap_pp']


def spec_P4(r):
    x = r['excl_misdrop_shaped']
    rows = [['placed on the taller half (%)', num(r['player_rate_pct']), num(r['cc_rate_pct']), num(r['eligible'])],
            ['… without misdrop-shaped moves', num(x['player_rate_pct']), num(x['cc_rate_pct']), num(x['eligible'])]]
    notes = [f"{num(r['occurrences'])} times pinglamb went tall where Cold Clear did not; {num(r['reverse_cc_tall_player_not'])} the other way round. "
             f"Mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}. Per night the counts are small."]
    return rows, notes, r['gap_pp']


def spec_P6(r):
    ci = r['current_I_only']
    rows = [['took the quad (%)', num(pct_of_frac(r['player_quad_rate'])), num(pct_of_frac(r['cc_quad_rate'])), num(r['n'])],
            ['… only when the I is the current piece', num(pct_of_frac(ci['player_quad_rate'])), num(pct_of_frac(ci['cc_quad_rate'])), num(ci['n'])]]
    notes = [f"{num(r['occurrences'])} times pinglamb pressed hold on a current I where Cold Clear quadded "
             f"(mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}). This is the weakest of pinglamb's habits."]
    return rows, notes, pct_of_frac(r['gap'])


SPEC = {'Y1': spec_Y1, 'Y2': spec_Y2, 'Y3': spec_Y3, 'Y4': spec_Y4, 'Y5': spec_Y5, 'Y6': spec_Y6,
        'P1': spec_P1, 'P2': spec_P2, 'P3': spec_P3, 'P4': spec_P4, 'P5': spec_P5, 'P6': spec_P6}

STRIP = {   # label for the per-night strip, and what above zero means
    'Y1': ("{Poss} hole moves per 100 positions (no per-night Cold Clear rate worth reading)", 'rate'),
    'P1': ("{Poss} hole moves per 100 positions (no per-night Cold Clear rate worth reading)", 'rate'),
    'Y4': ("{Poss} seals per 100 positions where Cold Clear placed cleanly", 'rate'),
    'P2': ("{Poss} seals per 100 positions where Cold Clear placed cleanly", 'rate'),
    'Y2': ("lines per move, {s} minus Cold Clear (below zero = fewer clears)", 'gap'),
    'P5': ("lines per move, {s} minus Cold Clear (below zero = fewer clears)", 'gap'),
    'Y3': ("quad rate, {s} minus Cold Clear, pp (below zero = fewer quads)", 'gap'),
    'P6': ("quad rate, {s} minus Cold Clear, pp (below zero = fewer quads)", 'gap'),
    'Y5': ("bury rate, {s} minus Cold Clear, pp (above zero = more burying)", 'gap'),
    'Y6': ("sideways-T rate, {s} minus Cold Clear, pp", 'gap'),
    'P3': ("follow-up clear rate, {s} minus Cold Clear, pp", 'gap'),
    'P4': ("tall-half rate, {s} minus Cold Clear, pp", 'gap'),
}

DESC = {   # one plain line per habit; no figures beyond the habit's own definition thresholds
    'Y1': "From a 6+ row stack, the piece lands one column or one rotation away from a clean spot and leaves a hole under it.",
    'Y2': "Stack at 12–15 rows with 4–7 garbage rows: Cold Clear takes the line clear on offer, {s} kept stacking instead.",
    'Y3': "The I is in hand or in hold and a clean well is ready 4 rows deep: Cold Clear takes the quad now, {s} played another piece first.",
    'Y4': "A piece locks over a cell and cuts it off completely (no tuck or spin can reach it), where Cold Clear's pick placed cleanly.",
    'Y5': "The top garbage hole is open to dig; a piece is laid across that column without clearing the row, where Cold Clear kept it open.",
    'Y6': "The T goes into a ready TSD slot, but an extra rotate press locks it sideways: a T-spin single instead of the double.",
    'P1': "From a 6+ row stack, a placement leaves a covered cell where Cold Clear's pick does not, one column off or otherwise.",
    'P2': "On a board with garbage, a placement seals a cell off completely while Cold Clear's pick placed cleanly.",
    'P3': "Right after a line clear, with no B2B to protect, pinglamb cleared again to keep a short combo where Cold Clear kept building.",
    'P4': "One half of the board is clearly taller (10–13 rows, garbage below): pinglamb placed on the tall half where Cold Clear filled the low side.",
    'P5': "Stack at 12–15 rows with 4–7 garbage rows: Cold Clear takes the line clear on offer, pinglamb kept stacking instead.",
    'P6': "At 10+ rows, with the I as the current piece and a well ready 4+ deep, pinglamb pressed hold instead of taking the quad.",
}

# Y6 has no pooled block in its nights.json; sum the per-night counts and check them against the
# figures its own comparison text prints, so a summing slip cannot reach the page.
y6 = next(h for h in HAB if h['id'] == 'Y6')
tot = {k: sum(v['rates'][k] for v in y6['nights'].values())
       for k in ('player_tss', 'player_tsd', 'eligible', 'graded', 'cc_tss', 'pinglamb_tss', 'pinglamb_eligible')}
y6_pooled = {'player_rate_graded_pct': round(100 * tot['player_tss'] / tot['eligible'], 2),
             'cc_rate_pct': round(100 * tot['cc_tss'] / tot['graded'], 2),
             'graded': tot['graded'],
             'pinglamb_rate_pct': round(100 * tot['pinglamb_tss'] / tot['pinglamb_eligible'], 2),
             'pinglamb_eligible': tot['pinglamb_eligible'],
             'player_tss': tot['player_tss'], 'player_tsd': tot['player_tsd']}
y6_pooled['gap_pp'] = round(y6_pooled['player_rate_graded_pct'] - y6_pooled['cc_rate_pct'], 2)
_cmp = y6['cc_comparison'].replace('−', '-')
for want in (f"{y6_pooled['player_rate_graded_pct']}%", f"{y6_pooled['cc_rate_pct']}%", f"{y6_pooled['pinglamb_rate_pct']}%",
             f"{tot['player_tss']} of all {tot['eligible']}", f"{tot['graded']}", f"{tot['pinglamb_tss']} of {tot['pinglamb_eligible']}",
             f"{y6_pooled['gap_pp']:.2f} pp"):
    assert want in _cmp, f'Y6 summed figure {want!r} is not in its comparison text'
# label: the player row is over every eligible placement here, as in the comparison text
Y6_ALL_NOTE = "All nights summed from the per-night counts: the TSS share is over every in-slot placement, Cold Clear's over the graded ones."


def card(h, rates, pooled=False):
    if h['id'] == 'Y6' and pooled:
        rates = y6_pooled
        rows, notes, _ = spec_Y6(dict(rates, player_tss=rates['player_tss'], player_tsd=rates['player_tsd']))
        rows[0][3] = f"{num(tot['eligible'])} / {num(tot['graded'])}"
        notes = notes[:1] + [Y6_ALL_NOTE]
        return rows, notes
    rows, notes, _ = SPEC[h['id']](rates)
    return rows, notes


# --- clips: slimmed to what the page draws and captions ------------------------------------------
def slim_step(s):
    if s.get('dead'):
        return {'dead': True, 'why': s.get('why', '')}
    o = {k: s[k] for k in ('piece', 'hold', 'cells', 'lines', 'cleared_rows', 'spin', 'attack', 'b2b', 'combo', 'garbage_in')}
    o['after'] = ''.join(s['after'])
    if 'kind' in s:
        o['kind'] = s['kind']
    if 'queue' in s:
        o['q'] = [s['queue']['current'], s['queue']['hold'], ''.join(s['queue']['next'])]
    return o


FACT_KEYS = ('max_height_before', 'garbage_rows_before', 'covered_cells_before', 'incoming_before', 'b2b_before',
             'combo_before', 'current', 'hold', 'next', 'well_rows_ready', 'well_column', 'quad_available',
             'tsd_slot_ready', 'tsd_available', 'player_first', 'cc_first', 'player_4', 'cc_4',
             'cc_first_contrasts_with_habit', 'contrast_rule')


def slim_clip(c):
    R = c['rows']
    assert len(c['start']['field']) == R and all(len(''.join(s['after'])) == 10 * R for s in c['human'])
    assert all(s.get('verified') for s in c['human']), c['id']
    m = c['id'].split('/')
    run = c['cc_run']
    return {'id': c['id'], 'file': c['file'], 'round': c['round'] + 1, 'piece': c['lock'] + 1, 'rows': R,
            'regret': c['regret'], 'misdrop': c['misdrop_shaped'],
            'pool': [c['why_picked']['pool_size'], c['why_picked']['pool_regret_median'], c['why_picked']['rank_by_distance']],
            'start': {'field': ''.join(c['start']['field']), 'b2b': c['start']['b2b'], 'combo': c['start']['combo'],
                      'q': [c['start']['current'], c['start']['hold'], ''.join(c['start']['next'])]},
            'human': [slim_step(s) for s in c['human']], 'cc': [slim_step(s) for s in c['cc']],
            'same': run['first_move_same_as_shown'], 'nseeds': len(run['seeds']), 'graded_eq': run['first_move_equals_graded_pick'],
            'facts': {k: c['facts'].get(k) for k in FACT_KEYS}}


out_h = []
n_ex = []
for h in HAB:
    strip = []
    nights = {}
    for n in NIGHTS:
        v = h['nights'][n]
        rows, notes = card(h, v['rates'])
        strip.append(SPEC[h['id']](v['rates'])[2])
        nights[n] = {'rows': rows, 'notes': notes, 'pool': v['pool']['pool'], 'occ': v['pool']['occurrences'],
                     'ex': [slim_clip(c) for c in v['examples']]}
        assert all(c['night'] == n and c['player'] == h['player'] and c['habit'] == h['id'] for c in v['examples'])
        n_ex.append(len(v['examples']))
    prow, pnotes = card(h, h['pooled'], pooled=True)
    out_h.append({'id': h['id'], 'player': h['player'], 'name': h['name'], 'desc': DESC[h['id']],
                  'definition': h['definition'], 'cmp': h['cc_comparison'], 'strip': strip,
                  'stripLabel': STRIP[h['id']][0], 'stripKind': STRIP[h['id']][1],
                  'all': {'rows': prow, 'notes': pnotes}, 'nights': nights})

DATA = {'nights': NIGHTS, 'players': PLAYERS, 'k': K, 'seeds': len(SEEDS), 'nodes': NODES, 'habits': out_h}
n_clips = sum(n_ex)
lo, hi = min(n_ex), max(n_ex)
one_ex = D['log']['habit_nights_with_one_example']
meta = {'n_clips': n_clips, 'per_night': hi, 'one_ex': one_ex, 'n_habits': len(HAB)}

TEMPLATE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'habits-template.html'), encoding='utf-8').read()
page = (TEMPLATE.replace('{{DATA}}', json.dumps(DATA, separators=(',', ':'), ensure_ascii=False))
        .replace('{{META}}', json.dumps(meta, separators=(',', ':'))))
assert '{{' not in page.replace(json.dumps(DATA, separators=(',', ':'), ensure_ascii=False), ''), 'unfilled placeholder'

# --- page-level guards ---------------------------------------------------------------------------
assert not re.search(r'https?://', page.replace('http://www.w3.org/2000/svg', '')), 'external URL in a self-contained page'
assert not re.search(r'<(link|img|iframe)\b[^>]*\b(href|src)=', page, re.I), 'external resource tag'
text = re.sub(r'<[^>]+>', ' ', page)
bad = re.findall(r"\b(he|she|his|her|him|hers)\b", text, re.I)
assert not bad, f'gendered pronouns in the page: {sorted(set(bad))}'
assert not re.search(r'\b(claude-|opus|sonnet|haiku|gpt-)', page, re.I), 'model identifier in the page'
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
open(a.out, 'w', encoding='utf-8').write(page)
print('ok', a.out, len(page.encode()), f'habits={len(HAB)} nights={len(NIGHTS)} clips={n_clips} per-night={lo}..{hi}')
