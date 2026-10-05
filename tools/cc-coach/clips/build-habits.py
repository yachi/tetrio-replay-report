#!/usr/bin/env python3
"""Render pages/cc-habits.html: each player's recurring habits, night by night, against Cold Clear.

    python3 build-habits.py --clips <work>/scen/habit-clips.json --out ../pages/cc-habits.html

The input is habit-clips.json, written by tools/cc-coach/habits/clips/finalize.py (see the README's
"Habits page" section). Every figure on the page is read out of that file: each habit-night's rates
are its detector's nights.json entry copied verbatim, the examples carry their own `facts`, and the
few labels this script prints beside a number (which field a row reads) are the only text written
here. Each card's "how it is measured" text is written here for readers (READER); every figure in
it must appear in that habit's detector output text (or in the quoted skeptic output lines in
SOURCE_EXTRA), and the build fails otherwise.

The page addresses yachi as "you" on yachi's view only; pinglamb is always named. Captions are
templated in the page's script from each clip's facts, so no caption is typed.
"""
import argparse, json, os, re

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument('--clips', required=True, help='habit-clips.json')
ap.add_argument('--out', required=True)
ap.add_argument('--corpus', required=True, help="the work directory's corpus/ (per-night <date>.jsonl.rounds.json)")
ap.add_argument('--sessions', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'sessions'),
                help="the repo's sessions/ (each night's match report facts.json)")
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

# Each night's match files, from the match report the page links to (sessions/<night>/report/facts.json), checked
# against the files the habit corpus was built from: the same files, with the same number of rounds in each. The
# page prints the count, and every example is placed by its match report index (m<index>r<round>).
MATCHES = {}
for n in NIGHTS:
    fm = json.load(open(os.path.join(a.sessions, n, 'report', 'facts.json')))['matches']
    rep = {m['file']: m for m in fm}
    cr = json.load(open(os.path.join(a.corpus, n + '.jsonl.rounds.json')))
    crounds = {}
    for r in cr:
        crounds.setdefault(r['file'], set()).add(r['round'])
    assert set(crounds) == set(rep), (n, 'habit corpus files differ from the match report', sorted(set(crounds) ^ set(rep)))
    for f, m in rep.items():
        assert crounds[f] == {r['index'] for r in m['rounds']}, (n, f, 'round set differs from the match report')
    MATCHES[n] = rep


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
# `here` names the scope of a note: 'this night' on a night's view, 'over all 15 nights' on the pooled one.
HERE = 'this night'
# A note starting with QUAL qualifies the habit itself (a control explains part of it), like a STRENGTH note does; the
# header counts the cards carrying either on the view shown, so that count is read off the notes, never typed.
QUAL = '\x00qual\x00'
def cc_cost(cs):
    """Cold Clear's mean cost on the second-run subsample. Y1 can value only the events whose graded seed-1
    move is the hole move itself (cc_regret_n of cc_count); say so when that is not all of them."""
    v = num(cs['cc_regret_mean'])
    n = cs.get('cc_regret_n')
    if n is not None and n != cs['cc_count']:
        v = f"{v} ({n} of {cs['cc_count']} valued)" if n else f"– (0 of {cs['cc_count']} valued)"
    return v


ALT_LABEL = "Cold Clear, same rule, from a separate second search (another draw)"
def alt_row(cs):
    """Cold Clear's second-run count from the OTHER seed-1 search of the same positions (the detector's cc_alt_seed1)."""
    x = cs['cc_alt_seed1']
    return [ALT_LABEL, '—', f"{num(x['cc_rate_per100'])} ({num(x['cc_count'])})", num(x['eligible'])]


def alt_note(cs):
    x = cs['cc_alt_seed1']
    return (f"Cold Clear's second-run figure is one noisy draw: a separate second search of the same positions gives "
            f"{num(x['cc_rate_per100'])} per 100 ({num(x['cc_count'])}) instead of {num(cs['cc_rate_per100'])} ({num(cs['cc_count'])}) {HERE}, "
            "so read Cold Clear's rate there as a range between the two, not a point.")


def spec_Y1(r):
    cs = r['cc_same_positions']
    rows = [['hole moves per 100 positions (6+ rows)', f"{num(r['player_rate_per100'])} ({num(r['occurrences'])})", '—', num(r['eligible'])],
            ['… with a second Cold Clear pick: shift or rotation shapes only, both sides', f"{num(cs['player_rate_per100'])} ({num(cs['player_count'])})",
             f"{num(cs['cc_rate_per100'])} ({num(cs['cc_count'])})", num(cs['eligible'])],
            alt_row(cs),
            ['mean graded cost of those moves', num(cs['player_regret_mean']), cc_cost(cs), '']]
    pc = Y1_POOLED_CC
    notes = [f"Over all 15 nights, on the positions where Cold Clear can be compared, it makes this shape at a similar rate "
             f"({num(pc['cc_rate_per100'])} against {{poss}} {num(pc['player_rate_per100'])} per 100); what separates the two is the cost. "
             + ("Per night that subsample is too small to compare rates, so read the cost line, not this night's two rates." if HERE == 'this night'
                else "Read the cost line."),
             alt_note(cs),
             f"All {num(r['occurrences'])} of {{poss}} hole moves {HERE}: mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}."]
    return rows, notes, r['player_rate_per100']


def spec_P1(r):
    cs = r['cc_same_positions']
    rows = [['hole moves per 100 positions (6+ rows)', f"{num(r['player_rate_per100'])} ({num(r['occurrences'])})", '—', num(r['eligible'])],
            ['… on positions with a second Cold Clear pick', f"{num(cs['player_rate_per100'])} ({num(cs['player_count'])})",
             f"{num(cs['cc_rate_per100'])} ({num(cs['cc_count'])})", num(cs['eligible'])],
            alt_row(cs),
            ['mean graded cost of those moves', num(cs['player_regret_mean']), cc_cost(cs), '']]
    v = r['player_rate_per100']
    notes = [alt_note(cs), "For pinglamb every hole shape counts, not only one column off: in the re-checks' stricter measure (cost above "
             "pinglamb's other moves that differ from Cold Clear's) the other hole moves cost about as much. In plain graded cost the "
             "one-column-off ones average more (559.0 against 419.6 over all 15 nights), and both are costly. "
             "The Cold Clear subsample is small per night; read the cost line, not a per-night gap.",
             f"All {num(r['occurrences'])} hole moves {HERE}: mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}."]
    return rows, notes, v


def spec_lines(r, gap_key):
    rows = [['lines cleared per move', num(r['player_lines_per_move']), num(r['cc_lines_per_move']), num(r['n'])],
            ['chance the move clears', num(r['player_p_clear']), num(r['cc_p_clear']), num(r['n'])]]
    notes = [f"Cold Clear's pick cleared on {num(r['cc_clear_positions'])} of these positions; "
             f"{{s}} kept stacking on {num(r['occurrences'])} of them (misdrop-shaped included; mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])})."]
    return rows, notes, r[gap_key]


def spec_Y2(r): return spec_lines(r, 'gap_lines_per_move')
def spec_P5(r):
    rows, notes, v = spec_lines(r, 'gap_lines_per_move')
    b = r['band_10_13_any_garbage']
    rows.append(['lines per move at 10–13 rows, any garbage: the band the re-checks recommend for pinglamb',
                 num(b['player_lines_per_move']), num(b['cc_lines_per_move']), num(b['n'])])
    notes.append(f"In that recommended band the gap {HERE} is {sg(b['gap_lines_per_move'])} lines per move, against "
                 f"{sg(r['gap_lines_per_move'])} in the 12–15 row band the rest of this card shows.")
    return rows, notes, v


def spec_Y3(r):
    x = r['excl_misdrops']
    rows = [['took the ready quad (%)', num(r['player_rate_pct']), num(r['cc_rate_pct']), num(r['eligible'])],
            ['… without misdrop-shaped declines', num(x['player_rate_pct']), num(x['cc_rate_pct']), num(x['eligible'])]]
    notes = [f"{num(r['eligible'] - r['player_quad'])} declines in all; on {num(r['occurrences'])} of them Cold Clear took the quad "
             f"(these are the occurrences, {num(r['occurrences_deliberate'])} deliberate). "
             f"The quad came on the very next piece {num(r['quad_next_piece'])} times and within 2 pieces {num(r['quad_within_2'])} times. "
             f"Over all of them, misdrop-shaped included: mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}."]
    return rows, notes, r['gap_pp']


def spec_Y4(r):
    nz = r['cc_vs_cc_noise']
    rows = [["seals where Cold Clear's pick sealed nothing, per 100", f"{num(r['occurrence_rate_per100'])} ({num(r['occurrences'])})", '—', num(r['eligible'])],
            ['same rule, Cold Clear judged by its own second run', f"{num(nz['player_rate_per100'])} ({num(nz['player_count'])})",
             f"{num(nz['cc_rate_per100'])} ({num(nz['cc_count'])})", num(nz['eligible'])],
            alt_row(nz),
            ['mean graded cost there', num(nz['player_regret_mean']), num(nz['cc_regret_mean']), '']]
    notes = [alt_note(nz), f"Careful: counting every seal, Cold Clear's own moves seal a cell more often ({num(r['cc_rate_per100'])} against {{poss}} "
             f"{num(r['player_any_seal_rate_per100'])} per 100 {HERE}). The habit is not sealing more; it is sealing where Cold Clear's pick sealed nothing, "
             f"at a mean graded cost of {num(r['regret_mean'])} (median {num(r['regret_median'])})."]
    return rows, notes, r['occurrence_rate_per100']


def spec_P2(r):
    cs = r['cc_same_positions']; an = r['any_seal']
    rows = [["seals where Cold Clear's pick sealed nothing, per 100 (garbage boards)", f"{num(r['player_rate_per100'])} ({num(r['occurrences'])})", '—', num(r['eligible'])],
            ['same rule, Cold Clear judged by its own second run', f"{num(cs['player_rate_per100'])} ({num(cs['player_count'])})",
             f"{num(cs['cc_rate_per100'])} ({num(cs['cc_count'])})", num(cs['eligible'])],
            alt_row(cs),
            ['mean graded cost there', num(cs['player_regret_mean']), num(cs['cc_regret_mean']), '']]
    notes = [alt_note(cs), f"Careful: counting every seal, Cold Clear seals more often ({num(an['cc_rate_per100'])} against pinglamb's "
             f"{num(an['player_rate_per100'])} per 100 {HERE}). The habit is sealing where Cold Clear's pick sealed nothing, "
             f"at a mean graded cost of {num(r['regret_mean'])} (median {num(r['regret_median'])})."]
    return rows, notes, r['player_rate_per100']


def spec_Y5(r):
    x = r['excl_misdrop_rows']
    rows = [['buried the open garbage hole (%)', num(r['player_rate_pct']), num(r['cc_rate_pct']), num(r['eligible'])],
            ['… without misdrop-shaped moves', num(x['player_rate_pct']), num(x['cc_rate_pct']), num(x['eligible'])]]
    notes = [f"{num(r['occurrences'])} times {{s}} buried it where Cold Clear did not ({num(r['occurrences_deliberate'])} deliberate); "
             f"{num(r['reverse_cc_covers_player_not'])} times the other way round. "
             f"Over all of them, misdrop-shaped included: mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}."]
    return rows, notes, r['gap_pp']


def spec_Y6(r):
    # every rate on this card is over the GRADED in-slot placements (Cold Clear's pick exists only there)
    rows = [['T locked sideways (TSS) in a ready TSD slot (%)', num(r['player_rate_graded_pct']), num(r['cc_rate_pct']), num(r['graded'])],
            ["pinglamb on its own ready slots (%)", num(r['pinglamb_rate_pct']), '', num(r['pinglamb_eligible'])]]
    pr, cr = r['player_rate_graded_pct'], r['cc_rate_pct']
    cmpw = ('more often than' if cr > pr else 'less often than' if cr < pr else 'exactly as often as')
    nt = Y6_SIGN
    allsep = (f"{{s}} are above Cold Clear on only {nt['player_above_cc_nights']} of the {nt['nights_differing']} nights where the two rates differ")
    if HERE == 'this night' and pr > cr:   # this night does show yachi above Cold Clear: say so first, then the corpus verdict
        head = (f"This night {{s}} turned the T sideways in these slots more often than Cold Clear's pick did ({num(pr)}% against {num(cr)}%). "
                f"Over the 15 nights the habit still does not separate from Cold Clear: {allsep}, and this is one of them. ")
    else:
        head = (f"Against Cold Clear this habit does not separate: {HERE} Cold Clear turned the T sideways in these slots {cmpw} {{s}} "
                f"({num(cr)}% against {num(pr)}%), and {allsep}. ")
    notes = [head +
             "What makes it a habit is the comparison with pinglamb, and how it happens: {poss} TSDs are exactly two same-direction rotates "
             "98% of the time (3980 of 4060), while of the 190 sideways Ts over the 15 nights 184 had exactly three rotate presses "
             "(89 three clockwise, 70 three counter-clockwise, 25 CW CW CCW) and the rest 5, 7 or 9.",
             f"{num(r['player_tss_graded'])} TSS against {num(r['player_tsd_graded'])} TSD on the {num(r['graded'])} graded placements {HERE} "
             f"(counting the {num(r['eligible'] - r['graded'])} that could not be graded too: {num(r['player_tss'])} TSS, {num(r['player_tsd'])} TSD)."
             if r['eligible'] != r['graded'] else
             f"{num(r['player_tss_graded'])} TSS against {num(r['player_tsd_graded'])} TSD on the {num(r['graded'])} graded placements {HERE}."]
    return rows, notes, r['gap_pp']


def spec_P3(r):
    x = r['excl_misdrop_shaped']
    rows = [['cleared again after a clear, no B2B (%)', num(r['player_clear_rate_pct']), num(r['cc_clear_rate_pct']), num(r['eligible'])],
            ['… without misdrop-shaped moves', num(x['player_clear_rate_pct']), num(x['cc_clear_rate_pct']), num(x['eligible'])]]
    c = r['control_no_prior_clear']
    g, g0, d = r['gap_pp'], c['gap_pp'], c['combo_specific_gap_pp']
    if g0 <= 0:
        why = ("so none of the gap here comes from a general taste for clearing: away from a clear pinglamb does not clear more "
               "than Cold Clear" + (" (pinglamb clears less)" if g0 < 0 else "") + ".")
    elif g0 >= g:
        why = "so all of the gap here is matched by a general taste for clearing, with nothing extra after a clear."
    elif 2 * g0 >= g:
        why = "so most of the gap here is a general taste for clearing, not something tied to the clear just before."
    else:
        why = "so part of the gap here is a general taste for clearing."
    notes = [(QUAL if g0 > 0 else '') + f"Control: with no clear just before, the gap is {sg(g0)} pp (n {num(c['eligible'])}), {why} "
             f"The gap after a clear is {sg(d)} pp {'above' if d >= 0 else 'below'} that control; "
             "this is a difference of two gaps, not a measured cause.",
             f"{num(r['occurrences'])} times pinglamb cleared where Cold Clear stacked (misdrop-shaped included; mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])})."]
    if x['gap_pp'] is not None and x['gap_pp'] <= 0:
        notes.append(f"Without the misdrop-shaped moves there is no gap {HERE} ({num(x['player_clear_rate_pct'])}% against "
                     f"{num(x['cc_clear_rate_pct'])}%): the whole of the gap sits in positions where pinglamb's move is misdrop-shaped.")
    return rows, notes, r['gap_pp']


def spec_P4(r):
    x = r['excl_misdrop_shaped']
    rows = [['placed on the taller half (%)', num(r['player_rate_pct']), num(r['cc_rate_pct']), num(r['eligible'])],
            ['… without misdrop-shaped moves', num(x['player_rate_pct']), num(x['cc_rate_pct']), num(x['eligible'])]]
    notes = [f"{num(r['occurrences'])} times pinglamb went tall where Cold Clear did not; {num(r['reverse_cc_tall_player_not'])} the other way round. "
             f"Over all of them, misdrop-shaped included: mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])}. Per night the counts are small."]
    return rows, notes, r['gap_pp']


def spec_P6(r):
    ci = r['current_I_only']
    rows = [['took the quad (%)', num(pct_of_frac(r['player_quad_rate'])), num(pct_of_frac(r['cc_quad_rate'])), num(r['n'])],
            ['… only when the I is the current piece', num(pct_of_frac(ci['player_quad_rate'])), num(pct_of_frac(ci['cc_quad_rate'])), num(ci['n'])]]
    notes = [f"{num(r['occurrences'])} times pinglamb pressed hold on a current I where Cold Clear quadded "
             f"(mean graded cost {num(r['regret_mean'])}, median {num(r['regret_median'])})."]
    return rows, notes, pct_of_frac(r['gap'])


SPEC = {'Y1': spec_Y1, 'Y2': spec_Y2, 'Y3': spec_Y3, 'Y4': spec_Y4, 'Y5': spec_Y5, 'Y6': spec_Y6,
        'P1': spec_P1, 'P2': spec_P2, 'P3': spec_P3, 'P4': spec_P4, 'P5': spec_P5, 'P6': spec_P6}

STRIP = {   # label for the per-night strip, and what above zero means
    'Y1': ("{Poss} hole moves per 100 positions (no per-night Cold Clear rate worth reading)", 'rate'),
    'P1': ("{Poss} hole moves per 100 positions (no per-night Cold Clear rate worth reading)", 'rate'),
    'Y4': ("{Poss} seals per 100 positions where Cold Clear's pick sealed nothing", 'rate'),
    'P2': ("{Poss} seals per 100 positions where Cold Clear's pick sealed nothing", 'rate'),
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
    'Y4': "A piece locks over a cell and cuts it off completely (no tuck or spin can reach it), where Cold Clear's pick at the same position sealed nothing.",
    'Y5': "The top garbage hole is open to dig; a piece is laid across that column without clearing the row, where Cold Clear kept it open.",
    'Y6': "The T goes into a ready TSD slot but locks sideways: a T-spin single instead of the double. Each example lists the keys pressed for that T.",
    'P1': "From a 6+ row stack, a placement leaves a covered cell where Cold Clear's pick does not, one column off or otherwise.",
    'P2': "On a board with garbage, a placement seals a cell off completely while Cold Clear's pick at the same position sealed nothing.",
    'P3': "Right after a line clear, with no B2B to protect, pinglamb cleared again (usually a single, which keeps a short combo going) where Cold Clear cleared nothing and kept building. The examples are single-line clears.",
    'P4': "One half of the board is clearly taller (10–13 rows, garbage below): pinglamb placed on the tall half where Cold Clear filled the low side. "
          "A piece goes by the average column of its four cells; one whose average sits exactly on the midline, between columns 5 and 6, "
          "counts as on the right half, for both sides.",
    'P5': "Stack at 12–15 rows with 4–7 garbage rows: Cold Clear takes the line clear on offer, pinglamb kept stacking instead. "
          "The rates below are for the 12–15 row band; the last table row is the 10–13 row band the re-checks recommend for pinglamb, "
          "where the gap is much smaller.",
    'P6': "At 10+ rows, with the I as the current piece and a well ready 4+ deep, pinglamb pressed hold instead of taking the quad.",
}

# "How it is measured", written for readers. The detector's own text (definition + cc_comparison, both
# carried in habit-clips.json) is the source of every figure here: reader_text() fails the build when a
# number in this text is not in that source, or in SOURCE_EXTRA (skeptic output lines quoted verbatim).
# {S}/{s}/{poss} become You/you/your on yachi's view; pinglamb is named.
SOURCE_EXTRA = {
    # scen/verify-tspins-TS2-misdrop.out, lines 2, 38 and 40
    'Y6': "[yachi] TSS 190 / 4250 in-slot T | yachi TSD n=4060: 2 same rot 3980 (98%) | "
          "yachi TSS rotation counts: {3: 184, 5: 3, 7: 2, 9: 1} | "
          "[(('rotateCW', 'rotateCW', 'rotateCW'), 89), (('rotateCCW', 'rotateCCW', 'rotateCCW'), 70), (('rotateCW', 'rotateCW', 'rotateCCW'), 25)] | "
          # FINDINGS.md yachi #6, the research summary's own comparison (quoted verbatim)
          "Above cc's own sideways-in-slot rate (3.71%) in only 11/15.",
    # scen/verify-quads-Q2-pinglamb-delayed-quad-misdrop.out, PART 3
    'P6': "I current       clean n=557 gap -0.065 [-0.106,-0.021]; sessions neg 10/13 p=9.2e-02",
}
READER = {
 'Y1': ["Every one of {poss} graded positions with the stack at 6 or more rows. A hole move leaves a new covered cell where Cold Clear's pick "
        "does not, and is one column or one rotation away from Cold Clear's choice (or the same shape one column over would have been clean). "
        "Over the 15 nights {s} made 378 of them in 23 722 positions (1.593 per 100), at a mean graded cost of 744.8 (median 486); 166 cost 600 or more. "
        "Per night the rate runs from 1.065 (07-22) to 2.273 (08-19) per 100.",
        "Against Cold Clear: on the 1 961 positions where Cold Clear was also run a second time with a different random seed, {s} made 25 hole moves "
        "(1.275 per 100) and Cold Clear's second run made 21 of the same shape against its first (1.071 per 100). On both sides this "
        "comparison counts only the one-column-shift and rotation shapes: the own-shape-one-column-over test is left out, so {poss} count "
        "here is not the subsample's share of the hole moves above. Cold Clear's 21 is one noisy draw: a separate second search of the "
        "same positions gives {=cc_same_positions.cc_alt_seed1.cc_count} ({=cc_same_positions.cc_alt_seed1.cc_rate_per100} per 100). So Cold Clear makes this shape "
        "at a similar rate, and the difference is the cost: {poss} hole moves cost 635.4 on average there (median 461), while the 16 of Cold Clear's 21 that "
        "can be valued average −43.5 (median −1.5), i.e. nothing. That subsample holds only 73–247 positions and 0–5 events a night, so read the "
        "cost, not a per-night gap."],
 'Y2': ["Every one of {poss} graded positions with the stack at 12–15 rows and 4–7 garbage rows: 2508 over the 15 nights. {S} clear 0.8166 lines "
        "per move against Cold Clear's 1.0008 (−0.1842), and clear at all on 0.339 of moves against 0.401 (−0.062). The gap is negative on 14 nights "
        "and positive on one (09-03, +0.011, n 91), and runs as wide as −0.3535 (07-24).",
        "An occurrence is a position where Cold Clear's pick clears a line and {poss} move does not: 340 in all, from 11 (09-03) to 47 (10-03) a "
        "night, at a mean graded cost of 306.0 (median 205.5). In the wider band of 10–15 rows with 1–7 garbage rows: 6220 positions, 0.688 "
        "against 0.842 lines per move (−0.1545), 824 occurrences."],
 'Y3': ["Every one of {poss} graded positions where the I is the current piece or in hold and a clean well is ready at least 4 rows deep: 2465 over "
        "the 15 nights. {S} took the quad on 65.96% of them, Cold Clear on 79.27% (−13.31 pp). The gap is negative on all 15 nights: smallest on "
        "08-14 (−6.98) and 09-03 (−9.35), largest on 09-10 (−24.78).",
        "Of the 556 declines, 124 are misdrop-shaped (the I dropped one column beside the well, the right piece one column off, or a very fast "
        "drop with many keys) and 432 deliberate. With the misdrop-shaped declines removed the gap is −8.71 pp (69.46% against 78.17%, n 2341)."],
 'Y4': ["Every one of {poss} graded positions: 25348 over the 15 nights. A seal cuts empty cells off completely, so no tuck or spin can reach them. "
        "The habit is a seal where Cold Clear's own pick at the same position (same queue, hold and garbage) seals nothing, the two moves differ, "
        "and {poss} move is not one column or one rotation off Cold Clear's. That happened 297 times (1.172 per 100), at a mean graded cost of "
        "438.1 (median 391); 96 cost 600 or more.",
        "Counting every seal, Cold Clear seals more than {s} do: its pick seals at 4.052 per 100 (1027 positions) against {poss} moves at 2.884 per 100 "
        "(731), or 1.976 per 100 (501) without the misdrop-shaped ones, and that is so on all 15 nights. So the habit is not sealing more often; "
        "it is sealing where Cold Clear's pick sealed nothing, at a cost.",
        "Against Cold Clear's own second run (a different random seed) on 2097 positions, by the same rule: {s} 23 (1.097 per 100, mean graded "
        "cost 562.3); Cold Clear 18 (0.858 per 100, mean 209.7), or 15 (0.715 per 100, mean 138.3) with the full one-column-off filter applied "
        "to its side too. That last count is one noisy draw: a separate second search of the same positions gives "
        "{=cc_vs_cc_noise.cc_alt_seed1.cc_count} ({=cc_vs_cc_noise.cc_alt_seed1.cc_rate_per100} per 100) by the same full rule. "
        "About as often either way; the difference is the cost."],
 'Y5': ["Every one of {poss} graded positions where a garbage hole is open to the surface: 11386 over the 15 nights. Burying it means putting a "
        "cell in that column above the hole so that the count of covered cells goes up. {S} bury it on 3.43% of them (390), Cold Clear on "
        "1.94% (221): +1.48 pp. {S} are above Cold Clear on all 15 nights, from +0.43 (07-24) to +2.28 (09-11).",
        "296 times {s} buried it where Cold Clear did not (108 misdrop-shaped, 188 deliberate), and 127 times it went the other way round. "
        "Mean graded cost 502.4 (median 423); the deliberate ones alone 475.3 (median 405.5). With the misdrop-shaped moves removed from the "
        "positions (9007): 2.92% against 1.93%, +0.99 pp, above on 14 nights and level on 07-24. At 12+ rows (5791 positions): 4.08% "
        "against 2.45%, +1.62 pp."],
 'Y6': ["Every T {s} put into a ready TSD slot, locked as a TSD or sideways as a TSS: 4250 over the 15 nights, of which 4229 could "
        "be graded (Cold Clear treats the rest as lost). On the graded ones {s} locked the TSS on 4.47% and Cold Clear's pick at the same "
        "position was the sideways TSS on 4.97%: −0.50 pp. {S} are above Cold Clear on only 4 of the 14 nights where the two differ "
        "(sign test p = 0.18).",
        "Where {s} played the TSS (189 graded), Cold Clear played the TSD 118 times (these are the occurrences), the TSS too 47 times, and "
        "did not use the slot 24 times. Where {s} played the TSD (4040 graded), Cold Clear went sideways 163 times. So against Cold Clear "
        "this does not separate. It is a habit next to pinglamb (0.24%, 11 of 4672, lower than {poss} rate on every night) and in how it "
        "happens: {poss} TSDs are exactly two same-direction rotates 98% of the time (3980 of 4060), while of the 190 sideways Ts 184 had "
        "exactly three rotate presses (89 three clockwise, 70 three counter-clockwise, 25 CW CW CCW) and the rest 5, 7 or 9. Graded cost is not "
        "the measure here; the re-checks put the cost at about 2 attack lines per event.",
        "The research summary says {s} are above Cold Clear on 11 of the 15 nights. That compares {poss} rate with a different Cold Clear "
        "figure, its sideways rate over its own in-slot T placements (3.71%), not its pick on {poss} positions; this card uses the pick on "
        "the same positions, where {s} are above on only 4 nights."],
 'P1': ["Every graded position of pinglamb with the stack at 6 or more rows. A hole move leaves a new covered cell where Cold Clear's pick "
        "does not, whatever its shape: 808 of them in 20 704 positions over the 15 nights (3.903 per 100), at a mean graded cost of 470.1 "
        "(median 272.5); 243 cost 600 or more. 293 of the 808 are one column or one rotation off Cold Clear's choice (1.415 per 100, mean "
        "559.0, median 362); the other 515 average 419.6 (median 240).",
        "Against Cold Clear's own second run (a different random seed) on 1 708 positions: pinglamb 73 hole moves (4.274 per 100, mean graded "
        "cost 706.6, median 470), Cold Clear 30 (1.756 per 100, mean 3.3, median 41.5): +2.518 per 100. That is 12 nights above, 2 level and "
        "1 below, but each night has only 63–218 such positions and 0–12 events, so per-night gaps are very noisy. "
        "Cold Clear's 30 is itself one noisy draw: a separate second search of the same positions gives "
        "{=cc_same_positions.cc_alt_seed1.cc_count} ({=cc_same_positions.cc_alt_seed1.cc_rate_per100} per 100), "
        "which leaves a gap of {=+p1_alt_gap} per 100, so the size of the gap depends on which draw is read."],
 'P2': ["Every graded position of pinglamb with garbage on the board: 21266 over the 15 nights. A seal cuts empty cells off completely, so "
        "no tuck or spin can reach them. The habit is a seal where Cold Clear's own pick at the same position seals nothing, and the move is "
        "not one column or one rotation off Cold Clear's (nor, when it adds covered cells, a shape that one column over would add none): 210 times (0.987 per 100), at a mean graded cost of 560.6 (median 351); 76 cost 600 "
        "or more.",
        "Counting every seal, Cold Clear seals more than pinglamb (3.898 per 100, 829 positions, against 2.285, 486), and that is so on all "
        "15 nights. So the habit is not sealing more often; it is sealing where Cold Clear's pick sealed nothing.",
        "Against Cold Clear's own second run on {=cc_same_positions.eligible} positions, by the same rule, applied to Cold Clear's pick "
        "exactly as to pinglamb's move (the one-column-over test only when the pick adds covered cells): pinglamb "
        "{=cc_same_positions.player_count} ({=cc_same_positions.player_rate_per100} per 100, mean graded cost "
        "{=cc_same_positions.player_regret_mean}, median {=cc_same_positions.player_regret_median}), Cold Clear "
        "{=cc_same_positions.cc_count} ({=cc_same_positions.cc_rate_per100} per 100, mean {=cc_same_positions.cc_regret_mean}, median "
        "{=cc_same_positions.cc_regret_median}; 14 without the one-column-off filter): {=+cc_same_positions.gap_per100} per 100. "
        "Cold Clear's count is one noisy draw: a separate second search of the same positions gives "
        "{=cc_same_positions.cc_alt_seed1.cc_count} ({=cc_same_positions.cc_alt_seed1.cc_rate_per100} per 100). Per night that "
        "subsample is small: 0–4 events for pinglamb and 0–2 for Cold Clear."],
 'P3': ["Every graded position of pinglamb right after a line clear, with no B2B chain: 4803 over the 15 nights. pinglamb clears again on "
        "41.70% of them, Cold Clear's pick on 32.92%: +8.79 pp (+6.47 pp without the misdrop-shaped moves, n 4684). With no clear just "
        "before, the gap is +3.07 pp; the gap after a clear is +5.72 pp above that (a difference of two gaps, not a measured cause). Cold Clear's own second run, on 352 of these positions, "
        "clears 32.67% against its first run's 32.39%: search noise of +0.3 pp.",
        "The gap is positive on all 15 nights, from +5.86 pp (09-11) to +12.63 pp (08-25), and so is that difference, from +1.09 "
        "(09-10) to +11.94 (08-14). An occurrence is pinglamb clearing where Cold Clear's pick clears nothing: 478 singles, 139 doubles, "
        "30 triples and 36 quads, from 23 (07-24) to 110 (10-03) a night, at a mean graded cost of 308.2 (median 212); 131 cost 600 or more."],
 'P4': ["Graded positions of pinglamb where one half of the board is on average at least 2 rows taller than the other, the tallest column "
        "is 10–13 rows, at least 4 rows hold garbage, pinglamb and Cold Clear made the same hold choice, and neither move is a T-spin or a "
        "quad: 1110 over the 15 nights. pinglamb places on the taller half 36.126% of the time, Cold Clear 28.829%: +7.297 pp; without "
        "misdrop-shaped positions (927) +6.904 pp. 14 nights are above and 1 is level (08-09).",
        "149 times pinglamb went tall where Cold Clear did not, and 68 times the other way round; each night has 5 to 23. Mean graded cost "
        "+342.8 (median 219), 35 at 600 or more; 42 of the 149 are misdrop-shaped, and without them the mean is +362.4."],
 'P5': ["Every graded position of pinglamb with the stack at 12–15 rows and 4–7 garbage rows, the core band both re-checks derived: 1953 "
        "over the 15 nights. pinglamb clears 0.745 lines per move against Cold Clear's 0.855 (−0.110), and clears at all on 0.339 of moves "
        "against 0.365 (−0.026). By night 12 gaps are negative, 1 positive (07-28, +0.036) and 2 zero (07-22, 09-10); the widest are 08-01 "
        "(−0.272), 08-19 (−0.224) and 09-19 (−0.199).",
        "Cold Clear's pick clears on 712 of these positions, and on 237 of them (33.3%) pinglamb stacked instead, at a mean graded cost of "
        "361.2 (median 259); 36 of the 237 are misdrop-shaped. Leaving out every position where pinglamb's move is misdrop-shaped (not only "
        "those 36), the gap is −0.127. In the wider band of 10–13 rows at any garbage level (none included), the band the re-checks recommend "
        "for pinglamb, the gap is much smaller: −0.039 on 7406 positions, with 759 occurrences. The examples are taken where the two bands "
        "meet, at 12–13 rows."],
 'P6': ["Graded positions of pinglamb at 10+ rows where the I is the current piece or in hold and a clean well is ready at least 4 deep, "
        "keeping only declines that were a hold decision: 1367 over the 15 nights. pinglamb quads on 76.66% of them (1048), Cold Clear on "
        "83.61% (1143): −6.95 pp. 14 nights are below and 1 above (09-11, +3.0 pp). With the I as the current piece only (765 positions): "
        "81.57% against 87.32%, −5.75 pp; by night 13 below, 1 level (09-03) and 1 above (09-11).",
        "The habit itself is pinglamb pressing hold on a current I where Cold Clear quads: 108 times, from 2 to 22 (10-03) a night, at a "
        "mean graded cost of 181.8 (median 55.5); 84.26% of them quad within pinglamb's next 3 pieces, and none is misdrop-shaped."],
}
SHORT = {n[5:] for n in NIGHTS}
_NUM = re.compile(r'\d+(?:\.\d+)?')
def _nums(t):
    t = re.sub(r'\b(?:20\d\d-)?(\d\d-\d\d)\b', lambda m: ' ' if m.group(1) in SHORT else m.group(0), t)   # night dates: checked separately
    t = re.sub(r'(?<=\d)[ \u2009\u202f\u00a0](?=\d{3}\b)', '', t.replace('−', '-'))
    return set(_NUM.findall(t))
_PH = re.compile(r'\{=(\+?)([a-z0-9_.]+)\}')
DERIVED = {}   # placeholders computed here from the pooled entry (a difference of two of its fields), keyed by name
def _resolve(h, t):
    """{=a.b.c} is the pooled entry's field a.b.c printed as the data holds it; {=+...} signs it."""
    def one(m):
        k = m.group(2)
        if k in DERIVED.get(h['id'], {}):
            v = DERIVED[h['id']][k]
        else:
            v = h['pooled']
            for part in k.split('.'): v = v[part]
        assert v is not None, (h['id'], k)
        return sg(v) if m.group(1) else num(v)
    return _PH.sub(one, t)
def reader_text(h):
    """The reader-facing measurement text, checked figure by figure against the detector's own text; {=...}
    placeholders are filled from the detector's pooled entry and so are not typed."""
    src = _nums(h['definition'] + ' ' + h['cc_comparison'] + ' ' + SOURCE_EXTRA.get(h['id'], ''))
    paras = [_PH.sub(' ', t) for t in READER[h['id']]]
    for d in re.findall(r'\b\d\d-\d\d\b', ' '.join(paras)):
        assert d in SHORT and d in h['cc_comparison'], (h['id'], 'date not a night in the detector text', d)
    missing = sorted(_nums(' '.join(paras)) - src - {'15'}, key=float)   # 15 = the number of nights
    assert not missing, (h['id'], 'figures not in the detector output', missing)
    bad = re.findall(r"\b(cc|regret|skeptic|sub4000|seed-0|seed-1|nights\.json|\.py|\.out)\b", ' '.join(paras), re.I)
    assert not bad, (h['id'], 'internal wording', bad)
    return [_resolve(h, t) for t in READER[h['id']]]


STRENGTH = {   # how firm each habit is, in the skeptics' words (FINDINGS.md); shown on every view of the card
    'Y4': "Weaker than the hole and line-clear habits: it held on 12 of the 15 nights in the re-checks, "
          "and with every exclusion applied at once the interval on its extra cost touches zero.",
    'Y5': "Fragile: at 12+ rows, with the 10 costliest rounds and every misdrop-shaped move removed, the gap is +0.5 pp with an interval of −0.1 to +1.3, i.e. it may be nothing.",
    'Y6': "Against Cold Clear this does not separate (see below); it is a habit only next to pinglamb's rate.",
    'P5': "Weaker than yachi's: under the broadest misdrop exclusion it is below Cold Clear on 11 of 15 nights (sign test p = 0.12). "
          "The band the re-checks recommend for pinglamb is 10–13 rows; there, at any garbage level (none included), the gap is much smaller: {P5_BROAD}. "
          "The examples are taken at 12–13 rows, where the two bands meet.",
    'P6': "The weakest of pinglamb's habits. In one re-check, with the I as the current piece and fast or many-key moves "
          "dropped from both sides alike (557 positions), the gap was −0.065 as a share of positions (on a 0–1 scale; the table is in %) "
          "and negative on only 10 of the 13 nights where it was not zero (p = 0.09).",
}
# Habits whose gap has a direction: on a night where it runs the other way the card says so.
DIRECTION = {'Y2': -1, 'P5': -1, 'Y3': -1, 'P6': -1, 'Y5': +1, 'P3': +1, 'P4': +1}

Y1_POOLED_CC = next(h for h in HAB if h['id'] == 'Y1')['pooled']['cc_same_positions']
_p1 = next(h for h in HAB if h['id'] == 'P1')['pooled']['cc_same_positions']
DERIVED['P1'] = {'p1_alt_gap': round(_p1['player_rate_per100'] - _p1['cc_alt_seed1']['cc_rate_per100'], 3)}   # both 3-dp rates: exact
# Y6's all-nights figures are the detector's own pooled entry (session 'pooled'), not a sum made here.
y6 = next(h for h in HAB if h['id'] == 'Y6')
assert y6['pooled'] and y6['pooled']['session'] == 'pooled', 'Y6 pooled entry missing'
Y6_SIGN = y6['extra']['night_sign_test']
STRENGTH['P5'] = STRENGTH['P5'].replace('{P5_BROAD}', (lambda b: f"{num(b['gap_lines_per_move'])} lines per move (n {num(b['n'])})")(
    next(h for h in HAB if h['id'] == 'P5')['pooled']['band_10_13_any_garbage']))


def dec(t):
    t = t.replace('−', '-')
    return len(t.split('.')[1]) if '.' in t else 0


def strip_value(hid, rows, v):
    """The strip bar: the detector's own field (its gap for a gap habit), never a difference taken here."""
    return v


def card(h, rates, pooled=False, n_ex=None):
    global HERE
    HERE = 'over all 15 nights' if pooled else 'this night'
    assert len(NIGHTS) == 15
    rows, notes, v = SPEC[h['id']](rates)
    qual = any(t.startswith(QUAL) for t in notes)
    notes = [t[len(QUAL):] if t.startswith(QUAL) else t for t in notes]
    sv = strip_value(h['id'], rows, v)
    if h['id'] in DIRECTION and not pooled:
        want = DIRECTION[h['id']]
        if sv == 0:
            notes.append("On this night there is no gap: the two rates in the first row are equal.")
        elif (sv > 0) != (want > 0):
            notes.append(f"On this night the gap runs the other way ({sg(sv)}), so this night does not show the habit." +
                         (" The examples below are still this night's occurrences of it." if n_ex else ""))
    return rows, notes, sv, qual


MUCH = D['much_better']   # finalize.py's "clearly better" thresholds; the page prints them from here
# finalize.py's reasons, in reader words (a reason it does not list here is printed as finalize.py wrote it)
REASON = {'Cold Clear does not contrast': f"fewer than {MUCH['min_seeds']} of the {len(SEEDS)} Cold Clear runs made a first move that contrasts with the habit",
          'Cold Clear not clearly better': f"Cold Clear's line was clearly better in fewer than {MUCH['min_seeds']} of the {len(SEEDS)} runs",
          'self-check failed': "a rebuilt board or attack did not match the recording or the harness",
          'same match file as the other example': "same match as the other example",
          'position already shown under another habit': "already shown under another habit",
          'its pieces are already shown under another habit': "its pieces are already shown under another habit"}
SMALL_POOL = 10   # below this many occurrences a night's median is called a loose guide, on the card and in each caption


def pool_note(h, v):
    """Where this night's examples come from, and why there are fewer than two when there are."""
    p = v['pool']
    occ = lambda k: 'occurrence' if k == 1 else 'occurrences'
    n = len(v['examples'])
    if not p:
        return "No play this night where Cold Clear's line was clearly better: the habit has no occurrence to try this night."
    md = '' if p['misdrop_ok'] else ' that are not misdrop-shaped'
    t = (f"Examples are tried from this night's {p['pool']} verified {occ(p['pool'])}{md} "
         f"(median graded cost {num(p['pool_regret_median'])}), nearest that median first, from any part of the cost range, "
         f"and shown only where Cold Clear's line was clearly better over the {K} pieces in at least {MUCH['min_seeds']} of the {len(SEEDS)} runs.")
    npos = p.get('nonpositive_cost') or 0
    if npos:
        t += f" {npos} of the {p['pool']} {'scores' if npos == 1 else 'score'} at least as well as Cold Clear's own pick (graded cost 0 or below) and {'is' if npos == 1 else 'are'} not tried."
    if p['pool'] < SMALL_POOL:
        t += f" With only {p['pool']} this night, that median is a loose guide."
    if p.get('example_restriction'):
        t += f" For this habit they are also limited to its most common kind, {p['example_restriction']}."
    if p.get('example_only'):
        t += f" Examples are also limited to positions where {p['example_only']}, so that they show the scene described above."
    if n < 2:
        tried = p.get('candidates', 0)
        reasons = []
        if p.get('example_only_excluded'):
            k = p['example_only_excluded']
            reasons.append(f"{k} positive-cost {occ(k)} that {'does' if k == 1 else 'do'} not show the scene described above")
        if p.get('windows_rejected'):
            k = p['windows_rejected']
            reasons.append(f"{k} {'has' if k == 1 else 'have'} fewer than {K} verified recorded pieces after {'it' if k == 1 else 'them'}")
        # finalize.py retries a round another habit uses whenever a night is short, so on a short night that round is
        # never the final reason; if it were, the rule printed in the header would be contradicted by this note
        assert not (v.get('not_used') or {}).get('round already shown under another habit'), (h['id'], v['pool'], 'round reason on a short night')
        for w_, c_ in sorted((v.get('not_used') or {}).items(), key=lambda kv: (-kv[1], kv[0])):
            reasons.append(f"{c_} tried: {REASON.get(w_, w_)}")
        untried = p.get('capped_untried') or 0
        if untried:
            reasons.append(f"{untried} more not tried (at most {v['cap']} are tried a night)")
        head = ("Only one play this night" if n == 1 else "No play this night") + \
            f" where Cold Clear's line was clearly better over the {K} pieces" + (f" among the {tried} tried" if untried else "") + \
            (" that is not already shown under another habit" if any(k_ in (v.get('not_used') or {}) for k_ in
             ('position already shown under another habit', 'its pieces are already shown under another habit')) else "")
        t += f" {head}." + (" Not shown: " + "; ".join(reasons) + "." if reasons else "")
    return t


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
        o['keys'] = s['keys']
    return o


FACT_KEYS = ('max_height_before', 'garbage_rows_before', 'covered_cells_before', 'incoming_before', 'b2b_before',
             'combo_before', 'current', 'hold', 'next', 'well_rows_ready', 'well_column', 'quad_available',
             'tsd_slot_ready', 'tsd_available', 'player_first', 'cc_first', 'player_4', 'cc_4',
             'cc_first_contrasts_with_habit', 'contrast_rule')


def slim_clip(c):
    R = c['rows']
    assert len(c['start']['field']) == R and all(len(''.join(s['after'])) == 10 * R for s in c['human'])
    assert all(s.get('verified') for s in c['human']), c['id']
    assert c['facts']['cc_first_contrasts_with_habit'] and not c['facts']['cc_4']['topped_out'], c['id']
    assert c['regret'] > 0, c['id']
    # the shown run is clearly better than the player's K pieces, re-checked here from the clip's own facts, and at
    # least MUCH['min_seeds'] seeds were
    run = c['cc_run']; p4, q4 = c['facts']['player_4'], c['facts']['cc_4']
    da, dc = q4['attack'] - p4['attack'], p4['covered_cells_end'] - q4['covered_cells_end_with_waiting']
    assert (da, dc) == (run['margin']['attack'], run['margin']['covered']), c['id']
    assert (p4['topped_out'] and not q4['topped_out']) or (da >= MUCH['attack'] and dc >= 0) or (dc >= MUCH['covered'] and da >= 0), (c['id'], 'not clearly better')
    assert not (p4['attack'] > q4['attack'] and p4['covered_cells_end'] <= q4['covered_cells_end']), c['id']
    assert run['seeds_clearly_better'] >= MUCH['min_seeds'] and sum(1 for x in run['per_seed'] if x['clearly_better']) == run['seeds_clearly_better'], c['id']
    assert all(s['garbage_in'] <= 8 for s in c['cc'] if not s.get('dead')), (c['id'], 'more rows than the per-lock cap')
    # the hold flag agrees with the recorded inputs: hold used iff the played piece is not the current one, or hold was
    # pressed while the current and held pieces were the same (later presses on one piece are ignored by the game)
    assert all(s['hold'] == (s['piece'] != s['queue']['current'] or ('hold' in s['keys'] and s['queue']['current'] == s['queue']['hold']))
               for s in c['human']), c['id']
    mr = MATCHES[c['night']][c['file']]   # the match report's own match: index and round must exist there
    assert any(r['index'] == c['round'] for r in mr['rounds']), (c['id'], 'round not in the match report')
    extra = {}
    if c['habit'] == 'Y5':   # the open garbage hole(s) and the one buried, 1-based columns as the captions print them
        dd = c['detector_detail']; off = 40 - R
        for hl in dd['open_holes']:   # the hole is an empty cell in a garbage row of the start board
            row = c['start']['field'][hl['row'] - off]
            assert row[hl['column']] == '.' and 'G' in row, (c['id'], hl)
        extra = {'hole_cols': sorted(hl['column'] + 1 for hl in dd['open_holes']),
                 'buried_cols': sorted(hl['column'] + 1 for hl in dd['buried_holes'])}
    return {'id': c['id'], 'night': c['night'], 'file': c['file'], 'm': mr['index'], 'round': c['round'] + 1, 'piece': c['lock'] + 1, 'rows': R, **extra,
            'regret': c['regret'], 'misdrop': c['misdrop_shaped'],
            'pool': [c['why_picked']['pool_size'], c['why_picked']['pool_regret_median'], c['why_picked']['regret_percentile_in_pool_midrank']],
            'r0': c['round'], 'misdrop_ok': c['why_picked']['misdrop_ok'],
            'start': {'field': ''.join(c['start']['field']), 'b2b': c['start']['b2b'], 'combo': c['start']['combo'],
                      'q': [c['start']['current'], c['start']['hold'], ''.join(c['start']['next'])]},
            'human': [slim_step(s) for s in c['human']], 'cc': [slim_step(s) for s in c['cc']],
            'same': run['first_move_same_as_shown'], 'nseeds': len(run['seeds']), 'graded_eq': run['first_move_equals_graded_pick'],
            'ncon': run['seeds_contrasting'], 'nbetter': run['seeds_clearly_better'],
            'margin': [run['margin']['attack'], run['margin']['covered'], run['margin']['clause']],
            'facts': {k: c['facts'].get(k) for k in FACT_KEYS}}


out_h = []
n_ex = []
for h in HAB:
    strip = []
    nights = {}
    for n in NIGHTS:
        v = h['nights'][n]
        rows, notes, sv, qual = card(h, v['rates'], n_ex=len(v['examples']))
        strip.append(sv)
        nights[n] = {'rows': rows, 'notes': notes, 'qual': qual, 'poolnote': pool_note(h, v),
                     'ex': [slim_clip(c) for c in v['examples']]}
        assert all(c['night'] == n and c['player'] == h['player'] and c['habit'] == h['id'] for c in v['examples'])
        n_ex.append(len(v['examples']))
    prow, pnotes, _, pqual = card(h, h['pooled'], pooled=True)
    out_h.append({'id': h['id'], 'player': h['player'], 'name': h['name'], 'desc': DESC[h['id']], 'strength': STRENGTH.get(h['id']),
                  'measured': reader_text(h), 'strip': strip,
                  'stripLabel': STRIP[h['id']][0], 'stripKind': STRIP[h['id']][1],
                  'all': {'rows': prow, 'notes': pnotes, 'qual': pqual}, 'nights': nights})

# no clip shown twice: no piece of any round appears in two examples; a habit-night's two examples
# come from different match files; the all-nights notes never speak of "this night"
_seen = {}
for h in out_h:
    for n, v in h['nights'].items():
        assert len({c['file'] for c in v['ex']}) == len(v['ex']), (h['id'], n, 'two examples from one match file')
        for c in v['ex']:
            rk, l0 = c['id'].rsplit('/', 1)
            for j in range(K):
                assert (rk, int(l0) + j) not in _seen, (c['id'], h['id'], _seen.get((rk, int(l0) + j)), 'piece shown twice')
                _seen[(rk, int(l0) + j)] = h['id']
    assert not any('this night' in t for t in h['all']['notes']), (h['id'], 'pooled note says this night')
DATA = {'nights': NIGHTS, 'players': PLAYERS, 'k': K, 'seeds': len(SEEDS), 'nodes': NODES, 'habits': out_h,
        'matches': {n: [len(MATCHES[n]), sum(len(m['rounds']) for m in MATCHES[n].values())] for n in NIGHTS}}
n_clips = sum(n_ex)
lo, hi = min(n_ex), max(n_ex)
one_ex = D['log']['habit_nights_with_one_example']
# per player: how many examples, and in how many the Cold Clear move shown is not the pick the graded cost used
by_p = {p: [0, 0] for p in PLAYERS}
for h in out_h:
    for v in h['nights'].values():
        for c in v['ex']:
            by_p[h['player']][0] += 1; by_p[h['player']][1] += not c['graded_eq']
meta = {'small_pool': SMALL_POOL, 'much': MUCH, 'cap': D['habits'][0]['nights'][NIGHTS[0]]['cap'], 'n_clips': n_clips, 'per_night': hi, 'one_ex': one_ex, 'zero_ex': D['log']['habit_nights_without_examples'],
        'n_habits': len(HAB), 'clips_by_player': by_p}

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
