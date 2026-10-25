# tetrio-replay-report — operating context

Public repo: <https://github.com/yachi/tetrio-replay-report> · Site: <https://yachi.github.io/tetrio-replay-report/>

Turns a batch of TETR.IO `.ttrm` replays into a Cantonese match report where every
factual sentence is badge-linked to a Dafny-verified lemma. Nineteen sessions so far
(2026-07-22: yachi 6:4 · 2026-07-24: pinglamb 4:3 · 2026-07-28: pinglamb 6:2 ·
2026-08-01: yachi 4:3 · 2026-08-09: pinglamb 6:0 · 2026-08-14: pinglamb 7:4 ·
2026-08-19: pinglamb 7:3 · 2026-08-25: pinglamb 5:4 · 2026-09-03: pinglamb 5:1 ·
2026-09-10: **drawn 4:4** · 2026-09-11: pinglamb 6:1 · 2026-09-17: pinglamb 5:2 ·
2026-09-18: pinglamb 11:7 · 2026-09-19: pinglamb 15:5 · 2026-10-03: pinglamb 14:6 ·
2026-10-09: pinglamb 7:5 · 2026-10-12: pinglamb 5:3 · 2026-10-20: **drawn 2:2** ·
2026-10-22: pinglamb 6:3), 1407 rounds, 1707 generated claims
plus the hand ledgers — count those from `sessions/*/report/claims-narrative.json` and
`claims-coaching.json` rather than from a total typed here, because hand prose lands after
the session does. **The three largest sessions are 09-19 (20 matches, 150 rounds), 10-03 (20, 146) and 09-18
(18, 127)**, against the 11 and 84 that were the records before any of them landed. Together they
are 30.1% of every round the corpus holds (31.5% before 10-22 landed, 32.2% before 10-20, 33.6% before 10-12 and 36.6% before 10-09 —
re-derive it, the share moves every session), which is the single most important thing to know before
reading any pooled figure below. Ranked over all nineteen: **2026-10-09 is fourth by both matches
(12) and rounds (102)**, which pushes 2026-08-14 to fifth on both (11, 84); 2026-08-25 is seventh
by rounds (73, behind 07-22's 79) with 9 matches; 2026-08-19 is eighth by rounds (70) and **ties**
07-22 at 10 matches. **2026-10-22 is eleventh by rounds (63, one behind 07-28's 64) and ties
08-25 at 9 matches**, which pushes **2026-10-12 to twelfth by rounds** (55, eleventh at
seventeen and eighteen), still tied with 07-28 and 09-10 at 8 matches; 10-22 moves no rank above
eleventh on either measure. (Those ranks have
been wrong in this sentence before, in both directions, and every one of them moved by a place on
10-09's pass — re-derive them, never carry them; on 10-12's pass none above eleventh moved, which
is a fact about where it landed and not a reason to stop re-deriving. **2026-10-20 lands at the
bottom of both**, 4 matches and 30 rounds, so it moves no rank above it and takes both minima from
the sessions below.)
2026-09-03 has the fewest rounds of the first seventeen (46; second-fewest of nineteen behind
10-20's 30) and **ties** 08-09 for the fewest matches of the first seventeen (6) — and it is NO
LONGER the most lopsided in matches; see 09-11 below.
Read its 5:1 with C010 beside it: the round split after three matches was 13:12 to yachi, and
the whole margin is in the last three. 2026-09-17 is second-fewest by rounds (49) and sits in
the four-session group at 7 matches with 07-24, 08-01 and 09-11 — so it is near the bottom of
both measures without being lowest on either.

**2026-10-22 is pinglamb 6:3 in matches and 38:25 in rounds [C001][C010], and its finding is the
efficiency gap, not the scoreline.** 60.32% of the night's rounds is fourth by that measure (behind
09-11's 62.75, 09-17's 61.22 and 09-19's 60.67); 66.67% of matches is mid-table. It is the
nineteenth session in date order AND in arrival. Its C010 pins four stretches: yachi took m1 5:4,
pinglamb took m2-m5 20:6, yachi took m6-m8 14:9, and pinglamb took m9 5:0 — so the night was lost in
its second stretch, and both 5-0s are pinglamb's (m5, m9). **Its session APP gap is +20.59% [C004],
the corpus record**, past 09-17's +20.11%, and **both regime gaps are large at once** (won +15.17,
lost +20.13 [C002], each SECOND in its own column, behind 08-14's 18.93 and 08-09's 25.4) — the
second session after 09-17 to have both, and on that ranking a larger instance of it; neither
needs a leave-one-out caveat (`check_loo`, rel 0.139 and 0.104). pinglamb's APP is higher in all
nine matches [C020] and the per-match ordering interleaves (1 in 84 by chance, no C007). The volume
route failed by the largest shortfall the corpus holds (10.60 pp: +573 pieces [C005][C009] against
the gap, −349 lines of attack, −8.79%), and the attack total decided 7 of the 9 matches [C021].
KPP's AUC, 35.7, is the corpus low. Every rank in this paragraph is re-derived over the nineteen
from facts.json by hand; none is gated.

**2026-10-20 is DRAWN ON BOTH MEASURES — 2:2 in matches and 15:15 in rounds [C001][C010] — the first
session level on both**, where 09-10 was 4:4 and 32:33. It is also the corpus's SMALLEST, 4 matches
and 30 rounds, against 08-09's and 09-03's 6 and 09-03's 46. It is the eighteenth session in date
order AND in arrival. Its C010 is the cleanest shape the corpus has: yachi took both of the first
two matches 10:5 on rounds, pinglamb both of the last two 5:10, two halves of fifteen rounds
mirrored exactly. **The volume route more than covered the gap, by the widest margin the corpus
holds**: a +11.18% piece surplus [C009] against a +6.73% APP gap [C004], so yachi's attack total
is the higher by 80 lines, 4.16% of pinglamb's [C005] — past 10-09's +1.00% as the largest attack
lead yachi has had — and his score total is higher too [G059], the second session after 10-09. It
was still drawn, because the higher attack total won each MATCH [C015] and the second half's
totals were pinglamb's. Both regime figures need a leave-one-out caveat, and the lost-gap's SIGN is
one round's; see the regime paragraph. yachi topped out in none of the 30 rounds [C006].

**2026-10-12 is pinglamb 5:3 in matches and 30:25 in rounds [C001][C010] — a mid-table scoreline
on both measures** (54.55% of rounds to pinglamb, seventh-closest of seventeen; 62.50% of matches,
eighth-closest). It is the seventeenth session in date order AND in arrival. Its C010 pins three
stretches: yachi took matches 1-3 10:7 on rounds, pinglamb took matches 4-6 15:7, and m7-m8 split
8:8 — so the night was decided in its middle third, which is neither 09-03's late shape nor 09-11's
early one. It holds a 5-0 each way (pinglamb's m1, yachi's m3 [C011][C013]), the third session to
do so after 09-18 and 10-03, and **none of its eight matches went to a ninth round** — 09-11 is the
only other session of the seventeen with none, and this is the session after 10-09's seven. Two
things in its ledger are corpus firsts or records and both are per-match: the per-match APP
ordering SEPARATES the match winners at 1 in 56 [C007], and m3 is the largest per-match yachi lead
the corpus holds, pinglamb's attack per piece 28.01% BELOW yachi's [C020] against the previous
extreme, 09-18 m4's −18.26%. And in all eight matches the player with more attack won [C019] —
m2 and m7 included, which yachi won on volume against a higher pinglamb APP. See the per-match
section for what each of those does to its count.

**2026-10-09 is pinglamb 7:5 in matches and 53:49 in rounds [C001][C010] — the second-closest
session by ROUNDS** (51.96% to pinglamb, behind only the drawn 09-10's 50.77% and past 08-25's
52.05%), while its 58.33% of matches is fifth-closest of seventeen (behind 09-10's 50.00, 08-25's 55.56 and
07-24's and 08-01's 57.14). It is the sixteenth session in date order AND in
arrival. Two things make it unlike any earlier night, and both are in its ledger rather than its
scoreline. **7 of its 12 matches went to a ninth round [G016]** — no earlier session had more
than 4 (08-25, 09-10, 09-19 and 10-03). And its C010 pins 09-03's shape at a different size: the
match score was **4:4 and the rounds 33:34 after eight matches**, m9-m11 went 11:15 to pinglamb in
three straight matches, and that is the whole series margin; yachi took m12 5:4. **It is also the
first session where yachi's attack total is the higher since 07-22** (+58 lines, +1.00% of
pinglamb's [C005]) **and the first of sixteen where his in-game score total is higher** (10-20 is the second)
(+85 519 [G074]) — both carried by the largest piece surplus the corpus holds (+1064, +12.64%
[C005][C009]). It lost anyway; see the shortfall table, where it was the top end until 10-20.

**2026-10-03 is pinglamb 14:6 in matches and 82:64 in rounds [C001][C010] — a mid-table
scoreline on both measures** (56.16% of rounds, 70.00% of matches, which ties 08-19). It was first
published from the last five of its twenty replays and rebuilt from all twenty; every 10-03 figure
in this file is the full night's. Its C010 pins four five-match blocks at 16:22, 17:20, 12:23 and
19:17 (yachi:pinglamb) — the last block, the one the first version was built from, is the only
one yachi won on rounds, which is why that version read as a different night. It holds the
corpus's second yachi shutout (m8, 5-0; 09-18's m4 is the first) and a pinglamb one (m13), so
09-18 is no longer the only session with a shutout each way. It is the fifteenth session in date
order AND in arrival.

**2026-09-18 IS THE FIRST SESSION ADDED ANYWHERE BUT AT THE END OF THE ORDERING, and that is a
fact about this document before it is one about the night.** It sits between 09-17 and 09-19.
Every earlier session arrived last, so 「the Nth session」, 「the previous session」, 「one session
later」 and 「the next session to land」 all picked out the same thing and nothing here had to
choose between them. They now come apart: 09-19 is the fourteenth session to ARRIVE and the
thirteenth in DATE order, and a sentence like 09-19's 「the thirteenth session is this one」 is
still true of arrival and false of position. **Where this file says 「the Nth session」 it means
position in the date ordering; where it means arrival it now says so.** The sentences written
before this session landed were checked rather than rewritten — the ones that moved are marked
in place — and the general rule is the one 冇第二份 already gives for counts: re-derive 「N of
M」 from the corpus, never carry it, and that applies to an ordinal just as much as to a count.

**2026-09-19's size IS its finding, and the finding is about this document rather than about the
night.** 15:5 in matches and 91:59 in rounds is a one-sided scoreline and nothing more: 60.67% of
the night's rounds is **third** (behind 09-11's 62.75% and 09-17's 61.22%), and 75.00% of its
matches ties 07-28 for **fourth** (behind 08-09's sweep, 09-11's 85.71% and 09-03's 83.33%), so it
is not the most lopsided night on either measure and is not close to it on either. Its C002 puts both regime gaps back in the middle of their columns (11th and 7th of
fourteen, the same at fifteen, 12th and 8th at sixteen, and 13th and 9th at seventeen — where its
lost-gap IS the column median), which is the 「roughly level」 class and the answer to whether 09-17's 「both large」 was
one instance — it was. What the session actually produces is this: **a corpus quantity that is
secretly proportional to session length cannot be caught by twelve sessions that all sit within a
factor of 1.8 of each other.** The shortfall ordering below is such a quantity, and 150 rounds is
what shows it. Two smaller instances of the same shape sit inside the session and are recorded
beside their claims rather than here: its 714-piece surplus and 476-line attack deficit [C005] are
the largest raw numbers the volume route has produced, and its 15 topouts [C006] are the largest
raw tally any player has recorded — all three because the night is longest, and all three
unremarkable as rates.

**2026-09-17 is the first session where BOTH regime gaps are large at once, and that is the
finding eleven earlier nights did not produce.** pinglamb takes it 5:2 and the rounds 30:19, but
the scoreline is the least interesting thing about it. Two things have to be read together. Its
C010 pins **14:10 to YACHI after three matches** — he then took 5 of the last 20 — so this is
09-03's shape (the margin arrives late) at a larger size, and the final 5:2 says none of it.
And its C002 puts the won-regime APP gap at +14.57% against a lost-regime +15.63%: ranked against
their own columns over the fourteen sessions those are **2nd and 3rd**, where every earlier session
has one regime apart and the other level. Do not upgrade that into 「the most balanced session」 —
07-28's won/lost ratio (0.98) is closer to 1 than this one's (0.93); what is new is that the
balance sits on LARGE values, 07-28 being +5.9/+6.0 with both BELOW their medians, which is the
「roughly level」 class and the opposite reading. Its C004 session gap of +20.11% was the corpus
record, past 08-09's +18.08%, until 10-22's +20.59%, and it exceeds both regimes' gaps, which is the arithmetic of
pooling over two differently-sized round pools and not a finding.

**2026-09-11 is the most lopsided session the corpus has by ROUNDS — 32:19, i.e. 62.7% of the
night's rounds — past 08-09's and 08-19's 60.0%.** In matches its 6:1 is second to 08-09's 6:0
sweep, so the two measures disagree about which session is the most one-sided and the sentence
has to say which one it means. It lands immediately after the only drawn session, which is
worth one clause and no mechanism: two nights are two nights, and the pair is recorded rather
than explained. Its C010 pins 8:20 after four matches — this one really was decided early,
which is the opposite of 09-03's shape and the reason both scorelines need their C010 read
beside them rather than either being taken as the night's story.

**2026-09-10 is the first DRAWN session, and it is now the closest on both measures at once —
4:4 in matches and 32:33 in rounds, with the rounds level at 28:28 after seven of the eight
matches [C010].** 08-25 held both of those records (5:4, 38:35) and now holds neither. Two
consequences for anything written about the corpus. **A session no longer necessarily has a
winner**: `series_result` said 「yachi 攞低個系列」 about this 4:4 for the same reason nine
sessions of `max()` never had to decide a tie, and its spec pinned only the two counts, so
every gate agreed with a false sentence — see the family's docstring. And **08-25 must not be
carried forward as 「the closest」**; it is second by matches and, since 10-09's 53:49 (51.96%
against its 52.05%), third by rounds.

## The one invariant

**Dafny proves "claim ⇔ extracted data", not the extraction.** That the dataset matches
the `.ttrm` files rests on two independently written extractors agreeing byte-for-byte.
Never let a report, README, or commit message blur those two things — every audit round
in this project's history caught someone doing exactly that.

Corollaries that are gates, not preferences:
- a proof-map status may only come from real `dafny verify` output, never stamped by codegen
- a proof-map entry must name a lemma that still exists. `codegen` builds lemma *names* from
  each claim's `english_gloss`, so editing a gloss renames the lemma and strands the badge's
  link while the verifier still reports 0 errors and the status gate still counts 54/54.
  `pipeline/check_proof_links.py` is the gate; rebuild a stranded map with the session's
  `build_proof_map.py` (the committed hand layout) or `pipeline.build_proof_map` (generated)
- a lemma that no mutation can kill is decorative; `mutation_test.sh` must kill every mutant —
  with the SAME escalation ladder `check_smt --mutate` uses, because it is the same question
  and a second copy of the operator drifted from the first for months (see 「Three backends」)
- **before adding a check, ask whether an existing gate already entails it.** A check that cannot
  fail against correctly-produced data is not a weak gate, it is a comment — and this repo has
  produced four of them by four different routes: the naive Donation clause (`NaiveClauseForced` —
  entailed by what a line clear *is*), the STMB cave's roof test (`RoofCannotDiscriminate` —
  vacuous), `width_ge_3` in `openers.test.ts` (a tautology of the data it was written against,
  which broke the day that data changed), and `cspin <= min(TST, TSD)` (entailed by
  `tspinCounterCheck`'s existing 900/900 agreement, caught before shipping on 2026-08-23). The
  screening question is one line and catches all four: *what would have to be true for this to
  fire?* If the answer needs a bug that another gate already rejects, the check belongs somewhere
  else or nowhere — `cspin <= min(TST, TSD)` survives only because it was re-scoped to guard the
  ROW JOIN, which nothing else does, and given a mutant that fires
- every countable statement in a report needs a claim id whose predicate covers *that*
  number — not a weaker one nearby
- a **rate** record (APM, VS) is only over rounds of `generators.QUALIFYING_MS` or more;
  **count** records (lines, spike, combo, B2B, T-spin) are over every round. See
  「速率紀錄要有局長下限」 below — the rule is measured, not a preference

## Relevant skills / tools

R 4.6.1 with `jsonlite` is installed; `analysis/rate_records.R` is the worked example of
using it against `sessions/*/report/facts.json`. Reach for it before changing a metric's
definition — the qualifier below came out of it and the argument for the threshold is a
regression, not an opinion.

## Commands

```bash
bin/new-session sessions/<date> <replay-dir>   # extract → claims → Dafny → verify → proof map
bin/verify-session sessions/<date>/report      # re-run all gates (MUTATION=1 adds mutation test)
bin/build-docs [--out <dir>]                   # render the Pages site (default docs/, git-ignored; CI deploys it)
python3 -m pipeline.build_report sessions/<date>/report         # regenerate the derived report sections
python3 -m pipeline.build_report sessions/<date>/report --check # CI gate: fail if they drifted from facts.json
python3 -m pipeline.check_prose_figures sessions/<date>/report   # CI gate: every 約-figure is floored
python3 -m pipeline.check_proof_links sessions/<date>/report      # CI gate: every badge's lemma exists
python3 -m pipeline.check_generated_css sessions/<date>/report    # CI gate: generated CSS stays in its region
python3 -m pipeline.build_round_table sessions/<date>/report   # regenerate the 逐局全數據 section
python3 -m pipeline.claims.build_claims <facts> --out <ledger> # generated ledger
python3 -m pipeline.codegen <facts> --claims <ledger> --outdir <dir>
python3 -m pipeline.claims.equiv <facts> --hand <ledgers...>   # coverage by exhaustive mutation
python3 -m pipeline.claims.equiv --selftest [--selftest-round]  # the relevance index vs the frozen oracle
python3 -m pipeline.codegen_smt <facts> --claims <ledger> --out <dir>/claims.smt2
python3 -m pipeline.check_smt sessions/<date>/report --regen --mutate 12
python3 -m pipeline.check_dead_consts sessions/<date>/report
python3 -m pipeline.check_mutation_ladder   # CI gate: mutation_test.sh's escalation ladder
python3 -m pipeline.check_mutation_ladder --selftest   #   still covers check_smt's
python3 -m pipeline.check_rate_coverage sessions/<date>/report  # CI gate: short rounds' rates still pinned
python3 -m pipeline.check_badge_links sessions/<date>/report    # CI gate: every badge citation resolves
python3 -m pipeline.check_report_shell sessions/<date>/report   # CI gate: no hand-written <section> in the body
python3 -m pipeline.check_cross_artefact             # CI gate: two artefacts of ONE session agree
python3 -m pipeline.check_cross_artefact --selftest  #   its mutants (8 planted, 4 controls)
python3 -m pipeline.check_finesse_denominator sessions/<date>/report  # CI gate: every per-piece rate names 每粒
python3 -m pipeline.check_finesse_denominator sessions/<date>/report --selftest  # its mutants
python3 -m pipeline.check_opener_section sessions/<date>/report  # CI gate: the C-Spin / DT 砲 section
python3 -m pipeline.check_opener_section sessions/<date>/report --selftest
python3 -m pipeline.check_donation_bands            # CI gate: the Donation ablation bands, rolled
python3 -m pipeline.check_donation_bands --render   #   up from the seven artefacts. --render prints
python3 -m pipeline.check_donation_bands --selftest #   the fragments to paste; --selftest its mutants
python3 -m pipeline.check_dual_engine               # CI gate: the dual_engine confusion matrix, its
python3 -m pipeline.check_dual_engine --render      #   board split, coverage and prefix lengths —
python3 -m pipeline.check_dual_engine --selftest    #   --selftest also checks each rounding DIRECTION
python3 -m pipeline.check_rounding           # CI gate: every rendered figure declares a rounding
python3 -m pipeline.check_rounding --selftest #   rule, and which rule PAIRS the corpus enforces
python3 -m pipeline.openers.extract_wiki_openers            # CI gate: harddrop's own opener drawings
python3 -m pipeline.openers.extract_wiki_openers --selftest # its mutants
python3 -m pipeline.openers.extract_wiki_techniques            # CI gate: the Donation / STMB Cave
python3 -m pipeline.openers.extract_wiki_techniques --selftest #   drawings and their controls
python3 -m pipeline.openers.extract_wiki_openers \
  --html-dir <dir> --write                                 # re-transcribe (needs the pages fetched)
REPLAY_DIR=sessions/<date> bun pipeline/sim/emit-opener-facts.ts \
  --out sessions/<date>/sim/opener-facts.json                   # the C-Spin / DT Cannon metrics
REPLAY_DIR=sessions/<date> bun pipeline/sim/emit-replay.ts \
  --out sessions/<date>/sim/replay-facts.json                   # the animated replay's timeline (quarantined)
bun test pipeline/sim/replay.test.ts                           #   its round trip + named exception lists
bun pipeline/sim/oracle-cache.ts --warm [--jobs 4]             # fill the shared oracle-replay cache bun test reads; ON by
                                                               #   default only under bun test (ORACLE_CACHE=off|on|verify,
                                                               #   ORACLE_CACHE_DIR); emitters never read it. PERF-PLAN.md
bun test pipeline/sim/oracle-cache.test.ts                     #   cached == fresh, the key moves with pipeline/sim, closure stays inside
python3 -m pipeline.check_replay_section sessions/<date>/report  # CI gate: the replay region re-renders
python3 -m pipeline.check_replay_section sessions/<date>/report --selftest  #   and stays quarantined
python3 -m pipeline.replay_page --selftest      # the docs/<date>-replay.html audit's mutants
python3 -m pipeline.openers.extract_meisou_routes            # CI gate: the 迷走砲 route transcription
python3 -m pipeline.openers.extract_meisou_routes --selftest #   its mutants; --html-dir <dir> re-checks a refetch
bun pipeline/sim/emit-stray-cannon-facts.ts \
  --out analysis/stray-cannon-facts.json                        # which corpus round reached which route node (quarantined)
bun test pipeline/openers/stray-cannon.test.ts                 #   byte rebuild + named lists + mutants
python3 -m pipeline.stray_cannon_page --selftest # the docs/stray-cannon*.html audit's mutants
bun pipeline/sim/emit-stray-cannon-demos.ts \
  --out analysis/stray-cannon-demos.json                        # the constructed 迷走砲 demos (quarantined, not corpus data)
bun test pipeline/openers/stray-cannon-demos.test.ts           #   re-run, classify, board, completeness + mutants
python3 -m pipeline.stray_cannon_page --out-dir <dir>  #   render the pages somewhere other than docs/
python3 -m pipeline.openers.extract_honeycup_routes            # CI gate: the はちみつ砲 route transcription
python3 -m pipeline.openers.extract_honeycup_routes --selftest #   its mutants
bun pipeline/sim/emit-route-facts.ts --opener honeycup \
  --out analysis/honey-cup-facts.json                           # はちみつ砲's corpus route artefact (quarantined)
bun pipeline/sim/emit-route-demos.ts --opener honeycup \
  --out analysis/honey-cup-demos.json                           # the constructed はちみつ砲 demos (quarantined, not corpus data)
bun test pipeline/openers/honey-cup.test.ts pipeline/openers/honey-cup-demos.test.ts  # its two tests
python3 -m pipeline.honey_cup_page --selftest   # the docs/honey-cup*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_mountainous2_routes            # CI gate: the 山岳積み2号 route transcription
python3 -m pipeline.openers.extract_mountainous2_routes --selftest #   its mutants; --html-dir <dir> re-checks a refetch
bun pipeline/sim/emit-route-facts.ts --opener mountainous2 \
  --out analysis/mountainous2-facts.json                        # 山岳積み2号's corpus route artefact (quarantined)
bun pipeline/sim/emit-route-demos.ts --opener mountainous2 \
  --out analysis/mountainous2-demos.json                        # the constructed 山岳積み2号 demos (quarantined, not corpus data)
bun test pipeline/openers/mountainous2.test.ts pipeline/openers/mountainous2-demos.test.ts  # its two tests
python3 -m pipeline.mountainous2_page --selftest # the docs/mountainous2*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_stickspin_routes            # CI gate: the stick spin route transcription
python3 -m pipeline.openers.extract_stickspin_routes --selftest #   its mutants; --html-dir <dir> re-checks a refetch
bun pipeline/sim/emit-route-facts.ts --opener stickspin \
  --out analysis/stickspin-facts.json                           # stick spin's corpus route artefact (quarantined)
bun pipeline/sim/emit-route-demos.ts --opener stickspin \
  --out analysis/stickspin-demos.json                           # the constructed stick spin demos (quarantined, not corpus data)
bun test pipeline/openers/stickspin.test.ts pipeline/openers/stickspin-demos.test.ts  # its two tests
python3 -m pipeline.stickspin_page --selftest   # the docs/stickspin*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_gamushiro_routes            # CI gate: the ガムシロ積み route transcription
python3 -m pipeline.openers.extract_gamushiro_routes --selftest #   its mutants; --html-dir <dir> re-checks a refetch (with harddrop's page beside it)
bun pipeline/sim/emit-route-facts.ts --opener gamushiro \
  --out analysis/gamushiro-facts.json                           # ガムシロ積み's corpus route artefact (quarantined)
bun pipeline/sim/emit-route-demos.ts --opener gamushiro \
  --out analysis/gamushiro-demos.json                           # the constructed ガムシロ積み demos (quarantined, not corpus data)
bun test pipeline/openers/gamushiro.test.ts pipeline/openers/gamushiro-demos.test.ts  # its two tests
python3 -m pipeline.gamushiro_page --selftest   # the docs/gamushiro*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_sdpcspin_routes            # CI gate: the SDPC Spin route transcription
python3 -m pipeline.openers.extract_sdpcspin_routes --selftest #   its mutants; --html-dir <dir> re-checks the two harddrop wikitext snapshots (SDPC_Spin + SingleYou)
bun pipeline/sim/emit-route-facts.ts --opener sdpcspin \
  --out analysis/sdpcspin-facts.json                            # SDPC Spin's corpus route artefact (quarantined)
bun pipeline/sim/emit-route-demos.ts --opener sdpcspin \
  --out analysis/sdpcspin-demos.json                            # the constructed SDPC Spin demos (quarantined, not corpus data); emit AFTER the facts
bun test pipeline/openers/sdpcspin.test.ts pipeline/openers/sdpcspin-demos.test.ts  # its two tests
python3 -m pipeline.sdpcspin_page --selftest    # the docs/sdpcspin*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_stsd_shapes            # CI gate: the STSD technique transcription
python3 -m pipeline.openers.extract_stsd_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch
bun pipeline/sim/emit-technique-facts.ts --technique stsd \
  --out analysis/stsd-facts.json                               # STSD's corpus artefact (quarantined)
bun pipeline/sim/emit-technique-demos.ts --technique stsd \
  --out analysis/stsd-demos.json                               # the constructed STSD demos (quarantined, not corpus data); emit AFTER the facts
bun test pipeline/openers/stsd.test.ts pipeline/openers/stsd-demos.test.ts  # its two tests
python3 -m pipeline.stsd_page --selftest        # the docs/stsd*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_stmbcave_shapes            # CI gate: the STMB Cave technique transcription
python3 -m pipeline.openers.extract_stmbcave_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch
bun pipeline/sim/emit-technique-facts.ts --technique stmbcave \
  --out analysis/stmbcave-facts.json                           # STMB Cave's corpus artefact (quarantined)
bun pipeline/sim/emit-technique-demos.ts --technique stmbcave \
  --out analysis/stmbcave-demos.json                           # its constructed demos (quarantined; none built, each board's reason published); emit AFTER the facts
bun test pipeline/openers/stmbcave.test.ts pipeline/openers/stmbcave-demos.test.ts  # its two tests
python3 -m pipeline.stmbcave_page --selftest    # the docs/stmbcave*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_imperialcross_shapes            # CI gate: the Imperial Cross technique transcription
python3 -m pipeline.openers.extract_imperialcross_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch
bun pipeline/sim/emit-technique-facts.ts --technique imperialcross \
  --out analysis/imperialcross-facts.json                      # Imperial Cross's corpus artefact (quarantined)
bun pipeline/sim/emit-technique-demos.ts --technique imperialcross \
  --out analysis/imperialcross-demos.json                      # its constructed demos (quarantined; none built, each board's reason published); emit AFTER the facts
bun test pipeline/openers/imperialcross.test.ts pipeline/openers/imperialcross-demos.test.ts  # its two tests
python3 -m pipeline.imperialcross_page --selftest # the docs/imperialcross*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_doubledagger_shapes            # CI gate: the Double Dagger technique transcription
python3 -m pipeline.openers.extract_doubledagger_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch
bun pipeline/sim/emit-technique-facts.ts --technique doubledagger \
  --out analysis/doubledagger-facts.json                       # Double Dagger's corpus artefact (quarantined)
bun pipeline/sim/emit-technique-demos.ts --technique doubledagger \
  --out analysis/doubledagger-demos.json                       # its constructed demos (quarantined; none built, each board's reason published); emit AFTER the facts
bun test pipeline/openers/doubledagger.test.ts pipeline/openers/doubledagger-demos.test.ts  # its two tests
python3 -m pipeline.doubledagger_page --selftest  # the docs/doubledagger*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_btcannon_shapes            # CI gate: the BT砲 (途中BT) technique transcription
python3 -m pipeline.openers.extract_btcannon_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch (with harddrop's BT_Cannon.wikitext beside it)
bun pipeline/sim/emit-technique-facts.ts --technique btcannon \
  --out analysis/btcannon-facts.json                           # BT砲's corpus artefact (quarantined)
bun pipeline/sim/emit-technique-demos.ts --technique btcannon \
  --out analysis/btcannon-demos.json                           # its constructed demos (quarantined; none built, each board's reason published); emit AFTER the facts
bun test pipeline/openers/btcannon.test.ts pipeline/openers/btcannon-demos.test.ts  # its two tests
python3 -m pipeline.btcannon_page --selftest      # the docs/btcannon*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_cutcopy_shapes            # CI gate: the 千鳥格子 (Cut Copy) technique transcription
python3 -m pipeline.openers.extract_cutcopy_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch (with harddrop's Cut_copy.wikitext beside it)
bun pipeline/sim/emit-technique-facts.ts --technique cutcopy \
  --out analysis/cutcopy-facts.json                            # 千鳥格子's corpus artefact (quarantined)
bun pipeline/sim/emit-technique-demos.ts --technique cutcopy \
  --out analysis/cutcopy-demos.json                            # its constructed demos (quarantined; none built, each board's reason published); emit AFTER the facts
bun test pipeline/openers/cutcopy.test.ts pipeline/openers/cutcopy-demos.test.ts  # its two tests
python3 -m pipeline.cutcopy_page --selftest       # the docs/cutcopy*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_shachikutrain_shapes            # CI gate: the 社畜トレイン (Shachiku Train) technique transcription
python3 -m pipeline.openers.extract_shachikutrain_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch (with harddrop's Shachiku_Train.wikitext and STMB_Cave.wikitext beside it)
bun pipeline/sim/emit-technique-facts.ts --technique shachikutrain \
  --out analysis/shachikutrain-facts.json                      # 社畜トレイン's corpus artefact (quarantined)
bun pipeline/sim/emit-technique-demos.ts --technique shachikutrain \
  --out analysis/shachikutrain-demos.json                      # its constructed demos (quarantined; none built, each board's reason published); emit AFTER the facts
bun test pipeline/openers/shachikutrain.test.ts pipeline/openers/shachikutrain-demos.test.ts  # its two tests
python3 -m pipeline.shachikutrain_page --selftest # the docs/shachikutrain*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_parapet_shapes            # CI gate: the 欄干 (Parapet) technique transcription
python3 -m pipeline.openers.extract_parapet_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch (with harddrop's Parapet.wikitext, tetrisch_parapet.html and tetrisch-parapet/ beside it)
bun pipeline/sim/emit-technique-facts.ts --technique parapet \
  --out analysis/parapet-facts.json                            # 欄干's corpus artefact (quarantined; two variants, a payoff)
bun pipeline/sim/emit-technique-demos.ts --technique parapet \
  --out analysis/parapet-demos.json                            # its constructed demos (quarantined; none built, each board's reason published); emit AFTER the facts
bun test pipeline/openers/parapet.test.ts pipeline/openers/parapet-demos.test.ts  # its two tests
python3 -m pipeline.parapet_page --selftest       # the docs/parapet*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_kaidan_shapes            # CI gate: the 階段のドネイト (Kaidan Setups) technique transcription
python3 -m pipeline.openers.extract_kaidan_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch (with harddrop's Kaidan_Setups.wikitext, Anchor_Set.wikitext and STMB_Cave.wikitext beside it)
bun pipeline/sim/emit-technique-facts.ts --technique kaidan \
  --out analysis/kaidan-facts.json                             # 階段のドネイト's corpus artefact (quarantined; a payoff, harddrop's)
bun pipeline/sim/emit-technique-demos.ts --technique kaidan \
  --out analysis/kaidan-demos.json                             # its constructed demos (quarantined; none built, each board's reason published); emit AFTER the facts
bun test pipeline/openers/kaidan.test.ts pipeline/openers/kaidan-demos.test.ts  # its two tests
python3 -m pipeline.kaidan_page --selftest        # the docs/kaidan*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_dtcannon_shapes            # CI gate: the 途中DT砲 (mid-game DT Cannon) technique transcription
python3 -m pipeline.openers.extract_dtcannon_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch (dtcannon.html, with harddrop's Double_Triple_Cannon_Setups.wikitext beside it)
bun pipeline/sim/emit-technique-facts.ts --technique dtcannon \
  --out analysis/dtcannon-facts.json                           # 途中DT砲's corpus artefact (quarantined; a TSD into a TST)
bun pipeline/sim/emit-technique-demos.ts --technique dtcannon \
  --out analysis/dtcannon-demos.json                           # its constructed demos (quarantined; none built, each board's reason published); emit AFTER the facts
bun test pipeline/openers/dtcannon.test.ts pipeline/openers/dtcannon-demos.test.ts  # its two tests
python3 -m pipeline.dtcannon_page --selftest      # the docs/dtcannon*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_basicdonating_shapes            # CI gate: the 基本的なドネイト (basic donating) technique transcription
python3 -m pipeline.openers.extract_basicdonating_shapes --selftest #   its mutants; --html-dir <dir> re-checks a refetch (basicdonating.html)
bun pipeline/sim/emit-technique-facts.ts --technique basicdonating \
  --out analysis/basicdonating-facts.json                      # 基本的なドネイト's corpus artefact (quarantined; six hole windows, a payoff)
bun pipeline/sim/emit-technique-demos.ts --technique basicdonating \
  --out analysis/basicdonating-demos.json                      # its constructed demos (quarantined; none built, each board's reason published); emit AFTER the facts
bun test pipeline/openers/basicdonating.test.ts pipeline/openers/basicdonating-demos.test.ts  # its two tests
python3 -m pipeline.basicdonating_page --selftest # the docs/basicdonating*.html audit's mutants (--out-dir <dir> renders)
python3 -m pipeline.openers.extract_dpc_setups            # CI gate: harddrop's six DPC Setups pages
python3 -m pipeline.openers.extract_dpc_setups --selftest #   its mutants; --wikitext-dir <dir> re-checks a refetch
bun pipeline/sim/emit-dpc-facts.ts --out analysis/dpc-facts.json  # the first T-spin after each PC, against those setups (quarantined)
bun test pipeline/openers/dpc.test.ts            #   byte rebuild, the allclear anchor, named list + mutants
python3 -m pipeline.dpc_page --selftest          # the docs/dpc.html audit's mutants (--out-dir <dir> renders)
REPLAY_DIR=sessions/<date> bun pipeline/sim/emit-attack-facts.ts \
  --out sessions/<date>/sim/attack-facts.json                   # the 攻擊由邊度嚟 split (quarantined)
bun test pipeline/sim/attack-facts.test.ts                     #   byte identity + named anchor exceptions
python3 -m pipeline.check_attack_section sessions/<date>/report  # CI gate: the attack-sources region
python3 -m pipeline.check_attack_section sessions/<date>/report --selftest  #   its mutants
python3 -m pipeline.check_routes_techniques sessions/<date>/report  # CI gate: 定式路線同中盤手法 + 建議's tagged items
python3 -m pipeline.check_routes_techniques sessions/<date>/report --selftest  #   its mutants
python3 -m analysis.app_decomposition [--json]  # the corpus APP-gap roll-up over every attack-facts.json
python3 -m pipeline.check_app_decomposition     # CI gate: CLAUDE.md's APP-gap figures; --render
python3 -m pipeline.check_app_decomposition --selftest  #   prints them, --selftest its mutants + probe control
Rscript analysis/rate_records.R                                 # the evidence for QUALIFYING_MS
Rscript analysis/rate_records.R --json analysis/rate-records.json  #   ...as the committed artefact
python3 -m pipeline.check_rate_records            # CI gate: that artefact is current, and every
python3 -m pipeline.check_rate_records --rerun    #   figure CLAUDE.md quotes from it agrees
python3 -m pipeline.check_rate_records --selftest #   its mutants
dafny verify spec/Forecast.dfy spec/ForecastExamples.dfy       # the hand-written concept spec
dafny verify spec/BfsKey.dfy               # why bestTspin's visited key carries the arrival mode
bash spec/mutate-bfskey.sh                 # its mutants — a lemma none can kill is decorative
bash spec/mutate-forecast-spec.sh          # spec mutants — a TIMEOUT is UNRESOLVED, not killed
dafny verify spec/DonationCave.dfy         # why the naive Donation clause and the cave's roof test
bash spec/mutate-donationcave.sh           #   discriminate nothing; 10 mutants, all killed
python3 spec/check_spec_vacuity.py         # no lemma in the spec is vacuously true — controls are
python3 spec/check_spec_vacuity.py spec/DonationCave.dfy   # per-module, so run it once per file
python3 -m pipeline.forecast_examples      # the drawn boards (example-boards.ts) agree with the
                                           #   proven witnesses (ForecastExamples.dfy); --write regens
                                           #   spec/forecast-examples.json, --selftest proves teeth
python3 -m pipeline.sim.extract_jp_forecast # re-extract the 38 Tetrisちゃんねる forecast diagrams from
                                           #   their JPEGs (needs Pillow); --write regens the JSON.
                                           #   CI gate is bun test pipeline/sim/jp-forecast.test.ts
python3 -m pipeline.sim.extract_four_forecast # re-decode four.lol's 26 forecast frames from the
                                           #   committed fumen codes (needs py_fumen); CI gate is
                                           #   bun test pipeline/sim/four-forecast.test.ts
```

## Three backends, one spec

`pipeline/claims/spec.py` renders each claim to a **Python** predicate, a **Dafny**
`ensures`, and **SMT-LIB 2.6** (`pipeline/claims/smt.py`). One spec, three targets, so what
Python evaluates, what Dafny proves and what a solver refutes cannot drift apart — the
dual-extractor argument applied to the proof side.

Why SMT-LIB exists alongside Dafny: **every generated lemma has an empty body** and uses no
quantifiers, functions or loops, so the obligation is ground integer arithmetic that Dafny
hands to Boogie which hands it to Z3. Going straight to SMT-LIB skips two layers and is about
two orders of magnitude faster — measured, over the same claims:

| | Dafny (`--cores 4`) | `claims.smt2` + z3 |
|---|---|---|
| 2026-07-22 · 144 claims | ~8.3 s (the 54 committed hand lemmas) | **100 ms** |
| 2026-07-24 · 141 claims | ~3.8 s (the 52 committed hand lemmas) | **60 ms** |

That speed is what makes the anti-vacuity mutation test affordable on every push
(`--mutate 12` finishes in under a second) rather than weekly. `claims.smt2` is committed and
byte-identity gated, so it doubles as a portable artefact: any SMT-LIB solver can re-check the
claims without this pipeline.

**The `.smt2` covers every ledger of every session — there is no longer a second kind.** Hand
claims are written as **specs** in `sessions/<date>/report/hand_claims*.py` and built with
`pipeline.claims.build_hand`, so they render to all three backends and need no per-session
emitter: `--claims` on `codegen`, `codegen_smt` and `build_proof_map` takes several ledgers,
and `pipeline.codegen.session_ledgers` defines their canonical order. A session may hold more
than one hand ledger (07-22 and 07-24 split theirs narrative/coaching); the module→ledger
mapping is `build_hand.hand_ledgers`, which **raises on a ledger no module rebuilds** rather
than skipping it, because a skip is what leaves a ledger with nothing checking it.

Two windowed operators exist for claims about how a session *changed*:
`sum_round_range` / `count_rounds_range` restrict to a contiguous window of matches. The
window is part of the claim's identity (like `sum_ge`'s explicit mi/ri), so it is rendered by
emitting only the in-window terms — never `if <window> then x else 0`, whose folded-away
`if false` would leave a const referenced in the text but unread by the proof, i.e. a mutation
that can never be killed. Windows of different sizes must be compared as cross-multiplied
rates, never as raw sums.

**Encoding, and why it is what it is.** Strings are integer codes with a legend in the header
(`1 = yachi`), not the `String` sort — the sort restricted the file to the two solvers with a
string theory, which defeats emitting a standard format. The logic is `QF_NIA`, not `QF_LIA`:
the integer variance identity squares a datum, and `QF_LIA` rejects `(* v v)` outright. Both
facts were found by a solver refusing the file, not by reading a spec.

**Mutating the SMT artefact needs an operator per kind of datum.** `check_smt --mutate`
perturbs a *stratified* sample (every kind of datum, not a uniform draw) because both bugs this
gate has had were confined to a kind:

| Kind | Operator | Why the obvious one fails |
|---|---|---|
| categorical code (`_winner`, `_gameoverreason`) | try the **other codes** | claims count members of a category; `5 → 6` changes no count, `5 → 3` does |
| measurement | escalate **both ways** (+1, −1, +1000, −1000, far up, 0) | many claims are one-sided — "yachi's KPP is lower than pinglamb's" survives *any* increase to pinglamb |

Coded-ness is read from the constant's **name** (the emitter marks them with a trailing
`; label`), never from its value — detecting by value quietly reclassified a `topcombo` of 4 as
"the code for topout" and reported six real measurements as survivors.

**THAT OPERATOR HAS TWO IMPLEMENTATIONS AND THE SECOND ONE LACKED THE BOTH-WAYS RUNG UNTIL
2026-09-21.** `pipeline/mutation_test.sh` asks the identical question of `Facts.dfy` that
`check_smt --mutate` asks of `claims.smt2`, and its ladder was `+1`, then `v*10 + 100000` —
upward only. The weekly run of 2026-09-21 is where that cost a red build.
2026-09-19's `m13_r2_yachi_finesse_perfect` is 156; the only claim naming it is **G056**, whose
spec is the one-sided `sum(yachi.finesse_perfect)·sum(pinglamb.pieces) >
sum(pinglamb.finesse_perfect)·sum(yachi.pieces)` with yachi's datum on the winning side. Evaluate
those four sums over that session's `facts.json` — which is what re-derives every figure in this
paragraph, and this is the figures' only home, the harness's own comment deliberately carrying
none of them — and the margin is 156 405, i.e. **11.39 units of that pooled sum**, so the smallest
falsifying change is a DECREASE of 12 and *every* increase leaves the claim true. The harness was
reporting a constrained datum as a vacuous lemma. Its ladder is `check_smt.perturbations`' now,
plus the rung it already had.

**It was latent, not flaky, and that distinction is how to read any mutation result here.** The
harness picks its consts deterministically — evenly spaced through the file — so *which* datum
lands in the sample is a function of how many consts the file holds and in what order, i.e. of the
session's shape, never of chance. 09-19 is the corpus's longest session, its generated `Facts.dfy`
holds the 12 343 numeric consts the harness's own first line prints, and index 8 of 12 falls on a
`finesse_perfect`. Thirteen of the fourteen `pipeline` jobs in that run were green and the same
09-19 would have failed the week before, had 09-19 existed then. **A deterministic sampler does not
produce flakes; it produces findings that arrive when the corpus grows**, so 「re-run it」 is never
the response. That rule is stated nowhere else in this file, which is why it is stated here rather
than assumed: a survivor is the one CI failure in this repo that cannot be a flake, and the
temptation to treat a once-a-week red as one is what a schedule-only gate invites.

**A RULE with two implementations drifts exactly the way a FIGURE with two copies does, and it is
harder to see.** 冇第二份 below is about numbers, and a stale number at least looks like something
a reader could check. Here both implementations were internally consistent, both gates were green
for months, and the divergence was invisible until a sampled datum happened to be one-sided. The
prose that recorded the lesson is the table above, and it named SMT alone — so **the document was
accurate and the other gate was wrong**, which is the one shape that re-reading the prose cannot
catch. What made the repair safe to land without re-measuring every session is structural rather
than empirical: keeping the harness's old rung makes the new ladder a **superset** of both
operators, and a kill is the first rung that breaks verification, so no mutant that died under the
old ladder can survive under this one.

**The two ladders are still two implementations, and `pipeline/check_mutation_ladder.py` is what
now makes them agree.** Collapsing them into one would have been the wrong repair — two
independent implementations of one question is this repo's method, on the proof side exactly as
on the extraction side — so what is gated is that the shell ladder is never WEAKER: every rung
`check_smt.perturbations` would try still appears in it, in that order. Two decisions inside it
are the transferable part. The shell side **prints** its own ladder (`mutation_test.sh --ladder
<v>`) instead of being parsed, because a gate a reformat breaks is a gate whose normal state is
red — the same objection this file records against recomputing the repertoire bands. And its
values are chosen by SHAPE rather than sampled: zero, the two points where the shell ladder's own
dedup fires, their neighbours, and a score-sized value where the two 「far up」 rungs diverge. A
uniform draw would have missed all four boundaries, which is the stratification argument the SMT
gate already makes about kinds of datum, reached here about kinds of value. It runs on every push
rather than weekly, because the drift happens at edit time and the weekly is only where it gets
found.

**Two solvers, and they agree.** z3 4.16.0 and cvc5 1.3.4 both answer `unsat` on every claim of
every committed `claims.smt2` — 690 across the six artefacts on 2026-08-18, and that total is
printed by the run rather than maintained here, because the figure that used to sit in this
sentence ("153 generated claims, 77 + 76") was a two-session number still being published at six.
`check_smt` runs every solver on PATH and reports how many it found, so an n-solver run is stated
rather than implied — and the count is derived from that list, not a literal, which is what makes
the line survive a solver being added to a job. Each solver needs different argv —
z3 reads stdin only with `-in`, cvc5 needs `--incremental` before it honours the file's
`push`/`pop` — so `SOLVERS` maps a name to its flags and the file is passed as a path.

Installing cvc5: the documented way is the project's **own Homebrew tap, as a cask**, which is
why `brew install cvc5` and `brew search --formula cvc5` both come up empty:

```fish
brew install --cask cvc5/cvc5/cvc5
```

The PyPI `cvc5` package is Python bindings only — no CLI. yices2 installs from core
(`brew install yices2`) but its nonlinear support is limited, so it may refuse the variance
claims.

CI pins cvc5 by sha256 (`CVC5_SHA256` in the workflow), and that hash has **two independent
authorities that agree**: cvc5's own Homebrew cask and GitHub's asset digest — verified against
the downloaded bytes before use.

**Which solver runs where is decided by the QUERY, not by the runner — and that only became true
on 2026-08-18.** The `verify` job installs z3 alone because verify-session step 7's lemma-vacuity
gate needs a solver and fails rather than skips without one, and it must be z3: cvc5 produced no
result in 120 s on 2026-07-24's 78 claims where z3 settles them in 2.6 s, so the two are not
interchangeable for those free-variable queries. The `pipeline` job installs **both** and runs
`check_smt` over the committed `claims.smt2`, so "the two solvers agree" is now checked on every
push instead of only locally.

Until that date the answer was the runner instead. CI sat on `ubuntu-22.04`, whose glibc is 2.35,
and every z3 release after 4.14.1 ships `x64-glibc-2.39` only — so CI could run just the one z3 old
enough to load, and the `pipeline` job could not run z3 at all. **ubuntu-22.04's deprecation is what
moved the runners**, and the solver constraint fell out with it: all 15 jobs are on 24.04
(fourteen `ubuntu-24.04`, `oracle-image` on `ubuntu-24.04-arm`, where it already was) and
`Z3_VERSION` is 4.16.0.

**The pin got better, and by exactly one step — do not write it up as two.** GitHub publishes no
asset `digest` for **any** z3 build against glibc-2.35, and those releases carry no signature,
checksum or SBOM, so 4.14.1's hash was trust-on-first-use: computed from a download of ours,
defending against the asset changing from here on but not against it having been wrong when first
fetched. 4.16.0's `x64-glibc-2.39` asset does have a digest, and `Z3_SHA256` is copied out of it,
so `sha256sum -c` in the workflow now checks the bytes against someone else's number. That is one
authority. It is **not** the cvc5 standard, which is two that agree — a Homebrew cask hash and the
GitHub digest — because z3 has no cask (the formula builds from source) and no attestation either
(`gh attestation`, still 404 at 4.16.0).

**Dafny's asset stays `x64-ubuntu-22.04` and that is not a stale pin.** It is the only Linux asset
Dafny publishes, at 4.11.0 and at latest, so the 24.04 URL a reader reaches for does not exist. The
workflow names it `DAFNY_ASSET_OS` precisely so the three install steps have nothing to "correct".
A glibc-2.35 build on a glibc-2.39 runner is glibc's supported direction, and Dafny's own xunit,
integration, refman and doc-tests workflows all run on `ubuntu-24.04`. The reason that is safe to
rely on rather than merely likely is that the dependency is **fail-closed**: a Dafny that will not
load dies at `dafny --version`, before a claim is checked. There is no arrangement in which a broken
verifier produces a green verification, which is the property worth checking whenever this pin moves
— not "does it work", but "what does it do when it doesn't".

Every generator replaces only the region between its HTML comment markers, so all of them are
idempotent and safe to re-run over a hand-edited report. `pipeline/region.py` owns that
mechanism (`markers()` / `replace()`); `build_round_table.py` predates it and carries its own
equivalent marker pair.

## Workflow

- **The Pages site is rendered by CI and NOT committed (since 2026-10-23).** `docs/` is git-ignored;
  the `docs` job in verify.yml renders the site into `_site/` with `bin/build-docs --out _site`,
  renders it again with `--check` (the second render must be byte-identical to the first), uploads
  it, and the `deploy` job publishes it to GitHub Pages on a push to main once every other job in
  verify.yml has passed — `bin/verify-repo --check` refuses a `deploy.needs` list that leaves one
  out. The repo's Pages source is "GitHub Actions". `docs/<page>` in this file names the page's
  path on the site (and in a local `bin/build-docs` render), not a committed file; a sentence below
  saying `--check` "byte-compares" a page against a committed copy is from before this change and
  now means the second render. Committing docs/ had made every pipeline change re-commit each
  report twice (`docs/<date>.html` was a byte copy of `report.html`).
- **I commit; the user pushes.** `git push` and remote changes are blocked for the agent.
  Stage, commit with a Conventional Commit message, then tell the user to push.
- CI re-runs every gate on push, including regenerating each ledger and checking it is
  byte-identical to what is committed. Weekly runs add mutation testing. **20 job definitions
  across 4 workflows; the 13 of 2026-08-20 expanded to 26 check runs that day** — `verify` is a matrix over
  artefact directories (21 — twenty session artefacts plus the `subsets/2026-09-18-onform`
  filtered subset, which is NOT in the corpus even though the night it is drawn from now IS) and
  `pipeline` over sessions (19), so both counts move with the corpus
  and neither should be typed from memory. Re-derive the first with
  `awk 'FNR==1{j=0} /^jobs:/{j=1;next} j && /^  [a-zA-Z_-]+:$/{n++} END{print n}'
  .github/workflows/*.yml` — the `FNR==1` reset is load-bearing, because without it `j` stays set
  across files and the count comes back 21. (This bullet read 「6 jobs」 until 2026-08-23 —
  the 冇第二份 class, in the paragraph describing the gates.)
- **`subsets/2026-09-18-onform`'s report is in ONE matrix and the drift gate is in the other, so
  nothing catches it drifting.** The subset sits in `verify` (per-artefact gates, all internal to
  the directory) and is deliberately absent from `pipeline`, which builds `sessions/<date>/report`
  from a date list — and `build_report --check` runs only in `pipeline`. Its report nonetheless
  carries the two CORPUS-WIDE blocks every report carries (the `QUALIFYING_MS` footnote and the
  最癲一局 lede), both of which move whenever a session lands. So it drifts on exactly the
  occasions the eighteen sessions do, and only they are checked. Found on 2026-09-19 by running the
  check by hand, not by a red build; the report was rebuilt in the same pass, **and again on
  2026-09-18's pass, where the footnote moved from 「13個 session 夾埋 1768 個 player-round」 to
  「14個 / 2022」 and the SD ratio from 4.5× to 4.6×** — the second consecutive session where the
  manual step was the only thing standing between the subset and a stale published figure; 2026-10-03's
  pass moved it a third time (「15個 / 2314」, SD ratio 4.7×) and 2026-10-09's a fourth (「16個 / 2518」,
  SD ratio back to 4.5×), 2026-10-12's a fifth (「17個 / 2628」, SD ratio unchanged at 4.5×), and 2026-10-20's a sixth
  (「18個 / 2688」, SD ratio down to 4.4×), and 2026-10-22's a seventh
  (「19個 / 2814」, SD ratio unchanged at 4.4×). **Until a gate
  covers it, re-run `python3 -m pipeline.build_report subsets/*/report --check` whenever a session
  is added** — that is a manual-only step, which this file elsewhere calls the thing
  `bin/verify-repo` exists to abolish, so it is named here rather than left to memory.
- **Every job but the two matrices (`verify`, `pipeline`) is repo-wide, and `bin/verify-repo` is what
  runs them** (eighteen of the twenty on 2026-10-16; this read 「Sixteen」 until then, and was already
  one short at nineteen jobs — derive it as the job count less two, never carry it). `bin/new-session`
  covers steps 1-7 of adding a session (step 6 runs the four sim emitters); `bin/verify-session` takes ONE artefact directory and every
  gate it runs is internal to it. Until 2026-08-23 nothing ran `cross-extractor`, `leave-one-out`,
  `intense-round-corpus`, `typescript`, `spec`, `oracle-image`, `preregistrations`, `manifest` or
  `coverage` — only `docs`, via `bin/build-docs --check` — so the last mile of adding a session was
  discovered from CI rather than locally, which on 2026-08-20 cost three push→CI→fix cycles for
  four failures that were all reproducible in minutes.

  `bin/verify-repo` closes that, and **the way it holds is the part to keep, not the fact that it
  exists**: it does not carry a list of commands, it READS the workflow files and runs each job's
  own `run:` blocks. A list would have been the eleventh hand-maintained list in this repo and it
  would go stale in the direction that reads green. So every job must appear in its `PLAN` — run at
  a tier, or excused by a named predicate with a reason — and six things are errors rather than
  skips: a job in CI that `PLAN` does not name, a `PLAN` entry no job answers to, a step skipped by
  a name no step has, a step carrying an `if:` nobody decided, a step whose `${{ }}` cannot be
  resolved here, and a step reading a `$GITHUB_*` / `$RUNNER_*` variable the script does not supply.
  A plain new `run:` step, by contrast, is **absorbed silently and runs**, and there is a control
  asserting exactly that, because it is what tells derivation from copying. `workflow-plan` is the
  CI job that checks all of it, because a script standing in for CI that CI does not check is the
  manual-only gate this repo has now paid for three times.

  ```bash
  bin/verify-repo               # every repo-wide gate a push would run
  bin/verify-repo --fast        # omit the slow tier (coverage, oracle-image)
  bin/verify-repo --weekly      # add the schedule-only jobs and steps (mutation, coverage-round)
  bin/verify-repo --sessions    # add the `verify` and `pipeline` matrices, from the workflow's own lists
  bin/verify-repo --only docs   # reproduce ONE red job, whatever its tier
  bin/verify-repo --check       # completeness only: is this script still CI's equal
  ```

  **`RUNNER_TEMP` is why "run the workflow's own commands" is not free.** The `pipeline` job's Dafny
  step reads it, and under `set -u` a local run dies with `unbound variable` — which is how the first
  `--only pipeline` failed all seven sessions in nine seconds. The runner-provided variables with an
  honest local equivalent are supplied (`RUNNER_TEMP` → a scratch dir, `GITHUB_WORKSPACE` → the repo,
  `GITHUB_ENV`/`GITHUB_PATH`/`GITHUB_OUTPUT`/`GITHUB_STEP_SUMMARY` → scratch files, `GITHUB_EVENT_NAME` → `schedule` under `--weekly` and `push` otherwise) and **any other
  `$GITHUB_*` or `$RUNNER_*` reference is a completeness error**, so the next one is refused up front
  rather than dying halfway through a matrix.

  Two things it deliberately does NOT do. `oracle-image` needs an aarch64-**linux** runner, so on a
  Mac it is named as skipped rather than quietly dropped — every unrun job, unrun step and toolchain
  version that differs from the workflow's pin is printed in the summary, because a run that covered
  less than it claimed is the failure the tool was written to stop. And it does not replace
  `bin/verify-session`: `--sessions` runs the two matrices, but the default does not, and the
  summary says so.

  **The `pipeline` matrix is where `bin/verify-session` turned out to be narrower than CI**, found
  while writing this: `verify-session` runs 7 gates over an artefact directory, while CI's
  `pipeline` job runs 18 steps per session — `build_report --check`, `check_prose_figures`,
  `check_generated_css`, `check_finesse_denominator`, `check_badge_links`, `check_report_shell`, the
  forecast/opener/wiki section gates and `check_smt` are in the second list and not the first. That
  is not a bug in `verify-session`, whose scope is deliberate, but it does mean **`bin/verify-repo
  --sessions` is the only local command that runs everything a push runs**.
- **A figure with a renderer is PASTED, never typed.** `check_equiv_coverage`, `check_intense_corpus`
  and `check_loo` each emit their published blocks (`--render`), and the renderer and the parser
  live in one file so a reword is a one-place edit. Hand-editing one of those sentences can
  disable the gate that checks it: on 2026-08-20 a scope caveat added to this file's per-session
  coverage line — honest, because the session's artefact genuinely did not exist yet — broke the
  single-line match `check_equiv_coverage.DOCS` anchors on, and the gate went from checking six
  figures to checking none. **When a required artefact is missing, generate it rather than
  documenting its absence**; the caveat is only correct when the artefact cannot yet be produced.
  **Do not write that line's anchor token anywhere else in this file.** The spec matches the
  FIRST line carrying it, so a mention shadows the real sentence and the gate fails to parse —
  which is how this very bullet broke it on 2026-08-23, one paragraph after describing the
  hazard. Quote the rule, never the token.

  **A sentence beside a table is gated by a MARKED FRAGMENT, not by an anchor regex, and the
  difference is what the paragraph above keeps failing at.** Since 2026-08-23 the four counts
  in the equiv-coverage prose — how many sessions sit below the ≥85% gate, which ones, and how
  many lose coverage to the second family at each of the two granularities — sit inside inline
  HTML-comment pairs whose contents `check_equiv_coverage` byte-compares against its renderer.
  An anchor regex could not do it: this repo's own dated sections carry EARLIER VERSIONS of both
  sentences (ROADMAP.md's 2026-08-15 block says 「three of six sessions」 and 「Five of six
  sessions lose coverage」), and `paragraph()` takes the first match, so the gate would have
  checked the historical paragraph and passed the live one. The rule the markers enforce is
  **exactly one pair per document** — not "at least one" — which is the shadowing hazard turned
  from a written warning into a red build. It fired within a minute of being written, on the
  ROADMAP section documenting it, because the example spelled a real fragment name. Use a
  placeholder when writing one down. And note what this buys over 「quote the rule, never the
  token」: the marker is enforced, the rule is not.
- Report prose is Hong Kong colloquial Cantonese, traditional characters. `build_claims.py`
  asserts no simplified glyphs; reviews have repeatedly caught 净/实/约 slipping in.
- **Closing a ROADMAP item means striking it AT ITS ORIGINAL SITE, not only writing a new dated
  section.** An audit on 2026-08-16 found **six** items filed as open that were already done in
  committed code — 最癲一局 items 4 and 5, Re-classified item 7 (done the same day it was filed
  "not yet actioned"), the `cc-movegen` standing gate, the `## P5 — in progress` header contradicted
  by its own body 266 lines later, and Original TODO item 2 (false for eighteen days) — plus one
  obsolete item arguing about a mechanism that had been deleted. Every one has the same shape: the
  closure landed in a NEW section or in a commit message, and the original entry was never touched.
  A commit message is not documentation; nothing re-derives it. **A DONE record that repeats a wrong
  reason is worth less than none** — item 7's justification for its `<= 3` bound was measurably false
  in both the item text and the commit that closed it.
## 冇第二份 — a number whose only home is this prose

**A figure whose only copy is here has nothing to disagree with it, so it cannot go stale loudly.**
It goes stale silently, stays published, and reads exactly like a measurement until somebody happens
to re-derive it by hand. Every other class of drift in this repo announces itself — a ledger stops
being byte-identical, a lemma stops verifying, a gate goes red. This one has no announcement
mechanism at all, which is what makes it the hardest class the document carries.

Four instances, all live as of 2026-08-19, and they are not the same kind of thing on the surface:

| | what it was | how it failed |
|---|---|---|
| the repertoire ranges | Honey Cup 17-25, MS1 11-25, TKI-3 5-8 | **two of three already false when 08-14 landed**; five days published. `grep` confirms no file in the repo ever contained them |
| ~~the `cavity ≥ 1` band~~ | 74.6-77.0% | nothing recomputed it; it survived only because 08-14 tied 08-09 at one decimal. **CLOSED 2026-08-24**: `donation.ablation` in each artefact carries the session's own counts and `pipeline/check_donation_bands.py` renders all three bands. The band it replaces was `29-34%` — wrong at both ends and **pinned inside seven byte-identity-gated artefacts**, which is the sharpest form this class takes: re-emitting reproduced the wrong string exactly, so every gate agreed with it |
| the raw-DS AUC series | 68.4 · 62.0 · 81.2 · 83.0 · 64.0 | quoted from a probe; stopped at five sessions and nothing said so |
| ~~the `760` numerators~~ | 183, 257, 245, 201, 650/750 … | correct when written, silently wrong the moment the corpus reached 900. **CLOSED 2026-08-23**: `analysis/stat_sources.py` re-derives all 28 of them and `pipeline/check_stat_sources.py` gates the sentences. They were the hardest row here because **every one carried an honest caveat** — 「measured over the first six sessions, not re-run at 900」 — and a caveat cannot go red |
| ~~the R statistics~~ | slopes, CIs, p's, the SD fall, the cut-off band | the only family whose producer ran in NO workflow and no `bin/` script, so its figures could not even be re-derived without remembering to. **CLOSED 2026-08-23**: `analysis/rate_records.R --json` writes a committed artefact, `records.py` reads it instead of holding copies, `pipeline/check_rate_records.py` gates the eighteen sentences. THREE of them were already wrong — the band (VS's quoted for a claim naming APM), 約262.6 (the rounded value this file's own 約 section names as the mistake), and twenty-six lines of four-session figures in `generators.py` beside the `QUALIFYING_MS` they justify |

**A gate can have the same defect, so "it is checked" is not the test.**
`expect(out).toBe(sum(width_ge_3))` in `openers.test.ts` looked like a gate and was arithmetic
standing in for the empirical claim "no ≥3-wide hit is ever in an opener" — true only while
`in_opener` was 0 everywhere, so it was a tautology of the data it was written against, and it broke
on the day that stopped being true. The question is never "is there a check", it is **"what would
have to change for this number to be recomputed"**.

The corollary, and it is where to look next: **the remaining exposure is concentrated wherever a
figure was quoted from a probe that was never committed.** A probe that ships an artefact leaves
something to diff; a probe run once and discarded leaves a number in prose and no way back to it.
So before writing a figure here, ask what re-derives it — and when the answer is "nothing", either
point at what does (a committed artefact, a test, a generator) or say plainly, in the sentence
itself, that it is hand-measured and must be re-measured. Both of those are done for each of the
four rows below; a bare number is not.

**A count measured against a pinned SET is void the moment that set changes.** The fifth instance
arrived while this section was being written, and it is the one that should worry a reader most.
`forecast-access-class.test.ts` carried 「20 planted, 16 killed, 4 survive」 in its header — a
mutation score measured on 2026-08-16 against an `ACCESS_CLASS` holding two entries. 2026-08-19
added two more, and the score silently became a statement about a file that no longer existed.
**That file already knew.** It carries a paragraph warning against exactly this, and the warning
did not prevent the recurrence, for the reason the whole section is about: *prose cannot fail*.
The header now says which five mutants were re-run and which fifteen were not. The actionable
rule: when a pinned set changes, every count measured against the old set is void until it is
re-run or explicitly scoped to the set it was measured on.

**The sixth instance is a claim's PROSE saying more than its spec proves, and it survived nine
sessions because the case that falsifies it had never occurred.** `series_result` built its
sentence with `champ = max(w, key=…)` and asserted 「{champ} 攞低個系列」. Its spec pins the two
match-win counts and nothing else, so on 2026-09-10's 4-4 the predicate evaluated True, the lemma
verified, `check_smt` found no surviving mutant and the proof map read 86/86 — **every gate in the
repo agreed with a false sentence**, because no gate in this repo reads the Cantonese. This is the
`29-34%` shape with the byte-identity gate swapped for the whole proof chain: a verifier certifies
what the spec says, never what the prose beside it says.

Two things generalise. **A claim whose prose adds a word its spec does not carry is unfalsifiable
by construction** — 攞低, 全面壓住, 最, 淨係 are all this shape, and the screening question is the
same one the section above asks: *what would have to be true for this to fire?* If the answer is
「nothing the spec mentions」, the word belongs in the spec or nowhere. And **a branch no session has
ever taken is not tested by nine green sessions**; it is untested. `match_rate_dominance` carried
the identical defect one function away, does not fire on 09-10, and was fixed in the same commit
precisely because a corpus that has never drawn is not evidence that the draw branch works.

**The seventh instance is the one this section makes MORE likely, and it landed on 2026-09-10's own
write-up.** Seven figures in this file went stale in the same pass that updated their neighbours:
「3 of the 114」 PCO-window clears, the whole-round T-spin total in the gate-figure aside (6599),
the cave's differing-board row (19 of 19), 全消's 「3 of 124」, PC's pooled AUC quoted out of the
block above (50.67 over 450), and two 「seven sessions」 that are ten. Every one sits in a paragraph
whose OTHER figures are marked fragments, and the gates went green because the gates only read the
markers. **The figures in this bullet are the STALE ones as found, deliberately without their
replacements beside them** — the first version of this paragraph printed 「now 4 of 138」, 「now
7282」, 「now 24 of 24」 and 「now 51.66 over 634」, every one of which was itself stale one session
later, so a record of a correction was generating the very class it records. Read the live values
at their own sections; this bullet is a list of what went wrong, not a table of what is true.

**A gated fragment beside an ungated one makes the ungated one harder to see, not easier.** A
paragraph with markers in it reads as a checked paragraph; the green build is evidence about the
marked spans only, and the eye takes it as evidence about the prose. That is the reverse of the
usual 冇第二份 shape — there the figure is alone and obviously unbacked, here it is camouflaged by
a neighbour that IS backed. The actionable rule: **when a marked fragment's value changes, re-read
the whole paragraph for unmarked numbers that move with it**, because the gate that just went green
did not. And the one that changed the underlying claim — the PCO numerator moving 3 → 4 — is why a
digit swap is not enough: that paragraph's argument was 「the numerator did not move」, so the
sentence had to be rewritten rather than corrected.

**The eighth instance is a sub-class the previous seven do not cover, and it is the cheapest one to
prevent: a COUNT taken over a LIST printed in the same paragraph.** Two were found on 2026-09-11's
pass, both about the within-player APP separation series, and both wrong for more than one session:
「Three of ten with pinglamb wider」 (it was five of ten) and 「09-10 makes it three in a row」 (it
was two). The series they summarise is printed three lines above them, so both counts were
falsifiable by reading upward, and neither was. A third of the same shape sat one section away:
「APP … higher in rounds won than lost in 14 of 14 player-sessions」, a seven-session count still
standing at ten, where the quantity is simply twice the session count.

What makes this class distinct is that **the evidence is already in the document and the reader's
eye treats the count as a summary of it rather than as a separate claim.** An ordinary 冇第二份
figure has nothing to check it against; this one has everything to check it against and still goes
unchecked, because summarising is what a sentence after a list appears to be doing. The actionable
rule: **a count over a list in the same document is re-derived from the list, never carried** — and
when the list is a per-session series, prefer a form that cannot drift (「N of the twelve」 with the
series beside it) over one that can (「three in a row」, which is a claim about ORDER that a new
session can falsify from either end).

**2026-09-17's pass found two more of that eighth class, and the second is the worst instance the
document has held, because the list contradicting it was four lines away.**

* 「pinglamb leads attack per piece in every match」 **held in eight of ten sessions and this is one
  of the two where it does not.** It was five of ten and 09-10 was one of five. The bullet two
  paragraphs above it lists 08-19's three smallest per-match gaps as 「−10.13, −0.98, +0.72」 — two
  of them negative, i.e. two matches where yachi leads, in a session the count treats as having
  none. The document contained its own refutation and the count was still carried for two sessions.
* the topout bullet carried **two copies of its own series**, a stale ten-value one mid-paragraph
  and a live eleven-value one below it. Neither was wrong when written; the first simply stopped
  being updated when the second was added, which is how a paragraph comes to disagree with itself
  without either half ever being edited incorrectly.

**The generalisation those two force is about REDUNDANCY, not about counting.** The eighth class as
first written assumed the list and the count sit adjacent, so 「read upward」 was the remedy. Neither
of these is adjacent: one is four lines and a paragraph break away, the other is a duplicate of the
very list it disagrees with. So the remedy has to be structural rather than attentional — **a
quantity gets ONE home in this document, and a second copy is a defect on sight, even when both
copies are currently correct.** The second copy is what makes the first unfalsifiable by reading:
a reader who checks one has no reason to suspect the other exists.

**A third arrived in the same pass and it is the sharpest instance the class has, because it sat
one line from a GATED fragment and survived four sessions anyway.** README.md and ROADMAP.md each
close the equiv-coverage section with 「a floor all eight pass would sit at 60%」. 「Eight」 was the
session COUNT, written on 2026-08-25 when there were eight; the sentence directly above it carries
`equiv:gate-count`, which is rendered and byte-compared on every push and has since moved
eight → nine → … → **nine of the twelve**. So a marked fragment and an unmarked number sat in
adjacent lines, both saying 「eight」 for one session, and then only one of them moved. Four
sessions passed. **2026-09-12's pass was specifically hunting this class and did not find it** —
which is the point worth keeping, not the fix.

Two things this adds. **The gated neighbour is what hid it**: 「eight」 beside a green fragment
reads as checked, and the rule 「when a marked fragment's value changes, re-read the whole
paragraph」 was written for exactly this and still needs a human to run it. And **the number was
not a summary of anything** — it is a session count, so it belongs to the class the previous
bullet names: re-derive 「N of M」 from the corpus, never carry it, and that applies to an M
standing alone just as much as to the N in front of it.

## Data semantics that cost real debugging

- `lifetime` is **milliseconds**, not frames (verify via `pieces / pps`; 60 fps is ~15× off).
- `ige` `interaction_confirm` events are **queued incoming attack**, before cancellation —
  consistently ~10–20% above `garbagereceived`, which is what materialised. The reports say
  射埋 vs 食 and must never conflate them.
- The raw `tspins` counter includes spins that cleared nothing, so it exceeds the sum of the
  T-spin clear types. Always say which measure is meant.
- Kills equal round wins by construction in first-to-death 1v1 — never presented as a second
  independent signal.
- Player order in `users` / `leaderboard` is **not stable across files**; key by username.
- A match's `index` is its **position in the session**, not the export number in the
  filename — the filename stays in `file`. The two agreed by accident until 2026-08-01,
  whose exports are numbered 2-8: claims have always said `m{position}` while the report
  card printed `第 {index} 場`, so a badge proving something about m1 would have sat on a
  card labelled 第 2 場. Both extractors renumber after sorting; every earlier session's
  `facts.json` is byte-identical under the change, which is what makes it safe.
- **A round carries THREE stat objects and both extractors mix two of them.** `player.stats` is a
  live in-game tick; `player.replay.results.stats` is the final snapshot; `player.replay.results.`
  `aggregatestats` = `{apm, pps, vsscore}` is the final *rate* triple and nothing in the repo reads
  it. `apm_x1000`/`pps_x1000`/`vs_x1000` come from the live tick while `garbage_attack` /
  `garbage_cleared` / `finaltime_ms` come from the final snapshot, so a rate and its own counters
  can be one tick apart — the whole of the VS-identity residual. **Every count in the rest of this
  bullet and the next is re-derived by `analysis/stat_sources.py` over all
  <!--stat:corpus-->2814 player-rounds<!--/stat:corpus--> and gated by `pipeline/check_stat_sources.py`, so
  none of them is typed.** (They were, until 2026-08-23: six-session numbers in a
  seven-session document, each honestly captioned 「not re-run at 900」 — which is why none of
  them ever went red. A caveat is not a measurement.) The live tick is
  stale in <!--stat:tick-stale-->635 of 2814<!--/stat:tick-stale--> player-rounds and
  **<!--stat:tick-stale-survivor-->628<!--/stat:tick-stale-survivor--> of those are the round's SURVIVOR**: the survivor keeps playing frames after
  the opponent tops out and `player.stats` freezes before those frames fold in, so a per-player skew
  in the residual is a fact about whose round ran longer, never about how someone plays.
  `aggregatestats` reproduces every rate to ≤<!--stat:resid-worst-->4.2e-16<!--/stat:resid-worst--> over
  <!--stat:corpus-agg-->2814 player-rounds<!--/stat:corpus-agg--> as
  `100·(attack+cleared)/T`, `60·attack/T`, `pieces/T` — where **T is the integer FRAME count, and
  `finaltime_ms` does not yield it.** `⌊finaltime_ms·60/1000⌋/60` gives the wrong frame count on
  **<!--stat:floor-wrong-->971 of the 2814<!--/stat:floor-wrong-->** and leaves up to <!--stat:floor-worst-->1.6e-3<!--/stat:floor-worst-->, because `finaltime_ms` is `results.stats.finaltime`
  rounded to the millisecond (`extract.py`'s `x1`) while the clock ticks every 1/60 s — the rounding
  destroys the frame the flooring is trying to recover. Recover it from `pps` instead:
  `round(60·pieces/pps)` is an integer to <!--stat:frames-integer-->1.9e-12<!--/stat:frames-integer--> on all
  <!--stat:corpus-frames-->2814<!--/stat:corpus-frames-->, and under **T = round(60·pieces/pps)/60**
  the residual is <!--stat:resid-pair-->2.9e-16 for APM and 4.2e-16 for VS<!--/stat:resid-pair-->, which is where the ≤ above came from. PPS is
  exact by construction on that route, so the **checkable** statement is the T-free identity
  `vs·60·attack == apm·100·(attack+cleared)`: worst relative residual
  **<!--stat:identity-->6.2e-16<!--/stat:identity-->** over the <!--stat:identity-rounds-->2792<!--/stat:identity-rounds--> rounds
  with a nonzero APM and VS. A probe that uses `finaltime_ms/1000` reports a discrepancy the data
  does not have — up to <!--stat:secs-worst-->1.4e-3<!--/stat:secs-worst-->, and above 1e-4 on
  <!--stat:secs-over-->868 of the 2814<!--/stat:secs-over-->. (That last count is over all THREE rates: VS and
  APM alone give two fewer. `aggregatestats` is a triple, so a route claiming to reconstruct
  it has to reconstruct the triple.)
- **`kills` runs the OTHER way, so do not "finish the job" by moving the rest of `player.stats`.**
  The 2026-08-16 re-source moved `apm`/`pps`/`vs` off the live tick because the tick predates the end
  of the round. `kills` has the opposite problem: `results.stats.kills` disagrees with
  `player.stats.kills` in **<!--stat:kills-->782 of 2814<!--/stat:kills-->** player-rounds, and every one is the live tick reading 1
  against the results snapshot reading 0 for a player who SURVIVED — because the results snapshot is
  taken when that player's own game ends, while the kill is credited later, when the opponent tops
  out. For `kills` the live tick is the correct source and the final snapshot is the stale one.
  `aggregatestats` carries only `apm`/`pps`/`vsscore`, so the re-source is complete as scoped rather
  than truncated; and the match-level rollup stays on the live tick because
  **<!--stat:leaderboard-agg-->0 of 374<!--/stat:leaderboard-agg--> leaderboard entries carry
  `aggregatestats` at all** — so round figures will not reconcile against the leaderboard's, and
  there is no better source for it. `garbagesent`/`garbagereceived` differ from their
  `results.stats` counterparts in
  <!--stat:garbage-differ-->18 and 16 of 2814<!--/stat:garbage-differ--> and are a different measure anyway (both sides are already extracted, as
  `garbage_sent_raw` / `garbage_received_raw`). Moving any of these for consistency would introduce
  the bug the rate change removed.
- **The finesse counters are on two different units, so any finesse rate must name its denominator.**
  `perfectpieces` counts **pieces**; `faults` counts **fault events**, and one piece can register
  several — pooled, <!--stat:finesse-pool-->45 249 faults over 27 720 non-perfect pieces<!--/stat:finesse-pool--> =
  **<!--stat:finesse-per-piece-->1.632<!--/stat:finesse-per-piece--> per faulty piece**. Four
  defensible rates, four different numbers, and only one is what TETR.IO displays:
  `faults/pieces` = **<!--stat:finesse-fault-rate-->17.14%<!--/stat:finesse-fault-rate-->** is fault events per piece; the share of pieces that were faulty is
  `1 − perfect/pieces` = **<!--stat:finesse-share-->10.50%<!--/stat:finesse-share-->**; TETR.IO's own figure is
  `perfect/pieces` = **<!--stat:finesse-tetrio-->89.50%<!--/stat:finesse-tetrio-->**; and
  `faults/(faults+perfect)` = **<!--stat:finesse-meaningless-->16.07%<!--/stat:finesse-meaningless-->** is on no meaningful denominator and must not be used. A
  bare「失誤率」 reads as the share and is usually the event rate. osk publishes no definition for any
  of the three fields, so the per-excess-input granularity is inferred, not specified. The four
  rates are definitions and keep their meaning at any n; the four *numbers* are re-derived over
  the whole corpus by `analysis/stat_sources.py`.

  **All six reports then in the corpus shipped the bare label, and
  `pipeline/check_finesse_denominator.py` is now the
  gate.** The tape chart plotted `faults/pieces` as 「finesse 失誤率」 formatted `(v*100).toFixed(1)+"%"`
  — the event rate under a label that reads as the share. The row is 「每粒 finesse 失誤」 rendered `toFixed(3)`
  now, matching 每粒攻擊 beside it, because **a percentage rendering asserts a share** and a label
  alone does not undo one: an event rate reads as a share however the row is titled. `hold 使用率` keeps its
  percentage — a hold IS at most one per piece, which is what the gate's `SHARE` kind records. The
  data refutes the share reading outright: in **<!--stat:finesse-exceed-->2419 of 2744<!--/stat:finesse-exceed-->** player-rounds the faults outnumber the
  non-perfect pieces, and **<!--stat:finesse-worst-->10-03 m10r1 puts 8 faults on a single non-perfect piece<!--/stat:finesse-worst-->**.

  Two things this cost that are worth keeping. **The defect lived where no gate looked** — the chart's
  renderer is in each session's committed shell, outside every marker region, so `build_report --check`
  never saw it and fixing `skeleton.py` alone would have shipped to no existing report; all six
  `report.html` had to be patched directly. So this gate reads the WHOLE document, generated regions
  included, unlike `check_prose_figures`. And **every accessor the chart plots must be classified**
  COUNT/SHARE/EVENT_RATE — an unclassified key fails, so a new row forces the decision instead of
  leaving it to whoever writes the label.

## What the data actually says (measured, not asserted)

Paired AUC over 129 rounds — how often the round's winner held the higher value. **This block is
07-22 and 07-24 pooled**, and its buckets are therefore two-session buckets; the numbers were
always labelled with their n, but the bucket NAMES read as corpus verdicts and two of them are
false at 450 rounds. See the pooled correction below the per-session paragraphs.

- **Strong**: VS 100% · APM 93.8 · 攻 93.8 · APP 91.5 · 送 88.0 · 射埋 12.0 (88 inverted) ·
  食 14.3 · 分 85.3
- **Filed here as "no signal" on two sessions**: COMBO 45.0 · PC 50.8 (89% zeros) · TST 55.8 ·
  TSD 60.9 · KPP 39.9 — COMBO and TST do not survive to 450 rounds as no-signal; PC does
- Near-constant (CV 0.05): KPP, FIN% — their flatness is the finding, not a column of numbers

2026-07-28 (64 rounds) reproduces all of it independently: VS 100% · APP 96.9 · APM 95.3 ·
攻 93.8 · DS 75.0 · 食 12.5 · 射埋 14.1 — and **KPP 42.2**, below chance for a third time.

2026-08-01 (53 rounds) is the fourth independent reproduction: VS 100% · 攻 90.6 · APM 90.6 ·
APP 83.0 · 食 15.1 · 射埋 19.8 — **DS 84.0, the highest of any session** (66.5 · 60.0 · 75.0 · 84.0
across the four) — and **KPP 53.8**, i.e. chance, for a fourth time.

2026-08-09 (50 rounds) is the fifth: VS 100% · 攻 94.0 · APM 94.0 · APP 88.0 · 分 86.0 ·
食 20.0 · 射埋 23.0 · DS 66.0 — and **KPP 58.0**, i.e. chance from the other side, for a fifth
time. DS is the per-*piece* variant throughout (raw `garbage_cleared` gives 68.4 · 62.0 · 81.2 ·
83.0 · 64.0 and is a different series); the 129-round headline block above is 07-22 and 07-24
pooled, not one session.

2026-08-14 (84 rounds) is the sixth, and the largest: VS 100% · 攻 91.1 · APM 90.5 · 送 82.7 ·
**APP 81.0, still the lowest of eleven** · 分 79.8 · DS 70.2 · 食 17.9 · 射埋 18.5 — and **KPP 40.5**, below
chance for a sixth time.

2026-08-19 (70 rounds) is the seventh: VS 100.0 · 攻 93.6 · APM 92.9 · **分 91.4, the highest of
seven by 5.4 points** · APP 87.1 · 送 87.1 · DS 73.6 (raw 75.7) · 食 15.0 · 射埋 12.9 — and
**KPP 41.4**, the seventh measurement and the fifth of the seven below chance. Three columns take
their corpus high here (分 91.4 · COMBO 67.9 · FIN% 67.1) and **PC 48.6 is the first below 50 in
seven**, which is the least surprising thing on the list: see 全消 below for why PC has no
denominator worth a rate.

2026-08-25 (73 rounds) is the eighth: VS 100.0 · 攻 90.4 · APM 90.4 · APP 84.9 · 送 82.9 ·
分 79.5 · DS 66.4 (raw 67.8) · 食 18.5 · 射埋 19.2 — and **KPP 45.2**, the eighth measurement and
the sixth of the eight below chance. Nothing takes a corpus high or low here; it is the flattest
session on the board, which is the point of recording it.

2026-09-03 (46 rounds) is the ninth, and the smallest: VS 100.0 · APM 95.7 · 攻 94.6 · 分 91.3 ·
送 90.2 · APP 89.1 · DS 59.8 (raw 62.0) · 食 9.8 · 射埋 9.8 — and **KPP 52.2**, the ninth
measurement and the third of the nine ABOVE chance, after 08-01 and 08-09. Six columns take a
corpus extreme here, which is what 46 rounds buys: highs in APM, 攻, TSD (79.3), TST (65.2),
FIN% (71.7) and PC (54.3), lows in 食 (9.8) and DS (59.8). Read every one of them as a
small-n reading first — this session has the fewest rounds of the twelve, so it is the most likely
to hold an extreme for no reason, and PC's 54.3 sits on six decided pairs. **PC's high did not
survive one session**: 09-10 reads 57.7.

2026-09-10 (65 rounds) is the tenth: VS 100.0 · APM 95.4 · 攻 94.6 · 分 89.2 · APP 87.7 ·
送 84.6 · DS 65.4 (raw 70.0) · 食 16.9 · 射埋 15.4 — and **KPP 43.1**, the tenth measurement and
the seventh of the ten below chance. Two columns take a corpus extreme and both are the kind to
read carefully. **PC 57.7 is the corpus high** on 14 decided pairs of 65 rounds (51 ties), and it
moves the pooled raw p more than its size suggests — see the table below. **COMBO 48.5 is the
first sub-50 reading since 07-22's 41.1** and the second-lowest of the twelve. Nothing else is
notable, which is the point of recording it: the session that finished level on every scoreboard
measure is unremarkable on this board.

2026-09-11 (51 rounds) is the eleventh: VS 100.0 · APM 94.1 · 攻 94.1 · APP 88.2 · 分 84.3 ·
送 83.3 · DS 71.6 (raw 70.6) · 食 16.7 · 射埋 16.7 — and **KPP 37.3, the corpus LOW**, under
07-22's 38.6, the eleventh measurement and the eighth of the eleven below chance. The other
extreme is **PC 59.8, a third consecutive corpus high** (54.3 · 57.7 · 59.8), and it is the one
to be most careful with: PC's decided count is tiny everywhere, so three rises in a row is three
small denominators pointing the same way and not a trend — the pooled row below still corrects
to no signal. Nothing else takes a corpus extreme. Note what the most one-sided session on the
scoreboard did NOT do to this board: 攻 94.1 and APP 88.2 are both mid-range, so a lopsided night
is not a night where the columns separate harder.

2026-09-17 (49 rounds) is the twelfth: VS 100.0 · APM 95.9 · 攻 95.9 · 送 88.8 · APP 87.8 ·
分 85.7 · **DS 79.6 (raw 78.6)** · 食 11.2 · 射埋 11.2 — and **KPP 49.0**, the twelfth measurement
and the ninth of the twelve below chance, though only just. Two columns come second in the corpus
and both matter downstream. **DS 79.6 is the second-highest of the twelve** behind 08-01's 84.0,
which is the column this session's coaching note rests on. **COMBO 67.3 is the second-highest**
behind 08-19's 67.9 — and it arrives after two sub-52 readings, so it reverses the drift the pooled
row below had been recording for two sessions running. The one run this session ENDS is PC's:
**49.0 is the first sub-50 reading since 08-19's 48.6**, immediately after three consecutive corpus
highs (54.3 · 57.7 · 59.8), which is exactly what a column with 7 decided pairs of 49 rounds does
and is the reason those three highs were never written up as a trend. Nothing takes a corpus high
or low.

2026-09-18 (127 rounds) is the thirteenth in date order and the fourteenth to arrive: VS
100.0 · **攻 96.1, the corpus HIGH** · APM 95.3 · APP 92.1 · 送 85.8 · 分 83.5 · DS 70.9
(raw 72.4) · 食 15.0 · 射埋 14.6 — and **KPP 47.2**, the thirteenth measurement and the tenth
of the fourteen below chance. Three columns take a corpus extreme and one of them is the
flattest reading on the board. 攻 96.1 passes 09-17's 95.9 by two-tenths, which at 125 decided
pairs is not a distance worth a sentence of its own. **TST 50.0 is the corpus LOW and it is
exactly chance, on 68 decided pairs that split 34-34.** That is a real measurement landing on
the line rather than an empty cell — the distinction matters because this column's other
readings sit on 30-90 decided pairs too, so 50.00 here is as well-evidenced as 65.2 was at
09-03 and means the opposite. It is also the reason the pooled TST row barely moves below.
**APP 92.1 is second of the fourteen** behind 07-28's 96.9, and **FIN% 52.0 is second-lowest**
behind 08-09's 50.0. **PC 54.3 over 25 decided pairs** was the second-largest decided count any
session had contributed to that column, behind only 09-19's 26 (10-03's 29 now tops both) — and the two of them arrive on
consecutive nights, which is what the pooled PC row below now has to be read against.

2026-09-19 (150 rounds) is the fourteenth in date order, and it is worth three of the others put together: VS
100.0 · APM 92.0 · 攻 92.7 · APP 90.7 · 分 86.0 · 送 82.3 · DS 72.3 (raw 74.0) · 食 16.0 ·
射埋 17.7 — and **KPP 36.7, the corpus LOW**, under 09-11's 37.3, the fourteenth measurement and
the eleventh of the fourteen below chance. **Nothing else takes a corpus extreme, and at 150 rounds
that is the most informative thing on the row**: every earlier session's extremes sit on 46-84
rounds, so a night three times the size landing mid-column everywhere is evidence that those
extremes were sample size. Two columns are worth naming for what they do downstream rather than
for their rank. APM 92.0 and 攻 92.7 are both **fourth-lowest of the fourteen** — a first draft of
this sentence called them the lowest and second-lowest, which is wrong by three places on each:
08-25 (90.4/90.4), 08-14 (90.5/91.1) and 08-01 (90.6/90.6) are all below. So this session is not
near a boundary anywhere, which strengthens rather than weakens the paragraph above.
**PC 54.0 over 26 decided pairs** was the largest decided count any session had
contributed to that column until 10-03's 29 — the most any session had contributed before these last two was 16,
shared by 07-22, 08-14 and 09-11 — and it is what moved the pooled row below across its
correction threshold for the first time. 09-18's 25 has since arrived beside it, so that row is
no longer one session's; see the table.

2026-10-03 (146 rounds) is the fifteenth: VS 100.0 · APM 95.9 · 攻 95.2 · APP 92.5 · 送 88.4 ·
分 85.6 · DS 69.2 (raw 71.6) · 食 11.0 · 射埋 12.0 — and **KPP 37.0**, the fifteenth measurement
and the twelfth of the fifteen below chance. **Nothing takes a corpus extreme outright, and five
columns come second**: APM 95.9 (140 of 146, behind 09-17's 47 of 49 at the second decimal), APP
92.5 behind 07-28's 96.9, TSD 71.9 behind 09-03's 79.3, and from the low end KPP 37.0 behind
09-19's 36.7 and COMBO 44.9 behind 07-22's 41.1. That is 09-19's reading again — a session of
nearly 150 rounds landing near the edges and not on them. **PC 50.3 sits on 29 decided pairs
(15-14)**, the largest decided count any session has contributed to that column, and it is
exactly what pulls the pooled PC row below back toward the line.

2026-10-09 (102 rounds) is the sixteenth: VS 100.0 · APM 95.1 · 攻 94.6 · APP 91.2 · 送 88.7 ·
分 85.3 · DS 69.1 (raw 69.6) · 食 10.8 · 射埋 11.3 — and **KPP 48.0**, the sixteenth measurement
and the thirteenth of the sixteen below chance, though only just. **Nothing takes a corpus
extreme, and one column comes second**: TSD 72.5, behind 09-03's 79.3 and past 10-03's 71.9.
Everything else lands mid-column — DS is tenth of sixteen, COMBO 52.5 tenth. **PC 52.5 sits on 21
decided pairs (13-8)**, the fourth-largest decided count any session has contributed to that
column after 10-03's 29, 09-19's 26 and 09-18's 25, and it leans the same way as the pooled row;
see the table for what that does to the leave-one-out. KPP's near-chance reading on 102 rounds is
what moves that row's corrected p the other way this revision.

2026-10-12 (55 rounds) is the seventeenth: VS 100.0 · **APM 100.0** · **攻 99.1** · APP 92.7 ·
送 90.0 · 分 89.1 · DS 67.3 (raw 68.2) · **食 7.3** · 射埋 10.0 — and **KPP 52.7**, the seventeenth
measurement and the fourth of the seventeen ABOVE chance, after 08-01, 08-09 and 09-03. **Three
columns take a corpus extreme and all three are the attacking exchange**: APM 100.0 is the first
time any column but VS has decided every round of a session (55 of 55, no ties), 攻 99.1 is 54 of
55 with one tie, and 食 7.3 (4-51) is the corpus LOW. Several more come second or third — APP 92.7
behind 07-28's 96.9, QUAD 80.0 behind 07-22's 80.4, the raw T-spin count 74.5 behind 09-03's 81.5,
送 90.0 third, 射埋 10.0 third-lowest — and COMBO 46.4 is third-lowest of the seventeen, after
07-22's 41.1 and 10-03's 44.9. Read every one of those as 09-03's were read: this is the
seventh-smallest session (55 rounds), and a session this size is the one most likely to hold an
extreme for no reason. DS 67.3 is eleventh of seventeen. **PC 50.9 sits on 7 decided pairs (4-3)**,
which is what a column with 48 ties in 55 rounds contributes, and it barely moves the pooled row.

2026-10-20 (30 rounds) is the eighteenth, and the smallest by a margin: VS 100.0 · **APM 90.0** ·
**攻 90.0** · APP 90.0 · 送 85.0 · 分 83.3 · DS 76.7 (raw 81.7) · 食 13.3 · 射埋 15.0 — and **KPP 46.7**,
the eighteenth measurement and the fourteenth of the eighteen below chance. **APM and 攻 both take
the corpus LOW** (27 of 30 each, under 08-25's 90.4), one session after 10-12 took both columns'
HIGHS — which is what a 30-round night does to a column that sits in the low nineties: three
rounds are ten points. DS 76.7 is third of eighteen, behind 08-01's 84.0 and 09-17's 79.6. COMBO
58.3 (14 of 23 decided), TST 46.7 (5 of 12) and **PC 51.7 on 5 decided pairs (3-2)** are all
small-denominator readings and move the pooled rows by little. Read every figure on this row as
the n = 30 reading it is; nothing here is evidence of anything a 46-round session could not also
have produced by chance.

2026-10-22 (63 rounds) is the nineteenth: VS 100.0 · APM 92.1 · 攻 92.1 · 分 87.3 · APP 84.1 ·
送 81.0 · DS 72.2 (raw 69.8) · 食 19.8 (射埋 not re-measured this revision) — and **KPP 35.7, the corpus LOW**, under 09-19's 36.7,
the nineteenth measurement and the fifteenth of the nineteen below chance. **APP 84.1 and 送 81.0
are third-lowest of the nineteen** in their columns, on the night with the corpus's largest session
APP gap — which is not a contradiction: the gap is a rate pooled over pieces, the AUC a count of
rounds in which the winner held the higher APP, and a large pooled gap is compatible with many
yachi wins at a lower APP (10 of his 25, by this AUC). TSD
73.0 is second of nineteen behind 09-03's 79.3, and 食 19.8 third-highest. **PC 55.6 sits on 23
decided pairs (15-8)**, the fifth-largest decided count any session has contributed and third in
the column by value, and it is what moves the pooled PC row this revision; COMBO 58.7 (27 of 43)
leans with the effect too. Every rank on this row was computed over the nineteen per-session
values by the same probe that reproduces 10-20's published row; none of it is gated.

**Two of the 129-round block's "no signal" entries are false at 1407 rounds, and the fault is
provenance, not arithmetic.** COMBO 45.0 and TST 55.8 were measured on the FIRST TWO SESSIONS
ONLY; the label was then carried forward as if it ranged over the corpus. Pooled over all 1407
rounds, Bonferroni-corrected across the 17 columns. **The test is the two-sided exact binomial
sign test over decided pairs** — named here because the previous revision of this table published
p's that nothing in the repo could re-derive, and a figure whose test is unstated is a figure that
cannot be checked:

| | pooled AUC | decided | raw p | ×17 | verdict |
|---|---|---|---|---|---|
| COMBO | 54.62 | 573/1016 | 5.1e-05 | 8.7e-04 | **survives correction and any single drop** (worst: without 09-18, 0.024); 9 of the 171 pairs take it over (worst: 08-19 + 09-18, 0.25) |
| TST | 55.40 | 431/710 | 1.3e-08 | 2.2e-07 | **survives correction** |
| KPP | 43.39 | 609/1404 | 7.7e-07 | **1.3e-05** | below chance and distinguishable from it — survives any single drop AND, for the first time, every one of the 171 pairs; see the leave-one-out |
| PC | 52.42 | 171/274 | 4.8e-05 | **8.1e-04** | crosses for a seventh revision, and **survives any single drop (worst: without 09-19, 0.0078)** — but not 09-10, 09-18 or 09-11 together with 09-19 (0.055, 0.054, 0.052) |

**KPP HAS NOW CROSSED, UNCROSSED AND RE-CROSSED, and the three events together say more than any
one of them.** The corrected p ran 0.048 at eleven sessions, 0.059 at twelve, **0.0010** at
thirteen, **0.0012** at fourteen, **2.3e-05** at fifteen, **3.5e-05** at sixteen, **8.7e-05** at
seventeen, **8.6e-05** at eighteen and **1.3e-05** at nineteen. Each revision of this section stated the margin beside the
verdict, and that is the only reason the record reads as a continuous measurement rather than as
three contradictions:

* **State the margin or do not state the result.** 0.048 and 0.059 are the same measurement
  either side of an arbitrary line; 0.0010 is not, and the difference is visible only because the
  earlier numbers were published. Had any revision written 「KPP survives correction」 with no
  figure beside it, the next session would have made the document wrong rather than out of date.
* **A threshold is not a discovery, in either direction.** Nothing about the data changed at 0.05
  on the way up, on the way down, or on the way back. The AUC has moved 44.23 → 44.55 → 43.21 →
  43.72 → 42.87 → 43.29 → 43.68, i.e. within a 1.7-point range across six sessions.
* **What moved it is SIZE, not a new effect, and a fourteenth session has now tested that.**
  09-19 is 150 rounds at KPP 36.7 — the corpus low — so it both pulls the pooled AUC down and
  roughly doubles the evidence behind it. **Drop 09-19 and the row reads 44.95 / 0.056, i.e. back
  over the line**; drop 09-18 instead and it reads 43.21 / 0.0010, essentially unmoved. So the
  re-crossing is still that ONE session's, and 09-18 — 127 rounds at a mild KPP 47.2 — did not
  confirm it and did not undo it. Saying which session carries a verdict is the same discipline
  as stating the margin. **At fifteen that no longer holds**: 10-03 is 146 rounds
  at KPP 37.0, the second-lowest reading, so drop 09-19 and the row reads 43.79 / 0.0015, and drop
  09-18 and 09-19 together and it reads 43.30 / 0.0013 — but **drop 09-19 and 10-03 together and it
  reads 44.95 / 0.056, back over the line**, the worst of every pair. So the crossing survives any
  single drop and rests on the two largest sessions jointly. That is a second large session
  pointing the same way as 09-19, not a new effect — the size of the effect has barely moved.
  **Sixteen leaves that shape intact and slightly weaker**: 10-09 is 102 rounds at KPP 48.0, close
  to chance, so it adds denominator without adding effect — drop 09-19 and the row reads
  44.18 / 0.0020, and drop 09-19 and 10-03 together and it reads 45.28 / 0.062, still the worst
  pair and still over the line. **Seventeen is the same again, from the other side of chance**:
  10-12 reads KPP 52.7 on 55 rounds, so it adds evidence AGAINST the effect — drop 09-19 and the
  row reads 44.59 / 0.0042, and drop 09-19 and 10-03 together it reads 45.68 / 0.11, still the
  only one of the 136 pairs over the line. **Eighteen does not move it**: 10-20 is 30 rounds at
  KPP 46.7 — drop 09-19 and the row reads 44.64 / 0.0039, and drop 09-19 and 10-03 together it
  reads 45.71 / 0.10, still the only one of the 153 pairs over the line. **Nineteen ends that
  dependence**: 10-22 is 63 rounds at KPP 35.7, the corpus low, so it adds effect as well as
  denominator — no single drop and none of the 171 pairs takes the row over the line (worst single
  drops 09-19, 7.1e-04, and 10-03, 5.7e-04). That is a third large-effect session, not a new
  effect; the AUC has moved 43.68 → 43.39.
* **The standing conclusion never depended on any of it.** The pooled AUC in the table above means
  the round winner had the *lower* KPP in a little over half of decided rounds — real, small, consistent with every per-session
  reading since 07-22, and **still not 「inverted」**, which would be over 6 points of AUC away. The
  coaching conclusion below (「KPP is flat — reported as a negative result」) has now survived this
  row crossing, uncrossing and crossing again, which is a better test of it than any single state.

TST's corrected p goes 2.0e-05 → 7.4e-07 → 6.0e-06 → 5.5e-06 → 5.3e-07 → 1.5e-07 → 3.2e-07 → **2.2e-07** across the last eight revisions,
and COMBO's 0.0028 → 4.3e-05 → 0.0018 → 0.0017 → 0.0041 → 0.0026 → **8.7e-04** — COMBO worse at fifteen because 10-03 read 44.9,
second-lowest in its column, and added evidence against the effect at the same time as it added
denominator, which is what 09-18's TST 50.0 did two revisions earlier. **At fifteen COMBO fell
back over the line without 09-18 (0.056); at sixteen the same drop reads 0.049**, so its crossing
is robust to dropping one session again on the letter and by a thousandth in fact — 10-09's 52.5
on 73 decided pairs is what moved it, and it is not a reason to call the row settled.
**At seventeen that thousandth is gone, and the row is weaker than it has been since it crossed**:
10-12's COMBO 46.4 (19-23 on 42 decided pairs) is evidence against the effect again, and now TWO
single drops take the row back over — without 09-18 it reads 53.45 / 0.095 and without 08-19
53.58 / 0.057 — and 30 of the 136 two-session drops do (worst: 08-19 + 09-18, 0.83). The crossing
survives on the full corpus and on nothing narrower; that is the 0.048 / 0.059 state KPP was in
at eleven and twelve, and it is to be read as a margin, not as a verdict about combos.
**At eighteen one of those two single drops goes back under**: 10-20's COMBO 58.3 (14 of 23) leans
with the effect, so without 08-19 the row reads 53.69 / 0.037 and without 09-18 53.57 / 0.063 — one
single drop over the line rather than two, and 25 of the 153 two-session drops (worst: 08-19 +
09-18, 0.58). Thirty rounds moved it; read that as the size of the margin, not as a recovery.
**At nineteen neither single drop takes it over**: 10-22's COMBO 58.7 (27 of 43) leans with the
effect again, so without 09-18 the row reads 0.024 and without 08-19 0.014, and 9 of the 171
two-session drops take it over (worst: 08-19 + 09-18, 0.25). Two sessions leaning with it in a row
is the same kind of margin as two against; it is still the row whose margin to watch.
TST remains a survivor by a wide margin either way; COMBO is the row whose margin to watch. The margins still travel with the claims —
which is the whole reason a row that got worse and a row that got better can sit side by side here
without either being news.

**PC STAYS ACROSS THE CORRECTION THRESHOLD, and at sixteen and seventeen no single session can
take it back over — which is exactly the state it was in at fourteen and lost at fifteen.** The AUC
series is 50.97 → 51.66 → 52.26 → 52.04 → 52.38 → 52.62 → 52.33 → 52.34 → 52.28 → 52.27 and the raw p has
gone 0.32 → 0.062 → 0.0085 → 0.013 → 0.0013 → 0.00014 → 3.1e-04 → 1.6e-04 → 1.6e-04 → **1.5e-04**
(0.000164, 0.000158, then 10-20's 3-2 on top), and at nineteen 52.42 / **4.8e-05** on 10-22's 15-8;
corrected, 8.1e-04 is under 0.05 by a factor of 60. Four things have to be read
with it:

* **The denominator is still tiny.** 274 decided of 1407 rounds — 81% of the corpus ties at zero;
  10-09 added 21, split 13-8, 10-12 7, split 4-3, 10-20 5, split 3-2, and 10-22 adds 23, split 15-8.
* **At nineteen it survives any single drop and fails three of the 171 pairs**, all three with
  09-19 in them and all three just over the line: 09-10 + 09-19 (0.054), 09-18 + 09-19 (0.053) and
  09-11 + 09-19 (0.052). The worst single drops are 09-19 (0.0078), 09-10 (0.0066) and 09-11
  (0.0063). The eighteen-session record follows, kept as measured.
* **At eighteen it survives any single drop and fails six of the 153 pairs.** The worst single
  drops are 09-19 (137/225, corrected 0.023), 09-10 (0.019) and 09-18 (0.018), and the
  six pairs over the line are 09-10 + 09-19 (125/211, 0.149), 09-18 + 09-19 (119/200, 0.148),
  09-11 + 09-19 (0.143), 09-10 + 09-18 (0.123), 09-10 + 09-11 and 09-11 + 09-18 (0.119 each) — the
  seventeen-session seven less 09-03 + 09-19, which 10-20's 3-2 pulls back under (0.049).
* **It survives any single drop and fails seven of the 136 pairs** (at seventeen; the sixteen-session
  record that follows is kept as measured). At seventeen the worst single drops are 09-19
  (134/220, corrected 0.026), 09-10 (0.022) and 09-18 (0.021), and the seven pairs over the line
  are 09-10 + 09-19 (122/206, 0.166) and 09-18 + 09-19 (116/195, 0.165), 09-11 + 09-19 (0.160),
  09-10 + 09-18 (0.137), 09-10 + 09-11 and 09-11 + 09-18 (0.132 each) and 09-03 + 09-19 (0.054) —
  the sixteen-session eight less 09-19 + 10-09, which 10-12's 4-3 pulls back under (0.048). At
  sixteen: **Drop 09-19 and the row is
  130/213, corrected 0.027 (the worst single drop); drop 09-18 and it is 131/214, corrected
  0.021.** Over all 120 two-session drops, EIGHT take it back over the line, the worst being
  09-10 + 09-19 (118/199, 0.179) and 09-18 + 09-19 (112/188, 0.178), then 09-11 + 09-19 (0.172),
  09-10 + 09-18 (0.148), 09-10 + 09-11 (0.143) — which holds neither large night — 09-11 + 09-18
  (0.143), 09-03 + 09-19 (0.058) and 09-19 + 10-09 (0.051). So the row is fragile to most
  pairings of its sessions with lopsided PC counts (09-10's 12-2 and 09-11's 13-3 among them),
  not to one pair; a revision of this bullet singled out 09-18 + 09-19 as the pair it 「rests on」,
  which an exhaustive re-derivation on 2026-10-09's pass showed to be one of eight and not the
  worst.
  At fourteen sessions neither single drop undid it (0.028 and 0.022); at fifteen 10-03's
  near-even 29 pairs took that away (without 09-19: 117/192, 0.051); at sixteen 10-09's 13-8
  gives it back, and at seventeen 10-12's 4-3 leaves it there. This is the 0.048 / 0.059 situation KPP was in at eleven and twelve sessions,
  and it is to be read the same way: a margin, not a verdict.
* **Two of those nights are CONSECUTIVE, and that is the caveat the arithmetic cannot supply** —
  scoped to the 09-18 / 09-19 pair, one example of the eight above.
  09-18 and 09-19 are two of the three largest sessions in the corpus and they are one day apart. Two
  measurements from adjacent nights are not two independent replications of anything — whatever
  was true of how these two were playing that week is common to both — so 「it reproduced」 is
  exactly the word to avoid. The narrow statement 「the row no longer falls over when any single
  session is removed」 was true at fourteen, false at fifteen and true again at sixteen and
  seventeen — a sentence that flips with each session is a margin being read as a property.
* **This document named PC as the row whose crossing would mean least, and that judgement is
  unchanged.** It is not evidence that perfect clears decide rounds. The 全消 section's own
  conclusion — the section refuses to print a rate because the per-player denominators are 2-18
  rounds — is unchanged and is the one to cite.

Read the column as what it is: a denominator so small that a handful of sessions swing its
uncorrected p by a factor of nearly forty in one direction, straight back, and then across a line
— and which at nineteen survives losing any one session (worst: without 09-19, 0.0078) but not
three of the 171 two-session drops (worst: 09-10 + 09-19, 0.054, then 09-18 + 09-19, 0.053).

**This table is one of the 冇第二份 class and says so**: no committed artefact re-derives it, so it
is hand-measured and must be re-measured when a session lands. Do not carry a cell forward.

**The p's in this table moved on 2026-09-03 for TWO reasons and only one of them is the new
session.** The AUCs are computed with ties counted as half over ALL rounds (the Mann-Whitney
convention); that reproduces every per-session figure published above, exactly, for all nine.
The p's are then `binom.test(wins, decided, 0.5)` — verified against R's own `binom.test` and an
independent exact implementation, which agree to every digit shown. The p's this table carried at
eight sessions did NOT match that test on the eight-session data (0.000316 against 0.00037,
0.000208 against 0.00025, 0.0097 against 0.011, 0.473 against 0.54), so they came from some other
computation. No verdict changes and no AUC moved, but the row that says which test produced a
number has to be true of the number beside it — which is the whole reason that sentence was added
in the first place. Re-derive both columns together whenever a session lands — at eighteen that
convention reproduces every per-session figure published above, exactly, and it also reproduces
every cell of the pooled table at SEVENTEEN sessions (AUC, decided count, raw p and corrected p
alike), which is the check worth running before trusting an eighteenth-session cell:
a probe that reproduces the previous revision's whole table is measuring the same thing it did.

COMBO's per-session series drifts upward, back, and up again — 41.1 · 51.0 · 62.5 · 55.7 · 57.0 ·
58.9 · **67.9** · 58.9 · 52.2 · 48.5 · 51.0 · **67.3** · 62.6 · 53.0 · 44.9 · 52.5 · 46.4 · 58.3 — so 45.0 was not *wrong* when
written. It was a
two-session figure that the document kept presenting as a corpus verdict, which is the same defect
as the 「70-89%」 donation figure below wearing a different disguise: **a bucket label is a claim
about the corpus even when the number under it is honest about its n.** The series fell for three
sessions from that 67.9 peak, spent two near 50, went back to 67.3 and has come down three times since, the third to 44.9 (10-03, second-lowest after 07-22's 41.1), 10-09 is back at 52.5 and 10-12 down
again at 46.4, third-lowest, and 10-20 back up at 58.3 on 23 decided pairs — so the 「drifting toward the line」 reading the pooled row carried for two revisions was itself a
two-session reading, and the series is the reason it should not have been extrapolated. KPP's
series is 38.6 · 42.0 · 42.2 ·
53.8 · 58.0 · 40.5 · 41.4 · 45.2 · 52.2 · 43.1 · **37.3** · 49.0 · 47.2 · **36.7** · 37.0 · 48.0 · 52.7 · 46.7 — below
chance in 14 of the 18 and
pooled below 50, and **distinguishable from chance after correction**, which is the state the
table above records and which this sentence contradicted for one revision while saying the
opposite three inches higher.
It crossed on 09-11 by two thousandths, uncrossed on 09-17 and re-crossed on 09-19; through all
three it is the same small
effect, and **it must still not be upgraded to "inverted"**, because that is over 6 points of AUC.
See the table above for the margin, which has to travel with the claim in every state.

(**Both series in that paragraph stood at twelve values for a revision after the thirteenth
session landed, and the KPP sentence beside them asserted the opposite of the table three inches
above it.** This is 冇第二份's eighth class in its purest form — a count over a list, where the
list is in the same document and the refutation is in the same section — and it is recorded here
rather than silently corrected because the previous revision's own prose says a session landing is
when to re-derive them. Neither series is gated; nothing but a reader re-counting the entries
against the session count will catch the next one.)

Coaching conclusions, cross-validated over nineteen sessions: **APP is the lever** — higher in
rounds
won than rounds lost in 38 of 38 player-sessions (the count was published as 「14 of 14」 for four
sessions after it stopped being true; it is two per session, so re-derive it as 2× the session
count rather than carrying it), though the *size* of that separation is not stable and does not
settle. **Its series has ONE home in this document and it is not here** — the (yachi, pinglamb)
pair series further down is the live copy, and a second copy of yachi's half used to sit in this
sentence, went stale at seven values for five sessions, was refreshed to twelve, and then stood at
twelve while the pair series below it held thirteen. Two copies of one quantity is a defect on
sight even while both are correct, which is the rule that removed this one; read 08-14's +7.2% as
the outlier of that series at its own site. **DS matters** in 9 of 10
player-sessions through 08-09 — deliberately left scoped to the session it was measured at rather
than restated at eighteen; **KPP is flat** (0–3%) — reported as a negative result, a conclusion that
has now survived the pooled row crossing, uncrossing and re-crossing the correction threshold. When adding
a column or a claim, run `pipeline/claims/equiv.py` or the AUC probe rather than assuming a stat is
informative.

**08-09 splits APP the other way, and that is the finding of the fifth session.** Every earlier
session had one player ahead in *both* regimes by a similar margin — a style difference. Pool
attack over pieces after splitting the 50 rounds by who won them and the two regimes come
apart: won .6738 vs .6862 (+1.8%), lost .5124 vs .6425 (+25.4%) [C002]。個 won-gap 得一局撐住
（留一局：抽走 m2r5，數字變 +4.26%，即係郁 2.41 pp），50 局入面排第一，係第二大嗰局嘅
1.38 倍——所以「+1.8，成個 corpus 最細」講得，「兩邊贏嘅局打成平手」講唔得。yachi's won-round rate
is above pinglamb's *lost*-round rate [C003]. The rank test says this is not a variance
artefact — **both p's two-sided**: over losing rounds P(yachi > pinglamb) = 0.138, permutation
p = 1e-5; over winning rounds 0.464, p = 0.68 — and it survives dropping the three near-zero
rounds. (The winning-rounds figure was published as `p = 0.34` for months, which is the *one*-sided
value beside a two-sided one; the two-sided is exactly 2× it. Nothing here compares p's across the
two regimes, so the conclusion never moved — but a mixed convention in one sentence is how a
comparison across them would go wrong silently.) The per-session won-gap runs +5.8 · +10.8 · +5.9 ·
+7.9 · **+1.8**, the lost-gap +12.8 · +7.3 · +6.0 · +6.1 · **+25.4**。十個 session 嘅全套系列喺
下面；其中 09-03 個 won-gap 一樣得一局撐住
（留一局：抽走 m3r6，數字變 +2.89%，即係郁 4.76 pp），
佢 rel 0.622 喺 corpus 排第六，但**最大嗰局係第二大嗰局嘅 2.57 倍,呢個係全 corpus 最集中
嘅一次**（下一個係 08-14 嘅 1.72）—— 脆喺得一局孭住，唔係脆喺個數細。而 09-10 個 lost-gap
都係得一局撐住（留一局：抽走 m8r4，數字變 +3.86%，即係郁 2.60 pp），
佢 rel 2.081 喺 corpus 排第三——同 08-14 嗰個 +1.78 一樣，「地板撞埋」呢句嘅**尺寸**係一局話事，
**方向**唔係。09-18 個 lost-gap 都一樣得一局撐住
（留一局：抽走 m1r7，數字變 +0.58%，即係郁 0.95 pp），
rel 0.618 排第九——但佢同上面兩個唔同：抽走嗰局個差距係**更窄**，唔係更闊，
所以「地板撞埋」企得更穩，散嘅淨係 +1.54 呢個數字。10-20 係第一晚兩個數都要 annotation：
won-gap（留一局：抽走 m4r8，數字變 +11.74%，即係郁 4.50 pp），
lost-gap（留一局：抽走 m2r1，數字變 -1.87%，即係郁 3.15 pp）——後者連正負號都反轉，
所以嗰晚嘅「地板撞埋」連方向都係一局話事。Two consequences worth
knowing before writing another report:

- **The volume route is not a law.** 08-01's headline was that 326 extra pieces bought back a
  7% efficiency gap to within 32 lines. 08-09 ran the same route into 382 extra pieces and
  **271 fewer** lines of attack, 8%+ of pinglamb's total [C004] — because buying it back
  requires the per-piece value not to collapse, and here it collapsed on one side only.
  (Seven sessions later this has a mechanism and a number; see 「個 shortfall 先係話事嗰個」 below.
  08-09 had the worst shortfall in the corpus when this was written, which is why it was the worst
  outcome; 09-17's and 09-11's are larger now, and the table there is the live ranking.)
- **Advice taken can leave the score wider.** 08-01 flagged that 6 of 8 topouts were yachi's.
  08-09 has 4 topouts, all pinglamb's, yachi none [C006] — and the match score went 4:3 to 0:6.
  A metric moving the right way is not the same as the metric that decides. **08-19 is the second
  instance and it runs the other way** — 08-14's 11-of-13 did not persist, the split came back to
  4:3, and the series still went 4:7 → 3:7. Two independent instances from opposite directions, so
  this is a pattern in the corpus and not one night's anecdote.

**08-14 is 08-09's mirror, and that pair is why the split must be re-derived every session.**
Same decomposition, opposite answer: won .6032 vs .7174 (+18.9%), lost .5629 vs .5729 (+1.8%)
[C002]. The floors have met; the ceilings have not. 但個 lost-gap 得一局撐住
（留一局：抽走 m11r2，數字變 +4.65%，即係郁 2.87 pp），84 局入面排第一，係第二大嗰局嘅
1.72 倍——「地板撞埋」係成晚嘅講法,「差 1.8 pp」唔係。

**08-19 is the control on that pair, and it says the swing was an excursion.** Same decomposition
again: won .6803 vs .7226 (+4.23 pp, +6.22%), lost .5528 vs .6140 (+6.11 pp, +11.05%), session
gap +7.50 pp (112.4%) — which is 07-22's shape almost exactly (+5.8/+12.8 against +6.2/+11.1):
ceilings close,
floors apart. **08-25 then reproduces that shape a third time** — won .6417 vs .6734 (+3.17 pp,
+4.95%), lost .5211 vs .6122 (+9.11 pp, +17.48%), session gap +6.87 pp (111.9%) — with the widest
floor gap in the corpus bar 08-09's. **09-03 then lands level in both regimes** — won .6329 vs
.6814 (+4.85 pp, +7.66%), lost .5303 vs .5509 (+2.06 pp, +3.88%), session gap +5.48 pp (109.5%).
個 won-gap 得一局撐住（留一局：抽走 m3r6，數字變 +2.89%，即係郁 4.76 pp），46 局入面排第一，
係第二大嗰局嘅 2.57 倍，而 2.57 呢個比例係全 corpus 最高。m3r6 係嗰晚最長（約 210 秒）同清行最多
（198 行）嗰局，所以佢一局嘅 pooled 粒數重過任何一局。抽走佢之後 won-gap 剩返 +2.89% 對 lost-gap
+3.88%，即係「天花板爭得多過地板」係嗰一局講嘅,「兩邊都爭得唔多」先係成晚企得住嘅講法。
（lost-gap 自己都唔算硬淨，rel 0.485，喺 THRESHOLD 之下所以冇 annotation，但兩邊都指向同一個
「打成平手」嘅讀法。）**09-10 then lands in 08-14's shape rather than beside 09-03** — won .6271
vs .7022 (+7.52 pp, +11.99%), lost .5317 vs .5384 (+0.67 pp, +1.25%), session gap +3.86 pp
(106.6%) [C002][C004]。個 lost-gap 得一局撐住
（留一局：抽走 m8r4，數字變 +3.86%，即係郁 2.60 pp），
`rel` 2.081 喺 corpus 排第三，而且 +1.25% 本身係全 corpus 最窄嘅地板差距——所以
「地板貼到實」呢個講法企唔企得穩，同「差 1.25 pp」呢個數字企唔企得穩，係兩件事：方向企得穩，
個尺寸企唔穩。**09-11 is the third session to lean mirror-wards, by far the mildest of them, and
the only one of the three that needs no caveat** — won .6371 vs .6996 (+6.25 pp, +9.82%), lost .5479 vs .5734 (+2.55 pp, +4.65%), session
gap +7.21 pp (112.4%) [C002][C004]。冇一個數要 annotation：最脆嗰個係 lost-gap 嘅 `rel` 0.447，
喺 THRESHOLD 之下，不過亦係全 corpus 最貼門檻而又過到嘅一個。**09-17 is the session the
previous eleven said does not happen: BOTH gaps large** — won .6093 vs .6981 (+8.88 pp, +14.57%),
lost .5120 vs .5920 (+8.00 pp, +15.63%), session gap +11.04 pp (120.1%) [C002][C004]。兩個數都冇要
annotation，而呢一次「冇加註」本身就係主張嘅一部分：won-gap `rel` 0.107（而且係全 corpus 最平嘅
x2nd，1.02 倍，即係冇一局突出得過其他），lost-gap `rel` 0.226，兩個都唔夠 THRESHOLD 一半，
正負號都唔變。**09-19 puts both back in the middle, and it is the answer to whether 09-17 was a
class** — won .6478 vs .6856 (+3.78 pp, +5.84%), lost .5418 vs .5765 (+3.46 pp, +6.39%), session
gap +6.49 pp (111.2%) [C002][C004]。兩個數喺自己嗰欄分別排第十一同第七，
won/lost 比率 0.91，即係「兩邊都爭得唔多」嗰一類，同 07-24、07-28、08-01 一齊。
冇一個數要 annotation，而呢一場係全 corpus 最靜嗰場：五個數最高嘅 `rel` 得 0.150，
比 09-17 嗰 0.226 仲低（點解唔可以讀成「局數多就穩陣」，見下面）。**09-18 係第三次出現
「鏡像」嗰個樣，而佢帶嚟嘅係一個之前十三晚都未出現過嘅嘢** — won .6431 vs .6967 (+5.36 pp,
+8.33%), lost .5447 vs .5531 (+0.84 pp, +1.54%), session gap +5.23 pp (108.9%) [C002][C004]。
won-gap 喺自己嗰欄排第六，lost-gap 排第十三，即係全 corpus 第二窄，僅次於 09-10 嗰 +1.25%；
won/lost 比率 5.40，坐喺「真鏡像」（08-14 嘅 10.6、09-10 嘅 9.6）同「淡鏡像」（09-03 1.98、
09-11 2.11）中間。個 lost-gap 要 annotation（`rel` 0.618，過咗 THRESHOLD）
（留一局：抽走 m1r7，數字變 +0.58%，即係郁 0.95 pp），
**但佢郁嘅方向同 08-14、09-10 啱啱相反：抽走嗰局之後個差距係更窄，唔係更闊。**
08-14 抽走 m11r2 由 +1.78 變 +4.65，09-10 抽走 m8r4 由 +1.25 變 +3.86 ——兩次都係「地板撞埋」
呢個講法散咗；今次係「地板撞埋」企得更穩，散嘅淨係 +1.54 呢個數字。m1r7 係 pinglamb 輸嗰局，
佢喺嗰局用 151 粒方塊打出 .7086 每粒攻擊。即係話 `rel` 唔分方向，而呢一晚就係話俾你聽
唔分方向嘅代價喺邊：**一個「脆」嘅數字可以係脆到令個講法更啱，唔一定係脆到令個講法唔啱。**
**10-03 係「兩邊都爭得唔多」嗰一類嘅第五個** — won .6524 vs .6830 (+3.07 pp, +4.70%),
lost .5371 vs .5684 (+3.13 pp, +5.83%), session gap +7.24% [C002][C004]。十五個 session 嗰陣，won-gap 喺自己嗰欄
排第十四（當時中位數 +7.66，淨係 08-09 嘅 +1.85 細過佢），lost-gap 排第十（當時中位數 +6.05），
won/lost 比率 0.81，屬於同 07-24、07-28、08-01、09-19 一齊嘅「兩邊都爭得唔多」一類；兩個數都喺中位數之下，呢一點成類淨係 07-28 同佢一樣。冇一個數要
annotation：五個數最高嘅 `rel` 係 0.158（won-gap，抽走 m8r3），喺 09-19 嘅 0.150 之後係全 corpus
第二靜。**10-09 兩個數都喺中位數之上，但唔係 09-17 嗰種「兩邊都闊」** — won .6716 vs .7537
(+8.21 pp, +12.23%), lost .5599 vs .6015 (+4.16 pp, +7.43%), session gap +11.52% [C002][C004]。
十六個 session 排落去，won-gap 喺自己嗰欄排第三（淨係 08-14 嘅 +18.93 同 09-17 嘅 +14.57 大過佢），
lost-gap 排第六（當時兩欄嘅中位數係 +7.78 同 +6.22；十七個 session 係第三同第七）。won/lost 比率 1.65。09-17 係第二同第三，呢晚係第三同第六——lost-gap 只係高過中位數
1.2 點，所以佢最近嘅鄰居唔係 09-17，係 07-24（+10.79 / +7.26，比率 1.49，十六個 session 排第五
同第七，兩個都喺中位數之上）。冇一個 regime 數要 annotation：won-gap `rel` 0.134，lost-gap 0.184，
兩個都係抽走 m3r8；呢晚要 annotation 嘅係攻擊總差額，見 shortfall 嗰節。**10-12 係「天花板近、
地板遠」嗰一類嘅第四個** — won .6814 vs .7301 (+4.86 pp, +7.14%), lost .5402 vs .6237 (+8.34 pp,
+15.44%), session gap +13.50% [C002][C004]。十七個 session 排落去，won-gap 喺自己嗰欄排第十，
lost-gap 排第四（淨係 08-09 嘅 +25.38、08-25 嘅 +17.48 同 09-17 嘅 +15.63 大過佢）；**兩欄嘅中位數
而家係 +7.66 同 +6.39**（呢對數喺呢度得一個屋企，每加一個 session 都要重計；十七係單數，所以兩個
中位數都啱啱係某一晚自己嘅數——won 係 09-03，lost 係 09-19）。won/lost 比率 0.46，同 07-22 嘅 0.45
幾乎一樣，所以佢同 07-22、08-19、08-25 一齊。冇一個 regime 數要 annotation：won-gap `rel` 0.318
（抽走 m5r7），lost-gap `rel` 0.156（抽走 m8r5），兩個都唔夠 THRESHOLD。**10-20 係「鏡像」嗰個樣
嘅第四個，亦係兩個數都要 annotation 嘅第一晚** — won-gap +7.23%
（留一局：抽走 m4r8，數字變 +11.74%，即係郁 4.50 pp），
lost-gap +1.27%
（留一局：抽走 m2r1，數字變 -1.87%，即係郁 3.15 pp），
session gap +6.73% [C002][C004]。十八個 session 排落去，won-gap 喺自己嗰欄排第十，lost-gap 排第十七
（淨係 09-10 嘅 +1.25 窄過佢）；十八係雙數，**兩欄嘅中位數而家大約係 +7.45 同 +6.25**（中間兩個數
嘅平均，唔再係某一晚自己嘅數；上面 10-12 嗰行嘅 +7.66 / +6.39 係十七個 session 嘅紀錄）。won/lost
比率大約 5.7，同 09-18 嘅 5.40 最近。**但呢個「鏡像」嘅方向本身都企唔穩**：抽走 m2r1（pinglamb 輸嗰局，
用 144 粒打出 .7361 每粒攻擊），lost-gap 連正負號都反轉，即係「地板撞埋」呢句喺 30 局入面係一局話事
——同 08-14、09-10 一樣係闊咗嗰邊，不過今次闊到過咗零。won-gap 嘅 m4r8 係成晚最長嗰局（約 233 秒），
pinglamb 用 336 粒、.5923 每粒贏落嚟，佔佢贏局粒數兩成。30 局係 corpus 最細嘅一晚，一局佔嘅份量
係最大，所以呢兩個 annotation 係預期之內，唔係發現。
The nineteen-session series now read

    won-gap    +5.8  +10.8  +5.9  +7.9   +1.8  +18.9   +6.2   +4.9   +7.7  +12.0   +9.8  +14.6   +8.3   +5.8   +4.7  +12.2   +7.1   +7.2  +15.2
    lost-gap  +12.8   +7.3  +6.0  +6.1  +25.4   +1.8  +11.1  +17.5   +3.9   +1.3   +4.6  +15.6   +1.5   +6.4   +5.8   +7.4  +15.4   +1.3  +20.1

(**Units, because this paragraph mixes two and one line used to get them wrong.** The two series
rows above and every 「+X% / +X pp」 pair above quote the RATIO gap — 100·(pinglamb's rate /
yachi's rate) − 100 — which is what the C002-family claims pin; the 「pp」 figure beside it is the
plain difference of the two rates. 08-19's line published its ratio figures labelled 「pp」 for
several sessions, so its +6.22 and +11.05 read as rates-difference when they are ratio gaps; it is
corrected above. The rows are ratio gaps throughout.)

so **the 17-point swing between 08-09 and 08-14 was a two-session excursion, not a trend in either
direction**, and the split returned to where the corpus started — three times by 08-25 and a
fourth on 10-12, which is what turns 「excursion」 from a reading into the default one. Read 09-03's column with its
leave-one-out caveat — one round takes it from +7.7 to +2.9.

**A first draft of this section said 09-11 falsified 「both gaps are never large together」. It
does not, and the check that caught it is the one worth keeping.** +9.8/+4.6 reads like two large
gaps until both are placed in their own columns: the won-gap ranks 4th of eleven and the lost-gap
ranks **8th of eleven**, i.e. below its column's median of +6.1. The ratio between them is 2.11,
which puts this session with 09-03 (1.98) and nowhere near 08-14 (10.6) or 09-10 (9.6). It is a
mild mirror, and the ten-session sentence survives its eleventh test.

**Kept because 09-17 then did falsify it (three paragraphs down), and the two cases are worth
reading side by side.** The
draft above was wrong about 09-11 and the sentence was right about 09-11; one session later the
same sentence is false, and the thing that settled both was the same ranking. A reader who
concluded from this paragraph that 「both gaps large」 simply never happens would have been reading
a record of eleven measurements as a law — which is precisely what the paragraph warns against two
sentences later. The check is what survives here, not the finding.

The general form, because this is the third time the two-row table has invited it: **a pair of
numbers cannot be read as 「both large」 without ranking each against ITS OWN column.** +4.6 looks
large beside +1.3 and +1.8, which are the two values a reader of the mirror paragraph has just
been looking at — and those are the two smallest in the corpus. Rank before you characterise.

**Read the two rows as rows, not as a pair of trends.** Four of the nineteen sessions (07-22,
08-19, 08-25 and 10-12) sit in the ceilings-close/floors-apart shape, **four are its mirror (08-14, 09-10,
09-18 and 10-20 — the last on a lost-gap whose SIGN one round carries, see its line above)**, one is an extreme version of the first (08-09), **five are roughly level (07-24,
07-28, 08-01, 09-19 and 10-03)**, **two are mild mirrors (09-03 and 09-11)** at won/lost ratios of 1.98
and 2.11
against the true mirrors' 10.6 and 9.6, **two share a shape of their own (09-17 and 10-22): both apart**, and
**one (10-09) fits no class cleanly**: both its gaps sit above their column medians (ranks 3 and
6 at sixteen, 3 and 7 at seventeen), at a won/lost ratio of 1.65 that falls between 07-24's 1.49
and the mild mirrors' 1.98. Its nearest neighbour is 07-24, which this list files as level — and
at sixteen and seventeen sessions 07-24's pair is above both medians too (ranks 5 and 7, then 5
and 8), so that filing is the one to hold most loosely. 10-12's won/lost ratio of 0.46 sits beside
07-22's 0.45, and its won-gap is below its median and its lost-gap fourth of its column, which is
the class's defining property; it is filed there without a caveat.
09-03 reads as level on the ROBUST reading rather than on its printed pair: its won-gap is the one
round m3r6 carries, and without that round it is +2.9/+3.9. 09-11 has no such caveat, so it is the
one unambiguous mild mirror the corpus holds. 09-19 (won/lost 0.91) and 10-03 (0.81) are the
level class's two largest members by a factor of two over the next.

**09-18 joins the mirror class and does not sit cleanly inside it, which is worth one sentence
and no more.** Its won/lost ratio is 5.40, against 10.6 and 9.6 for the other two mirrors and
1.98 and 2.11 for the mild pair — so on the measure that separates those two groups it falls
between them, roughly halfway on a log scale. Filed with the mirrors because its lost-gap is the
corpus's second-narrowest and that is the property the class is about; **a reader who needs the
groups to be crisp should note that this is the session which shows they are not.** The ratio is a
continuum and the four-way split is a reading aid, not a taxonomy the data supports.

**「Both gaps large together」 HAPPENED, on 2026-09-17, after eleven sessions in which it did not —
and the sentence it replaces was correct every time it was written.** The rule for reading the pair
is unchanged and is what establishes this: rank each figure against ITS OWN column. 09-17's won-gap
is **2nd** of its column and its lost-gap **3rd** — re-ranked at seventeen sessions, and unmoved
by the five since it landed; at nineteen 10-22 takes second in both columns (+15.17 and +20.13),
pushing 09-17 to 3rd and 4th, so 「both large」 now has two instances and 10-22 is the larger. **The column medians have ONE home, the 10-12 line of the
regime paragraph above**; the 10-03 and 10-09 lines' 「當時中位數」 pairs are labelled there as
fifteen- and sixteen-session values and are records, not the live median. They move every session, and the fourteen-session pair that
used to sit here had already gone stale beside it. Through fifteen sessions no earlier session had
both above the median by more than a hair — 07-24's +10.8/+7.3 was ranks 4 and 6 at fourteen
sessions, with its second figure about 1.0 over that session-count's median (+7.26 against
+6.22; this clause read 「a tenth of a point over」 until 2026-10-09's pass re-derived it, a stale
figure of the eighth class), which is why it was named the closest case rather than an instance. **At sixteen that sentence no longer holds as
written**: 10-09 has both above (ranks 3 and 6) and 07-24 does too (ranks 5 and 7, its lost-gap
1.0 over the median — and it was already 1.2 over the fifteen-session median of +6.05, which the
parenthesis that stood here at fifteen did not say). **Seventeen leaves both above**: 10-09 at
ranks 3 and 7, 07-24 at 5 and 8, its lost-gap 0.87 over the seventeen-session median of +6.39 —
and 10-12, the session that moved the medians, is not a candidate (rank 10 on its won-gap). Neither reaches
09-17's ranks, which is the distinction to keep: 「above both medians」 and 「both large」 are not the
same claim, and the first is a property a median-hugging pair can acquire when a session lands.

Four things this does and does not change:

* **It does not make 09-17 「the most balanced session」.** Its won/lost ratio is 0.93; 07-28's is
  0.98, closer to 1. The difference is the LEVEL, not the balance — 07-28 is +5.9/+6.0 with both
  figures BELOW their medians, which is the 「roughly level」 class. Balance at small values and
  balance at large values are opposite readings, and the ratio alone cannot tell them apart.
* **It does not weaken the standing rule; it is the rule's sharpest instance yet.** Even here,
  the *session-level* APP gap (110.0% on 08-14, 118.1% on 08-09, 112.4% on 08-19, 106.6% on 09-10,
  112.4% on 09-11, **120.1% on 09-17**) still tells you nothing about which regime carries it —
  08-19 and 09-11 share 112.4% to one decimal and split it +6.2/+11.1 against +9.8/+4.6, and
  09-17's record 120.1% splits almost evenly. Neither does the previous session's decomposition:
  09-11 is a mild mirror and 09-17 is not a mirror at all.
* **It retires an absence, not a mechanism.** Eleven sessions of 「this does not happen」 was a
  record of what had been measured, and one session ends it. Nothing here explains WHY the two
  regimes came apart together, and nothing should be written as though it did.
* **A twelfth session cannot make 09-17 a class.** It is one instance. The three-shape grouping
  above took three sessions to earn the word 「default」 for 「excursion」; this has one.

**The two sessions since are the test that sentence asked for, and 09-17 stays one instance.**
09-19's two gaps are +5.84 and +6.39, ranks 11 and 7 of fourteen, and 09-18's are +8.33 and +1.54,
ranks 6 and 13 (at fifteen: 11 and 7, and 6 and 14; at sixteen: 12 and 8, and 7 and 15; at
seventeen: 13 and 9, and 7 and 16, 09-19's lost-gap now BEING the median rather than above it) — so neither has both above its own median — the 「roughly level」 class and not a repeat. Three things follow and the third is the
one to keep. It does not make 09-17 wrong: that session measured what it measured. It does not
make 「both large」 rare in any quantified sense, because one non-repeat is not a rate. And **it is
the best-powered instance of the level class the corpus holds** — 150 rounds against 07-28's 64,
and 10-03 then added a second at 146 —
which matters because the level class has always been the one most easily produced by small n, and
this is the first time it has been produced by a session that cannot be dismissed that way.

**The mirror shape is the one with repeats, and it now has three.** 08-14's
lost-gap was +1.78 and rested on m11r2 (`rel` 1.615); 09-10's is +1.25 and rests on m8r4 (`rel`
2.081); **09-18's is +1.54 and rests on m1r7 (`rel` 0.618)**. Three sessions, the same shape, the
same fragility, the same rhetorical move
(「the floors have met」) — and in all three the SIZE is one round's and the DIRECTION is not.

**What the third instance ADDS is that the fragility does not always point the same way, and two
instances could not have shown it.** Dropping the influential round widens 08-14's gap (+1.78 →
+4.65) and 09-10's (+1.25 → +3.86), so in both the caveat undercuts the sentence beside it.
Dropping 09-18's NARROWS it (+1.54 → +0.59), so there the caveat supports the sentence. The
`rel` statistic is a magnitude over a magnitude and cannot tell those apart — which is correct
for what it is built to do, since either way the printed figure is one round's — but it means
**「this figure is fragile」 and 「this reading might not hold」 are different claims, and only the
first is what crossing THRESHOLD establishes.** Two instances pointing the same way made them
look like one claim for two sessions.

What all three DO reproduce is the *caveat*, which is worth more than a reproduction of the
number. **09-11 is the control the group needed**: it has the same figure (a lost-gap) at a
comfortable
+4.7 with `rel` 0.447, i.e. the fragility travels with the gap being NEAR ZERO and not with the
session or the shape. Four of the five most fragile figures the corpus has measured sit on values
near zero, which is what `check_loo`'s own header says is correctly the most fragile kind.

Said within a player, 08-14 has pinglamb separating his own won and lost rounds by +25.2% and yachi
by only +7.2% [C003]. **That was a one-night state, not a standing property of either player.** The
(yachi, pinglamb) separation series runs (24.9, 17.1) (17.4, 21.3) (23.2, 23.1) (15.9, 17.9)
(31.5, 6.8) **(7.2, 25.2)** (23.1, 17.7) (23.1, 10.0) (19.3, 23.7) **(17.9, 30.4)** (16.3, 22.0)
(19.0, 17.9) **(18.1, 26.0)** **(19.6, 18.9)** **(21.5, 20.2)** **(19.9, 25.3)** **(26.1, 17.1)** **(12.4, 19.0)** **(21.2, 16.2)** — so 08-14 is the only session where the
separation is effectively one player's alone, and yachi's +7.2 there is the outlier of his own
series, not a level he settled at; on 08-19 he is back to +23.05% against pinglamb's +17.70%, and
on 08-25 he sits at +23.14% against pinglamb's **+10.00%**, the second-narrowest of pinglamb's
eight after 08-09's 6.8. **09-03 ends that run at two**: yachi +19.3% against pinglamb's +23.7%,
so the wider of the two is pinglamb again; 09-10 (17.9 against 30.4) and 09-11 (16.3 against 22.0)
made it three consecutive sessions with pinglamb wider. **09-17 ends THAT run at three**: yachi
+19.0% against pinglamb's +17.9%. 09-18 goes back to pinglamb (18.1 against 26.0) and 09-19 to
yachi (19.6 against 18.9), so the count over
the fourteen was **seven each**; 10-03 goes to yachi (21.5 against 20.2, 1.3 points apart), so over the
fifteen it was **eight yachi, seven pinglamb**; 10-09 goes to pinglamb (19.9 against 25.3 [C003],
5.4 points apart, his third-widest of sixteen after 09-10's 30.4 and 09-18's 26.0 and a tenth past
08-14's 25.2), so over the sixteen it was **eight each**; 10-12 goes to yachi (26.1 against 17.1
[C003], 9.1 points apart, HIS second-widest of seventeen after 08-09's 31.5 and the third-widest of
the thirty-four player-sessions), so over the seventeen it was **nine yachi, eight pinglamb**;
10-20 goes to pinglamb (12.36 against 18.97 [C003], 6.6 points apart — and yachi's 12.36 is the
second-narrowest of his eighteen, after 08-14's 7.2, on a 30-round night), so over the eighteen it
was **nine each**; 10-22 goes to yachi (21.20 against 16.20 [C003], 5.0 points apart), so over the
nineteen it is **ten yachi, nine pinglamb** — re-derived from the series above rather than carried.
The negative result reads exactly as it did at seven each.

**09-19's entry is the SECOND-closest pair the column has produced (0.62 points apart, behind
07-28's 0.11) and it is the one the corpus can least dismiss**, because it sits on 150 rounds
against 07-28's 64. A first draft of this sentence called it the closest and named 07-28's
(23.2, 23.1) as the previous closest in the same breath — 23.19 against 23.08 is 0.11 apart, so
the sentence contradicted its own example. That is 冇第二份's eighth class exactly: a superlative
standing next to the data that refutes it, in a paragraph whose series is printed three lines
above. Note what the corrected version does NOT license either: the column's two extremes are
24.7 points apart and belong to different players two sessions apart, so a near-tie at the
largest n is one more reading and not a convergence. Written as a count, never as a trend.

**Both counts in the sentence that stood here were wrong, and they are worth recording rather than
just fixing.** It read 「09-10 makes it three in a row … Three of ten with pinglamb wider」. At ten
sessions the run was TWO (08-25 has yachi wider, so 09-03 and 09-10 are the run) and the total was
FIVE of ten, not three — both readable straight off the series printed three lines above, which is
exactly why this is the 冇第二份 class rather than a typo: the series is right there, nothing
re-derives the counts from it, and a wrong count beside a right series reads like a summary of it.
The rule 「a marked fragment's neighbours move with it」 has a sibling here: **a count derived from
a list in the same paragraph must be re-derived from that list, not carried**.

Nine of nineteen with pinglamb wider (re-derived from the series above; this read 「Six of twelve」 for four sessions after it stopped being true) is not a pattern to act on either, and the run of three ENDING
immediately is the reason to say so out loud rather than the reason to act: the column's two
extremes belong to different players, and both runs the corpus has recorded (two, then three) were
written up as counts rather than trends and then ended on the next session.
**What IS a corpus record is pinglamb's 30.4 on 09-10**: his own high, past his
25.2 on 08-14, and the second-widest of the thirty-six player-sessions behind yachi's 31.5 on
08-09 —
so the two extremes of this column belong to different players two sessions apart in the ordering,
which is the clearest statement available that it is a night's state and not a trait. Likewise his
won-round rate, which had sat in a .657–.674 band for five sessions and fell to .6032 on 08-14, is
.6803 on 08-19. Read the 08-14 figures in this block as that night's, not as a trajectory.
His ceiling on 08-14 sat nearer pinglamb's floor (+5.3%) than pinglamb's ceiling (−15.9%) [C004].

Three consequences:

- **The volume route failed a second time.** 415 more pieces, 206 less attack, over 4% of
  pinglamb's total [C005] — after 08-09's 382 for −271. ~~Two runs, two failures; 08-01's success
  is the outlier, not the rule.~~ **That reading is wrong and 08-19 is what falsifies it** — the
  route is not unreliable, it is *bounded*, and the bound is arithmetic. See below.
- **The topout column swung from one extreme to the other in one session.** 11 of 13 are yachi's
  [C006] — his worst — where 08-09 had all 4 on pinglamb and yachi none. A single night's death
  tally is not a trend, and 08-19 confirms it did not become one: **4:3, the most balanced split
  of any session**, at 10.0% of rounds — then 08-25 swings it back to **9:4 at 17.8%, the highest
  RATE of the eight** and yachi's second-worst tally. What made 08-14's worth acting on was that it
  moved *with*
  the piece surplus, i.e. there was a mechanism; what 08-19 showed is that acting on it moved the
  tally and **not the series**, which went 4:7 → 3:7. **08-25 is the third data point and it settles
  the column: this is a quantity that swings hard every session and predicts nothing.** Eighteen
  values now (the series below — re-count it there, this read 「Twelve」 for four sessions), from
  0:2 to 15:9 in raw tallies and 6.7% to 23.5% as a rate, with no run of three consecutive moves
  in the same direction in the rate — read a night's tally as
  that night's, and stop reading a trend into it. 09-03 sits one apart (3:4, [C006]) right after
  the highest rate — close, but NOT the flattest: 07-24's 4:4 is the corpus's only even split, and
  07-28 and 08-19 are one apart too. 09-10 is one apart as well (5:6, [C006]) and is the first
  session where **pinglamb** has the higher tally on a one-apart split. **10-12's 4:4 [C006] is the
  second even split**, after 07-24's, so 「the corpus's only even split」 above is a nine-session
  sentence, kept as written and true of the corpus it was written about.

  **ONE series, printed once** — this bullet carried two copies for a session, a stale ten-value
  one mid-paragraph and a live eleven-value one below it, which is the 冇第二份 class occurring
  inside a single bullet. It is
  y:p = 8:3 · 4:4 · 5:4 · 6:2 · 0:4 · 11:2 · 4:3 · 9:4 · 3:4 · 5:6 · **7:5** · 4:2 · **11:12** ·
  **15:9** · **14:13** · **7:5** · **4:4** · **0:2** · **5:1**, at
  13.9 · 16.0 · 14.1 · 15.1 · 8.0 · 15.5 · 10.0 · 17.8 · 15.2 · 16.9 · **23.5** · 12.2 · **18.1** ·
  16.0 · **18.5** · **11.8** · **14.5** · **6.7** · **9.5** % of
  rounds. **10-22's 9.5% (6 of 63 [C006]) is the third-lowest rate of the nineteen**, after 10-20's
  6.7 and 08-09's 8.0; 5 of the 6 are yachi's.
  **10-20's 6.7% (2 of 30 [C006]) is the new LOWEST rate**, past 08-09's 8.0, and its 0:2 is the
  second night yachi topped out in no round, after 08-09's 0:4 — on 30 rounds, i.e. two topouts.
  Every rank below that names 「lowest」 moved by one place because of it.
  09-11's 23.5% is still the highest RATE of the eighteen, by 5.0 points over 10-03's 18.5,
  and **10-09's 11.8% (12 of 102 [C006]) was the THIRD-lowest at sixteen and seventeen** — after
  08-09's 8.0 and 08-19's 10.0 — which made **09-17's 12.2% the fourth-lowest** (fourth and fifth at
  eighteen, behind 10-20's 6.7); it was third through fifteen sessions, and
  the 「third」 that stood here is exactly the rank a new session moves without touching the session
  it names. 10-12's 14.5% (8 of 55) was seventh-lowest at seventeen and moved none of those ranks. (It read
  「second-LOWEST」 for two sessions before that and
  was wrong when written: the list refuting it was already in this bullet, which is 冇第二份's
  eighth class exactly — a rank taken over a list the reader is looking at.) Read the column
  exactly as this bullet has said
  for four sessions: the rate swings and the column predicts nothing, which is precisely why
  neither a corpus high nor a near-low in it is news.

  **09-18 is the second one-apart split with pinglamb on the higher side**, after 09-10's 5:6 —
  and at 18.1% it was the second-highest rate in the corpus (third since 10-03's 18.5), on a night
  the series was not close.
  Both facts are recorded and neither is read: a column that predicts nothing does not start
  predicting because its extremes land on interesting nights.

  **09-19 is the sharpest illustration this bullet has of why the RATE is what is printed.** Its
  15:9 is 24 topouts, and **15 is the largest raw tally any player has recorded**, past 08-14's
  eleven — but it is 15 of 150 rounds, i.e. 10.0% for yachi against 13.1% on 08-14, so the raw
  record and the rate disagree about which was the worse night for him. The session's own 16.0%
  ties 07-24 for mid-table and takes no extreme at all. A reader who took 「yachi's worst topout
  tally」 from the raw column would be reading a session-length record as a performance one, which
  is the same defect the shortfall table below turns out to have at corpus scale.

  **10-03's 14:13 is 27 topouts, the largest session total** (09-19 had 24), and 13 is pinglamb's
  largest tally — both raw records of a 146-round night, and a one-apart split at a rate of 18.5%.
- **The night has three acts and the gap tracks them**: over 17% across matches 1-3, under 7%
  across 4-9, over 11% across 10-11 [C007] — and all four of yachi's match wins fall in the
  middle window [C001]. Per-match, m9 is the only one of eleven where his attack per piece beats
  pinglamb's [C019].

### 每粒攻擊點解爭 — where the APP gap comes from, and the two halves of it

**pinglamb's attack per piece is higher than yachi's in every session, and the gap is attack PER
LINE, not lines per piece.** Pooled: APP <!--app:app-->yachi 0.589 against pinglamb 0.652<!--/app:app-->, lines per piece <!--app:lpp-->yachi 0.546 against pinglamb 0.555<!--/app:lpp-->, attack
per line <!--app:apl-->yachi 1.078 against pinglamb 1.175<!--/app:apl-->. Every figure in this section is a marked fragment rendered by
`pipeline/check_app_decomposition.py` from `analysis/app_decomposition.py`, which rolls up each
session's `sim/attack-facts.json` (`pipeline/sim/emit-attack-facts.ts`) — paste from `--render`,
never type. Each session's report carries the same split for that night in 攻擊由邊度嚟, the
fourth quarantined section.

**What is anchored and what is not.** The engine re-runs every round and reads `res.rawGarbage`,
the attack BEFORE cancellation; it agrees with the replay's own counters in <!--app:anchor-->2810 of 2814 player-rounds for the attack total and 2807 of 2814 for the clear-type counts<!--/app:anchor-->
(the exceptions are named in `attack-facts.test.ts`). So the clear-type COUNTS below are as good as
facts.json; attack per clear and the base/B2B/combo split are one engine's. **Do not use
`oracle-source.ts`'s `records[].attack` for this** — it is post-cancel; measured once on 2026-10-11 and not re-derived, it summed to about 80% of
the replay's total and made a T-spin Triple look worth 4.9 lines instead of 6.1.

The engine gap is <!--app:gap-->+6.35<!--/app:gap--> attack per 100 pieces, split two ways that each sum to it exactly:

* **by window** — <!--app:windows-->+2.68 from the first 21 locks and +3.67 after them<!--/app:windows-->.
* **by clear type (Kitagawa 1955)** — <!--app:kitagawa-->+3.98 of mix and +2.37 of value<!--/app:kitagawa-->: the MIX of clears (how many per piece of
  each type) and the VALUE of each clear (B2B, combo, Perfect Clear riding on it). The largest mix
  terms are <!--app:terms-->T-spin Doubles +4.16, T-spin Triples +2.99, quads -2.61, T-spin Singles -0.62<!--/app:terms-->.

**The two windows are two different mechanisms, and pooling hides one of them.** T-spin Triples
are an OPENER phenomenon: <!--app:tst-window-->1394 against 827 inside the window and 51 against 47 after it<!--/app:tst-window-->. That is the repertoire split — pinglamb's Honey
Cup and Stray Cannon fire a Triple first, yachi's TKI-3 does not (see 六個具名定式). T-spin Doubles
run the OTHER way inside the window and the expected way after it: <!--app:tsd-window-->1070 against 1300 inside the window and 5130 against 4112 after it<!--/app:tsd-window-->. So
「pinglamb does more T-spin Doubles」 is a mid-game statement; in the opener yachi does more, and a
sentence that pools the two says the opposite of what happens in the first three bags.

It is a property of the pair rather than of a few nights: pinglamb's per-piece rate is the higher
in <!--app:signs-->T-spin Doubles in 18 of 19, T-spin Triples in 19 of 19, quads in 2 of 19<!--/app:signs-->, and the <!--app:jackknife-->187 single-match drops leave it between 6.28 and 6.43<!--/app:jackknife--> attack per 100 pieces. Two things it is not.
It is not who won — APP decides rounds and not nights (08-01, 10-09) — and it is not a mechanism
for WHY each player chose his openers; the data shows what they played, nothing more.

### 逐場排開就分得開 — the per-match APP gap separates the match winner, five times of eighteen

**Order a session's matches by pinglamb's attack-per-piece advantage and, on five of the eighteen
nights, the match winner falls out perfectly — though not on equal evidence; see the tiers below.** 08-19 was the first: yachi's three wins are the
three smallest gaps (−10.13, −0.98, +0.72), pinglamb's seven the seven largest (+11.53 … +40.67),
nothing between [C007]. 08-25 reproduces it: yachi's four wins are the four smallest (+3.47, +6.15,
+7.99, +8.21), pinglamb's five the five largest (+10.32 … +30.00), nothing between 8.21 and 10.32
[C007]. **No other session separates**, and that was checked over all ten rather than assumed —
07-22, 07-24, 07-28, 08-01, 08-14 all interleave, and 08-09 「separates」 only because yachi won no
match at all, which is not the same statement. **09-03 interleaves too**: yachi's single win (m3,
+6.61%) sits between pinglamb's m4 (+0.58%) and m2 (+7.98%), so the back-to-back run ended at two
and the count stays 2 of 9. **09-10 interleaves worse than any session in the corpus**: yachi won
m5 at +18.89% — the LARGEST per-match gap of its eight — and also m7 at −8.43%, the smallest, so
his wins are the two ends of the range with three of pinglamb's in between. The count stays 2 of
10. Neither session mints a C007 — a weakened claim that 「nearly」 separates would be fitting the
claim to the night.

**09-11 formally SEPARATES and still mints no C007, which is the sharpest case this rule has had.**
yachi won exactly one match (m5) and its gap, +0.21%, is the smallest of the seven; pinglamb's six
run +5.57% to +19.57% with nothing between. By the letter of 08-19's and 08-25's claim that is a
third separating session. It is not, because the EVIDENCE is a different order of magnitude, and
that is countable rather than a matter of taste: with k wins among m matches, a random assignment
puts all k at the bottom with probability 1/C(m,k) — **1/120 for 08-19's 3 of 10, 1/126 for
08-25's 4 of 9, and 1/7 here.** A pattern that arises by chance one night in seven is not a
reproduction of one that arises one night in 120. So 09-11 is filed with 08-09 as the degenerate
case — 08-09 「separated」 on zero wins, this one on one — and **the count stays 2 of 11.**

Two things this case adds to the rule. **The degenerate class is not just 「won no match」**: it is
「won too few matches for the ordering to be able to fail」, and the boundary is a probability, not
a win count. And **a session can satisfy the stated criterion while supplying almost no evidence
for it**, which is the general form of the trap — a criterion written when every instance happened
to be well-powered does not carry its power with it. The report for 09-11 states the 1-in-7 in its
own prose rather than leaving it here.

**09-17 separates, mints a C007, and lands BETWEEN the two classes the rule had — which is where
the probability boundary earns its keep.** yachi's two wins are the two smallest gaps (m2 +3.90%,
m3 +13.47%), pinglamb's five the five largest (+16.91% … +44.36%), nothing between 13.47 and 16.91.
Two wins among seven fall this way by chance with probability 1/C(7,2) = **1 in 21**. That is not
1 in 120, and it is not 09-11's 1 in 7 either: the ordering had twenty ways to fail and took none
of them, so it is not degenerate, and the claim is minted. **The count becomes 3 of 12 and the
three are NOT equally powered** — 1/120, 1/126 and 1/21, so this one is about six times weaker than
either of the others. Any sentence that says 「it separated again」 without the 1-in-21 beside it is
the provenance mistake this file's 冇第二份 section is about, and the report for 09-17 states the
figure in its own prose exactly as 09-11's states its 1-in-7.

What makes 09-17's separation substantive rather than merely ordinal is the spread it sits in: the
gaps run +3.90% to +44.36%, and the void the cut falls into is 3.4 points wide. **m7's +44.36% is
the largest per-match gap in the corpus**, past 08-19's +40.67%.

So the rule now has three tiers rather than two, and the tiers are probabilities: well-powered
(08-19, 08-25), intermediate (09-17), degenerate (08-09, 09-11). A fourth instance is filed by
computing 1/C(m,k) first and reading its size second — never by counting wins.

**09-19 is the strongest test the rule has had and it interleaves outright.** Twenty matches and
five yachi wins is 1/C(20,5) = 1 in 15 504 by chance — an order of magnitude more powered than
08-25's 1 in 126 — so this is the session where a separation would have meant most, and there is
nothing close to one. yachi's five wins sit at −6.19%, −5.24%, +8.07%, +10.96% and +14.89%;
pinglamb's fifteen run +2.43% to +24.36%. **Three of yachi's five are above six of pinglamb's**,
so no cut exists anywhere. No C007 is minted and the id is left empty, following 09-10 and 09-11.
The count stays **3 of 13**.

**09-18 is the second-strongest test and it also interleaves.** Eighteen matches and seven yachi
wins is 1/C(18,7) = **1 in 31 824**, i.e. more powered than every earlier session except 09-19
and twice as powered as 09-19 itself on this measure. yachi's seven wins run −18.26%, −11.41%,
−5.00%, −3.89%, −2.06%, +0.81% and +8.39%; pinglamb's eleven run −2.72% to +26.81%. The single
value that breaks it is **pinglamb's m17 at −2.72%, which sits inside yachi's band**, so no cut
exists — one match away from a separation worth 1 in 31 824, which was the closest the corpus had
come to a well-powered instance until 10-03. No C007 is minted. The count stays **3 of 14**.

**10-03 separates, mints a C007, and is the best-powered separation the corpus has.** yachi's
six wins are the six smallest gaps (m3 −9.36%, m8 −7.80%, m16 −7.59%, m4 −6.38%, m18 −4.08%,
m12 +3.25%), pinglamb's fourteen run +6.65% (m15) to +20.63% (m5), nothing between 3.25 and 6.65.
Six wins among twenty fall that way by chance with probability 1/C(20,6) = **1 in 38 760** — more
powered than 09-18's 1 in 31 824 and 09-19's 1 in 15 504, both of which interleaved, and about three
hundred times 08-19's 1 in 120. **The count becomes 4 of 15.** So the earlier reading — that the
best-powered sessions interleave, so the phenomenon does not turn up when there is enough data to
see it — held for two sessions and is now one-and-one against the best-powered three: 10-03
separates, 09-18 and 09-19 do not. Read 「four of fifteen」 as 08-19, 08-25, 09-17 and 10-03 at
1 in 120, 1 in 126, 1 in 21 and 1 in 38 760, i.e. four observations of very unequal weight.

**10-09 interleaves, and from both ends at once.** Five yachi wins among twelve is 1/C(12,5) =
**1 in 792** by chance, so a separation would have been the second-best-powered after 10-03's. The
gaps run +1.94% (m10) to +27.95% (m2), and the two ends of yachi's band are the failure: **m10, the
SMALLEST gap of the night, is a pinglamb win**, and **m4, the second-largest at +22.66%, is a yachi
win**. yachi's other four wins (m5 +2.41, m12 +2.85, m7 +6.66, m8 +9.59) do sit at the bottom, so
the ordering is two matches from a clean cut rather than nowhere near one — which is the
description to give, not 「nearly separates」. No C007 is minted and the id is left empty,
following 09-10, 09-11 and 09-19. **The count stays 4 of 16.**

**10-12 separates, mints a C007, and lands in the intermediate tier beside 09-17.** yachi's three
wins are the three smallest gaps (m3 −28.01%, m7 +3.13%, m2 +4.54%), pinglamb's five the five
largest (m5 +11.97% … m1 +30.99%), nothing between 4.54 and 11.97 [C007]. Three wins among eight
fall that way by chance with probability 1/C(8,3) = **1 in 56** — under half of 08-19's 1 in 120
and about two and a half times 09-17's 1 in 21, so it is filed with 09-17 and not with the
well-powered three. **The count becomes 5 of 17.** The void the cut falls into is 7.4 points wide,
the widest after 08-19's 10.8, and its bottom end holds a corpus extreme: **m3's −28.01% is the
largest per-match lead yachi has had**, past 09-18 m4's −18.26%, and the one match of the eight in
which he leads at all [C020]. So the tiers now read: well-powered (08-19, 08-25, 10-03),
intermediate (09-17, 10-12), degenerate (08-09, 09-11) — five separations at 1 in 120, 126, 21,
38 760 and 56, which is five observations of very unequal weight and not a rate.

**10-20 interleaves, and could not have said much if it had not.** Two yachi wins among four
matches is 1/C(4,2) = **1 in 6** by chance — below 09-11's 1 in 7, so a separation would have been
filed as degenerate before it was read. It does not separate anyway: yachi won m2 (−7.37%) and m1
(+10.52%), pinglamb m4 (+8.28%) and m3 (+11.20%), so pinglamb's m4 sits inside yachi's band. No
C007 is minted and the id is left empty, following 09-10, 09-11, 09-19 and 10-09. **The count stays
5 of 18.**

**10-22 interleaves by one match.** Three yachi wins among nine is 1/C(9,3) = **1 in 84** by chance.
His wins are m8 (+7.97%), m1 (+13.61%) and m6 (+18.03%); pinglamb's six run +17.28% (m7) to +31.50%
(m5), so m7 sits inside yachi's band, 0.75 points below m6. No C007 is minted. **The count stays 5
of 19.**

Three things this must not be turned into, each of which is a sentence someone will write next:

- **It is not a sign test.** On 08-25 pinglamb's attack per piece is higher in *every one of the
  nine matches*, yachi's four wins included, so 「yachi won the matches where his attack per piece
  was higher」 is false nine times over. 08-19's version had one match on the wrong side of zero; at
  twelve sessions the safe wording is that what separates is the SIZE of the gap, never who leads —
  and 09-10 shows even 「who leads」 is not fixed.
  09-03 says the same thing from the failing side: pinglamb leads APP in all six matches there
  too, and the winner does *not* fall out. **09-10 removes even the premise**: yachi leads attack
  per piece outright in m1 (−1.49%) and m7 (−8.43%), so 「pinglamb leads every match」 is not a
  corpus regularity either — **measured, it holds in 9 of the 19** (07-22, 07-28, 08-14, 08-19,
  09-10, 09-18, 09-19, 10-03, 10-12 and 10-20 each have at least one match yachi leads; 10-09 is the
  eighth where it holds, 10-12 the ninth where it fails, 10-20 the tenth, and 10-22 the ninth where it holds). This sentence published 「it held in
  eight of ten sessions and this is one of the two where it does not」 until 2026-09-12, and that
  was wrong at ten as well as at eleven: the true ten-session count was five of ten. Nobody had
  measured it — the 09-10 paragraph beside it names two matches, and 「the two where it does not」
  was read off that one session rather than off the corpus. Same sub-class as the separation
  series' miscounts (冇第二份's eighth instance), with the list one section away instead of three
  lines up. 09-11 and 09-17 are both among the seven where it holds: pinglamb leads all seven
  matches in each. 09-17 is therefore the same shape as 08-25 on this point — he leads every
  match and still loses two of them. **09-19 and 09-18 are both among the seven where it does
  not**: 09-19 has yachi leading in m3 (−6.19%) and m16 (−5.24%), two of the five matches he won,
  and 09-18 has him leading in six of eighteen (m4, m11, m14, m15, m16 and m17). Note that the
  count stayed at seven-of-N while N grew, so the SHARE moved 58% → 54% → 50% → **46%** without
  anyone writing a new number — re-derive it from the list in this bullet, never carry it. 10-03
  is the eighth where it fails: yachi leads in m3, m4, m8, m16 and m18, five of his six wins, and
  the APP leader won 19 of the 20 matches [C031] — the exception is m12, which yachi won 5-3 while
  pinglamb led by +3.25%. So on 10-03 the sign nearly decides and the size decides exactly.
  **10-09 is the eighth where it HOLDS** — pinglamb's APP is higher in all twelve matches [C023],
  m4 (a yachi win) by over 22% and m10 (a pinglamb win) by under 2% — so the share goes back up to
  **50%**, and 10-09 is 08-25's and 09-17's shape: he leads every match and loses five of them. What
  decides 10-09's matches is not the sign of the APP gap but the attack TOTAL: the player with more
  attack won 10 of the 12 [C024], the exceptions being m6 and m10, two pinglamb wins in which yachi
  out-attacked him on volume. **10-12 is the ninth where it FAILS** — yachi leads only m3, by the
  corpus's largest margin [C020] — so the share falls to **47%** (8 of 17). There the attack total
  decides every match [C019], as it does on 08-19, 09-03, 09-11 and 09-17: in m2 and m7 pinglamb
  had the higher APP and yachi still won both on volume — volume beating the APP sign twice, where
  10-09's two C024 exceptions were the APP sign beating volume twice. **10-20 is the tenth where it
  FAILS** — yachi leads m2 [C016] — so the share falls to **44%** (8 of 18), and the attack total
  decides all four matches again [C015], m1 included, which yachi won on volume against a pinglamb
  APP 10.52% higher. **10-22 is the ninth where it HOLDS** — pinglamb's APP is higher in all nine
  matches [C020] — so the share goes back up to **47%** (9 of 19), and the attack total decides 7 of
  the 9 [C021], the exceptions m1 and m6, two yachi wins against more pinglamb attack.
- **The cut point is not a constant, and the third instance widens the spread rather than
  narrowing it.** 08-19's separation falls between +0.72% and +11.53%, 08-25's between +8.21% and
  +10.32%, **09-17's between +13.47% and +16.91%**. There is no corpus-wide threshold: 08-25's
  whole yachi-win band sits *above* 08-19's whole pinglamb-win floor, and 09-17's cut sits above
  both sessions' cuts entirely. A reader who takes 「under 9%」 from one C007 and applies it to
  another session is reading a within-night ordering as a rule. **10-03's cut falls between +3.25%
  and +6.65%**, inside 08-19's void and below 08-25's and 09-17's, so no single threshold separates
  all four. (10-09 has no cut to add: it interleaves.) **10-12's falls between +4.54% and +11.97%**,
  inside 08-19's void again and straddling 10-03's whole cut, so no single threshold separates all
  five either.
- **Five of seventeen is not a law, and they are not one kind of evidence.** It is a reproduction,
  which is worth more than one instance and much less than a finding — and the third instance is
  six times weaker than the first two, so 「three of twelve」 read as three equal observations
  overstates it. It happened twice, back to back, on 08-19 and
  08-25, and an earlier revision of this bullet said a third session interleaving would refute
  nothing because the six earlier ones already did. 09-03 was that third session and 09-10 is the
  fourth — the statement stands as written both times, but note what it costs: the honest count is
  now 2 of 11 with the two adjacent in the MIDDLE of the corpus and three sessions since that do
  not reproduce it (09-03 and 09-10 interleave, 09-11 separates only degenerately), so 「the two
  most recent sessions」 is not available as a reason to expect the next one, and neither is
  「it separates more often than not」.

### 個 shortfall 先係話事嗰個 — the volume route is bounded, not unreliable

08-19 ran the route a third time: **+312 pieces, −236 lines of attack** (−6.13% of pinglamb's
total), −61 639 in-game score, +100 lines. 08-25 ran it a fourth: **+645 pieces, −176 lines**
(−3.42%), −85 057 in-game score, +382 lines. 09-03 ran it a fifth: **+207 pieces, −120 lines**
(−4.38%), −52 878 in-game score, +70 lines. 09-10 ran it a sixth: **+276 pieces, −47 lines**
(−1.41%), −35 607 in-game score, +123 lines. 09-11 ran it a seventh: **+110 pieces, −309 lines**
(−9.15%), −100 950 in-game score, +98 lines. 09-17 ran it an eighth: **+455 pieces, −250 lines**
(−8.38%), −67 450 in-game score, +247 lines. 09-18 ran it a ninth: **+426 pieces, −352 lines**
(−4.80%), −139 437 in-game score, +281 lines. 09-19 ran it a tenth: **+714 pieces, −476 lines**
(−5.36%), −117 513 in-game score, +142 lines. 10-03 ran it an eleventh: **+328 pieces, −395 lines**
(−4.53%), −101 470 in-game score, +103 lines [C005] — the second-smallest surplus in the corpus as
a rate (2.38%, after 09-11's 2.13%). Eleven consecutive failures on the letter, and 08-01's success
was 1 of 12 — which is exactly where this stops being a story about volume being unreliable.
**10-09 ran it a twelfth and the route MORE than covered the gap: +1064 pieces, +58 lines**
（留一局：抽走 m7r8，數字變 +23 行，即係郁 35 行）
**(+1.00%), +85 519 in-game score, +318 lines** [C005][G074] — the largest surplus the corpus holds
as a count (past 09-19's 714) and as a rate (12.64% [C009], past 09-17's 10.05%), the first session
since 07-22 where yachi's attack total is the higher, and the first of sixteen where his score
total is (10-20 is the second, of eighteen). The annotation is the session's own leave-one-out: the SIGN survives losing any one round
and the SIZE does not — m7r8, the night's longest round (about 217 s), carries 35 of the 58. So the
honest sentence is 「the route bought the gap back and a little more」, not 「yachi out-attacked him by
58」. It was 2 of 13 runs, and the series was still lost 5:7, because attack totals are not what
decides a match on this night either: see C024 under the per-match section. **10-12 ran it a
thirteenth and it failed again: +468 pieces, −102 lines** (−3.15% [C005]), −4 859 in-game score,
+208 lines — a 9.92% surplus [C009], the third-largest as a rate after 10-09's and 09-17's, against
a 13.50% gap [C004], the third-largest session gap after 09-17's and 08-09's. 2 of 14 runs now. And
the night the route lost on aggregate is a night it won two matches outright: the attack total
decided all eight [C019], m2 and m7 included, where yachi's volume beat a higher pinglamb APP.
**10-20 ran it a fourteenth and the route covered the gap with room to spare: +323 pieces, +80
lines** (+4.16% [C005]), +27 416 in-game score [G059], +33 lines — an 11.18% surplus [C009] against
a 6.73% gap [C004], the narrowest session gap since 09-10's. 3 of 15 runs now, and the series was
drawn: 2:2 in matches and 15:15 in rounds. The attack total decided all four matches
[C015]. **10-22 ran it a fifteenth and it failed by the largest shortfall the corpus holds: +573
pieces, −349 lines** (−8.79% [C005]), −113 511 in-game score [G068], +292 lines — a 9.99% surplus
[C009] against a 20.59% gap [C004], the largest session gap the corpus holds (past 09-17's
20.11%). 3 of 16 runs now; the attack total decided 7 of the 9 matches [C021].
09-10's is
the smallest failure in the corpus by a factor of two and 09-11's is the largest as a RATE; the two
are adjacent sessions and the reason is arithmetic, not effort: see below. (09-18's −139 437 is the
largest in-game score difference the corpus holds, past 09-11's −100 950 — worth one clause because
that column is a sum over the session and this is one of the three longest, which is the same
confound the y-axis below turned out to have.)

A piece surplus buys back an APP gap of **exactly** `100·(surplus_pieces/other_pieces − 1)`
percentage points. That is the whole of what volume can do, and it is arithmetic rather than a
tendency. Subtract it from the session's APP gap and the remainder — the **shortfall** —
rank-orders the attack difference across the nineteen sessions:

| shortfall (pp) | **−4.45** | **−1.12** | −0.67 | +0.50 | +1.00 | +1.51 | +2.66 | **+3.58** | +3.82 | +4.61 | +4.79 | **+4.86** | +5.22 | +5.96 | +6.89 | *+10.03* | *+10.06* | *+10.28* | ***+10.60*** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| yachi's attack − pinglamb's, as % of pinglamb's total | **+4.16** | **+1.00** | +0.63 | −0.46 | −0.93 | −1.41 | −2.42 | **−3.15** | −3.42 | −4.19 | −4.38 | **−4.53** | −4.80 | −5.36 | −6.13 | *−8.50* | *−8.38* | *−9.15* | ***−8.79*** |
| the same, in raw lines | **+80** | **+58** | +28 | −15 | −32 | −47 | −72 | **−102** | −176 | −206 | **−120** | **−395** | **−352** | **−476** | **−236** | −271 | −250 | −309 | **−349** |
| session | **10-20** | **10-09** | 07-22 | 07-28 | 08-01 | 09-10 | 07-24 | **10-12** | 08-25 | 08-14 | 09-03 | **10-03** | **09-18** | **09-19** | 08-19 | *08-09* | *09-17* | *09-11* | ***10-22*** |

**THE Y-AXIS CHANGED ON 2026-09-19, AND THAT IS THIS SESSION'S FINDING.** Every earlier revision
of this table ranked the RAW LINE COUNT. The x-axis is a rate and the y-axis was a sum over the
session, so the y grew with session length at fixed per-piece shortfall — and twelve sessions of
46 to 84 rounds, all within a factor of 1.8 of each other, could not tell the two apart. 09-19 is
150 rounds: 1.79x the largest at the time, 3.26x the smallest. It breaks the raw version and lands
exactly in its slot on the rate version. Measured both ways over the same points:

| y-axis | ρ at 12 | ρ at 13 | ρ at 14 | ρ at 15 | ρ at 16 | ρ at 17 | ρ at 18 | ρ at 19 | discordant pairs at 9 / 10 / 11 / 12 / 13 / 14 / 15 / 16 / 17 / 18 / 19 |
|---|---|---|---|---|---|---|---|---|---|
| raw lines | 0.9720 | 0.9231 | 0.8769 | 0.8321 | 0.8618 | 0.8849 | 0.9030 | **0.8860** | 2 · 2 · 2 · 3 · 7 · 11 · 16 · 16 · 16 · 16 · **19** |
| % of pinglamb's attack | 0.9930 | 0.9945 | 0.9956 | 0.9964 | 0.9970 | 0.9975 | 0.9979 | **0.9964** | 0 · 0 · 0 · 1 · 1 · 1 · 1 · 1 · 1 · 1 · **2** |

(The sixteen-session ρ's are 0.99706 and 0.86176, the seventeen-session ones 0.99754 and 0.88480,
the eighteen-session ones 0.99793 and 0.90299, the nineteen-session ones 0.996491 and 0.885965;
in both columns the rate axis's is floored and the raw axis's
ceiled, because the argument needs the first large and the second small — the per-claim rounding
rule this file states for the R statistics, applied here. **The earlier columns were NOT rounded
that way and are left as published**: they are round-half-up, so the row mixes conventions. On the
rate row it makes no difference (every earlier cell floors to the digits shown), but on the raw row
three of the four earlier cells would move under ceil — the exact values are 0.972028, 0.923077,
0.876923 and 0.832143, i.e. 0.9721 / 0.9231 / 0.8770 / 0.8322 ceiled — and the prose below quotes
the round-half digits, so they are kept rather than silently re-rounded. A first version of this
note said every earlier column 「lands on the same four digits either way」, which was false for the
raw row.)

**2026-09-18 IS THE OUT-OF-SAMPLE TEST THAT CORRECTION COULD NOT OTHERWISE HAVE HAD, and it
confirms it a second time.** The axis was changed on the evidence of one long session; the obvious
objection is that one point cannot establish which of two axes is right, and the only answer is
another long session. 09-18 is 127 rounds — the second-longest at the time — and it moves the two axes in
OPPOSITE directions again: the rate axis improves (0.9945 → 0.9956, still one discordant pair)
while the raw axis degrades further (0.9231 → 0.8769, seven discordant pairs to eleven). A
correction that keeps being confirmed by each new large session, on data collected after it was
made, is in a different position from one argued from the session that motivated it.

**2026-10-03 is the third long session, and it confirms the correction a third time.** At 146
rounds its shortfall is 4.86 pp (a 328-piece surplus buying 2.38 pp against C004's 7.24 pp gap
[C005][C009]), between 09-03's 4.79 and 09-18's 5.22. On the rate axis it lands in its slot,
−4.53% between −4.38% and −4.80%, and ρ improves again (0.9956 → 0.9964, still one discordant
pair). On the raw axis its −395 lines outranks 09-18's −352 and four sessions with larger
shortfalls (08-09, 08-19, 09-11, 09-17), five new discordant pairs, and ρ falls to 0.8321.

**2026-10-09 is the first point added at an END of the ordering since 09-11, and it is the first
session since 09-19 to move the raw axis UP.** Its shortfall is **−1.12 pp** — a 1064-piece surplus
buying 12.64 pp against C004's 11.52 pp gap [C004][C005][C009] — the first negative shortfall since
07-22's −0.67 and the new low. The ordering therefore predicts the largest attack difference in
yachi's favour the corpus holds, past 07-22's +0.63%, and it measures **+1.00%**: in its slot on the
rate axis, and in its slot on the raw axis too, because +58 lines is also the largest raw figure in
yachi's favour. So neither axis gains a discordant pair (one and sixteen, unchanged), the rate ρ
creeps up (0.9964 → 0.9970) and the raw ρ improves after three successive falls
(0.8321 → 0.8618). **That is not evidence for the raw axis**: a point at the end of the ordering
that is extreme on both axes is concordant with everything under any monotone y, which is the
same weakness 09-11's end-point test was written up with. The raw axis's 16 discordant pairs are
untouched, and they are the measurement. And the +1.00% itself rests on one round's size — see
the annotation in the paragraph above the table.

**2026-10-12 is an INTERIOR point bracketed on both sides, and it lands on both axes.** Its
shortfall is **3.58 pp** — a 468-piece surplus buying 9.92 pp against C004's 13.50 pp gap
[C004][C005][C009] — between 07-24's 2.66 and 08-25's 3.82, so the ordering predicts an attack
difference between −2.42% and −3.42%, and it measures **−3.15%**. That is the stronger kind of
test, the kind 09-10's and 09-18's were. On the raw axis it predicts between −72 and −176 lines and
measures −102, in its slot too, so neither axis gains a discordant pair (one and sixteen,
unchanged), the rate ρ creeps up again (0.9970 → 0.9975) and the raw ρ rises a second time
(0.8618 → 0.8849). **The raw axis's rise is again not evidence for it**: 10-12 is 55 rounds, inside
the 46-84 band of the twelve sessions that could not tell the axes apart, so its raw deficit is
on the same scale as its neighbours' and it could not have broken the raw ordering the way the
long sessions did. Adding a point that cannot discriminate raises a rank correlation that is
dominated by its existing sixteen discordant pairs; the pairs are the measurement, and they are
the same sixteen.

**2026-10-20 is a point at the far END of the ordering again, and it is the weakest test the
table has had.** Its shortfall is **−4.45 pp** — a 323-piece surplus buying 11.18 pp against
C004's 6.73 pp gap [C004][C005][C009] — the new low by more than three points, past 10-09's −1.12.
The ordering therefore predicts the largest attack difference in yachi's favour the corpus holds,
and it measures **+4.16%** (+80 lines): extreme on both axes, so concordant with everything under
any monotone y, and neither axis gains a discordant pair (one and sixteen, unchanged). The rate ρ
creeps up (0.9975 → 0.9979) and the raw ρ rises a third time (0.8849 → 0.9030), which is exactly
the 10-09 weakness written above, at a larger size: an end point cannot discriminate, and 10-20 is
also the corpus's shortest night (30 rounds), so its raw figure could not have broken the raw
ordering either. Read +4.16% as a reading on 30 rounds, not as the route's best night.

**2026-10-22 is a point at the far OTHER end, and it is the first point since the axis changed to
add a discordant pair on the rate axis.** Its shortfall is **10.60 pp** — a 573-piece surplus
buying 9.99 pp against C004's 20.59 pp gap [C004][C005][C009] — the new high, past 09-11's 10.28.
The ordering therefore predicts the largest attack deficit the corpus holds, past 09-11's −9.15%,
and it measures **−8.79%**: between 08-09's −8.50% and 09-11's −9.15%, so it swaps with 09-11.
That is the rate axis's second discordant pair, and it is NOT the 08-09 / 09-17 kind: the two
sessions are 0.32 pp apart on the x-axis, about ten times that pair's 0.03. All four sessions
from 08-09 to 10-22 sit within 0.6 pp of each other at 10.03-10.60, the one stretch of the table
where neighbours are that close. On the raw axis −349 lines outranks 08-09's −271, 09-17's −250 and 09-11's
−309 but not 09-19's −476 or 10-03's −395, three new discordant pairs (sixteen to nineteen). So the
rate ρ falls for the first time since the change (0.9979 → 0.9964) and the raw ρ falls too
(0.9030 → 0.8860). Both are hand-measured by the same probe that reproduces the eighteen-session
row exactly; nothing committed re-derives either. Read the swap as a limit of resolution at the
top of the table, not as the ordering breaking: one pair at 0.32 pp is a weaker failure than
09-03's two places at 2.1 pp would have been, and that one was an axis error.

Five things follow, and the third is the one that matters most for how this file is written.

* **This is a units correction, not a re-fit.** The x-axis is a ratio of rates, so the y-axis has
  to be one too; the percentage is **already printed beside every raw figure** in the paragraph
  above this table and in every per-session write-up below it. Nothing was searched for — the
  correct axis was in the document the whole time, in the same sentences.
* **It was strictly better on the OLD data, before this session existed.** The rate axis had
  **zero** discordant pairs at nine, ten and eleven sessions, where the raw axis already had two.
  So the improvement is not something 09-19 bought; 09-19 only made the difference large enough
  to see.
* **09-03 never missed its slot — the axis did.** This file has carried 「the perfect ordering is
  broken」 and 「one session out of place」 for four revisions, and the session it named is the
  corpus's SHORTEST (46 rounds), whose raw attack difference is small because it is short. On the
  rate axis 09-03 sits exactly where its shortfall puts it, and the ordering was perfect through
  eleven sessions rather than broken at nine. The 2.1 pp neighbour spacing that made it read as a
  「genuine miss」 was real; the miss was not.
* **The one discordant pair that survives is 08-09 / 09-17**, italicised above (this bullet's
  「one」 is the eighteen-session record; 10-22 adds 09-11 / 10-22, bold-italicised, see its
  paragraph) — the 0.03 pp
  adjacent swap the next-but-one paragraph already describes as beyond this quantity's resolving
  power. It is the same pair on both axes, which is the right outcome: a real limit of resolution
  does not care which units you plot.
* **The repo already had the rule and applied it one level down.** 「Windows of different sizes
  must be compared as cross-multiplied rates, never as raw sums」 is stated in the windowed-claims
  section above for claims *inside* a session. This table compared windows of very different
  sizes — whole sessions — as raw sums. A rule stated for one scope is not enforced at another,
  and nothing in this repo reads prose.

The raw row is kept in the table on purpose: it is what every earlier revision published, and
deleting it would leave the paragraph above making a claim the table no longer shows. The
normalisation choice is not load-bearing — 「per 1000 pooled pieces」 gives an identical ranking and
an identical ρ to four decimal places, so the finding is about raw-versus-rate and not about which
rate.

08-01's surplus bought 6.27 pp against a 7.27 pp gap — shortfall 1.00, and it landed within 32
lines. 08-19's bought **5.51 against a 12.40 gap** — shortfall 6.89. **So 08-19 did not fail for
lack of volume: its surplus is 08-01's.** It failed because the gap it was asked to cover was 1.7×
bigger. Never write 「加粒數買唔返」 without the shortfall beside it — the route works, and what
predicts the outcome is how much of the gap was handed to it.

**08-25 is the first point added since the ordering was written, so it is a prediction rather than
a fit — and it lands.** Its surplus is the largest in the corpus (645 pieces, buying 8.09 pp) but
the gap handed to it was 11.91 pp [C004][C009], for a shortfall of 3.82. The ordering says the
attack difference must fall between 08-01's −72 (shortfall 2.66) and 08-14's −206 (4.61); measured,
it is **−176**. Seven points can be arranged to rank-order by construction; the eighth arriving in
its slot is the first evidence that the ordering is a property of the data.

**09-03 was the ninth point and was recorded here for four revisions as MISSING its slot — and it
did not.** Its shortfall is 4.79 pp (a 207-piece surplus buying 4.75 pp against C004's 9.54 pp
gap), which sits between 08-14's 4.61 and 08-19's 6.89. On the RAW line axis the ordering predicts
an attack difference between −206 and −236 and measures **−120**, two places out; that is what was
published. On the RATE axis it predicts between −4.19% and −6.13% and measures **−4.38%**, in its
slot. 09-03 is the corpus's shortest session at 46 rounds, so its raw attack difference is small
because the night is short — which is exactly the confound the 2026-09-19 table above identifies.
**Struck at its original site rather than corrected only in a later section**, per this file's own
rule about closing an item where it was filed: there was no ninth-point miss.

**09-10 is the TENTH point, the second genuine out-of-sample test, and it LANDS.** Its shortfall
is 1.51 pp (a 276-piece surplus buying 5.14 pp against C004's 6.65 pp gap [C005][C009]), which sits
between 08-01's 1.00 and 07-24's 2.66, so the ordering predicts an attack difference between −32
and −72. Measured, it is **−47**: in its slot, and in its slot on the rate axis too (−1.41%
between −0.93% and −2.42%). Spearman on the raw axis rose from 0.950 at nine to **0.9636** at ten;
on the rate axis it was 1.0000 at both, with no inversion at either.

**09-11 is the ELEVENTH point, the third out-of-sample test, and it LANDS — at the far end.** Its
shortfall is 10.28 pp (a 110-piece surplus buying 2.13 pp against C004's 12.41 pp gap
[C005][C009]), which is the largest in the corpus, so the ordering predicts an attack difference
past 08-09's −271. Measured, it is **−309**. This is a weaker test than 09-10's and the paragraph
must say so: predicting a rank at the END of an ordering only requires beating one neighbour,
where 09-10's slot had to be bracketed on both sides. Spearman on the raw axis rises to **0.9727**
at eleven; on the rate axis it is still 1.0000, with no inversion at all — the last revision at
which the two axes could not be told apart by anything but a single session's rank.

**09-17 is the TWELFTH point and it is the case the ordering cannot resolve — which is a different
thing from a miss, and the difference is 0.03 pp.** Its shortfall is 10.06 pp (a 455-piece surplus
buying 10.05 pp against C004's 20.11 pp gap [C005][C009]), which sits between 08-09's 10.03 and
09-11's 10.28, so the ordering predicts an attack difference between −271 and −309. Measured, it
is **−250**: outside that band, on the side where a shortfall near 7 belongs. By the letter it is
a second inversion and the honest reading is weaker than that: **the two sessions it swaps with
are 0.03 pp apart on the x-axis**, which is well inside anything this quantity can distinguish, so
「09-17 missed its slot」 and 「the ordering has no resolving power at a 0.03 pp separation」 describe
the same fact and only the second is informative. Contrast 09-03's genuine miss, which is two
places out against neighbours 2.1 pp away. Spearman is **0.9720** at twelve — essentially
unmoved from eleven's 0.9727, which is what an unresolvable adjacent swap does to a rank
correlation.

**Both ends of this session's arithmetic were corpus records at twelve sessions, and they nearly cancel** (10-09's surplus and 10-22's gap have since passed both). The surplus
buys 10.05 pp, the largest the route has ever had; the gap handed to it is 20.11 pp, the largest in
the corpus. 08-09 reached almost the same shortfall from 8.04 against 18.08. Same residue, both
components two points higher — which is the cleanest statement available that the shortfall is
what the ordering ranges over and the size of either term is not.

**The p beside that ρ needs its convention named, because the two published so far disagree about
one.** At nineteen sessions the exact permutation p over all 19! orderings is **2.6e-15 two-sided**
on the rate axis (1.3e-15 one-sided) and **1.6e-06 two-sided** on the raw axis (both ceiled, since
each supports a rejection; the same probe reproduces the eighteen-session pair exactly before
adding the nineteenth point). At eighteen they were 5.7e-15 (2.9e-15 one-sided) and 1.1e-06 —
the rate p still improves at nineteen although ρ falls, because n grew. At seventeen they were 9.6e-14 (4.8e-14 one-sided) and 7.1e-06. At sixteen they were 1.6e-12 (7.7e-13 one-sided) and 4.3e-05. At fifteen they were 2.3e-11 (1.1e-11 one-sided) and 2.3e-04. At fourteen it
was 3.2e-10 (1.6e-10 one-sided) against 9.0e-05 — a factor of 280 000 between the two axes, the
same finding as the ρ pair. At thirteen the rate axis read 4.2e-09 and the raw
2.4e-05; at
twelve the raw axis read 1.6e-06 two-sided over 12!; at eleven 6.1e-06 over 11!; and at ten 4.9e-05
two-sided while the figure published here was 2.5e-05 — the one-sided value, unlabelled.
(Note the raw p WORSENED three times running, 1.6e-06 → 2.4e-05 → 9.0e-05 → 2.3e-04, while every session
before 09-19 improved it: n grows and the fit gets worse, which is what an axis error looks like
once the corpus contains sessions long enough to separate the two axes. The rate axis improved on
all three of those same sessions. 10-09 then improves the raw p to 4.3e-05 — by landing at the end
of the ordering on both axes, which the shortfall paragraph above explains is no evidence for the
raw axis, 10-12 to 7.1e-06 by landing in an interior slot a 55-round session could not miss on
either axis, and 10-20 to 1.1e-06 by landing at the end again; 10-22 worsens it to 1.6e-06 with three new
discordant pairs.) The p is exact rather than sampled: the null distribution of
S = Σd² over n! orderings is computed by a subset DP, self-checked against n! and against the two
counts it must reproduce (one permutation at S = 0, n−1 at S = 2, none at S = 1 by parity). That
self-check is written against n rather than against 13 because it had to survive a fourteenth
point — a control whose own constants are a session count is the guard this file names elsewhere
as a copy of the measurement.
Nothing downstream compares these p's to anything, so no conclusion
moves, but this file elsewhere records a mixed one-/two-sided convention costing months of a wrong
comparison, so the convention is stated: **two-sided, matching the binomial table above.**

What survives is a strong monotone relationship over nineteen sessions with **two discordant pairs**
— 08-09 against 09-17, 0.03 pp apart and below this quantity's resolution, and 09-11 against
10-22, 0.32 pp apart at the top of the table — and it survives on the
rate axis, which is the axis the units require. The history is worth keeping in the order it
happened: the ordering was published as perfect at eight points, read as broken at nine, and is
now neither. It was never broken; it was measured against a y-axis that carried session length.
**Do not repair anything further by re-fitting.** It is still a rank-ordering and not a curve,
there is still no coefficient to read off it, and the axis was changed because of units and not
because of fit — the test of that is that the change improves the ordering on data collected
before the change was made, which it does (0 discordant pairs at nine, ten and eleven against the
raw axis's 2), AND on data collected after it, which 09-18 supplied and 10-03, 10-09, 10-12 and 10-20
have not contradicted. 10-22 adds the second rate-axis pair and three raw-axis pairs, so it
worsens both axes; the rate axis is still the one with two pairs against nineteen.

**09-11 is the other half of 09-10's demonstration, and the pair is the cleanest statement of the
section's thesis the corpus will produce.** Its surplus (2.13 pp) is the SMALLEST in the corpus
and its gap (12.41 pp) among the largest, so the route covered a sixth of what it was handed and
the attack totals finish 309 lines apart out of 3378. One session earlier the same route covered
all but 47 of 3327. **Neither session's route changed; the hole did** — from 6.65 pp to 12.41 pp
in one night. 「加粒數買唔返」 is literally true for the seventh time running and is still the
wrong sentence: 09-10 and 09-11 are the same route against holes differing by a factor of two, and
the outcomes differ by a factor of six.

**09-18 is the FOURTEENTH point to arrive and the third genuine out-of-sample test bracketed on
both sides, and it LANDS.** Its shortfall is 5.22 pp (a 426-piece surplus buying 3.70 pp against
C004's 8.93 pp gap [C005][C009]), which sits between 09-03's 4.79 and 09-19's 5.96, so the
ordering predicts an attack difference between −4.38% and −5.36%. Measured, it is **−4.80%** —
in its slot, and almost exactly in the middle of the predicted band. This is the stronger kind of
test, the kind 09-10's was and 09-11's was not: a slot bracketed on both sides can fail in two
directions, where the end of an ordering only has to beat one neighbour. On the raw axis it
predicts between −120 and −476 lines and measures −352, which is inside that band but adds four
discordant pairs elsewhere, because a 127-round session's raw deficit outranks the raw deficits
of shorter sessions with larger shortfalls. Same session, same data: in its slot on one axis,
breaking the ordering on the other.

**09-19 is the THIRTEENTH point in date order and the one that changed the axis rather than the ordering.** Its
shortfall is 5.96 pp (a 714-piece surplus buying 5.20 pp against C004's 11.16 pp gap [C005][C009])
— mid-table, between 09-03's 4.79 and 08-19's 6.89. On the rate axis it lands in its slot: −5.36%
between −4.38% and −6.13%. On the raw axis it predicts between −120 and −236 lines and measures
**−476**, the largest raw attack difference the corpus holds, which is four new discordant pairs
in one session. The session did not behave unusually; it was just long enough for the two axes to
disagree. See the table above — this paragraph deliberately does not repeat the ρ figures, which
have one home there.

**09-10 is also the cleanest demonstration of what the shortfall is FOR**, and it is worth stating
because it is the sentence six sessions of failure kept obscuring. Its surplus (5.14 pp) is
mid-corpus and smaller than 08-19's; the difference is that the gap handed to it was **6.65 pp, the
narrowest in the corpus**, so the route very nearly covered it — the attack totals finish 47 lines
apart out of 3327. The route did not improve. The hole shrank. 「加粒數買唔返」 is still literally
true for the sixth time running, and it is still the wrong sentence: what changed the outcome was
the size of the gap, exactly as the shortfall says. **And 「爭 47 行」 itself is one round's** —
`rel` 0.766, 得一局撐住（留一局：抽走 m2r9，數字變 -11 行，即係郁 36 行）。The
statement that survives leave-one-out is that the route covered nearly all of it; the 47 does not.

**Neither 08-19 nor 08-25 needs a 「得一局撐住」 annotation, and that absence is itself a
measurement.** In each, no published figure flips sign under leave-one-out and none reaches
`check_loo.THRESHOLD = 0.5`; the largest relative move is **0.281** for 08-19 (the won-gap,
dropping m1r5) and **0.271** for 08-25 (the won-gap again, dropping m8r1). 08-19 was the first
session since 07-24 to need none — worth stating because 07-28, 08-01, 08-09 and 08-14 each carry
one above, and four in a row reads as though the caveat were universal rather than measured per
figure. Two in a row now say the opposite just as loudly, and neither direction is the rule: the
caveat is per figure, per session, and measured.

**09-03 ends that run, and it does so with the corpus's most CONCENTRATED single-round
dependence — which is not the same as its most fragile figure, and the difference is worth
keeping.** Its won-gap sits at `rel` 0.622 — sixth-largest in the corpus and the lowest of the six
that crossed THRESHOLD when written; at sixteen and seventeen sessions it is eighth of the ten that
cross, 09-10 having added two above it and 09-18 and 10-09 one each below it, and 10-12 none
(`check_loo --check` prints the live list). Of those above it when written, 08-01's `score_diff` (20.931), 07-28's `attack_diff` (2.267), 08-14's
`app_gap_lost` (1.615), 08-09's `app_gap_won` (1.306) and 08-01's `attack_diff` (0.969) are all
more fragile, and four of those are figures whose VALUE is near zero, which `check_loo`'s own
header says is correctly the most fragile kind. What IS a corpus maximum is the `x2nd` column:
09-03's worst round moves the figure **2.57× as far as the next round does**, against 1.72 for the
runner-up — so the dependence is unusually concentrated in one round rather than spread over
several. m3r6 is that session's longest round (~210 s) and its highest line count (198), so it
brings more pooled pieces than any other round in a 46-round session; a pooled ratio over the
corpus's smallest session is exactly where this shows up. The annotation is in the series
paragraph above. Read it as the reason 09-03 is filed 「roughly level」 rather than as a mirror of
08-14: without m3r6 its two gaps are +2.9 and +3.9.

**`equiv.py`'s single-value 100% for 07-28 was an artefact, and `--two-site` now measures it
as 60%.** A windowed claim shares its rounds with the session total meant to imply it, so no
*single*-value mutation falsifies one without the other. Two changes break the tie: moving
pieces from a match-3 round to a match-1 round keeps `total_pieces`, `total_garbage_attack`
and C008 true while flipping C005 false. The second family does exactly that, and the four
claims that drop out (C002, C004, C005, C006) are precisely 07-28's windowed ones.
Measured with `--two-site round`. Per-session: 07-22 81% → **79%**, 07-24 96% → **94%**, 07-28 100% → **60%**, 08-01 100% → **92%**, 08-09 82% → **73%**, 08-14 84% → **68%**, 08-19 82% → **76%**, 08-25 82% → **76%**, 09-03 81% → **69%**, 09-10 81% → **81%**, 09-11 80% → **80%**, 09-17 81% → **75%**, 09-18 89% → **89%**, 09-19 89% → **89%**, 10-03 87% → **83%**, 10-09 83% → **74%**, 10-12 79% → **68%**, 10-20 71% → **64%**, 10-22 84% → **74%**.

**07-28 is not the exception — <!--equiv:sf-match-->fourteen of the nineteen<!--/equiv:sf-match--> measured sessions lose coverage
to the second family**, and
every claim that drops is windowed or per-match (08-01 C002, 08-09 C005, 08-14 C007/C019/C020,
08-19 C007, **09-17 C007**, **10-03 C007**, **10-09 C024/C025**, **10-12 C007/C020**, **10-20 C016**, **10-22 C020/C021**). **That count used to be at `match` granularity only, and `match` used
to be the only reading on which any session was exempt**: 07-24 loses nothing there (48 → 48) but
loses R018 at `round`, so for nine sessions the `round` count was every session measured. At eighteen
it is **<!--equiv:sf-round-->fifteen of the nineteen<!--/equiv:sf-round-->**, because 2026-09-10,
2026-09-11, 2026-09-18 and 2026-09-19 are the four that lose nothing at EITHER
granularity — 13 of 16, 12 of 15, 24 of 27 and 25 of 28 at all three, the same covered
set each time.
Two granularities in one paragraph is how "five of the six" outlived the six-session corpus it
was measured on — check which one a count came from before carrying it forward.

**Why 09-10 and 09-11 are exempt is worth reading, because it is not those sessions being better
covered.** 09-10's 81% was joint-lowest with 07-22 and 09-03; **09-11's 80% was the corpus low
outright** until 10-12's 79%, which is not exempt. Each holds exactly ONE windowed claim (C010 both times — the round totals, plus the
28-28 after seven matches on 09-10 and the 8-20 after four on 09-11), and C010 is already in the
`covered` set at single value — a generated claim implies it — so the second family has nothing
left to take. The other sessions' drops are all claims that single-value could not falsify and
two-site could; here there are none of those, because both ledgers put their windows in one claim
rather than spreading them across the regime and route claims. **So a session can be exempt for
having FEWER windowed claims, not better ones**, and 「loses nothing to the second family」 must
never be read as 「is well covered」. C002, C003 and C008 are
uncovered at all three granularities in both, exactly as they are at single value.

**That paragraph used to end 「the two exempt sessions are the two LEAST covered in the corpus,
which is as sharp a statement of that as the data can make」, and 2026-09-19 falsified the sharp
half while confirming the mechanism.** It was the THIRD exempt session — 89% at all three
granularities, losing nothing — and the best-covered session in the corpus bar 07-24 and the
two 100%s. So exemption does not track poor coverage, and the sentence that said it did was an
observation about two sessions dressed as a principle.

**2026-09-18 is the FOURTH, at the same 89% and with the same uncovered set, and it settles what
the exemption does and does not track.** Four exempt sessions now span 80% to 89% coverage and 51
to 150 rounds — the corpus low at the time (second-lowest since 10-12) and two of its three highest, its smallest-but-four and its largest
and third-largest — so neither coverage nor size predicts exemption. Every one of the four has the identical
uncovered set **{C002, C003, C008}**, and every one of them mints no claim the second family can
falsify: 09-10's and 09-11's windows sit in C010 alone, 09-19 minted no C007 because its per-match
ordering interleaved, and 09-18 did not either, for the same reason. The mechanism is the whole
of it.

**2026-10-03 is NOT exempt, and it is the third test of the mechanism from the other side.** It
mints C007 (its per-match ordering separates) and loses exactly that claim to the second family —
26 of 30 at single value, 25 of 30 at both granularities — as 09-17 did.

**2026-10-09 is NOT exempt either, and it is a further confirmation of the 09-17 reading rather
than a new one.** Its ordering interleaves, so no C007 was minted — on 09-19's reading it would be
exempt. It is not: 19 of 23 at single value, 17 of 23 at both granularities, and the claims it
loses are **C024**, 「the higher attack total won 10 of 12 matches」 — per-match, and implied by no
generated family — and **C025**, m7r8's own attack (207 against 172) and the 23 the session lead
falls to without it, a single-round datum read against the session total that a value-preserving
move between rounds breaks while every total stays put. It is the first of the mechanism's tests
since 09-17 in which the claim lost is not C007, but not the first in the corpus — 08-14's C019 and
C020 are per-match too and dropped the same way — so it confirms the shape reading the 09-17
paragraph already states and adds nothing to it. Its single-value uncovered set is
{C002, C003, C008, C023}: the usual three plus C023, the all-twelve-matches APP lead together with
the cross-multiplied ordering that makes m10's gap the smallest and m4's the second-largest, which
is uncovered at every granularity.

**2026-10-12 is NOT exempt, and it is 10-03's case with a second per-match claim beside it.** It
mints C007 (its per-match ordering separates) and loses it to the second family, as 09-17 and 10-03
did, and loses **C020** with it — m3 as the one match in which yachi's APP is the higher, a
per-match claim a value-preserving move between matches breaks while every total stays put: 15 of
19 at single value, 13 of 19 at both granularities, C006 untested. Its single-value uncovered set
is {C002, C003, C008, C019}: the usual three plus C019, the attack total deciding all eight matches
— per-match like 10-09's C024 and, like it, implied by no generated family. Nothing here is new to
the mechanism; it is recorded because the exempt/not-exempt split is a set, and a session that
lands on the side the mechanism predicts is still a session that could have landed on the other.

**2026-10-20 is NOT exempt, and it loses the per-match claim it holds instead of a C007.** Its
ordering interleaves, so no C007 was minted; what it loses is **C016** — m2 as the one match in
which yachi's APP is the higher, the same shape as 10-12's C020: 10 of 14 at single value, 9 of 14
at both granularities, C006 untested. Its single-value uncovered set is {C002, C003, C008, C015}:
the usual three plus C015, the attack total deciding all four matches — 10-12's C019 again, implied
by no generated family.

**2026-10-22 is NOT exempt, and both claims it loses are per-match.** Its ordering interleaves, so
no C007 was minted; it loses **C020** (pinglamb's APP higher in all nine matches, with m8's gap the
smallest and m5's above 31%) and **C021** (the attack total deciding 7 of the 9, m1 and m6 the two
yachi wins with less attack): 16 of 19 at single value, 14 of 19 at both granularities, C006
untested. Its single-value uncovered set is the usual {C002, C003, C008} alone — the first session
since 09-19 with nothing beyond those three at single value.

What actually moved is the DENOMINATOR, and it is the same arithmetic the shortfall table's y-axis
turned out to have. 09-19 has twenty matches, so its ledger carries twenty `round_seq` claims
(C011-C030), every one of which a generated per-match family already implies. Twenty easy covered
claims lift 25/28 to 89% without anything about the hard claims changing: its uncovered set is
**C002, C003 and C008 — exactly 09-10's and 09-11's**. Read as a fraction the session looks
better covered; read as a set it is covered in precisely the same places and uncovered in
precisely the same places. **A coverage percentage over a ledger whose size the session's match
count controls is not comparable across sessions**, which is the reason `check_equiv_coverage`
stores verdict SETS rather than percentages — its own docstring says a scalar gate is structurally
blind, and this is what that blindness looks like from the reader's side rather than the gate's.

**Two sessions was where this stopped being an anecdote about one ledger and started being a
property of how these ledgers get written; at four it is that property and nothing more.** The windowed claims of 07-28 through 09-03 are spread across
the regime and route claims, so the second family finds them; 09-10's and 09-11's are concentrated
in one claim a generated family already implies. Nothing about the second family changed — what
changed is where a hand-written ledger puts its windows, which is an authoring choice and not a
measurement. Read the exemption as a fact about the ledger, never about the session.

**2026-09-17 is the test that explanation needed, and it passes.** That ledger holds C010 exactly
as 09-11's does — one windowed claim, already implied at single value — so on a reading where the
exemption were about the session it would be exempt too. It is not: it drops from 13 to 12, and
**the claim it loses is C007**, the per-match separation. C007 is the only claim this ledger adds
beyond 09-11's shape, and per-match is precisely what the second family can falsify and
single-value cannot. So the mechanism is confirmed by the one session that could have refuted it:
what decides the exemption is whether the ledger holds a windowed claim a generated family does
NOT already imply, and nothing else. It also prices the authoring choice — minting C007 is what
cost the point, and it was worth it.

**2026-09-19 is the second such test and it passes the same way, from the opposite side.** Its
ledger holds C010 and mints NO C007 — the per-match ordering interleaves, so the claim was not
available to write — and it is exempt, exactly as the mechanism predicts. Put beside 09-17 the
pair is a controlled comparison the corpus supplied by itself: same ledger shape, the presence or
absence of one per-match claim, and the exemption follows that claim and not the session, the
size or the coverage. Twenty matches did not cost it a point, because twenty `round_seq` claims
are all implied at single value; one C007 would have.
`sum_round_range` arrived at 07-28 and every session since uses it, so a single-value figure
published alone is blind to exactly the headline claims. `check_equiv_coverage.py` fails the
build if one is published without its two-site companion for a session holding windowed claims.

**The single-value figures were a seeded sample until 2026-08-15.** One perturbation kind was
drawn per site, so 07-22 read 85% at the committed seed, 87% at seed 3, 83% at seed 42 — with
the denominator moving too — while the docstring claimed the whole space of one-value changes.
Every kind is enumerated now: ~5× the mutants, deterministic across seed and `PYTHONHASHSEED`,
and 07-22 settles at 81%. `--seed` survives only because `--samples` still draws.

**The delta is HALF the source, and that is not a detail.** The first implementation moved the
whole value, leaving every source round at 0 — 145 615 of 145 615 moves — so its evidence was
rounds like `pieces=0, lines=48, lifetime=65591`, which no extractor can emit. It also made
both its asserts tautologies (`(va-d)+(vb+d)==va+vb` is an integer identity; `va-d>=0` with
`d==va` is `0>=0`), i.e. decorative guards sitting under a comment claiming the very standard
the code broke. And it *inflated* the result: 07-24 read 96% under whole-value moves against
98% under legal ones. Sources below 2 are dropped and counted. The surviving guard
(`1 <= d <= va - 1`) is unreachable by data and guards the delta *rule* — mutate it to `d = va`
and it fires, which is the mutation test that licenses keeping it.

`--two-site` is off by default; `match` granularity is an upper bound on coverage and `round`
must be re-run before publishing a figure.

07-28's own finding is about *change over a night*, which no earlier session asked: yachi won
the first two matches and lost six straight, but his rate did not collapse — in matches 1-2 the
two players' APP were level (0.62305 vs 0.62216, yachi ahead by 0.0009) and from match 3 they
separated, pinglamb +4.99% and yachi −4.92%. Both totals are nearly equal (attack 3264 vs 3249)
because yachi threw 378 more pieces to get there. 企得穩嘅係「兩邊差唔多」,唔係個差額:
「差 15 行」得一局撐住（留一局：抽走 m8r8，數字變 -49 行，即係郁 34 行），連正負號都反轉。
That is what `sum_round_range` exists for.

08-01 asks the next question down: **APP decides a round, and it does not decide a night.**
pinglamb's APP was higher in all seven matches and in both regimes — his won rounds beat
yachi's won rounds, his lost rounds beat yachi's lost rounds — yet he lost the series 3:4. The
totals land on top of each other (attack 3394 vs 3426, in-game score 1087345 vs 1087921, 0.05%
apart) because yachi bought the 7% efficiency gap back with 326 extra pieces at a higher PPS
in all seven matches. 兩個差額都係一局話事——攻擊差額
（留一局：抽走 m1r4，數字變 -1 行，即係郁 31 行），分數差額
（留一局：抽走 m6r5，數字變 +11480 分，即係郁 12056 分），兩個都會反轉正負號。
所以「差 32 行」同「差 576 分」唔好照抄,企得穩嘅係「兩邊撞埋一齊」。 Two routes, one destination; the night was then decided by *which* rounds
fell where — the seven matches alternate winners perfectly, so it came down to the last one.
Same window operator, per-match windows this time: `sum_round_range(pl, f, mi, mi+1)` is how
"in all seven matches" gets proved match by match instead of asserted from a session sum.
The visible cost of the volume route is in the death tally: 6 of the 8 topouts are yachi's.

## 速率紀錄要有局長下限 — and the two holes cutting one opens

For three sessions the APM/VS records were the plain argmax and were **all** short-round
artifacts. A rate has the round's length in its denominator, so over a short round it is a
sample mean over a small n. Measured in `analysis/rate_records.R` over all
<!--rate:corpus-->2814 player-rounds<!--/rate:corpus--> (<!--rate:sessions-->nineteen sessions<!--/rate:sessions-->):
regressing log SD on log t gives **<!--rate:slopes-->−0.676 for VS and −0.755 for APM<!--/rate:slopes-->**,
slope 0 rejected for both (p <!--rate:slope-p-->2.3e-07 / 3.8e-06<!--/rate:slope-p-->).
**<!--rate:records-->52<!--/rate:records-->** of the
<!--rate:records-denom-->57<!--/rate:records-denom--> unqualified records
(<!--rate:records-basis-->3 metrics × 19 sessions<!--/rate:records-basis-->) came from the shortest
quartile — p = <!--rate:records-p-->5.1e-26<!--/rate:records-p--> — and 07-22's headline
約<!--rate:headline-vs-->262.5<!--/rate:headline-vs--> was a <!--rate:headline-t-->15.6 s<!--/rate:headline-t--> round,
<!--rate:headline-pct-->46%<!--/rate:headline-pct--> above that session's qualified peak.

**That sentence read 「All 21 … (3 metrics × 7 sessions)」 until 2026-08-25, and the eighth session
broke the absolute.** 24 records, 23 in the shortest quartile: 08-25's VS record (pinglamb, m2r1,
178.1 over a 45.5 s round) is the first that is not. The wording had to change, not just the
numbers — 「All N (= 3×S)」 encodes an equality between two fragments that had been equal by
accident for seven sessions, and the renderer supplies them independently, so pasting alone would
have published 「All 23 (3 metrics × 8 sessions)」, i.e. 23 = 24. **A fragment pair whose sentence
asserts a relation between them is not made safe by both fragments being gated.** The conclusion is
untouched and in fact sharpened by every session since: 23 of 24 against a 0.25 base rate was
p = 2.6e-13 at eight. **Those two figures are the EIGHT-session record and are deliberately not
refreshed** — the live pair is the gated one in the paragraph above, and the denominator there is
now rendered rather than typed for the reason given in 冇第二份's eighth instance: it spent three
sessions as a literal 24 beside a factor pair that had moved to 3 × 11.

Read the quartile per SESSION, not against the corpus-wide cut the script prints beside it (「under
32.6s」 at seventeen sessions; this sentence carried a typed 35.5 s, from an earlier corpus, until
2026-10-12's pass — re-read it off the script's section 1, never from here). That figure is
the corpus-wide first quartile and is context only; `findInterval` uses each session's own
quantiles, so a record is 「in the shortest quartile」 relative to the night it was set. 08-25's PPS
record sits at 38.8 s — above the corpus cut, inside its own session's shortest quarter, and
therefore counted.

**Every figure in that paragraph, and in the three below it, is a marked fragment byte-compared
against `analysis/rate-records.json` by `pipeline/check_rate_records.py`.** Until 2026-08-23 they
were hand copies of a script that ran in no workflow and no `bin/` script. Two of them were
wrong — the band below, and 「約262.6」, which this very document identifies six hundred lines
further down as the ROUNDED figure the 2026-07-26 約-floor pass replaced with 約262.5 in every
report. (`check_prose_figures` runs over a session's report directory, so the one place still
publishing the value it corrected away was the file that records the rule.) A third copy lived
outside this section entirely: twenty-six lines of FOUR-session statistics in a comment beside
`QUALIFYING_MS` in `generators.py`, deleted rather than refreshed.

**Two things in that paragraph changed when the sixth session was added, and the honest version
is weaker than the five-session one. Both still hold.** (a) APM's −0.5 is **outside**
its CI — [−0.918, −0.525] at six, <!--rate:apm-ci-->[−0.871, −0.639]<!--/rate:apm-ci--> now — so
the decay is *steeper* than a pure sample mean and the conclusion holds a fortiori, but "both with
−0.5 inside the CI" is no longer true; (b) the mean is **no longer flat for VS**
(<!--rate:vs-mean-->97.1 → 119.3<!--/rate:vs-mean--> across the bins, p = <!--rate:vs-mean-p-->2.5e-04<!--/rate:vs-mean-p-->)
— longer rounds do carry a mildly higher mean VS. The SD still falls several times over the same
span, so the variance effect dominates and the qualifier stands, but the control is now "the mean
moves a little, the spread moves a lot", not "the mean is flat". **PPS's mean is NOT flat
again, and only just**: it read flat for sixteen sessions (p = 0.06 at sixteen), crossed at
seventeen (0.048, ceiled to 0.049), read flat at eighteen (0.0505, floored to 0.050), and at
nineteen it is p = <!--rate:pps-mean-p-->0.048<!--/rate:pps-mean-p--> (ceiled; unrounded 0.0470),
i.e. under 0.05 by three thousandths — the 0.048 / 0.059 situation KPP was in, a margin and not a
finding, crossing the line in each of the last three sessions. It moves the
OTHER way from VS, <!--rate:pps-mean-->1.462 → 1.413<!--/rate:pps-mean-->
across the bins, so shorter rounds carry the higher mean PPS; the SD still falls about three
times over the same span, so the control for PPS reads as VS's — the mean moves a little, the
spread a lot — and PPS carries no record qualifier for it to bear on.

**A rounding DIRECTION is per claim, not per number, and applying that moved three of these.**
A p supporting 「rejected」 must ceil, because a p rounded down claims more significance than the
fit gives — 8.6e-05 / 5.3e-05 became 8.7e-05 / 5.4e-05. A p supporting 「still flat」 must floor,
which is why PPS's 0.25 did not move — and why, at seventeen sessions, PPS's p CEILED: the sentence
beside it stopped saying 「flat」, and a direction belongs to the claim, so it flipped with it; at
eighteen the sentence says 「flat」 again and the p FLOORS again. The precision had to move as well
at seventeen, and stays at three places through the flip back. At two places 0.048 ceils to 0.05, which does not support the
rejection it is printed under; the right direction at the wrong precision still publishes a
figure contradicting its own sentence, so the fragment is quoted at three. A CI quoted to show −0.5 lies outside it widens rather than
narrows. And the two ratios below are quoted against each other, so the one the argument needs to
be large floors and the one it needs to be small ceils.

**Do not quote a number for that SD fall from here, and do not put one in the report either** —
paste it. `records.r_stats()["sd_ratio"]` derives it through `fmt.ratio1`, which floors:
4.1× at six sessions, **<!--rate:sd-ratio-->4.4×<!--/rate:sd-ratio--> now**. The report's
footnote said 「足足細咗四倍」 as a typed word for six sessions, where it was true, and shipped
**false into all seven rendered reports** the day 08-19 landed, because 足足 asserts a floor of
four and the ratio had fallen to 3.82. Nothing could catch it: `check_prose_figures` resolves
約-figures against facts.json, and this is a derived R statistic that appears in no dataset. It is
computed now, and guarded — `_MIN_SD_RATIO = 2.0`, which is the ratio the *argument* needs (the
mean moves <!--rate:mean-ratio-->1.23×<!--/rate:mean-ratio--> over the same span, so the spread must
clearly dominate it), deliberately not the 4 the number happens to sit near. A guard set to
today's measurement is a copy of the measurement.

**The script's session list was the last unguarded one in the repo, and it is gone**: `sessions`
is globbed off disk, `--json` writes `analysis/rate-records.json`, and `pipeline/records.py` reads
that artefact instead of holding copies of its output. The artefact records the md5 of every
`facts.json` it read AND of the R script itself, which is what closes the half a session-count
guard never could — on 2026-08-16 the rates were re-sourced from the live tick to
`results.aggregatestats` and the shortest bin's VS SD moved 59.91 → 59.60 with the corpus
unchanged at six. Three ways to go stale, three loud failures: a session lands, the data moves,
the analysis moves. The script hash is over the WHOLE file, comments included, because a rule
that tries to tell a comment from a statistic can be fooled; the cost is one re-run.
(Two older repairs, kept because both are still the reason a line reads as it does: the records
test carried a literal `12` for "3 metrics × 4 sessions" and `binom.test(15, 12, ...)` aborts when
the fifth session landed, so `n_records` is derived; and `repo` was an absolute path to one
checkout, so a git worktree silently regressed the *other* tree's sessions.)

`QUALIFYING_MS = 60_000` is where definition and data agree: APM and VS are per-*minute*, and
every session's record for both names the same round for every cut-off in
<!--rate:band-->[59, 60] s<!--/rate:band-->, so the exact number is not load-bearing within a second
below it and **not at all above it**. That band was [59, 61] through sixteen sessions; 2026-10-12's
APM record (yachi, m7r8, 約71.1 over a 60.7 s round) is what closed its top, because a 61 s cut-off
excludes the round. This sentence said 「within a few seconds either side」 until 2026-10-12's pass,
a reading of a band that no longer exists. **It is not the 「50 s to 70 s」 this paragraph claimed until 2026-08-23, and
how that survived is worth more than the correction.** [50, 72] is VS's band *alone*; the sentence
named APM as well, and APM's is [54, 62] — 07-24 and 08-14 each move their APM record at a cut-off
inside 50-70, 07-24 twice. The evidence printed underneath was section 4 of the R script, **a
table of VS only**, so the one metric the claim was false for was the one the evidence could not
display. A check that cannot fail, arriving from a direction this file has not listed before: not
a tautology, not a vacuous clause, but a table scoped to a subset of the claim beside it. The
script prints all three metrics and computes each band now. Over all three the band is
<!--rate:band-all-->[59, 60] s<!--/rate:band-all-->, and **60 sits at its TOP edge**, not near its
centre as this sentence said (false for the all-metric band at sixteen sessions already, where
PPS's [58, 60] set its top at 60). So the form of "not a tuned knob" the data supports is now the
weak one: nothing moves between 59 and 60 s, and one record moves one second above. 60 is the
threshold because APM and VS are per-minute, which is the definitional half of the argument and
the one that does not move with the corpus. Counts are deliberately unqualified —
fitting more lines into a short round is harder, not easier.

Two holes opened the moment the qualifier was written, and both are now gated:

1. **The record's `count_rounds(... > v) == 0` conjuncts stopped ranging over short rounds**,
   so their APM/VS constants lost their upper bound — the only remaining constraint,
   "the winner had the higher VS", survives every increase. `mutation_test.sh` caught it
   with a 14-of-4557 random sample, i.e. by luck. `unqualified_rate_peaks` fixes it by
   keeping the unqualified maximum as its own claim (worded as the burst it is), and
   `pipeline/check_rate_coverage.py` is the deterministic gate: every short round, both
   players, both fields, must be falsifiable by *raising*. Checking "some perturbation is
   caught" is too weak (the winner-gt-loser claim catches every decrease) and checking both
   directions is too strong (a round loser's VS has never been pinned from below, and
   inventing a claim to fix that would be writing for the checker, not the reader).
   **That fix had a branch no session took for seventeen sessions, and 2026-10-20 took it.**
   `unqualified_rate_peaks` skipped a rate whose peak landed in a QUALIFYING round, on the
   grounds that the record claim 「already covers it」 — but the record's conjuncts range over
   qualifying rounds only, so 10-20's VS peak (pinglamb m3r7, a 60 s-plus round) left all
   sixteen short-round VS constants unbounded and `check_rate_coverage` went red. The repair is
   a new family at the END of `generators.py`, `qualified_rate_peaks_unbounded`, which bounds
   every round when the peak is the record; it emits nothing for the seventeen earlier sessions,
   so every earlier ledger re-emits byte-identical and no claim id moved.
2. **`==` had never appeared in a Cond**, so nobody had noticed `smt.py` passed the operator
   through verbatim — SMT-LIB spells equality `=`, and both solvers answered
   `unknown constant ==` rather than a verdict. Only `check_smt` caught it; Python and Dafny
   accept `==` happily. `smt.py` now maps operators explicitly and dies on an unknown one,
   and `spec.py`'s `c_field`/`c_dur` reject an unsupported operator at construction, so the
   failure is a build error rather than a solver error.

## C-Spin 同 DT 砲 — the second quarantined section, and its three controls

`sim/opener-facts.json` → `pipeline/opener_section.py`, gated by `check_opener_section.py`. Same
quarantine as the forecast section and for the same reason: one simulator, no second independent
implementation, so **no claim ids and no ✓ badges**, and nothing merges into `facts.json`.

The two openers are the same pair of T-spins in the two orders — **DT 砲 is a Double then a Triple,
the C-Spin a Triple then a Double** — which is why one section covers both. Order is a property
`facts.json` does not have (it counts `tspin_doubles` and `tspin_triples`, not which came first), so
it is exactly the kind of question the quarantined tier exists for.

Each metric ships with the control that says what it is NOT, and each control is enforced, not
merely documented:

- **ordering** — control is *exposure*: scored only on rounds holding both spins, and re-run over
  the whole simulated round so the short verified prefix cannot manufacture the result. Nineteen
  sessions: **1556 of 1629 run the C-Spin order and 75 run the DT order** (09-19 adds 165
  rounds holding both, 155 C-Spin orders and TEN DT orders; 09-18 adds 127, 124 and FOUR; 10-03
  adds 163, 145 and EIGHTEEN; 10-09 adds 143, 114 and TWENTY-NINE; 10-12 adds 64, 61 and
  THREE; 10-20 adds 32, 28 and FOUR; 10-22 adds 78, 76 and TWO). The two
  counts no longer sum,
  because since 09-10 a single round can register both orders — see below.

  **2026-09-19 TRIPLED the DT count in one night, and 2026-09-18 — the night BEFORE it — puts
  four more in the same band.** Per round holding both spins the DT rate
  runs 0 · 0 · 0 · 0 · 0 · 0.99 · 0 · 1.11 · 0 · 1.22 · 0 · 4.00 · **3.15** · **6.06** · **11.04** ·
  **20.28** · 4.69 · **12.50** · 2.56 %, so the last EIGHT sessions hold 72 of the 75 on 822 of the 1629 rounds — 8.76%
  against 0.37% for the first eleven (3 of 807). **10-22's two are yachi's and are not one opener** —
  `replay-2026-10-22-06.ttrm` round 4 (m5r5) is the Single 6 / Double 13 / Triple 20 pattern again,
  verified to lock 40, and `replay-2026-10-22-02.ttrm` round 6 (m2r7, Double 13, Triple 19, no
  Single, verified to 61) is an exact DT Cannon first bag, the fifth the first-bag metric
  corroborates; both windows are complete and both are DT-only. **10-20's four are yachi's and the same pattern a
  fourth night** — `replay-2026-10-20-01.ttrm` round 3, `-02` round 2, `-03` round 4 and `-04` round 0
  (0-based), verified to locks 66, 43, 150 and 116, every window complete and all four DT-only; 10-20
  has no exact first-bag match of any opener, so they add nothing to the corroboration below. **10-12's three are yachi's and are that same
  pattern again** — Single on lock 6, Double on 13, Triple on 20, in `replay-2026-10-12-01.ttrm`
  round 2, `-03` round 3 and `-07` round 3, every window complete and all three DT-only — so the
  opener is now on three nights, at 3 of his 31 rounds holding both spins rather than 10-09's 29 of
  65. **10-03's eighteen are all yachi's**, and seventeen of them share one lock pattern —
  a T-spin Single on lock 6, a Double on lock 13 (12 once), a Triple on locks 18-20 — so this is
  one opener he played repeatedly that night, not eighteen independent events. The eighteenth,
  `replay-2026-10-03-07.ttrm` round 2 (Double 14, Triple 19, no Single), is an exact DT Cannon first
  bag; `replay-2026-10-03-15.ttrm` round 4 has its Triple on lock 20 with the prefix verified to
  exactly 20, i.e. on the boundary. **10-09's twenty-nine are all yachi's too, and all
  twenty-nine are that same pattern** — Single on lock 6, Double on 13 (12 twice), Triple on
  18-20 — in at least one round of every one of the twelve match files: 29 of the 65 rounds in
  which he held both spins (44.6%), against pinglamb's 0 of 78. The smallest verified prefix among
  them is 29 locks and every window is complete, so none sits on the prefix edge. Two consecutive
  sessions six days apart now show the same opener played over and over by one player, which is
  a description of what he chose to open with, not a mechanism, and still not a reason to relax
  the list: all 29 are named in `DT_ORDER_IN_OPENER` and `DT_ONLY_IN_OPENER`.
  None of 09-19's ten is a prefix artefact (`ordering_full_round` drops the verification
  requirement and finds the same ten), and 09-18's four verify to locks 86, 81, 30 and 135 against
  the opener window. The repeated pattern now has a name — stick spin, two paragraphs down — and
  that is an identification of the opener, not a mechanism for why he chose it; what IS settled is
  that 「exactly five, each investigated」 is no longer the right description of this column, and
  `DT_ORDER_IN_OPENER` says so at its own site rather than only here.

  **Every lock number in this section counts from 0, and the ordering metric's window is 22 locks,
  not 21.** `emit-opener-facts.ts` gives each spin `i`, its 0-based lock index (`.map((lk, i) => …)`),
  and `inOpener` is `i <= WINDOW_PIECES`, so the window is locks 0-21; the donation and cave
  `in_opener` columns use the same `lock <= WINDOW_PIECES` on the same 0-based index. So 「Single on
  lock 6, Double on 13, Triple on 18-20」 above is the 7th, 14th and 19th-21st piece, 「Double 14,
  Triple 19」 the 15th and 20th, and the cave paragraph's 「lock 21, the last lock inside the window」
  the 22nd piece. `emit-attack-facts.ts` numbers its locks from 1 and its opener window is 21 pieces,
  so **the two emitters import one `WINDOW_PIECES` and disagree by one about what it covers** — found
  on 2026-10-13 while checking this paragraph, and left as found: aligning either re-emits every
  session's artefact and moves published counts, which is a decision for its own pass, not a side
  effect of this one. (This paragraph said 「a 21-lock window」 in two places until then.)

  **The repeated yachi opener is SDPC Spin (Ecchou's, harddrop's `SDPC_Spin` page) — see
  「定式路線頁」, ### SDPC Spin.** It read as stick spin (SDパフェ, shiwehi.com's `stickspin.php`) for one
  pass, and that identification was of BAG 1 ONLY: SDPC Spin's bag 1 is stick spin's six-piece board
  letter for letter and the T laid flat into its T-spin Single (`bag1.pc`, the パフェ派生 branch),
  mirrored, so both route pages file the same bag-1 rounds. ~~bag 2 sits a few cells off the page's
  SDパフェ bag-2 board … bag 3 is his own TST build, matching none of this page's bag-3 boards — that
  last part is hand-measured by a 2026-10-13 probe and nothing committed re-derives it~~ — **struck
  2026-10-16: bag 3 is not his own build.** Bag 2 is still a few cells off stick spin's `2.sd` (he
  stands the L up at the right where that page lays the J flat; `BAG2_NONE_NEAR` stays true of the
  stick spin page), and it IS SDPC Spin's Second-bag board (`2.tsd`); bag 3 is SDPC Spin's Third-bag
  build, mostly its first form (`3.first`). Those figures are re-derived by `sdpcspin.test.ts`, never
  by this paragraph: `NODE_CASES` for the per-node counts, `STOPS_AT_2TSD` for every round that
  reached `2.tsd` and no bag-3 board (with the measured reason), `STICKSPIN_NEAR_NOT_2TSD` for stick
  spin's near-`2.sd` rounds that are not SDPC Spin bag-2 cases, and `DT_AND_SDPCSPIN` for the overlap
  with this column. Stick spin's own test re-derives its half: `stickspin.test.ts` reads every
  session's `ordering.per_round` and pins that **61 of the 75 Double-first rounds are stick-spin
  bag-1 rounds, all yachi's** (`DT_AND_STICKSPIN`), and names the other fourteen with a verified
  reason each in `DT_NOT_STICKSPIN`: the five DT Cannon rounds above, the two windows holding both
  orders (09-10 m7r3, 09-18 m2r3), and seven J/L-split boards — the stick-spin shape with the J and L
  cells divided another way, four of them pinglamb's (10-20 adds two of yachi's, m1r4 and m3r5). **That J/L split is SDPC Spin's other drawn
  colouring** (`bag1.lj`; SingleYou draws it too), so on the SDPC Spin page those rounds are ordinary
  cases, and `sdpcspin.test.ts` asserts that every stick-spin bag-1 case is an SDPC Spin case and names
  every difference. Per session, hand-summed on 2026-10-13 from the
  same two artefacts and to be re-derived, not carried: 09-17 1 of 2, 09-18 1 of 4, **09-19 8 of 10**
  (the other two pinglamb's J/L split, so 09-19's DT rounds are mostly this opener, which is the
  reading that night lacked), **10-03 16 of 18** (the others the DT Cannon m7r3 and the J/L split
  m7r7 — together the seventeen that share the lock pattern), 10-09 29 of 29, 10-12 3 of 3 and
  10-20 2 of 4 (the other two its J/L split; all four are SDPC Spin cases reaching `3.first`) and
  10-22 1 of 2 (the other its DT Cannon m2r7).

  **What 09-18 removes is the reading that 09-19 was one anomalous night**, which was the only
  way to hold the column's history and its last entry together at thirteen sessions. It does not
  replace it with a mechanism. Note also that 09-18's four arrived AFTER 09-19's ten in this
  repo's history while sitting BEFORE them in date order, so 「the last five sessions」 above is a
  date-ordered statement and the exception list's own numbering is an arrival-ordered one; the two
  disagree here for the first time and both are labelled at their own sites.
  **The corroboration by the first-bag metric is 5 of 75 — it was 3 of 5, then 3 of 15, then 3 of
  19, then 4 of 37, then 4 of 66, then 4 of 69, then 4 of 73, and the ratio has fallen because the denominator grew rather than because the
  instrument changed.** 09-19 has zero
  exact DT Cannon first bags and both players' nearest is 6 cells away, and 09-18 likewise has
  none, so between them they contribute fourteen to the denominator and nothing to the numerator;
  10-09 has no exact first-bag match of ANY opener, so its twenty-nine add nothing to it either,
  and neither has 10-12, whose three add nothing. 10-22 is the first session since 10-03 to move the
  numerator: one of its two is an exact DT Cannon first bag (m2r7).
  「3 of 5」 must not be carried forward; it was a statement about five rounds, and 「3 of 15」 was
  one about fifteen. 09-17 remains what settles that the corroboration is a property of
  the ROUND rather than of the session, the player or the metric.
  The first, yachi's `replay-2026-08-14-2.ttrm` round 3 (m3r4): a T-spin Double on lock 13 and a
  Triple on lock 18, and — from a completely different input, the board's occupancy at the end of
  bag 1 — an **exact** match against harddrop's DT Cannon page, as drawn and mirrored. Through five
  sessions every exact first-bag match had been a PCO, which made "the instrument only ever finds
  one thing" a fair worry; it is answered.

  **2026-08-25 is the second, and the corroboration repeated.** yachi again, this time
  `replay-2026-08-25-09.ttrm` round 2 (m9r3): Double-before-Triple inside the window, and the
  first-bag metric independently reaches the same round as an exact DT Cannon match. Two for two,
  from inputs that share nothing but the round — bag-1 occupancy on one side, spin lock indices on
  the other. **That is what the exception list bought.** Both are pinned in `openers.test.ts`
  (`DT_ORDER_IN_OPENER`, and the exact-match block) as a *named exception list* rather than a
  relaxed bound, so the second one arrived as a RED BUILD to investigate rather than as a number
  absorbed under a `<= 1`; a `dt_order <= 1` bound would have been satisfied by it silently and the
  pairing would never have been looked for. A third must be investigated the same way.
  Neither is a short-prefix artefact: the verified prefixes run to lock 208 and lock 117
  respectively, well past the opener window (0-based locks 0-21). `opener_section.py` needed no change — it already
  had the branch for a non-zero DT count.

  **2026-09-10 is the third, it arrived exactly as the list was built to make one arrive, and it
  BREAKS the pairing.** `replay-2026-09-10-07.ttrm` round 2 (m7r3), prefix verified to lock 67, so
  not a short-prefix artefact either. Two things are new and only one of them is cosmetic. It is
  **pinglamb's**, the first not yachi's. And the first-bag metric does not reach it: 2026-09-10 has
  **zero** exact first-bag matches of any opener, and pinglamb's nearest DT Cannon first bag all
  session is 8 cells away. So the corroboration is **2 of 3, not a property of the metric**, and
  「both positives have two independent metrics naming the same round」 has to be read as what it
  was — a statement about two rounds. That sentence was written when it covered every case, which
  is the correct way to write one; it is the carrying-forward that would have been the mistake.
  What survives is better than what it replaced: the ordering metric finds Double-first openers
  that the first-bag metric cannot see, which is what two metrics scored on different inputs are
  FOR. A fourth must be investigated the same way, and the question to ask it is which of the two
  patterns it joins.

  **2026-09-17 supplies the FOURTH AND FIFTH, both yachi's, in one night — and between them they
  answer that question with 「one each」.** Neither is a short-prefix artefact.

  * `replay-2026-09-17-02.ttrm` round 6 (m2r7), prefix verified to lock 28, past the 21-lock
    window. **No first-bag corroboration** — 09-10's pattern.
  * `replay-2026-09-17-07.ttrm` round 3 (m7r4), prefix verified to lock 103. **The first-bag
    metric independently reaches this exact round** as an exact DT Cannon match, as 08-14's and
    08-25's did.

  So the corpus holds five Double-first openers and the first-bag metric reaches three of them.
  The informative part is not the ratio, it is that **one session, one player and one night
  produced both outcomes**: whatever decides whether the first-bag metric sees a Double-first
  opener, it is not the session, not the player and not a change in either instrument. It is the
  round — which is what two metrics scored on different inputs are supposed to be able to
  establish, and could not while every instance pointed the same way. Both are named in
  `DT_ORDER_IN_OPENER`, and both are DT-ONLY rounds so they appear in `DT_ONLY_IN_OPENER` too;
  09-10 is in the first list and not the second, which is what keeps the two quantities separate.
  A sixth must still be investigated the same way.

  **A round can register BOTH orders, and nine sessions never showed it — now two rounds do.**
  09-10's m7r3 window holds one
  Double and two Triples, so it reads Triple-Double-Triple: `cspin_order` 1 and `dt_order` 1 in the
  same round. **2026-09-18's `replay-2026-09-18-02.ttrm` round 2 is the second**, the same shape
  on pinglamb, so 09-10 is no longer the only session where `DT_ORDER_IN_OPENER` and
  `DT_ONLY_IN_OPENER` disagree — a sentence both lists carried until this session. `openers.test.ts` asserted `cspin_order === rounds_with_both - DT_ORDER_IN_OPENER[…]`,
  which silently encoded 「a DT round is not also a C-Spin round」 — true whenever the window carries
  exactly one of each, which is every earlier case. The subtraction now goes through
  `DT_ONLY_IN_OPENER`, a separate named list that is empty for 09-10; the arithmetic identity it
  was standing in for is `rounds_with_both - cspin_order` = rounds showing no Triple before a
  Double, which is a different quantity from `dt_order`.
  **It names a CLASS, not the C-Spin, and that was found by measuring the named openers.**
  harddrop files **38** openers under `Category:Triple Double openers` — C-Spin, Honey Cup, Stray
  Cannon and Mountainous Stacking among them — and every one opens Triple-before-Double. A session
  playing Honey Cup every round would produce the same near-unanimity. The category is transcribed into
  `wiki-openers.json` (a class this repo drew itself would be a class chosen to fit the result) and
  `check_opener_section.py` fails if the table is published without the paragraph saying so.
- **first bag vs the catalogue** — control is *set choice*. `isCSpin` is a substring match whose
  three hits are `Fake C-Spin`, `Secspin` and an `SDPC-Spin` compound — arguably no real C-Spin at
  all — so every number is reported over a narrow and a widest reading of both openers
  (`NAME_SETS`). The reportable finding is that the answer does not move. A null here is always
  "not these catalogued pages", never "not this opener". **For sixteen sessions no clean first bag
  came within 4 cells of any C-Spin page, and 2026-10-12 ends that absolute with one board** —
  pinglamb's `replay-2026-10-12-07.ttrm` round 0, exactly 4 cells from the mirrored `SDPC-Spin`
  compound page, i.e. the doubtful third hit above. It is not a C-Spin: the board is 2 cells from
  SE Cannon 2, matches nothing exactly and the round holds no Triple, and the widest name set reads
  the same 1 within 4. It is pinned by name in `openers.test.ts` rather than under a bound, and it
  is the case this control exists for.
- **slot geometry vs harddrop's 38 diagrams** — control is the *cross-tab by lines*, and it is the
  reason this may be printed at all: ~9 in 10 Triples match the window against ~1 in 10 Doubles, so
  it detects a Triple-shaped slot, not an opener. `check_opener_section.py` fails if the Doubles
  sentence is deleted while the share stays, because that edit turns a shape test into "89% of
  these were C-Spins".

**The per-round and per-match rows carry the C-Spin count beside the T-spin counts it is bounded
by, and the two sides are NOT the same rounds.** `ordering.per_round` gives every (file, round,
player) its `cspin_order`, `dt_order`, the WINDOW-scoped `tspin_doubles_window` /
`tspin_triples_window` the order is decided on, and the WHOLE-ROUND `tspin_doubles` /
`tspin_triples` read out of the replay's own twice-extracted counters; `ordering.per_match` rolls
all five up per (file, player). The two T-spin pairs are both published because reading one as the
other is the hazard — 08-19 m1r0 pinglamb has **one** Double in the opener window and **six** in the
round. The `column_legend` and `denominators` fields say this inside the artefact.

`cspin_order <= min(tspin_doubles, tspin_triples)` holds on every row and is **asserted at build
time**, so a mis-joined emitter cannot produce an artefact at all; it lived only in `openers.test.ts`
until 2026-08-24, i.e. it was checked where the rows are read and not where they are written. What
the test keeps is the part only it can do: the emitted columns must EQUAL facts.json's, which is two
independent readers of the `.ttrm` agreeing rather than one value copied twice, plus the off-by-one
join mutant that gives the bound its teeth. **Never divide the two sides into each other**:
`cspin_order` sums over SCORED rounds only (a round whose window the verified prefix never reached
is in `rounds_unscored`), while the counters cover every round, so 「呢啲 spin 入面咁多個 % 係
C-Spin」 does not follow from the row.

`emit-opener-facts.ts` exports `build()` so `openers.test.ts` can assert the committed artefact
reproduces byte-for-byte — the same rule facts.json, the ledgers and the .dfy are held to.

## 六個具名定式 — the fourth table, and the coverage bug it exposed

Honey Cup, Stray Cannon, Mountainous Stacking 1/2/3, TKI-3, PCO. Same quarantine; the metric is
"is the opening board this opener's field, cell for cell".

**Sampling at seven locks only was a coverage bug, not a choice.** A player who holds a piece
through bag 1 has locked **six** pieces when the bag ends, and that is how harddrop draws four of
the six (Stray Cannon says "keep either S or Z in hold"). A 24-cell field can never equal a 28-cell
board, so those openers were never *compared*, not scoring zero. `OPENER_LOCKS = [6, 7]` fixes it
and also reaches the 75 clean 24-cell catalogue pages that were invisible — including the PCO setup
that keeps I on hold. Pre-existing blocks re-emit byte-identical on all pre-existing sessions.

**`opener_db` alone cannot answer this**, which is why `wiki-openers.json` exists: 484 of its 783
pages are drawn on a filled base, and a page with a full row is a state that would have cleared.
TKI-3 has 12 catalogue pages and **none** are clean. Where both sources draw an opener (MS1, PCO)
they agree cell-for-cell — `cross_check()` gates that, and the mutant proving it flips a cell on an
opener both draw.

**Read the exact column, never `≤4 格`.** The baseline — the same boards against openers the player
is *not* playing — reaches the ≤4 band about as often, because these boards sit 3-4 cells from
almost any opener page. Only exact separates. `occupancy_aliases` and `round_overlap` name the
columns that are the same rounds twice: MS1 and MS2 are one bag-1 shape built from different
pieces, so their rows are identical in every session and must never be added.

**The route pages count bag 1 differently, on purpose, and say so.** Three of these columns have a
route page — Stray Cannon (`docs/stray-cannon.html`), Honey Cup (`docs/honey-cup.html`) and
Mountainous Stacking 2 (`docs/mountainous2.html`) — and each column here is that opener's harddrop
field by occupancy, while the page follows shiwehi.com's tree, which also takes a second bag-1 board
(the 6-lock held-piece field for the first two, the 7-lock board with the L stood on end for
山岳積み2号, whose harddrop field is itself the 6-lock one), so every page's bag-1 total is LARGER
than its column. Each route artefact carries the column's own predicate as a flag (`matched_at_6`,
`matched_harddrop`), its test compares that flag with this table per (session, player), and each
overview prints both totals — see 「定式路線頁」. MS1 has no page: it is the same occupancy as MS2.
A fourth route page, stick spin (`docs/stickspin.html`), has NO column here: harddrop's transcription
draws no stick spin field, so it carries no flag, and its test cross-checks against the ordering
metric's Double-first rounds instead (see 「定式路線頁」 and 「C-Spin 同 DT 砲」). A fifth, ガムシロ積み
(`docs/gamushiro.html`), has no column either, for the same reason, and is a REFERENCE opener the
corpus barely plays; its test cross-checks against the ordering metric's Triple-first rounds. A
sixth, SDPC Spin (`docs/sdpcspin.html`), has no column either (`wiki-openers.json` draws no SDPC
field), and is the opener yachi's Double-first rounds actually are: its test cross-checks against the
ordering metric's Double-first rounds both ways and against stick spin's bag-1 cases.

The repertoires split, reproduced independently in all nineteen sessions (pinned in `openers.test.ts`):
**pinglamb opens Honey Cup** more than yachi does, **yachi opens Mountainous Stacking** more than
pinglamb does **and opens TKI-3 far more** (185 against 9 over the corpus; pinglamb's nine are the
named exceptions below, and 「the only one who plays it at all」 is a sentence this file used to
carry and can no longer). PCO appears only for yachi, on 07-24, 08-01, 09-19 and 10-03. **The per-session counts are deliberately not
written here** — read them off `sim/opener-facts.json`, or off the `openers.test.ts` assertions,
which pin the ORDERING and nothing else.

**That is a decision, not an omission, and it comes out of a defect.** This paragraph used to carry
per-session ranges — Honey Cup 17-25, MS1 11-25, TKI-3 5-8 — and **two of the three were already
false when 2026-08-14 landed**, five days before anyone looked: the true seven-session ranges are
17-30, 11-26 and 5-15. Nothing noticed because **no file in the repo contains those numbers**;
they existed only in this prose, so there was nothing to re-derive them from and nothing to
disagree with them. The obvious repair — a gate that recomputes the bands — is the wrong one:
three of the five bands moved inside seven sessions, so its normal state would be red, and a gate
whose normal state is red is not a gate. The ordinal claims are what has actually reproduced
nine times, so those are what is published.

**One of those ordinal claims had a stronger absolute inside it, and 2026-09-03 broke the
absolute.** 「yachi is the only one who plays TKI-3 at all」 held at pinglamb 0 for eight sessions;
09-03 has one board of his matching a TKI-3 field EXACTLY, and the outcome column corroborates it
(`matched_and_delivered` 1 of 1). The ORDINAL claim — yachi opens TKI-3 more than pinglamb — is
untouched at nineteen sessions and is what `openers.test.ts` asserts; **the 10-against-1 beside it is
09-03's OWN counts, not a corpus total** (that is 185 against 9). 09-10 and 09-11 put pinglamb back
to 0, and then **2026-09-17 supplies the SECOND exception** — one more board of his matching a
TKI-3 field exactly, again corroborated by the outcome column (`matched_and_delivered` 1 of 1),
against yachi's 9 that night. All are named in `TKI3_OFF_REPERTOIRE` rather than absorbed into a
bound, following `DT_ORDER_IN_OPENER`.

**THE 「ONE EVERY SIX SESSIONS」 READING IS DEAD, AND IT WAS ALREADY DEAD ONE SESSION BEFORE ANYONE
NOTICED.** This paragraph said 「two boards in twelve sessions against yachi's 96」 — a rate of about
one every six sessions — and kept saying it after 2026-09-19 put **three** of pinglamb's on the
board in a single night. 09-18 then put three more, and 10-03 one (`replay-2026-10-03-04.ttrm`
round 6, delivered); 10-09, 10-12, 10-20 and 10-22 put none (yachi 11, 7, 3 and 3, pinglamb 0 all four nights). The corpus
total is **185 against 9**,
and the nine are 09-03's one, 09-17's one, three each on 09-18 and 09-19, and 10-03's one: **six of
the nine arrived on two adjacent nights**, which is not a rate of one every six sessions by any
reading.

Three things follow, and the first is about this file rather than about pinglamb:

* **The stale figure survived the session that falsified it**, because 09-19's pass updated
  `TKI3_OFF_REPERTOIRE` in the test — where the gate reads — and not the prose here, where nothing
  does. That is 冇第二份 exactly: the pinned table was right the whole time and the sentence beside
  it was wrong for a session, and only a hand re-derivation found it.
* **The ordinal claim is untouched and is still the one to cite.** 185 to 9 is a wider split than
  the 96-to-2 it replaces, and `openers.test.ts` asserts the ordering rather than either number.
* **What is genuinely new is a rate, and it is too young to read.** Three in each of two adjacent
  nights, after eleven sessions holding two between them, is either the start of something or two
  nights; this file's own rule says two sessions is not a trend, and those two sessions are one
  day apart. Recorded as counts, with no mechanism proposed.

**PCO's payoff is bounded by facts.json, and its timing is the one simulator figure with a verified
counterpart.** PCO is defined by an outcome, so the row splits in two. HOW MANY perfect clears is
`clears.allclear`, twice-extracted — see 全消 below. WHEN each landed only the simulator can say, and
what licenses printing it is that `perfect_clear_timing` compares the simulator's per-round count
with the replay's own counter for **every** player-round and emits the piece numbers as `null` unless
all of them agree. They do: **2814/2814 rounds, 337/337 perfect clears**, nineteen sessions, no
unknowns.
`check_opener_section` fails if the piece numbers are published without that agreement figure or
without harddrop's ten-piece deadline beside them.

The finding is that **9 of the 337 arrived inside that deadline**, all nine on piece 10 exactly,
and the bulk land on piece 20. These are mid-game perfect clears, not the opener. 08-01 held the
corpus's only completed PCO (yachi matched the field twice and delivered once) until 10-03:
yachi's `replay-2026-10-03-13.ttrm` round 1 is an exact PCO first bag, delivered on piece 10.
**2026-10-03 has the most All Clears of any session (38: pinglamb 24, yachi 14)**, past 09-18's
36 (pinglamb 24, yachi 12) and 09-19's 32 (pinglamb 18, yachi 14); 09-11 had 22, 08-14 20 and 08-19 ten.
The top three are the three largest sessions, so this column is reporting session length; as a
rate 09-18's 36 over 127 rounds, 10-03's 38 over 146 and 09-19's 32 over 150 are 28.3%, 26.0%
and 21.3% of rounds. 10-03's two inside the window are both yachi's, both on piece 10. **10-09 has
23 (pinglamb 12, yachi 11 [G041]), 22.5% of its 102 rounds** — fourth by count, as it is fourth
by size — and two more inside the window, again both yachi's and both on piece 10
(`replay-2026-10-09-01.ttrm` round 5 and `-12.ttrm` round 1). Neither is a completed PCO on the
first-bag metric, and the reason is worth one clause: both rounds have an EMPTY verified prefix
(the reconstruction check fails at lock 9, because the game sends that clear's attack as two
packets, 1 + 10, where the oracle sends one of 11 — the shape 10-03-04 round 2 already showed), so
the first-bag metric cannot see them. Their TIMING is still licensed, by the per-round count
agreement (204/204 for the session), which is what this row has always rested on. **10-12 has 11
(yachi 6, pinglamb 5), none inside the window** — nine on piece 20 and one each on 15 and 21.
**10-22 has 25 (pinglamb 22, yachi 3), none inside the window, every one on piece 20** — 25 over 63
rounds is 39.7%, the highest rate any night holds (09-18's 28.3% was the previous high), and it is
not a session-length effect: 10-22 is eleventh by size. pinglamb's 22 is two short of his 24 on
09-18 and 10-03, on less than half their rounds.

**That numerator was 3 for five sessions, 2026-09-10 moved it to 4 and 2026-09-17 moved it to 5,
so the streak reading is retired for good and the rate reading is what is left.** It once read
「the denominator has grown by 29 across two more sessions without moving the numerator — the
reading is *reinforced* by each of them」. Both of those movers are yachi, and **both landed on
piece 10, exactly harddrop's deadline** — the same boundary twice, which is worth noticing and is
not a mechanism. The honest version is the simple one: the RATE has been stable at roughly one
PCO-timed clear in forty, and it has never been zero. 「Still the same three」 was a
sentence that could only ever be falsified by a session doing what those two did, and after five
sessions of not moving it moved twice in three — which is the argument for writing the rate
rather than the streak, made twice over. `IN_PCO_WINDOW` in `openers.test.ts` pins it per session,
so the next one is a red build either way.

**2026-09-19 was the largest test the rate reading had had and the numerator did not move:
32 more perfect clears, none inside the window. 2026-09-18 then added 36 more and the numerator
did not move either, so the count was 5 of 235.** 10-03 added 38 and moved it to **7 of 273** —
two more on piece 10, the same boundary again, and the rate reading is the one that absorbs that
without a new sentence. Two consecutive sessions had each added more perfect clears than any
earlier session held, and neither put one inside the window; the previous largest addition was
20. That is exactly the shape the streak reading would be re-tempted by, twice over. It must not
be: a zero after two ones is
not a return to anything, and the correct summary is still the rate, which has drifted 1-in-33 to
1-in-48 and back to 1-in-39, and 10-09's two take it to **9 of 296**, i.e. 1-in-33 again, without
any session doing anything unusual; 10-12's eleven, none in the window, leave it at **9 of 307**,
and 10-20's five (pinglamb 3, yachi 2, all on piece 20) at **9 of 312**, and 10-22's twenty-five at **9 of 337**. Note what two long sessions with 68 perfect
clears between them and none in the opener window does say — the window result is not an artefact
of small per-session counts, which is the one thing the first twelve sessions could not rule
out.

**An earlier revision of this section said the opposite** — that `eng.board.perfectClear` invented
clears the sessions did not have — and it was wrong for a reason worth keeping: the facts.json
lookup it rested on read `players[u].allclear`, one level above the counter, and `?? 0` turned every
undefined into a plausible zero. All five reports published 「一個 Perfect Clear 都冇出過」 while the
`.ttrm` files held 65. Nothing caught it: the value was in range, the artefact re-emitted
byte-identically, and the test recomputed the total down the same wrong path, so it agreed with
itself. Two rules came out of it — **a required field that goes missing must throw, never default**
(`sessionPerfectClears` declares `clears.allclear` non-optional and dies on a non-number), and **a
test that re-derives a value the way the code does can only catch a typo** (`openers.test.ts` now
pins each session's counts as literals and asserts the total is not zero).

## 全消 — the Perfect Clear section, and the two questions it keeps apart

`pipeline/pc_section.py`, region `perfect-clear`, **inside** the trust chain: every figure is read
out of the proved claims' own specs (`pc_rounds`, `pc_solo_lost`, `clears_allclear`), never
re-derived from facts.json, so the table cannot print a number no lemma covers. `clears.allclear` is
read out of the `.ttrm` independently by both extractors, which is why this one is badged while the
opener tables are not.

The point is not the count. Across nineteen sessions, **266 rounds had exactly one player with a
perfect clear and that player lost 100 of them** (10-09 adds 21 and 8 [G088][G090]; 10-12 adds 7 and
3 [G078][G080]; 10-20 adds 5 and 2 [G072][G074]; 10-22 adds 23 and 8 [G082][G084]). For the pooled AUC and its corrected p, read the
AUC table above rather than this paragraph — this sentence's copy is the one 冇第二份's seventh
instance names as having gone stale at 「50.67 over 450」 and again at 「51.66 over 634」, which is
twice in the same sentence, and the fix is to stop keeping a second copy at all rather than to
refresh it a third time. **That matters more this revision than last**: the PC row crossed its
correction threshold for the first time at thirteen sessions, entirely on 09-19's 26 decided
pairs, and a stale duplicate here would now disagree with the table about a VERDICT and not only
about a digit. So the section prints "rounds won" beside "rounds with one" and refuses to print a
rate: the denominators are 2-18 rounds per player, and a percentage over two rounds reads far more
confident than the data is. Two more controls it may not lose: 全消次數 ≠ 有全消嘅局 (a round can hold two), and
"whether" is facts.json while "when" is the simulator's, in the quarantined section below.

## 最癲一局 — one round, deep-dived, and why it needed no new operator

`pipeline/intense_round.py`, region `intense-round`, **inside** the trust chain. The round is the one
`most_intense_round` already selects — highest combined VS among rounds of `QUALIFYING_MS` or more —
via the shared `generators._intense_round`, so the section and the claim that announces it cannot
describe different rounds. Seven new families per session (`intense_round_profile` ×2, `_edges`,
`_attack_rate`, `_downstack_rate`, `_vs_split` ×2); every printed figure is read back out of the
proved spec by `intense_round.py`'s readers, never re-derived.

**The selected round is often won by the player losing the attacking exchange**, which is the reason
the section exists: 逐局全數據 gives every round the same row and explains none.

| session | round | winner trailed on | DS/piece W:L |
|---|---|---|---|
| 07-22 | m1r5 | APM, attack, PPS, maxspike, **APP** | ×2.00 |
| 07-24 | m6r8 | APM, attack, maxspike, topbtb, **APP** | ×2.20 |
| 07-28 | m8r8 | lines | ×0.51 |
| 08-01 | m7r3 | topbtb | ×1.12 |
| 08-09 | m5r7 | **nothing — led on everything** | ×0.82 |
| 08-14 | m11r2 | APM, PPS, pieces, attack, maxspike, topbtb | ×1.81 |
| 08-19 | m8r2 | lines | ×0.74 |

The 08-19 row is read out of that session's proved claims (G084's axis count and non-axis column,
G086's two per-piece figures), not re-derived — the same route `intense_round.py`'s readers take.
It is 07-28's shape: the winner trailed on one column only, led on APP (0.929 vs 0.669 [G085]),
and is behind on one *non-axis* column (清走) which the table does not list because the claim does
not count it as an axis.

The table lists **columns**, while the claim and the rendered section count **axes** — APM and 攻擊量
are one axis, PPS and 粒數 are another, so 07-22's five columns are three axes and the section says
「3 條軸」. That is two vocabularies on purpose (a reader scanning the table wants the columns; the
claim must not double-count an axis), and the bolded **APP** is a third thing again: it comes from
`intense_round_attack_rate`, not from `_edges`, so it is proved but it is not one of the axes the
count ranges over. Do not reconcile these by making the numbers agree — check which family a figure
came from first.

08-09 is why the generator has two shapes. A section that only had the dramatic sentence would be
writing for the sessions it liked; the flat case prints「呢局冇得拗」 as the result it is.

**07-22's PPS entry arrived on 2026-08-16 and is the sharpest argument in the repo for sourcing a
rate at results-time.** Under the old `player.stats` tick both players read PPS 1465 in that round, so
`intense_round_edges` rendered `==` and 落速 was not a trailing axis — the claim said "2 of 4". They
threw the same 108 pieces, but yachi survived 250 ms longer (73982 vs 73732 ms), so his PPS is
strictly lower: 108/73.9667 = 1.4601 against 108/73.7167 = 1.46506, exact under the frame-count T.
The tie was two stale samples coinciding, and a verified lemma was proving it. Nothing but
re-sourcing finds that class: the value was in range, every gate was green, and an equality is
exactly the shape a mutation test cannot flag as suspicious.

**Two idioms worth reusing, both of which the algebra already supported.** The algebra has no
division, so a derived rate is *pinned* — not merely compared — by bounding the numerator against the
denominator: `v = floor(1000·num/den)` iff `v·den <= 1000·num < (v+1)·den`, one `between`. It has
teeth because the band is `den` wide while a one-unit change to `num` moves the left side by 1000.
And `|d| <= ε` is `between(d, -ε, ε+1)` — `between` is `lo <= x < hi` in all three backends.

**The VS split is a BOUND, never an equality, and that wording is load-bearing.** `vs_x1000 ·
finaltime_ms == 10⁸ · (garbage_attack + garbage_cleared)` is an identity *observed in this data*;
TETR.IO publishes no such formula and this repo must not assert one. Corpus-wide the residual is
median 1.1e-4 for the player who died and at most **6.3e-4** for a survivor, so `intense_round_vs_split`
**skips any player whose residual reaches half a unit** rather than print a bound wide enough to
swallow a line of attack. On the six selected rounds through 08-14 the worst residual is 0.028 of a one-unit change,
which is also what makes every one of them mutation-killable.

**That paragraph read "reaches 13.4% for a survivor" and "0.489" until 2026-08-16, and the 13.4% was
an artefact of the reader, not a property of the data.** The rates came from `player.stats`, a live
in-game tick sampled before the round ended, so a survivor's mid-round VS was being checked against an
end-of-round attack count — the asymmetry was in the timestamp, which is exactly why it fell on
survivors. Re-sourced from `results.aggregatestats` the identity holds to floating point, and the guard
that fired on **13 of the 760 player-rounds then in the corpus** now fires on
**<!--stat:vs-guard-->0 of 2814<!--/stat:vs-guard-->**. Do not read that as a reason to
delete it: the residual does not go to zero, it goes to a quantization floor. The `13` stays a
six-session figure on purpose — it is a measurement of the data BEFORE the 2026-08-16 re-source
and there is nothing at 900 for it to be re-derived from; the `0` beside it is re-derived by
`analysis/stat_sources.py` over every round, which is the only form of "does it still fire"
worth publishing. `finaltime_ms` is
milliseconds while the clock is frames, so the residual grows with `attack + cleared`; the corpus's
worst player-round sits at <!--stat:vs-guard-worst-->0.060 of the trigger (~17× headroom)<!--/stat:vs-guard-worst-->, and on that round `attack + cleared`
would have to reach <!--stat:vs-guard-need-->~1404 against its actual 84<!--/stat:vs-guard-need-->. That is a fact about how much garbage these two move
in a round, not a theorem.

Two gate gaps the new figures exposed, both now closed in `check_prose_figures.pools`: it had no
per-*round* derived rates (only session aggregates), and its seconds pool held `lifetime` but not
`finaltime_ms` — 169748 ms floors to 169 and no `lifetime` in that session does. A correctly floored
figure that resolves against nothing is the state the gate cries wolf from.

**Every column in `_INTENSE_EDGES` must also be a row the section prints.** In-game `score` was in it
and is not now: it has no row (it rewards drop distance, so it is not an attack proxy), which made the
claim count seven trailing columns while the table could only mark six — and the section's sentence
points *at* the marked cells. Caught by reading the rendered page, not by any gate.

## 捐窿 同 STMB Cave — two techniques that are not openers, and the arithmetic trap under one

`pipeline/openers/wiki-tspin-techniques.json` → tables five and six of the quarantined section.
Same tier as slot geometry: a **per-T-spin board-state predicate over the whole round**, scored on
the verified prefix, no claim ids and no badges.

**Neither page is an opener, and reading them as openers is the first mistake available.** harddrop
files both under `T-Spin techniques / Mid-game T-Spin setups`; their diagrams are 24-112 cells drawn
on partial stacks, so a 24- or 28-cell opening board can never equal one. Putting them in the
六個具名定式 table would have printed a column of zeros meaning "never compared" while reading as
"these players never do this" — the same shape as the `OPENER_LOCKS` coverage bug.

**The naive Donation clause is forced by arithmetic: it fires on 100% of T-spin clears.**
"The well column is filled through the rows the spin cleared" cannot fail: a full row *requires*
every column filled, so that clause counts line clears. That is not a measurement any more — it is
`NaiveClauseForced` in `spec/DonationCave.dfy`, and the corpus agrees at exactly
<!--don:naive-->100.00%<!--/don:naive--> of all <!--don:scored-->15141<!--/don:scored--> scored
clears. As a *predicate* — the shipped thresholds (cavity ≥ 4, walled) with the re-opening clause
deleted — it fires on <!--don:noreopen-band-->15.40-20.72%<!--/don:noreopen-band-->. All the
discriminating power is in the **re-opening** clause: every filled cell of the column must lie
inside the cleared rows, so the clear leaves it open surface-to-floor. With it, the rate drops to
<!--don:shipped-band-->1.79-3.66%<!--/don:shipped-band--> per session
(<!--don:donations-->365<!--/don:donations--> donations across
<!--don:sessions-->nineteen<!--/don:sessions--> sessions).

**Every band above is RENDERED from the seven artefacts, and until 2026-08-24 none of them was.**
`pipeline/check_donation_bands.py --render` prints each marked fragment; `donation.ablation` in
every `sessions/*/sim/opener-facts.json` carries that session's own counts. The per-session series
read <!--don:noreopen-series-->15.60 · 17.83 · 17.57 · 16.83 · 18.23 · 20.72 · 20.05 · 15.92 · 16.60 · 16.50 · 16.09 · 19.85 · 17.17 · 16.77 · 15.40 · 17.81 · 18.21 · 17.68 · 16.92<!--/don:noreopen-series-->
for shipped-minus-re-opening (<!--don:noreopen-ceiling-->2026-08-14<!--/don:noreopen-ceiling--> is
the ceiling) and
<!--don:cav1-series-->48.55 · 47.79 · 49.20 · 52.45 · 49.20 · 47.03 · 47.94 · 48.00 · 45.95 · 47.88 · 48.09 · 48.55 · 46.29 · 48.50 · 45.22 · 48.16 · 45.36 · 48.90 · 45.27<!--/don:cav1-series-->
for the `cavity ≥ 1` composite, whose band is
<!--don:cav1-band-->45.22-52.45%<!--/don:cav1-band-->. Pooled, neither says anything: noReopen
<!--don:pooled-noreopen-->17.29<!--/don:pooled-noreopen-->, cav1
<!--don:pooled-cav1-->47.61<!--/don:pooled-cav1--> — a per-session band can break while no pooled
number moves, which is why the series is published beside them. A session above
<!--don:cav1-ceiling-->52.45<!--/don:cav1-ceiling--> moves that band and the fix is a paste.

**The bands are quoted at two decimals on purpose, and rounding them cost the third defect.** At one
decimal the shipped band was published as 「2.1-3.3%」 while its floor is 2.08 — a band's low end
must FLOOR and its high end must CEIL or the band no longer contains what it ranges over, and 2.1
excludes 07-28. Quoting a band at the same precision as its own series removes the decision
entirely. The same rounding is what made 「74.6-77.0%」 survive four sessions unchanged: 08-14's
77.04 tied 08-09's 76.99 only at one decimal place.

**`29-34%` was wrong in ten places at once, and seven of them were byte-identity gated.** Two
comments in `emit-opener-facts.ts`, one in `openers.test.ts`, and the `means` prose of all seven
committed artefacts said the predicate minus its re-opening clause "fires on 29-34%"; the range is 28.93-36.84%, wrong at both
ends and at the ceiling by nearly three points. Re-emitting an artefact reproduced the string
exactly, so **every gate in the repo agreed with it** — a byte-identity gate certifies *unchanged*,
never *correct*, and a typed figure inside one is pinned rather than checked. The repair has two
halves and the second is the transferable one: the band is rendered here, and a per-session
artefact no longer carries a corpus figure at all, because it cannot see the other sessions and so
has no way to check one.

**This is the repair the repertoire ranges refused, and the difference is a renderer.** That entry
rejected "a gate that recomputes the bands" because three of five bands moved inside seven sessions,
so its normal state would be red — and a gate whose normal state is red is not a gate. The
objection was never to recomputing; it was that red meant *hand-measuring again*. With `--render`,
a moved band costs a paste, which is this repo's standing rule for every figure that has one.

**The two paragraphs below are the RECORD of what was corrected, and their figures are the ones
that were published at the time.** They are deliberately not re-derived; read the fragments above
for the live values.

> **This paragraph said 70-89% until 2026-08-14, and that figure names no variant of the clause it
> describes.** The bare clause is 100%; at the shipped thresholds it is 28.9-36.8%; only a composite
> with `cavity ≥ 1` lands in the band (74.6-77.0%), and it never reaches 89%. A rate was being quoted
> for something proved to be always true — the same shape as the 3379-vs-3142 note above, and the same
> lesson: a figure quoted in prose is not the thing it describes.
>
> **Quote the band as a band, and re-measure it every session — it moved on the sixth.** Through five
> sessions the shipped-thresholds-minus-re-opening rate sat in 28.9-33.6%; 2026-08-14 fires at
> **36.8%**, three points above that ceiling, while the pooled rate barely moves (31.1% → 32.4%). The
> pooled figure alone would have hidden it.

`D = 4` and "walled at the **deepest** 4 cavity rows" are harddrop's numbers, not tuned: of its 20
named setups 17 draw a four-cell cavity and 3 draw five, never three or six; and requiring *every*
cavity row to be walled drops TSS L Donation, which the page draws as a donation.

**No column is excluded for holding the T, and every plug cell must be a complete piece (since 2026-10-25, yachi:
「跟 harddrop 都計，但要完整 pieces」).** harddrop's Donation page lets the T be part of the plug — J Donation 2, T
Donation and Example 2 put the well under the T's arm, and its Shachiku_Train page's 「Donation T-Spin Double」 plugs it
with the nub — so the code no longer skips the T's own slot (it did, by its first version) and no longer skips any T
column (#88 did, for one day). In its place, `plugComplete`: every cell plugging the well inside the cleared rows that is
not the T must carry a lock index whose four cells are all still on the board in the provenance grid before the T
(`provSnaps[i - 1]`), so garbage (`-1`) and a fragment a line clear left behind are no plug. `PlugIncomplete` in
`spec/DonationCave.dfy` mirrors it, `openers.test.ts` asserts it bites on every harddrop positive (the plug re-labelled
as garbage, or split, stops being a donation on the same occupancy), and the technique tests' `donationVerdict` reads
the digest's ownership grid (`shachikutrain-qualify.ts`'s `owners`) and calls the failure `incomplete`. The ablations
keep the clause (only `naive` drops it, being the whole naive reading), so every band above moved with it.

**Nearly every donation in this corpus sits on a garbage-derived well, and 2026-09-10 is the
session that ended the absolute**
(<!--don:latest-garbage-->10-22 adds 16 of 16<!--/don:latest-garbage-->;
**<!--don:self-built-->18 of 365<!--/don:self-built-->** self-built corpus-wide).
This sentence read 「every donation … 0 self-built, every session」 for nine sessions; 09-10 and 09-11
held the first three, all yachi's mid-game `natural` plugs (`replay-2026-09-10-01.ttrm` r6 plugs a
4-cell cavity at lock 40 of a prefix verified to 64, `replay-2026-09-10-07.ttrm` r7 a 5-cell cavity
at lock 75 of one verified to 82). Counting the T's columns again (2026-10-25) took the list to ten
sessions and both players (measured, not explained). They
are named per session in `SELF_BUILT_WELLS` in `openers.test.ts` rather than absorbed into a bound,
following `DT_ORDER_IN_OPENER`; read the counts there, never here. The three long sessions hold 102
of the 365, and 09-18 carries four of the self-built ones — so 「not one of them self-built」, which
this paragraph said of those nights until then, is no longer true either. **The same
absolute was also written into every per-session artefact**, in
the `donation.caveat` string, which is the `29-34%` defect exactly: a corpus claim inside a file
that cannot see the corpus. The caveat now points at the per-player `garbage_derived_well` /
`self_built_well` split instead, and every artefact was re-emitted.
The substantive caveat is untouched and does not rest on that column either way:
the oracle keeps the engine's own seeded-RNG garbage hole *columns*, which disagree with the
ige-recorded ones 97 of 103 times over the first six sessions (`oracle-source.ts`), so the count
says the board offered the
shape that often and can never say which column was donated into. The check that finds this must
read the row's **filled** cells for the `-1` garbage sentinel: the well cell is empty by
construction and carries `null`, so testing it directly is a guard nothing can fire — that exact
bug reported every well as self-built for a whole round of measurement.

**The STMB cave is OFFSET from the T and its roof test is vacuous.** The cave shares two of the T's
three columns and reaches one past them, so the test is *overlap*, never containment — containment
misses all six drawn Basic Structures. And the cave's roof is the nub row the Double just
completed, which roofs everything beneath it by definition. A roof test would have been a decorative
guard — and since 2026-08-14 that is **proved, so there is no count here to keep current**. Two
five-session counts used to stand in for the proof and had drifted into disagreeing with each other
by 2026-08-17 — "0 unroofed runs in 1914" here against "0 of 2378 real T-spin Doubles" at
`emit-opener-facts.ts:324` — neither re-derivable from any committed artefact, because nothing emits
a count of unroofed runs. Both are deleted rather than re-measured: a corpus count is weaker evidence
than the proof it now duplicates, and it is the half that goes stale every session
(`RoofForced` / `RoofCannotDiscriminate` in `spec/DonationCave.dfy`:
conjoining a roof test
to the cave predicate yields an equivalent predicate, over the whole board width and not merely over
cave runs). The proof also shows the code assumes more than it needs: **maximality is not used** —
any cleared row above the run roofs it, and a Double always has two full rows. `IsMaxCleared` and the
two-row hypothesis are kept for fidelity to `caveAt`, not because the argument rests on them.

Two cross-tabs, and the section may print neither number without both: **by depth**, 175 of the 177
width≥3 hits are one row deep — a dimple, not a cave — leaving **2 genuine caves in 2814
player-rounds** (see below for the second); **by lines**, the same gap appears under T-spin Triples
at a *higher* RATE (9.0% vs 1.7% on 08-09; pooled over the nineteen sessions, 164 hits on 2291
scored Triples is 7.15% against 177 on 10736 scored Doubles, 1.64%), where it is ordinary TST residue.
A shape that fires more often under the spin the technique is not about is a shape test — and the
Triple-side rate is the higher one in **every one of the nineteen sessions**.

(**That is a rate claim, and the RAW counts beside it used to be read as one.** Through fifteen
sessions the pooled raw counts also pointed the same way (136 against 131); at sixteen they
reverse, 146 against 162, because 10-09's 31 Double-side hits on 796 scored Doubles — 3.9%, twice
any earlier session's Double-side rate — sit beside 10 Triple-side hits on 183. The parenthesis that
stood here called 09-18 「the one session where the Triple side is LOWER」 (10 against 13): that was a
raw-count statement and false when written, since 08-01 (4 against 8), 08-25 (6 against 11),
09-03 (5 against 6) and 09-19 (19 against 20) were lower on the Triple side too — six of sixteen
sessions on raw counts once 10-09 (10 against 31) is added, none on rate. 10-12 (5 against 4) is
not one of them, so it is six of seventeen, and the pooled raw counts stay reversed at 151 against
166; nor is 10-20 (8 against 6), so six of eighteen, at 159 against 172; and 10-22 (5 against 5) is level on raw counts and
higher on rate, so six of nineteen, at 164 against 177. (The first version of
THIS correction named only 08-01 and 08-25, missing 09-03 and 09-19 — the latter already landed
when the 09-18 sentence was written; re-derived from `stmb_cave` in every opener-facts.json.) 冇第二份's eighth class once
more — a superlative over a per-session list nobody had re-derived — and the reason the pair is
printed here as rates with their denominators.)

**2026-09-19 was the strongest version of the depth cross-tab the corpus could produce, and 09-18
repeats it.** Between them they add 33 width≥3 hits — 25% of the corpus's 131 at fifteen sessions, from two
nights — and **every one is `min_depth` 1**, so the genuine-cave count stays at the same single
round it has been at
since the metric existed, over 2314 player-rounds instead of 1468 — and 10-03 adds 18 more,
all `min_depth` 1. That the ratio held through the three largest sessions in the corpus is what makes 「dimple, not cave」 a
measurement rather than an artefact of how few hits each earlier session contributed.

**2026-10-09 holds the corpus's SECOND genuine cave — the first new one since the metric
existed.** pinglamb, `replay-2026-10-09-01.ttrm` round 5, lock 55 of a prefix verified to 73: a
T-spin Double clearing two rows over a gap 3 wide and 2 deep to the floor in columns 2-4, offset
from the T over columns 3-5 — the drawn shape, not a dimple. It is mid-game, so the CAVE claim
below (no genuine cave inside the opener window) is untouched. The session's other 30 width≥3 hits
are all `min_depth` 1 (as are 10-12's four, 10-20's six and 10-22's five), so 「dimple, not cave」 survives at 175 of 177; what does not survive is
「exactly one, the same single one」, which this paragraph and the window section both said, and
which was a count, not a law.

**The class control is the article's own comparison list, not a category.** harddrop has no
"floating T-spin" category; `Mid-game T-Spin setups` (63 pages) is a *when*, not a shape, and
`Back-to-Back T-Spin setups` (38) does not even contain STMB Cave. The page itself says the cave
"is just Sky Prop but with 3 columns wide hole" and that a variant "has the same shape and steps as
Shachiku Train", so the metric names a **class** — the same move the `Triple Double openers`
category makes for the ordering metric. All three category counts are recorded as evidence.

Both metrics are licensed by one check: the per-lock board snapshot plus the lock's cells must make
exactly the rows full that the engine independently recorded clearing. Different state, so it is a
real gate — **15141/15141 across nineteen sessions**, and a spin it cannot reconstruct is dropped, never
scored. (This line read **3379/3379** until 2026-08-14. 3379 is the *whole-round* T-spin clear total
over the five sessions there were then; the check is scoped to the verified prefix, which was 3142.
The figure was written from a whole-round probe and matched no committed artefact —
`donation.check.tspin_clears` is what sums to the gate, and the whole-round total is now 16281, so
the two still differ by 1140. Nothing caught it because CLAUDE.md is prose: a gate figure quoted here
is not the gate.)

### 分母錨咗 replay 自己數嘅 counter — the one part of this section that is not simulator-only

The reconstruction check above is *internal*: two states the same engine built separately. It says
the boards are coherent; it cannot say the engine counts T-spins the way the game does. That
question has an outside witness — `results.stats.clears.tspindoubles` and its seven siblings, which
`extract.py` and `extract2.ts` each read into facts.json as `tspin_doubles` etc. **Both extractors
agree on them, so they are inside the trust chain**, and `tspinCounterCheck` compares them per
player-round, per kind, over the whole round:

| | |
|---|---|
| rounds where every kind agrees | **2814 / 2814** (nineteen sessions, no unknowns, 0 unclassified sim clears) |
| whole-round T-spin clears, sim vs replay | **16281 = 16281** |
| what the verified prefix scores of them | **15141**, i.e. **92.99%** coverage (floored) |

So the two tables' **denominator** leaves quarantine: `tspin_clears_scored` is now a subset of a
total the trust chain already carries, and 「可核覆蓋」 names the subset. This is the
`perfect_clear_timing` pattern (2814/2814 against `clears.allclear`) applied to a denominator
instead of a timing.

**The numerators do not.** Which clear was a donation, and how wide the gap under it was, still come
from one simulator with no second implementation — so the section keeps `report_eligible: false`,
mints no claim ids and carries no ✓ badges. `ANCHOR_MARKERS` / `CAVE_ANCHOR_MARKERS` in
`check_opener_section.py` demand **both** sentences at both tables, because deleting the second
while keeping the first is exactly the edit that reads as "this table has been verified".

Two traps, both of which have shipped here before in other forms:

- **Minis are part of the denominator**, so they are part of the anchor. The collection loop scores
  any T lock with `spin !== 'none'` that cleared, so an anchor over `tspinsingles/doubles/triples`
  alone would license a smaller set than it covers. All eight kinds are enumerated in
  `TSPIN_COUNTERS`, including the four that are zero throughout — a kind that starts appearing must
  surface as a disagreement, not vanish from both sides.
- **A missing counter is UNKNOWN, never 0.** `?? 0` on both sides makes a corpus of zeros agree with
  itself and `agrees` stay true — the same shape as the `?? 0` that published 「一個 Perfect Clear
  都冇出過」 for five sessions holding 65. A round carrying none of the eight counters is excluded
  and counted in `unknown_rounds`; `openers.test.ts` pins `tspin_clears_replay` per session as a
  literal and asserts it is nonzero, and the mutant that zeroes both sides is killed by it.

### 第二個引擎 — `dual_engine`, and why its headline rate is never the sentence

The other route is a second implementation, and two engines already exist that share no code: the
hand-port `runCase` and the vendored clean-room Triangle `runCaseOracle`. `dualEngineCheck` runs
both over every case and compares the two board-state verdicts lock by lock, as far as **both** are
verified.

**What is published is the confusion matrix, never the agreement rate**, and that distinction is the
whole finding. Both verdicts are rare —
<!--dual:rare-->177 caves and 365 donations in 15141 scored clears<!--/dual:rare--> — so an
overall rate is negatives agreeing with negatives. Split by the oracle's own verdict:

| | overall | **on the positives** |
|---|---|---|
| cave | <!--dual:cave-overall-->6331/6331 (100%)<!--/dual:cave-overall--> | **<!--dual:cave-pos-->75 / 75<!--/dual:cave-pos-->** |
| donation | <!--dual:don-overall-->6074/6331 (96.0%)<!--/dual:don-overall--> | **<!--dual:don-pos-->24 / 116<!--/dual:don-pos-->** (<!--dual:don-pos-pct-->20.7%<!--/dual:don-pos-pct-->) |

The donation's overall rate is **<!--dual:don-bothno-->6050 of 6074<!--/dual:don-bothno-->**
agreements being both engines saying "no". On the thing the
table actually counts the two engines disagree about **four donations in five** — the opposite
reading from the one the rate gives, and the same failure mode as a detector clause entailed by its
siblings. `openers.test.ts` asserts `both_no / overall_agreements > 0.99` (it is
<!--dual:bothno-share-->0.9960<!--/dual:bothno-share--> over the whole corpus, as rendered) so a future change cannot
quietly make the rate look meaningful, and `DUAL_ENGINE_MARKER`
fails the build if the section prints a rate without the sentence saying what is in its denominator.
`pipeline/check_dual_engine.py` asserts the same bound a second way — **it fails if `both_no` stops
dominating while the section still prints the rate**, because the bound is what makes the sentence
beside the table true and not merely what the number happens to be.

**Neither metric leaves quarantine on this.** The hand-port verifies a far shorter prefix
(<!--dual:prefix-->25.6 locks against 81.9<!--/dual:prefix--> on average), so the comparison reaches
**<!--dual:coverage-->6331 of 15141<!--/dual:coverage-->** scored clears — cave's
<!--dual:cave-of-corpus-->75 of the corpus's 177<!--/dual:cave-of-corpus-->. It is a check on the
verdicts, not a re-scoping of the tables,
exactly as the counter anchor licenses a denominator without redefining it. What it buys the
donation table is a *caveat it did not have*: the one metric here with no second implementation
backing it, stated as a measurement.

**The disagreement is the BOARD, not the predicate, and that is what `board_split` says.** Only
**<!--dual:same-board-->3555 of the 6331<!--/dual:same-board-->** comparison points put the two
engines on the same board, so at **<!--dual:diff-share-->43.8%<!--/dual:diff-share-->** of
them they are judging boards that differ cell for cell (median
<!--dual:diff-median-->12<!--/dual:diff-median--> cells), and every figure in the
table above is read inside that. Split the positives by board equality and the donation resolves
completely:

| | positives | on identical boards | agree | **agree · identical** | **agree · differing** |
|---|---|---|---|---|---|
| cave | <!--dual:row-cave-->75 | 11 | 75/75 | 11/11 | 64/64<!--/dual:row-cave--> |
| donation | <!--dual:row-don-->116 | 22 | 24/116 | 22/22 | 2/94<!--/dual:row-don--> |

So the two engines do not disagree about what a donation *is* — they disagree about the board, which
is `oracle-source.ts`'s garbage-hole problem showing through. **The cave's row is a different claim
and must never be worded like the donation's**: agreeing on every positive on boards that differ is the
verdict being *robust* to the drift (consistent with the drift sitting in low garbage rows while the
cave is local to the spin), not independent confirmations. `DUAL_SPLIT_MARKER` and
`CAVE_SPLIT_MARKER` fail the build if either sentence goes missing.

**Every figure in this section is a marked fragment as of 2026-08-24, and all but one of them was
already correct.** That is the point rather than a footnote: correct-today is the normal state of an
ungated figure, and this same section has watched two copies of these numbers go stale — a
five-session set in `emit-opener-facts.ts` that survived the sixth session by two days, and a
six-session set that replaced it *under a sentence promising it was "not a remembered one"* and was
wrong the day the seventh landed. `prefix_locks` and `board_diff_hist` are emitted per session now,
so the two figures that had no artefact behind them at all — the prefix means and the median board
difference — roll up like the rest. The one that was wrong is the prefix pair: published as 「27
locks against 81」, measured at 26.2 and 80.4. The hand-port's figure was rounded the harmless way
and the oracle's the flattering way, which made the gap look bigger than it is — **the fourth
figure on this branch to fail in exactly that direction**, after the shipped band's floor, the
`sd_ratio` and the cut-off band. A rounding rule is per CLAIM: the short prefix ceils and the long
one floors, so 「26.3 against 80.3」 holds at the most generous reading of the one and the least
generous of the other. `check_dual_engine.py --selftest` re-renders every directional figure with
the opposite rule and prints the pair, so a direction this corpus cannot discriminate is NAMED
rather than assumed.

A false start worth not repeating: the first version of that probe pushed both engines through the
reconstruction check and the hand-port licensed **0 of 1355** (over the five sessions there were
then). A 0%/100% split is a bug report about the comparison, not a result. **The reason recorded here
was wrong until 2026-08-14** — it said `records[].clearedRows` means different things in the two
engines, "the hand-port leaves it empty on most clearing locks". Measured: **0 empty of 5472**, and
`clearedRows.length == lines` every time in both engines. The real cause is that `records` and
`locks` are **index-aligned in the oracle only** (`records[i].frame == locks[i].frame` 18951/18951);
`sim.ts` pushes a record only inside the clear branch, and twice on an all-clear bonus, so the
alignment holds **0 of 5472** times there and `records[i]` reads an unrelated record. Looked up by
the lock's own **frame**, the hand-port passes the strong check at that call site on every
comparable lock — **<!--dual:strong-licence-->6331 of 6331<!--/dual:strong-licence-->** over the whole
corpus (the per-session figures are each session's
`locks_comparable`, so the artefacts cross-check it and this number tracks them), so
`dualVerdict` now uses the same reconstruction
check as the shipped path — the weaker licence is gone, and every artefact was byte-identical
under the change.

Two things that follow, and both are load-bearing:

- **The strong licence has no teeth from the artefacts.** Reverting to the index lookup or
  off-by-one-ing the frame collapses `locks_comparable` to 0 and byte-identity catches it; but
  weakening the *licence* (back to `rows.length == lk.cleared`, or comparing only the length of
  `clearedRows`) leaves every artefact byte-identical — re-checked on the sixth session, both
  mutants, rather than carried over. `dualVerdict` is exported and tested directly on synthetic
  boards for exactly that reason. A guard no gate can falsify is decorative.
- **A missing record is an EQUIVALENT mutant, not a coverage gap.** `?? []` instead of excluding it
  cannot change any output: a lock with `cleared > 0` always makes at least one row full, so an empty
  `theirs` never matches. The branch was also unreachable through the first six sessions (0 of
  2027). It is written
  explicitly because it states the intent — do not add a test that pretends to cover it.

## 開局定式 定 中盤手法 — the window was asserted, now it is measured

Three metrics answer "opener or mid-game" three different ways, and only one of them used to answer
it at all:

- **全消** always did: `pco_window_locks = 10`, `within_pco_window` per player, 9 of 337 inside it.
- **The ordering metric did NOT.** Its spins are filtered to lock ≤ `WINDOW_PIECES` before counting,
  so mid-game pairs were *excluded rather than counted*, and「先 Triple 後 Double」 was a claim about
  openings that a reader had no way to check — it reads identically to a claim about how these
  players throw T-spins at any point in a round, and the two mean completely different things about
  the C-Spin. `ordering.players[].mid_game` is the missing control. **Inside the window 1629 rounds
  hold both spins and 1556 run Triple-first — 75 exceptions in nineteen sessions, five of
  them corroborated by the first-bag metric (see above); outside it, 70 rounds hold
  both and the order goes BOTH ways (55 Triple-first, 45 Double-first — a round can register both,
  so these do not sum to 70, and since 2026-09-10 that is true INSIDE the window too).** The rate of
  Double-first orders is still more than an order of magnitude higher outside the window than
  inside it when POOLED — 4.60% against 64.3%, about 14.0× — **but that is a pooled sentence pinglamb
  carries, and it must say so.** Per player: pinglamb 6 of 949 (0.63%) inside against 12 of 27
  outside, about 70×; yachi 69 of 680 (10.15%) against 33 of 43, about 7.6×. 「Near-unanimous
  Triple-first inside the window」 is pinglamb's property; it was yachi's too through 09-19 (13 of
  469, 2.8%) and is not since 10-03 (56 of 211, 26.5%, mostly one repeated 0-based Single 6 / Double 12-13 /
  Triple 18-20 opener on five nights — SDPC Spin, see 「C-Spin 同 DT 砲」 — 10-03's eighteen, of
  which sixteen are that opener, 10-09's twenty-nine, 10-12's three, 10-20's four and one of
  10-22's two, the other an exact DT Cannon).
  **The test used to assert a pooled 20× ratio, and 2026-10-09 broke it (about 93× at twelve
  sessions, 22× at fifteen, 14× at sixteen, 13.7× at seventeen, 13.2× at eighteen, 14.0× at nineteen).** The bound was not lowered and was not kept: the 20
  was never a claim, only 「a twentieth」 borrowed from `DT_RIVALS_CSPIN_AT`, sitting about 5× under
  the measurement the day it was typed, and it passed pooled only because pinglamb's rounds carried
  yachi's. `openers.test.ts` now asserts what the test's name says — the window SEPARATES opening
  from mid-game — **per player**, as a one-sided exact Fisher test at α = 0.05 Bonferroni-corrected
  over the players (the AUC table's convention, fixed before the data): p ≈ 4e-22 for yachi and
  3e-16 for pinglamb at nineteen sessions (2e-20 and 2e-13 at eighteen, 3e-21 and 6e-12 at
  seventeen, 5e-21 and 1e-10 at sixteen; ceiled, R's `fisher.test`, and an independent exact
  implementation that reproduces the eighteen-session pair). What would have to be true for it to fire, outside counts held fixed: yachi's
  inside DT count reaching about 414 of 680 (61%), pinglamb's about 239 of 949 (25%), i.e. a
  player whose openings are as Double-first as his mid-game. A drift short of that is not that
  test's job: every Double-first round is still pinned by name in `DT_ORDER_IN_OPENER`, which is
  where near-unanimity was always really gated. Hand-summed from `ordering.players[]` and its
  `mid_game` in each artefact, and pinned as per-player quartets in the test — re-derive when a
  session lands. (`DT_RIVALS_CSPIN_AT`, the sibling pooled 20× bound, has TWO DT rounds of headroom at
  nineteen — 75 × 20 = 1500 against 1556, after 73 × 20 = 1460 against 1480 at eighteen,
  69 × 20 = 1380 against 1452 at seventeen and 66 × 20 = 1320 against 1391 at sixteen — and yachi
  alone is 69 against 611. 10-20's four took three rounds of headroom down to one on a 30-round
  night; 10-22's two DT rounds against 76 C-Spin orders took it back up to two, and a session with
  three more Double-first openers than C-Spin orders allow breaks it. The sentence that stood here said 「the next session like 10-09
  will break it」; 10-12 was not one like 10-09 (3 Double-first openers, not 29), so it did not, and
  the prediction stays a conditional rather than a forecast. Decide it the same way when one does.)
- **Donation / STMB Cave** now carry `in_opener` / `mid_game` too. Donation splits about 1:3.2
  (86 in-opener, 279 mid-game), so it is not purely mid-game.

**The cave's window result was an absolute for six sessions and 2026-08-19 broke half of it. Read
the two halves apart — they are not one claim.**

- the **SHAPE** claim — "no ≥3-wide hit falls inside the opener window". Held 0 of 39 for six
  sessions. **BROKEN**, and now broken twice over. 08-19 has two, both in
  `replay-2026-08-19-9.ttrm`: round 4, pinglamb, lock 20, and round 5, yachi, lock 17. 08-25 adds
  two more, both pinglamb and in *different* files: `replay-2026-08-25-04.ttrm` round 1 at lock 11
  and `replay-2026-08-25-06.ttrm` round 3 at lock 18. 09-03 adds a fifth:
  `replay-2026-09-03-06.ttrm` round 1, yachi, lock 18. 10-03 adds a sixth and seventh, both yachi's
  and both on lock 21, the last lock inside the window: `replay-2026-10-03-02.ttrm` round 2 and
  `replay-2026-10-03-04.ttrm` round 1, prefixes verified to 33 and 58. 10-12 adds the eighth, the
  third on lock 21: `replay-2026-10-12-04.ttrm` round 2, yachi, prefix verified to 102. All eight
  are width exactly 3, `minDepth` 1. Corpus-wide the width≥3 hits are now **177: 169 outside the
  window, 8 inside** — 09-17, 09-18 and 09-19 added five, thirteen and twenty, every one of them
  outside, 10-03 eighteen, two of them inside, 10-09 thirty-one, every one outside, 10-12
  four, one of them inside, 10-20 six, every one outside, and 10-22 five, every one outside.
- the **CAVE** claim — "no genuine cave falls inside the opener window". **STILL UNBROKEN** at
  nineteen sessions, and it is the one the section's sentence rests on. All eight hits are `minDepth`
  1, i.e. dimples; every session from 07-28 to 10-03, and 10-12, 10-20 and 10-22, has `min_depth_ge_2` **0** (08-19 is only where
  the in-opener exception list starts); and the corpus
  holds **two** genuine caves in 2814 player-rounds — the original one and 10-09's (pinglamb,
  `replay-2026-10-09-01.ttrm` round 5, lock 55) — neither of them in an opener. 10-09 is the first
  session since 07-24 — the one holding the original cave — with `min_depth_ge_2` above zero, and it carries no in-opener exception, so
  the test's coupling (an exception-carrying session must have no genuine cave) is not engaged.
  None of 09-10, 09-17, 09-18 or 09-19 added an exception, so the SHAPE list sat
  at five for four sessions while its denominator grew fourfold; 10-03 takes it to seven, 10-09
  leaves it there, 10-12 takes it to eight and 10-20 and 10-22 leave it there.
  So harddrop's filing of the technique under `Mid-game T-Spin setups` is still a measurement and
  not a citation — what was lost is the right to state it as an absolute over the *raw width
  column*, which is the trap `width_ge_3` sets everywhere else in this file arriving from a new
  direction.

Four of the first five hits are clearly not short-prefix artefacts: those rounds verify to locks 62, 64,
49 and 45 against spins at 20, 17, 11 and 18. **The fourth is the one to read carefully** —
`replay-2026-08-25-06.ttrm` round 3 has its spin at lock 18 with the prefix verified to exactly 18,
i.e. ON the boundary. The reconstruction check licensed that lock, so it is a real detection and
not a guess, but it is *not* ruled out as a prefix-edge effect the way the others are. **The fifth
exception is what that note was waiting for, and it answers the question the other way**: 09-03's
hit is also at lock 18 but its prefix runs to 45, two and a half times past the spin, so it is ruled
out as an edge effect exactly as the first three are. 08-25's boundary case therefore stays a single
unexplained instance rather than becoming a pattern, and the edge suspicion is **not** raised.
All eight are pinned in `openers.test.ts` as `CAVE_IN_OPENER_EXCEPTIONS`, a **named exception
list** rather than a relaxed bound (following `DT_ORDER_IN_OPENER`), so a new one — or any of
these moving — fails and has to be investigated instead of absorbed. **What makes that a list and
not a bound in disguise is structural, and you can see it by reading the assertion**: it compares
each player's `in_opener` against *the number of entries naming that session and that player*, so a
phantom entry fails by construction (`known` exceeds a count the data does not support) and a
deleted real hit fails the same way from the other side. A bound — `in_opener <= 2` — would be
satisfied by any in-opener hits anywhere in the corpus; this is satisfied only by these eight.
Note what is deliberately *not* claimed here: nothing in the repo re-runs a mutation over this, so
the evidence is the shape of the assertion, not a mutation score. **The cave claim is now
enforced rather than commented**: a session
carrying an in-opener exception must have `min_depth_ge_2 === 0`, so the two claims can never be
separated by session without the test saying so. That 08-19's two hits share a file, sit in
consecutive rounds and take one player each was recorded **with no proposed mechanism** — and
08-25's two are the reason that restraint was right: they are both one player's, in two *different*
files, so whatever pattern the first pair looked like, it is not that one. 09-03's fifth is a third
shape again — a lone hit, the other player, its own file. 10-03's two are one player's, in two
files, on the same lock. 10-12's eighth is a lone yachi hit on that same last lock, 21 — the
third there, which is the window's edge rather than a mechanism. Two events were not a pattern;
eight events across four shapes are still not one.

`ordering_full_round` is **not** the mid-game counterpart and must not be read as one — it applies
the *same* window (0-based locks 0-21, see the lock-numbering note above) and only drops the verification requirement, so its numbers are within a
round of `ordering`'s rather than identical, which is the whole of what dropping verification buys:
**1635 / 1562 / 75** against `ordering`'s **1629 / 1556 / 75** (rounds with both · C-Spin order ·
DT order, summed over the nineteen committed artefacts). Six extra rounds clear the window
unverified: 08-01's one, which stood alone from six sessions through twelve, plus two from 09-18,
one from 09-19, one from 10-12 and one from 10-22 (pinglamb's); 10-03, 10-09 and 10-20 add none. (This sentence still said 「one extra round」 for the two
sessions after 09-18 and 09-19 landed — 冇第二份 again, a count re-derivable from the artefacts
that nobody re-derived.) It answers "did the verified prefix
manufacture this", not "what happens later in the round" — and the answer being *a handful of
rounds*, not zero, is what makes it evidence instead of a tautology.

**The mid-game denominator is 70 rounds corpus-wide, so it is printed as counts and never as a rate**
— rounds usually end before accumulating both spin types that late, and the verified prefix truncates
what is left. Same rule 全消 follows for its 3-12 round denominators; two of the nineteen sessions
(07-24, 08-01) have no such round at all, which renders as an absence rather than a zero.

New claim families go at the **end** of `generators.py`. `build_claims` numbers claims in FAMILIES
order, prose cites those ids, and a shifted id still resolves — to the wrong claim. Nothing checks
that.

**A new `SECTIONS` entry must also be placed in `skeleton.LAYOUT` or named in `SELF_INSERTING`,
and a CONDITIONAL section belongs in the latter.** `skeleton._check_coverage` refuses to emit
otherwise, which is how 2026-08-14 — the first session created after 全消 shipped — failed at step
6 of `bin/new-session` with `build_report.SECTIONS owns ['perfect-clear'] but LAYOUT does not place
it`. The fix is `SELF_INSERTING`, not `LAYOUT`: `generators.perfect_clears` emits nothing for a
session with no All Clear, so `pc_section.build` returns `None`, and an unconditional empty region
in the skeleton would then trip `render`'s stale-region guard on that session instead. Same shape
as `forecast` and `openers`.

A `SECTIONS` entry's anchor must be a **marker comment**, not a `<section id=…>` tag. `<section
id="coaching">` lives inside the coaching region, so anchoring there inserts the new block into a
span a later pass rewrites: `build_report` prints `inserted: <name>` and the finished file contains
nothing at all.

## 定式路線同中盤手法 — the one quarantined section ABOVE the trust chain, and the advice written from it

`pipeline/routes_techniques_section.py`, region `routes-techniques`, inserted right after 數據對決
(before the moments region's BEGIN marker; in `SELF_INSERTING`, because a filtered subset has no
`sim/` directory and gets none). It prints one night's slice of the corpus route and technique
artefacts (`pipeline.sites`' lists, read through `replay_labels.load_sources`): per opener, the rounds
whose bag 1 matched and how many reached bag 2, bag 3 or a drawn Perfect Clear inside the verified
prefix; per technique variant, the hits over the night's scored TSDs (`opener-facts.json`
`stmb_cave.players[].tspin_doubles_scored`; a TSS variant has no per-night count and the cell says so),
how many reached the page's next step, the worded reasons the rest did not (`REASON`; an unknown code is
a build error) and opener against mid-game; and a per-match strip. Every cell links to the replay
moment. A technique whose artefact carries `qualify` (all nine since 2026-10-23) counts ONLY the hits that pass its build
rules — in the table, the per-match strip and 數據對決's chart (`routes_techniques_charts.py`) alike — and
prints the shape-only hits beside them as 「另外 N 次個形對到但唔算砌出嚟」, so a night's window hits are never
read as the technique played (the first pass printed the qualify count UNDER the raw hits, and the chart and
strip kept showing the raw ones). No win rate, the 全消 rule. Same tier as the four sections below the footer — no claim id, no ✓
— and it sits early only because 建議 cites it.

**建議 has a second kind of item, and it is the one place hand prose cites simulator figures.** A
`prose/coaching.json` column may carry `sim_recs`; `coaching.py` renders them after the proved `recs`,
numbered on, each opening with `coaching.SIM_TAG` (「未經證明」, linking to the section), and adds
`SIM_NOTE` and a `#coaching .cs-*` style. `pipeline/check_routes_techniques.py` gates both halves: the
region is a re-render with its eyebrow, title and `REQUIRED` sentences and no badge; every authored
item renders once with its tag (and the tag appears nowhere else), carries no badge, and **every Arabic
figure in it is a figure the region prints**. That last check is membership over the region's printed
numbers, not a match to the right cell — so write a tagged item's figures only from the cell it talks
about, use Arabic digits for every count so the check sees them, and never a total the cell does not
print (「冇接到嗰 5 次」 when the cell prints only the reasons is exactly the sentence it cannot catch).
The items are corpus-artefact-dependent: re-emitting any route or technique artefact moves every
night's region, `build_report --check` goes red, and each night's tagged items must be re-read against
the new cells, not just rebuilt.

## 重播 — the animated replay, the third quarantined section

Two boards side by side, stepped lock by lock. **Simulator output, quarantined exactly like the
forecast and opener sections**: one engine, no board snapshot in the `.ttrm` to check it against,
so the artefact says `report_eligible: false` and nothing that draws from it carries a claim id, a
✓ badge or a `data-claim`.

| piece | where |
|---|---|
| emitter | `pipeline/sim/emit-replay.ts` → `sessions/<date>/sim/replay-facts.json` (regenerate with the Commands-block line; one per session, none for `subsets/`) |
| test | `pipeline/sim/replay.test.ts` — the committed artefact must rebuild byte for byte, every timeline must decode back to the engine's board, and `ADMISSION_EXCEPTIONS` / `KNOCKOUT_EXCEPTIONS` are **named lists**, not bounds |
| report section | `pipeline/replay_section.py` + `pipeline/replay_player.js` (inlined), region `round-replay`, in `SELF_INSERTING`; it replays the round `generators._intense_round` picks, so it is the same round as 最癲一局 |
| gate | `pipeline/check_replay_section.py` (re-render, quarantine sentences `REQUIRED`, no badge, no `innerHTML`); `--selftest` plants the corruptions |
| whole-night page | `pipeline/replay_page.py` + `replay_page.js` → `docs/<date>-replay.html`, rendered (not copied) by `bin/build-docs`, so `--check` byte-compares it; `python3 -m pipeline.replay_page --selftest` |

Three things the wording must keep. **The garbage hole columns are the engine's seeded-RNG holes**:
they agree with the game's own counters and are never observed directly, so the copy must never call
them the recorded columns (the `oracle-source.ts` caveat is the same problem). **The ending comes
from `gameoverreason`, not from the engine.** The engine's own topout is recorded beside it as
`engine_knockout`, and where the two disagree the board after that point may not be the game's. **The
verified prefix is shown as a boundary on the board, not as a ✓.** It is what the `verifiedBoundary`
walk in `verified-prefix.ts` reached; `verifiedIndex` is now that walk's projection, not a second
copy of it.

**The whole-night page labels openers and mid-game techniques in its key moments** (`pipeline/replay_labels.py`,
since 2026-10-22): an `opener` moment at every route stage a case reached inside the verified prefix (bag-1 board,
bag-1 T-spin, bag-2 board, each snapshot, a drawn Perfect Clear) and a `technique` moment just before every
technique hit's T, read from the route and technique artefacts in `pipeline/sites.py` — the ONE list of sites,
which `bin/build-docs` now imports instead of keeping its own. Every label is re-checked against the page's own
decode (`decode_boards`; the board equals the drawing by occupancy in the recorded hand, or the technique window
fires through `window_fires`), and a label that fails is a build error, so `build-docs --check` runs all of them;
`python3 -m pipeline.replay_labels --selftest` plants a wrong lock, hand and a stale artefact. Several pages
matching one board are joined in ONE moment, never chosen between; the page must carry `replay_labels.SENTENCE`
(no label is no evidence the opener was not played). A technique hit that fails its artefact's `qualify` rules (every technique page) gets no key
moment at all (since 2026-10-23, yachi's call: every 社畜 window hit in the corpus failed them, so the labels only ever said
「not this technique」); the artefact still holds each one, and the selftest flips one to qualifying and
must see a label appear. The report's 最癲一局 region passes no labels and is unchanged.
TKI-3, PCO, DT Cannon and the harddrop-field columns are NOT labelled: `opener-facts.json` holds their counts, not
which rounds matched, so labelling them means an emitter change that re-emits every session's artefact.

The engine hooks the emitter needs are **opt-in**. `createEngine`'s `date` defaults to the wall clock
as before, and `TL_DEFAULTS` is only exported, so every pre-existing `sim/*.json` re-emits
byte-identical. Keep it that way. The emitter reads the engine directly; it does not change what
`runCaseOracle` returns.

## 定式路線頁（迷走砲、はちみつ砲、山岳積み2号、stick spin、ガムシロ積み、SDPC Spin）— the opener route pages, quarantined like the replays

Six opener pages are transcribed and matched against the corpus — five from shiwehi.com, 迷走砲
(Stray Cannon, `meisou.php`), はちみつ砲 (Honey Cup, `honeycup.php`), 山岳積み2号 (Mountainous
Stacking 2, `mountainous2.php`), stick spin (SDパフェ, `stickspin.php`) and ガムシロ積み (Gamushiro
Stacking, `gamushiro.php`), and one from harddrop, SDPC Spin (`SDPC_Spin`, read as wikitext). **One implementation per rule, one profile
per opener**, because a rule kept in two implementations drifts (「Three backends」): the classifier
is `pipeline/sim/route-facts.ts`, the demo planner `pipeline/sim/route-demos.ts`, the transcription
gate `pipeline/openers/route_transcription.py`, the page renderer and audit `pipeline/route_page.py`,
and the shared test checks `pipeline/openers/route-facts-checks.ts` / `route-demo-checks.ts`. What
differs per opener is DATA: `route-profile-meisou.ts` / `route-profile-honeycup.ts` /
`route-profile-mountainous2.ts` / `route-profile-stickspin.ts` / `route-profile-gamushiro.ts` /
`route-profile-sdpcspin.ts` (the TS profile: nodes, locks, artefact strings, named lists, the demo
half), and `stray_cannon_page.py` / `honey_cup_page.py` / `mountainous2_page.py` / `stickspin_page.py`
/ `gamushiro_page.py` / `sdpcspin_page.py` (the page profile) with their prose JSON. The CLIs are `emit-route-facts.ts` /
`emit-route-demos.ts --opener <key>`; 迷走砲 keeps its original entry files as shims with their old
signatures, so its tests and commands did not change.

**The md5 inputs are scoped per opener.** `emitter_md5` / `planner_md5` / `classifier_md5` each hash
the shared module, `route-profile.ts`, that opener's own profile file and its entry file
(`hashFiles` in the profile). An edit to one opener's profile stales only that opener's artefacts;
an edit to shared code stales all of them, loudly, and the regeneration must then differ in those hash
lines ONLY — that is the check that a shared-code edit left the other opener's behaviour alone.
The generalisation was landed that way: every 迷走砲 artefact and page byte-identical except the
three hash lines — and 山岳積み2号 was added the same way, moving only the hash lines of the other
two openers' four artefacts and none of their pages. stick spin moved the other three openers' six
artefacts in their hash lines only (`emitter_md5`; `planner_md5` and `classifier_md5`) and none of
their pages, because it changed `route-facts.ts`, `route-profile.ts` and `route-demos.ts`.
ガムシロ積み changed no hashed file — one registration line in `route-openers.ts`, which no profile
hashes, and a Python-only cross-source route in `route_transcription.py` — so every other opener's
artefacts and pages are byte-identical, hash lines included. SDPC Spin changed no hashed file either:
one registration line in `route-openers.ts`, an additive wikitext reader and cross-source route in
`route_transcription.py`, and four default-preserving branches in `route_page.py` (both Python, which
no profile hashes). The five sibling transcription gates printed byte-identical output under the
edited and the pre-edit `route_transcription.py` (compared with `cmp`), and `bin/build-docs --check`
passed against the edited `route_page.py` before SDPC Spin was registered, so no sibling page moved.

### 迷走砲

shiwehi.com's 迷走砲 page draws a tree: bag 1, five bag-2 branches, and the bag-3 Perfect Clear
and T-spin patterns under each. These pages match every corpus round against that tree and say how
deep it got. **Simulator output, quarantined exactly like 重播**: which bag-2 and bag-3 shape was
built comes from one engine, so the artefact says `report_eligible: false` and no page carries a
claim id, a ✓ or a `data-claim`. Counts only, always 「N / M」 with the denominator; the source
page's own percentages appear only inside quoted source text.

| piece | where |
|---|---|
| route transcription | `pipeline/openers/meisou-routes.json`, hand-checked and held as a literal in `pipeline/openers/extract_meisou_routes.py`, which gates it (grammar, `bag1.z_hold` against harddrop's `stray_cannon` field, parent/child consistency, distinctness, the named source discrepancies). The page HTML is never committed — CI cannot fetch it — so provenance carries the fetch date, a hash of the fetched markdown and the site's terms (non-commercial use allowed with a URL credit; the source link in every page header is that credit) |
| artefact | `pipeline/sim/emit-stray-cannon-facts.ts` → `analysis/stray-cannon-facts.json`, corpus-wide like `rate-records.json`; it records md5s of every session's replays, the routes file and itself, so it goes stale loudly |
| test | `pipeline/openers/stray-cannon.test.ts` — byte rebuild, the `matched_at_6` flag against each (session, player)'s `opener-facts.json` `stray_cannon.exact`, the named lists, and the emitter's mutants |
| pages | `pipeline/stray_cannon_page.py` + `stray_cannon_page.js` + `stray_cannon_prose.json` → `docs/stray-cannon.html` (every node, every count, the case index; no player) and one replay page per bag-2 node, `docs/stray-cannon-<node>.html`. Rendered by `bin/build-docs`, so `--check` byte-compares them and a `docs/stray-cannon*.html` nothing renders is drift. No name ends in `-replay.html`, which `bin/build-docs` owns |
| audit | reuses `replay_page.audit_quarantine` / `audit_player` (one copy of each rule), plus completeness: every route node appears with a count or a reason it has none, every case is embedded once and indexed once; `--selftest` plants the corruptions |

The named lists in the test are `Z_HOLD_BAG1`, `Z_PLACED_ELSEWHERE_BAG1`, `Z_LEFT_BAG1`,
`I_EARLY_CASES`, `TST_DONATE_CASES`, `PC_OFF_PAGE`, `MULTI_COLOUR_RESOLVED_BY_BRANCH`, and the
measured-empty `BAG2_HANDEDNESS_MISMATCH`, `COLOUR_DISAGREE` and `PC_GARBAGE_IN_WINDOW`. Each is a
named exception list, not a bound, following `DT_ORDER_IN_OPENER`: a new entry is a red build to
investigate. Their sizes are read off the test, never typed here.

Four rules the code depends on, each of which an obvious simplification would break:

* **Bag 1 tries the placed variants first.** The 7-lock boards (`z_right`, then `z_left`, as drawn
  or mirrored) are compared before the 6-lock `z_hold` field, because most rounds that match
  z_right at 7 locks also matched the 6-lock field. Trying z_hold first swallows them.
* **「Matched at 6 locks」 is a FLAG, not a node.** It is what the 六個具名定式 table's Stray Cannon
  column counts, and the test compares it with that column per (session, player). A 6-lock match
  says nothing about whether Z was held, which is why this page's bag-1 total and that table's
  differ, and the overview says so.
* **A hold is asserted only where the predicate tests one.** After a 6-lock-only match the emitter
  reads the piece placed 7th and compares it with the mirror-aware bag-1 Z (S when mirrored). Not Z
  → `bag1.z_hold`; Z → the outcome `bag1.z_placed_elsewhere`. The first version called every
  6-lock-only round a hold and never tested it; re-reading those rounds' placement order showed
  some of them placed Z 7th. That is 冇第二份's sixth instance (prose saying more than the spec
  proves), and the page audit enforces it: 「hold」 may appear only in the z_hold row and the bag-1
  sentence.
* **Bag-3 PC detection does not wait for a bag-2 match**, and is scoped to the matched branch's
  patterns before it throws on an ambiguous colour match. A PC under an unmatched bag 2 is recorded
  under `bag1.<node>.other`; gating it on bag 2 drops a real off-page PC from `PC_OFF_PAGE`, and an
  unscoped throw fails on the round in `MULTI_COLOUR_RESOLVED_BY_BRANCH`. A case's `match` is the
  replay-facts POSITION, never a filename-sort index.

A mirrored round is read with J↔L and S↔Z swapped before the page's bag-2 condition is tested.
Upper-case `Z` read as the bag-1 Z, and the derived bag-1 `z_left` board (the page draws it only
inside its bag-2 board), are this repo's readings, and the pages say so.

#### 示範重播 — a constructed replay for every drawn node, and why it is not corpus data

Beside the corpus cases, every route node that has a drawn board gets a **constructed** demo: from
an empty board, one piece at a time, from a queue and key inputs WE choose, through bag 1 → bag 2
(→ the TST) → bag 3, ending on the page's drawing. Nobody played these games, so they are quarantined
harder than the corpus pages: the artefact says `report_eligible: false` and `constructed: true`, the
page's player is labelled 示範, no figure from them enters any count, and nothing carries a claim id,
a ✓ or a `data-claim`.

| piece | where |
|---|---|
| planner | `pipeline/sim/route-demos.ts` (`stray-cannon-demos.ts` is 迷走砲's shim) — per bag, a DFS over placement orders; per piece, a BFS over the ENGINE's own moves (its `rotateCW/CCW/180` through SRS+ kicks on a scratch engine, lateral steps, one-row falls copied from `#__internal_fall`), keyed by the engine's `lastSpin` because a sideways step keeps it and a fall clears it |
| emitter | `pipeline/sim/emit-stray-cannon-demos.ts` → `analysis/stray-cannon-demos.json` (argv and file IO only); md5s of the routes file, the planner, `emit-replay.ts` and the classifier, so it goes stale loudly |
| test | `pipeline/openers/stray-cannon-demos.test.ts` — byte rebuild; every demo re-run through `instrumentEngine` to its committed locks; the corpus `classify()` reaching the node; board equality against the drawing; spins; whole 7-bags; prefix sharing; completeness; planner and data mutants, and two measured controls |
| page | `docs/stray-cannon-demos.html`, from `stray_cannon_page.render_demo_page`; every node block on the overview and node pages links to it (or says there is no demo). The page re-checks each EMBEDDED demo's end state with its own decoder (`replay_section.decode_boards`), a second implementation that runs in the bun-less `docs` job |

Five rules the code depends on:

* **The engine is the arbiter; the planner only proposes.** `build()` replays the whole input script
  on a fresh engine through `instrumentEngine` (factored out of `emit-replay.ts`'s `runPlayer`, so a
  demo lock and a corpus lock are recorded by the same hooks) and throws unless every lock lands on
  the planned cells with the planned spin and lines. A planner bug cannot reach the artefact.
* **The row map is `composite()`'s inverse and lives beside it** (`initialRowmap` / `advanceRowmap`
  in `emit-stray-cannon-facts.ts`). A bag-3 drawing is a kept-rows composite, so a piece is placeable
  only while every row it is drawn on is still on the board; without the map the split-piece
  patterns cannot be built at all (the `noRowMap` mutant).
* **A drawn `U` is the slot the T goes into, and the demo fires it.** On a bag-2 board and the two
  mid-route drawings (TST 捐窿, STSD) the T is the bag's LAST piece and the board just before it is
  the drawing; in a PC pattern the T goes wherever the order allows and the last lock is the Perfect
  Clear.
* **The shared player takes one board or two.** `replay_player.js` sizes its per-player state by
  `players.length`, and a payload whose `verified_to` is null (a demo: no recorded game, so no prefix
  to verify) draws no boundary band and no checked/unchecked state; `replay_section.player_box(…,
  bands=False)` emits no band and no legend for it. Two-player output is byte-identical.
* **「hold」 only where an input holds.** Only `bag1.z_hold` presses hold (its Z, held on arrival
  just before J). The demo page may say the word only inside that demo's own `scp-hold` span, and
  only while its locks carry a `held` flag; the overview's existing rule is unchanged.

The named lists are `DEMO_UNBUILT` (a drawn node with no demo, and the planner's own measured reason
— a placeholder template, a T that cannot reach its drawn slot from spawn when it must go last, and a
pattern whose pieces wait on each other's row clears in a cycle), `DEMO_SPIN_LINES` (the U line counts
the drawing does not fix), `DEMO_SPIN_EXCEPTIONS` (a plain `t` the engine credits as a spin; measured
empty) and `DEMO_PIECE_READINGS`. Their sizes are read off the test, never typed here.

**Two measured controls, not mutants, and the reason is the finding.** `ignoreConditions` changes
which queue is dealt and every check still passes: in every drawing the page's order conditions
(%J>%O, %O>%S, %S>%O, the bag-1 %J>%Z) are what gravity already requires, so the conditions are
entailed by the boards. `no180` changes paths and breaks nothing: no demo needs a 180. Either one
failing a check later means it has become a mutant.

**The page colours two PC patterns inconsistently** (`2.ideal.pc#16`, `2.i_early.pc#11`): one
piece's cells are drawn in another piece's colour across cleared rows. `extract_meisou_routes` rule 7
(every letter is whole pieces of that letter in the kept-rows frame) now finds exactly these two and
they are named in `known_discrepancies`; `PIECE_READINGS` in the planner is the ONE table that reads
them as the piece they must be, and the demo artefact carries it to the page. **The corpus classifier
does not apply it, on measurement**: the `2.ideal.other` off-page PCs share those patterns'
occupancy, but none of them matches either drawing under the reading by colour, so colour-matching as
drawn files nothing wrongly.

### はちみつ砲

The same deliverable for `honeycup.php`: `pipeline/openers/honeycup-routes.json` (gated by
`extract_honeycup_routes.py` through the shared gate), `analysis/honey-cup-facts.json`
(`honey-cup.test.ts`), `analysis/honey-cup-demos.json` (`honey-cup-demos.test.ts`), and
`docs/honey-cup.html` plus `honey-cup-bag1-only.html`, `honey-cup-ideal.html`,
`honey-cup-compromise.html` and `honey-cup-demos.html`, rendered by `bin/build-docs` from its
`ROUTE_SITES` list and linked as the second card under 定式路線 on the index. Counts are read off the
artefacts and tests, never typed here or in `honey_cup_prose.json`.

What this page needs that 迷走砲 did not, each a generic rule a profile switches on:

* **Bag 1 reuses the hold split with J for Z.** The 7-lock board `bag1.j_right` (harddrop's Honey
  Cup field) first; only if it misses, the 6-lock field, split by the piece placed 7th against the
  mirror-aware J (L when mirrored). The page's right-hand bag-1 board is the left one mirrored
  (`bag1.l_hold`, `mirror_of`), so it is one node, never a second branch. **The FLAG is
  `matched_harddrop`** — the 7-lock board by occupancy — and `honey-cup.test.ts` compares it with the
  六個具名定式 Honey Cup column (`opener-facts.json` `honey_cup.exact`) per (session, player). So this
  page's bag-1 total is that column plus the 6-lock-only rounds, and the overview says so. **Both
  players mirror Honey Cup**, unlike 迷走砲; `MIRRORED_BAG1` pins it per player.
* **Group scoping.** The five 理想形 forms (`2.ideal#1..#5`, `group: "2.ideal"`) share one occupancy
  and one PC list (`parent: "2.ideal"`), so COLOUR decides which form a round built, and a bag-3
  pattern is scoped by the matched form's group. One node page (`honey-cup-ideal.html`) holds the
  whole group. `MULTI_COLOUR_RESOLVED_BY_GROUP` is measured empty.
* **Bag 2 strips garbage, for this opener only** (`bag2Garbage: 'strip'`). Garbage lands under the
  13-piece board in a large share of rounds, and boards compare bottom-aligned, so complete garbage
  rows are stripped from the bottom before matching and the count travels in the case
  (`garbage_rows_stripped`, named in `BAG2_GARBAGE_STRIPPED`). A bag-2 OPPORTUNITY here is therefore
  "inside the verified prefix, no line cleared by the player before the sample", and the artefact's
  `caveat` / `rules` say so. 迷走砲 stays on `'refuse'`, which is why its artefact did not move.
* **A missed bag 2 is EXPLAINED, never matched** (`bag2Explain`). For a bag-1 round with no bag-2
  match, the board before its TST is compared by occupancy with every bag-2 board:
  `BAG2_NONE_TST_BEFORE_COMPLETE` (a strict subset — the TST came first), `BAG2_NONE_EXTRA_PIECE`
  (the board plus four cells) and `BAG2_NONE_MOVED_PIECE` (one piece's four cells elsewhere). The
  route is not relaxed; the bag-1-only page shows the reason beside each case.
* **The compromise form's condition is illustrative.** The page writes 「%L・%Z>%J・%Oの場合など」 —
  an example. It is evaluated and recorded (`condition_met`, the `CONDITIONS` table) but never
  presented as the reason a form was built, and the transcription marks it `illustrative: true`,
  which the page renders as 「係例子，唔係揀形嘅條件」.
* **The PC lists hidden in the page's HTML comments are provenance, never nodes** (Heart, and the
  compromise PCs): hand-copied from one raw-HTML fetch, outside the snapshot hash. A PC on no drawn
  pattern goes to `PC_OFF_PAGE` even when one of those hidden boards would match it.

**The demos needed the hold box to carry across bags, and the rule is one swap scheme.**
`bag1.j_hold` holds J (it arrives after L: the page's 遅いほうはホールド), and the hold box can never
be emptied again, so the planner (`route-demos.ts`) now plans a bag that STARTS with the box full:
the held piece comes out at its slot in the placement order, swapped for the piece the bag places
LAST (the T into the TST slot, which therefore arrives at that slot), and that T comes out when the
next bag's first piece arrives; in a Perfect Clear bag that piece is the pattern's unused one and
stays held, which the test asserts. Three more profile hooks: `spin_board` (this page draws its
bag-2 boards with the TST slot empty and the T on a separate board, whose U cells the demo fires
into and the test checks), `spinLetter` (the PC patterns draw the TSD's T as a plain `t`; only
pc#1-#10 have `t_in_tsd_slot`, which the page's own sentence gets wrong — a named discrepancy), and
`chainVia` (the PC patterns hang under the shared after-TST illustration; their demos run through
`2.ideal#1`). 迷走砲 uses none of them, and its demos artefact moved in its hash lines only.

`DEMO_UNBUILT` names the illustrations, the mirror, the STMB template's placeholders, the REN board's
B cells, and `2.compromise.roof.after`, which the planner measures as unbuildable (the page draws it
after its TSD cleared the two rows under it). The demo test's `ignoreConditions` is a **mutant here,
not a control** — the reverse of 迷走砲: dropping the bag-1 order deals J before L, so the held J
would be the earlier one, against the page's rule. `no180` stays a control.

### 山岳積み2号

The same deliverable for `mountainous2.php`: `pipeline/openers/mountainous2-routes.json` (gated by
`extract_mountainous2_routes.py` through the shared gate), `analysis/mountainous2-facts.json`
(`mountainous2.test.ts`), `analysis/mountainous2-demos.json` (`mountainous2-demos.test.ts`), and
`docs/mountainous2.html` plus `mountainous2-bag1-only.html`, `mountainous2-ideal.html`,
`mountainous2-normal.html`, `mountainous2-compromise.html` and `mountainous2-demos.html`, rendered by
`bin/build-docs` from `ROUTE_SITES` and linked as the third card under 定式路線. It is the page for
yachi's most-played named opener (the 六個具名定式 MS2 column). Counts are read off the artefacts and
tests, never typed here or in `mountainous2_prose.json`.

**Its snapshot is the page's RAW HTML, and that hash is not comparable with the other two.** curl
works here (with TLS verification on and a CA bundle adding the Let's Encrypt YE2 intermediate the
server omits), so the transcription is checked against the HTML byte for byte, while 迷走砲 and
はちみつ砲 hashed a markdown rendering. Board rows are read off the raw lines; sentences are compared
against the page with its tags dropped. Any byte of the page moves the hash, so a moved hash means
「read the board diff」, which `--html-dir` prints.

What this page needs that the other two did not:

* **The harddrop field is the 6-lock board, and the page never draws it.** The page draws bag 1 with
  the L stood on end (`bag1.l_top`, 7 locks); harddrop's Mountainous Stacking 2 field is that board
  with the L held, so `bag1.l_hold` is DERIVED (`bag1.l_top` less its four `l` cells, checked) and
  carries no source label. The hold split is はちみつ砲's with L for J. **The FLAG `matched_harddrop`
  is the 6-LOCK match** — the reverse of Honey Cup's — compared per (session, player) with
  `opener-facts.json` `mountainous_2.exact`; the page's bag-1 total is that column plus the rounds
  that match only at 7 locks (the L landed inside the first six). Upper-case `L` has no legend on the
  page and is read as the held bag-1 L; the gate checks every board drawing it sits on exactly the
  6-lock board. Both players mirror it (`MIRRORED_BAG1`).
* **Three Perfect Clear kinds** (`pcKinds` in the TS profile): a 4-line PC in bag 2 with no spin
  before it (`2.pc4`, on the L-held board, scoped to `bag1.l_hold`), the 8-line PC after the TST, and
  a 14-line 5巡パフェ whose frame starts after the last TSD (scoped to `2.compromise`, because the
  bag-4 boards between are 9 rows and unmatchable). A list carries its own `pc_lines` /
  `total_lines` in the transcription, and `route_page.pc_lines_of` reads them for the demo end check,
  which now tests a list BEFORE the bag-2 rule (a bag-2 list is a PC, not a TST board); the page
  selftest plants the profile's single count back and must see the 4- and 14-line demos fail.
* **A held piece comes out at the next piece DEALT, which is not always the next bag's.** In the
  4-line PCs the bag's unused pieces follow its last placement, so the piece swapped into the hold
  comes out when the first unused one arrives, and that one stays held. The planner's `out@next`
  token is unchanged (it is in はちみつ砲's artefact bytes); `route_page` words it with the prose
  key `hold_out_next_unused` whenever the bag has unused pieces, which only this opener does.
* **Boards past bag 2 are matched mid-round** (snapshots up to the bag-4 board); the 9-row ones are
  `unmatchable` with the reason saying 「non-empty rows」.
* **The TSD's T is the `t` in the slot, not the flat T shape.** `spinLetter` counts a `t` only when
  its cells are exactly the empty slot in the bottom two rows of the pattern's base board, which the
  demo test pins as `TSD_T_PATTERNS`; the patterns that do not are the two `no_tsd` discrepancies.
* **Cycle diagrams are `cycle_fragment` nodes, never boards.** Six 4- and 3-wide diagrams; the
  first of each set is checked against the board it is drawn from. A fragment's `c` means 「not one
  of these pieces」, so a `c` over an EMPTY board cell is the page's convention (all four O/S/Z
  cycles draw it in their corners) — the first transcription filed one as a drawing slip and the
  independent audit showed it was not, so it is no discrepancy.
* **Readings are marked, not smoothed.** 「%S%O」 and 「%O%S」 are read as ORDERS (as sets the two
  triggers would be one), the 通常形 trigger as two early pairs (it is a group condition, not tallied
  in `CONDITIONS`), the bag-1 condition is `illustrative`, and calling the second pair of 5巡パフェ
  boards bag 4 is ours (`heading_note`: the page gives them no heading). A `label_jp` is page text or
  a heading path, never an invented caption; the after-the-spin boards and the derived board have
  none.

The named lists are `L_HOLD_BAG1`, `L_PLACED_ELSEWHERE_BAG1`, `BAG2_GARBAGE_STRIPPED`,
`BAG2_NONE_TST_BEFORE_COMPLETE` / `_EXTRA_PIECE` / `_MOVED_PIECE`, `PC_OFF_PAGE`, and the
measured-empty `BAG2_HANDEDNESS_MISMATCH`, `COLOUR_DISAGREE`, `PC_GARBAGE_IN_WINDOW` and
`MULTI_COLOUR_RESOLVED_BY_GROUP`; demos `DEMO_UNBUILT` (the mirror, the after-the-spin illustrations,
and the planner's measured failure on one PC pattern), `DEMO_SPIN_LINES`, `DEMO_SPIN_EXCEPTIONS`,
`DEMO_PIECE_READINGS`. Sizes are read off the tests. **`ignoreConditions` is a control here**, as for
迷走砲 and unlike はちみつ砲: every order the page states is already forced by its boards; `no180` is
a control too. One wording leftover is deliberate: the off-page reason string says 「garbage between
the TST and the PC」 even for a 14-line PC, because that string is part of the other two openers'
artefact bytes.

### stick spin（SDパフェ）

The same deliverable for `stickspin.php` (「2022-08-06更新」): `pipeline/openers/stickspin-routes.json`
(gated by `extract_stickspin_routes.py` through the shared gate), `analysis/stickspin-facts.json`
(`stickspin.test.ts`), `analysis/stickspin-demos.json` (`stickspin-demos.test.ts`), and
`docs/stickspin.html` plus `stickspin-bag1-only.html` and `stickspin-demos.html`, rendered by
`bin/build-docs` from `ROUTE_SITES` and linked as the fourth card under 定式路線. Its snapshot is raw
HTML, fetched the way 山岳積み2号's was (YE2 intermediate, TLS verification on). It is the page for
the Double-first opener yachi repeats from 2026-09-17 on (see 「C-Spin 同 DT 砲」). Counts are read off
the artefacts and tests, never typed here or in `stickspin_prose.json`.

**Every corpus case stops at bag 1, and that is the page's main measurement.** The bag-2 boards are
compared (they have opportunities) and none matches; the reasons are per round in the artefact's
lists and the test's `STOPS_AT_BAG1`. So the page set has no per-branch node page: the shared
renderer refuses a node page with no case, and `node_pages` holds `bag1-only` alone.

What this page needs that the other three did not:

* **No harddrop field, so no flag — and the cross-check that replaces it.** `wiki-openers.json`
  draws no stick spin board and adding one would re-emit every session's `opener-facts.json`, so
  the transcription's cross-source is Ivan's opener database instead (`opener-fields.json`, the
  "Single Double PC … / Stickspin …" entry, whose four fields are `bag1.fire` and `bag1.pc` with the
  T placed, as drawn and mirrored): `route_transcription.py`'s spec takes `harddrop=None` and a
  `catalogue` route, and a spec with neither fails. On the corpus side the profile has no
  `bag1.flag` and no `lockPieceField`, the page profile `flag_field=None`, and `stickspin.test.ts`
  checks the ordering metric instead, both ways: every Double-first round (`opener-facts.json`
  `ordering.per_round` `dt_order`) is a stick-spin bag-1 case or named in `DT_NOT_STICKSPIN` with a
  reason the test verifies (`dt_cannon` against the first-bag metric, `both_orders` against
  `cspin_order`, `jl_split` against the board at 6 locks), the positives are pinned per player in
  `DT_AND_STICKSPIN`, and every stick-spin case with a complete window that is not Double-first is
  named in `STICKSPIN_NOT_DT` with no Triple in its window. The probe that motivated the page matched
  by shape alone; the colour check is what moves the J/L-split rounds into the exception list.
* **A bag-1 spin step** (`bag1.spin` in the TS profile). Bag 1 is six pieces (`bag1.left`) and then
  the T into a T-spin Single, stood up (`bag1.fire`, 火力派生) or laid flat (`bag1.pc`, パフェ派生);
  both children draw the T as `U`, so the step reads the 7th lock's own cells (exactly one child's U
  cells, mirror-aware, a full spin clearing one line). That clear is the route's own, so it does not
  stop the bag-2 sample (`spinClearStops` is the mutant). `bag1.left` keeps the rounds whose 7th lock
  is no drawn TSS; the off-page spins are `BAG1_SPIN_OFF_PAGE`. The three bag-1 nodes partition the
  bag-1 cases, which is what the overview's total is checked against in place of the flag split.
* **A fourth bag-2 explanation, `near`** (`bag2Explain: { nearCells: 8 }`): after subset, extra piece
  and moved piece, the nearest bag-2 board(s) within eight cells, with the missing and extra letters
  — measured, never a match, and never a relaxation of the route. yachi's bag 2 is this kind against
  `2.sd` (`BAG2_NONE_NEAR`) — because it is SDPC Spin's bag 2, which that page explains as a match
  (see ### SDPC Spin); the rest are `BAG2_NONE_UNEXPLAINED`. The other openers keep
  `bag2Explain: true`, so their artefacts did not move. The explanation reads the oracle board even
  past the verified prefix, as the shared code already did (10-09 m2r3, verified only to its TSS, still
  gets a near entry) — left alone so the other artefacts stay byte-identical, and an open item.
* **The denominator is every player with an opportunity, not every player with a case.** The shared
  `assemble` used to build its per-player tally from the cases, so pinglamb — bag-1 opportunities,
  no case — vanished and `bag1.left` read yachi's denominator alone. Found on this page because it is
  the first where a player has no case; the other three artefacts moved in `emitter_md5` only.
* **Colour-drawn after-the-spin boards and muted upper case.** The source draws its cleared rows in
  muted upper-case letters (no legend; the gate checks every upper-case row is a row the spin
  clears) and its after-the-TSS boards in colour with `U` for the T's surviving cells, so rule 7
  (whole pieces) skips `after_of` boards and the page-specific check compares each, letter for
  letter, against the board before it cleared. The page renders the upper case through `cell_classes`
  in its own CSS only.
* **Demo end states the renderer had no branch for**, in both implementations (`route-demo-checks.ts`
  and `route_page._demo_end`): a bag-1 board drawn with `U` ends on its named spin, and a board past
  bag 2 drawn with a separate `spin_board` (the TST / Imperial Cross / STMB Cave fallbacks) is the
  board before the last lock, the last lock its spin. The page selftest clears that lock's spin flag
  on three demos (`demo_spin_last`) and must see each fail. Its PC lists carry `total_lines` 8, which
  equals the profile's count, so the shared 「lists checked at the profile's count」 mutant is skipped
  as equivalent for them rather than counted.
* **No hold anywhere** (`hold_node=None`). The page's no-hold conditions (O before Z, J before L) are
  read as orders and checked against `bag1.left` by support; no input holds, and 「hold」 may appear
  only in the bag-1 sentence that reports them.
* **`t_flat_shape`, not `t_in_tsd_slot`.** This page's PC body is framed after the TSD, so a PC
  pattern's `t` is never the TSD's T; the flag is the flat ttt-over-t shape anywhere on the board
  (the independent audit found it true with the t on the surface), named for what it tests and
  defined in the routes JSON's `slot_flags`. Nothing downstream reads it.

The named lists are `BAG1_SPIN_OFF_PAGE`, `BAG2_NONE_NEAR`, `BAG2_NONE_UNEXPLAINED`,
`COLOUR_DISAGREE`, `DT_NOT_STICKSPIN`, `STICKSPIN_NOT_DT`, and the measured-empty
`BAG2_GARBAGE_STRIPPED`, `BAG2_NONE_TSD_BEFORE_COMPLETE` / `_EXTRA_PIECE` / `_MOVED_PIECE`,
`PC_OFF_PAGE`, `BAG2_HANDEDNESS_MISMATCH`, `MULTI_COLOUR_RESOLVED_BY_BRANCH` and
`PC_GARBAGE_IN_WINDOW`; demos `DEMO_UNBUILT` (the mirror, the illustrations, and the planner's
measured failures on two SDパフェ patterns whose T stands under an S that only becomes whole after
it), `DEMO_PIECE_READINGS` (the もっちパフェ pattern drawn with one L cell in J's colour),
`DEMO_SPIN_LINES` and `DEMO_SPIN_EXCEPTIONS`. Sizes are read off the tests. `ignoreConditions` and
`no180` are controls here, as for 迷走砲 and 山岳積み2号.

### ガムシロ積み

The same deliverable for `gamushiro.php` (「2024-08-01更新」): `pipeline/openers/gamushiro-routes.json`
(gated by `extract_gamushiro_routes.py` through the shared gate), `analysis/gamushiro-facts.json`
(`gamushiro.test.ts`), `analysis/gamushiro-demos.json` (`gamushiro-demos.test.ts`), and
`docs/gamushiro.html` plus `gamushiro-bag1-only.html` and `gamushiro-demos.html`, rendered by
`bin/build-docs` from `ROUTE_SITES` and linked as the fifth card under 定式路線. Its snapshot is raw
HTML, fetched the way 山岳積み2号's was (YE2 intermediate, TLS verification on). Counts are read off the
artefacts and tests, never typed here or in `gamushiro_prose.json`.

**It is a REFERENCE opener, and the pages say so before anything else.** The corpus barely plays it
(the bag-1 total is rendered on the overview from the artefact, and the one case is pinned by name in
the test), so it is not here for the two players. It is here because shiwehi.com's
`strongertemplate.php` (「強い人はどんな開幕テンプレを使っているのか(2024年)」, 2024-08-21 版, surveying
July 2024 streams) names it the most-used opener of the winner of the 2024-07-28 Tetris Block Party
PPT2 GRAND MASTERS tournament. The overview quotes that page's own two counts and its OWN caveat
about the sample (little data; the tournament-only games split about evenly with はちみつ砲; most games
against a player who plays ガムシロ積み almost exclusively) and nothing beyond it. Those are the only
typed figures in the prose, and they are the source's; the page's provenance (URL, dates, sha256,
size, the counts as printed) sits in the routes JSON's `source.why_this_opener`, hand-read and gated
by nothing — re-read it if a sentence about it changes.

**The cross-source is a second DRAWING, not a field or a catalogue entry.** harddrop's transcription
(`wiki-openers.json`) lists Gamushiro Stacking only as a `Triple Double openers` category member and
draws no field; Ivan's catalogue has no entry. So `route_transcription.py` gained a third route,
`harddrop_page`: harddrop's own Gamushiro_Stacking page (oldid and hash recorded), its four 「First
Bag setup」 diagrams read with the same parser `wiki-openers.json` is built with and compared with
`bag1.left` / `bag1.l_top`, as drawn and mirrored, cell for cell. The gate fails when none of the
three routes is given, and `--html-dir` fails when the harddrop page is missing beside the shiwehi
one. Two further ties are checked: the category membership (the normal route fires the TST first),
and the source's own sentence 「山岳積み2号と%Iの位置がずれた形」 against harddrop's Mountainous
Stacking 2 field (delete the I's column from each; the rest is equal letter for letter). Adding a
field to `wiki-openers.json` instead would have re-emitted every session's `opener-facts.json`.

What this page needed that the other four did not, and the readings that came out of an independent
audit of the transcription:

* **山岳積み2号's hold split with stick spin's no flag.** `bag1.l_top` (7 locks, the L stood on the O,
  drawn only as 基本形 1) first, then `bag1.left` (6 locks, L held) split by the 7th piece against the
  mirror-aware L; `bag1.left` is the page's `hold_node`. No 六個具名定式 column, so no flag: the
  corpus cross-check is the ordering metric — every bag-1 case with a complete opener window must hold
  a T-spin Triple and no Double-first order, and be Triple-first or named in `NOT_TRIPLE_FIRST` with
  a reason the test verifies on the round's own locks. Only that direction is checked: Triple-first
  is most of the corpus, so the reverse would test nothing.
* **A heading that cannot be an order.** The 妥協 board is headed 「%L>%Oの場合」, but its bag-2 l
  rests ON the O and only the held bag-1 L lies under it; with the T already in the hold (the trigger
  「%T>%L%O」), a bag-2 L dealt before the O has nowhere to go. The first transcription encoded the
  heading as a bag-2 order backed by the held L's support — evidence for a different piece — and the
  demo planner then measured the board unbuildable. It is now the named discrepancy
  `2.compromise:heading_vs_board` and no condition; the selftest puts the order back and must see the
  discrepancy vanish. **The demo is built**, and it is the one place the planner had to learn that a
  `before` pair is an order of DEALING. With the hold box full, the queue builder already dealt the
  bag's last placement (the spin's T) at the swap slot, but the search's wait check read the pair in
  PLACEMENT order, where the T is last, so 「T 早過 L、O」 could never be met and the board was reported
  unbuildable (「O 要等 T；L 要等 T」). The wait check now credits the swap slot by the queue builder's
  own rule (`dealtEarly` in `planBag`): the bag-2 T is dealt fourth, held, swaps out the bag-1 L, and
  is fired last as the TST. `noSwapDeal` turns the rule off; it is a MUTANT here (the demo goes back to
  unbuilt) and, measured on 2026-10-14, an EQUIVALENT mutant on the other four openers, whose demos
  build byte-identically with it — so the shared-code edit moved their artefacts in `planner_md5`
  only and none of their pages. The demos test reads the result off the ENGINE's record (the dealt
  queue, the hold key on the bag-1 L's lock, a full 3-line spin out of the hold on the last lock), and
  `route-demo-checks.ts` gained the branch an unmatchable BAG-2 demo needs: the board is too tall for
  the classifier, so the drawing check is what shows the demo reached it, and the classifier must file
  it under no bag-2 node at all.
* **A blank top row is not a ninth row.** `2.normal.imperial#2` is drawn nine rows tall under a blank
  row; it was first marked unmatchable for 「9 non-empty rows」, which is false (8). It is compared now,
  as both the gate's `bottom()` and the classifier's `occGrid` already allowed. `2.normal.imperial#1`
  (nine real rows), `2.compromise` and its spin board (ten) stay unmatchable, so the 妥協 branch is
  drawn among `bag2_extra` rather than in `bag2_order`, which reads every node's case count.
* **Muted cells.** `L` the held bag-1 L and `C` the rows a TST clears, checked by the gate and drawn
  through `cell_classes`. A `label_jp` is page text or a heading path: the after-the-TST board has
  none, as on 山岳積み2号 (the audit caught an invented one).
* **`2.normal.pc#3` is built without its TSD** (`TSD_NOT_FIRED`): its slot is roofed by the J's hook
  and the S, and the planner measured no order in which the engine credits the spin; the drawing is
  the same board either way, and the test re-runs the planner with it read as a TSD to keep that true.

The named lists are `BAG2_NONE_UNEXPLAINED`, `NOT_TRIPLE_FIRST`, and the measured-empty
`L_HOLD_BAG1`, `L_PLACED_ELSEWHERE_BAG1`, `BAG2_GARBAGE_STRIPPED`, `BAG2_NONE_TST_BEFORE_COMPLETE` /
`_EXTRA_PIECE` / `_MOVED_PIECE`, `PC_OFF_PAGE`, `BAG2_HANDEDNESS_MISMATCH`,
`MULTI_COLOUR_RESOLVED_BY_GROUP`, `COLOUR_DISAGREE` and `PC_GARBAGE_IN_WINDOW`; demos `DEMO_UNBUILT`
(the mirror, the illustrations and the commented-out template), `TSD_NOT_FIRED`,
`DEMO_SPIN_LINES`, `DEMO_SPIN_EXCEPTIONS` and `DEMO_PIECE_READINGS`. Sizes are read off the tests.
`no180` is a control; `ignoreConditions` is a MUTANT here, as on はちみつ砲: the bag-1 no-hold orders
(J before S, Z before T) are not forced by gravity.

### SDPC Spin

The same deliverable for harddrop's `SDPC_Spin` page (an opener by Ecchou; categories T-Spin openers,
T-Spin Single openers, Single Double openers): `pipeline/openers/sdpcspin-routes.json` (gated by
`extract_sdpcspin_routes.py` through the shared gate), `analysis/sdpcspin-facts.json`
(`sdpcspin.test.ts`), `analysis/sdpcspin-demos.json` (`sdpcspin-demos.test.ts`), and
`docs/sdpcspin.html` plus `sdpcspin-tsd.html`, `sdpcspin-bag1-only.html` and `sdpcspin-demos.html`,
rendered by `bin/build-docs` from `ROUTE_SITES` and linked as the sixth card under 定式路線. Counts are
read off the artefacts and tests, never typed here or in `sdpcspin_prose.json`. **Emit the facts
before the demos**: the demos artefact hashes the classifier, and its test classifies every demo.

**It is the opener yachi's Double-first rounds are, and that is the page's corpus finding.** The
2026-10-13 reading called them stick spin; a 2026-10-15 probe followed them through three bags and
found SDPC Spin's bag 1, its Second-bag TSD board and its Third-bag TST builds (the correction is at
the original site, 「C-Spin 同 DT 砲」). The probe used a bag-attributed composite and was never
committed, so **none of its figures is quoted anywhere**: the committed route is the classifier's
snapshot rule, and `sdpcspin.test.ts` is what re-derives every count — `NODE_CASES` per node,
`DT_AND_SDPCSPIN` for the Double-first rounds that are SDPC Spin cases (with `DT_NOT_SDPCSPIN` naming
the rest, each with a verified reason: `dt_cannon`, `both_orders`, or `garbage_bag1` for the one
round whose garbage arrived before lock 6), `SDPCSPIN_NOT_DT` for the converse, and `STOPS` for where
every case ends. **The snapshot rule files fewer bag-3 rounds than the composite did, and that is a
definition, not a miss**: a round that fires its TST with one or two bag-3 pieces still to place
never holds the drawn board at any lock. `STOPS_AT_2TSD` measures every round that reached `2.tsd`
and no bag-3 board, as `tst_before_complete`, `tst_off_page` or `no_tst`; the rule is not relaxed.

**The source is wikitext, not HTML, and it is the first route page not from shiwehi.com.** The page
was read with `oc raw` of its `action=edit` page (never curl); `source` in the routes JSON records
the oldid, the sha256 and byte count of the snapshot, and how it was fetched. Boards are
`{{pfstart}} … {{pfend}}` templates, read by a new additive reader in `route_transcription.py`
(`wikitext_tables` / `wikitext_cell` / `wikitext_boards`). harddrop publishes no licence for wiki
content, so `terms` records 「not stated」 and every page credits by link; the header credit comes from
the prose's `source_credit`, a branch `route_page.py` gained for this page (the shared default stays
shiwehi.com's terms). A refetch is re-checked with `--html-dir` holding both `.wikitext` snapshots.

**Both wikitext pins are now MediaWiki's own bytes, and a weekly job re-reads them.** The first
snapshots were oc's whitespace-collapsed renderings, so their sha256 was ours alone. On 2026-10-16
both records were re-pinned to the API's revision content: `revision_sha1` is MediaWiki's sha1 of the
revision, which equals sha1 of the bytes — an authority independent of this repo — and
`snapshot_sha256` / `snapshot_bytes` are of those bytes. (Collapsing whitespace in the API bytes
reproduces the old SDPC_Spin hash exactly, which is how the change was checked to be a re-encoding
and not an upstream edit.) `pipeline/openers/check_wikitext_sources.py` discovers every routes file
whose records pin a `revision_sha1`, fetches each pinned revision through `api.php` (urllib with a
descriptive User-Agent, never curl), checks the API sha1, the bytes' sha1 and the recorded sha1 agree
and the sha256 and byte count match (`snapshot_bytes` is required, not skipped when absent), re-runs
that routes file's extractor with `--html-dir` over the fetched bytes, and **fails when the page has a
newer revision than the pin** or the API returns no revid — an upstream edit means the transcription
has not been re-read, so it is a red build, not a pass. Revisions are immutable, so a green run says
the pinned page is still the one transcribed. It runs in `wikitext-sources.yml`, weekly and on
dispatch only, because a per-push network check would make every build depend on harddrop.com; its
`--selftest` (a fake MediaWiki API: wrong or disagreeing sha1s, a newer revision, a missing revid, a
missing `snapshot_bytes`, HTTP 403, a missing revision, a network error, a board edited under re-pinned
hashes) runs on every push in `docs`. ガムシロ積み's harddrop cross-source pins an oldid but no
`revision_sha1`, so it is not discovered — a control in the selftest.

**Since 2026-10-19 it re-reads the technique transcriptions too, and only their wikitext half.** Every
`*-technique.json` holding, anywhere in it, an object with both `oldid` and `revision_sha1` is discovered
by that structure (the record's role is its dotted path, e.g. `cross_source.harddrop`), never by a list;
each pinned revision gets the same fetch / sha1 / sha256 / bytes / latest checks, and then the extractor
(`extract_<key>_shapes`) runs with `--wikitext-dir`, not `--html-dir`, because the technique's own page is
shiwehi.com HTML that no `api.php` call returns. `--wikitext-dir` runs the spec's opt-in `wikitext_checks`
alone (`technique_transcription.TechniqueSpec`) and FAILS by name when a spec declares none, so a
discovered record is never passed with nothing re-parsed. Every snapshot the file records that is not a
pinned revision is printed as a `gap` line: the shiwehi page (and any other non-wiki page) is still
re-checked only by a person running `--html-dir` with a refetch. The selftest adds the structural
discovery cases (a pin nested inside a list is found at its path; the same record without
`revision_sha1` is not, and is a gap; a file with no pin is not discovered) and, for every discovered
technique whose spec declares the opt-in `synthetic_wikitext`, the record-level mutants and a board edited
under re-pinned hashes, which only the extractor's re-parse can see (a pfrow page loses a filled cell; a page
drawing its board as a fumen has one fumen character changed). A discovered technique missing either hook is a
SURVIVOR of the selftest, so the per-push `docs` job goes red on it: it used to be printed `NOT PLANTED` and
passed, while the live weekly run was red by construction — 欄干's harddrop pin shipped that way for one pass.

**Bag 1 has three cross-sources, all checked by the gate; bag 2 onward has none, and every page says
so.** (1) harddrop's SingleYou page, table 0 — the page's 「stacked the same way as SDPC」 is that
equality — through a new `harddrop_wikitext` route of the gate's rule 2; (2) stick spin's `bag1.pc` and
its after board, mirrored; (3) Ivan's catalogue's SDPC-Spin compound entry. `cross_source.bag2_onward`
records the single source, and `page_sentences.source` is a REQUIRED sentence on every page.

What this page needs that the other five did not:

* **Derived 6-lock stage nodes, one per colouring.** harddrop draws bag 1 only with the T placed
  (`bag1.lj`, the L under the J; `bag1.jl`, the J there), so the bag-1 spin step needs a 6-lock board
  to stand on: `bag1.lj.left` and `bag1.jl.left` are DERIVED (each TSS board less its `U` cells,
  checked by the gate's `bag1-derived:` rule, with two selftest mutants), and each TSS board is
  `spin_of` and `parent` its own. They carry no `group`: `bag1.sdpc`'s `drawn` is the page's own
  count of two boards, which the shared grammar rule pins. `bag1.requires` is `{}` (the page states no
  bag-1 order), so the shared demo check reads 「no early piece」 from the transcription itself. Two, not one, because both TSS boards
  draw the same `U` cells, so colour must decide at the stage — 山岳積み2号's `bag1.l_hold` precedent
  and stick spin's `bag1.left` → `bag1.pc` shape. Stick spin's J/L-split exceptions are `bag1.lj`
  rounds here.
* **No flag and no hold**, as stick spin: no 六個具名定式 column draws SDPC Spin, and no input holds.
  The source's transition board says 「hold O and tuck it」; that is quoted source text, which the
  shared 「hold」 audit now exempts exactly as the % rule always did. The siblings' hold mutants plant
  outside quotes and are still caught, so this narrows nothing they test.
* **A tree six bags deep.** Bag 3 has three TST builds (`3.first`, `3.second`, `3.third`) and bags 4
  and 5 hang under them: the STMB Cave and STSD, the Trinity, the C-Spin and its DT Cannon
  continuation, the Imperial Cross and its four 14-line PCs. `bag3_parents` places by id prefix, so
  the three builds are parents of their own and everything from bag 3 to bag 6 is drawn under 第三巡;
  the prose says so. Only one bag-2 board exists, so there is one bag-2 page (`sdpcspin-tsd.html`).
* **The PC frame is `{locks: 28}`, `lines: 14`, `rows: 7`, and the obvious rule cannot work.** All four
  Imperial Cross patterns roof the T slot, so the body's own TSD always fires before the PC's last
  lock and 「after the last TSD」 picks it; and the patterns are drawn seven rows tall, which a six-row
  frame refuses. `route-profile.ts`'s `PcKind` docstring still describes `{locks}` as 「with no spin
  before it」, which this use contradicts and `frameStart` does not enforce.
* **An `at_least` condition** (the STMB Cave's 「J before at least two of T, L and Z」): the board
  forces only J before T, so the other two are marked stated, not forced. The page reads it through a
  new branch of `_condition_words`; the shared planner and `conditionHolds` read only `all`, so the
  demo test checks it on the queue itself.
* **Readings, marked**: `P` and `T` read as `U`; `G` as `c` (earlier cells, checked as the post-spin
  base); an upper-case letter as a muted residue; the apostrophe as `v`. The two DT Cannon boards carry
  `residue_of` and no base, and draw the C-Spin's bag-3 I live beside the new one — the named
  discrepancies `3.second.cspin.dt#1:colour` / `dt#2:colour`. The page does not say which Trinity spin
  fires first (`order_note`).
* **`3.first.trinity.tss` is a STRUCTURAL zero, not a measured one.** Its sibling
  `3.first.trinity.tsd` draws the board the Trinity's TSD leaves, and the classifier files a round at
  the earliest matching sibling, so nothing — corpus or constructed — can reach the TSS node. The demo
  test names it in `CLASSIFIER_SIBLING` and checks the TSS demo is filed under the TSD, the facts test
  labels its 0 in `STRUCTURAL_ZERO`; the page's
  bag-3 note says so beside the count.

The named lists are `BAG1_SPIN_OFF_PAGE`, `BAG2_GARBAGE_STRIPPED`, `BAG2_NONE_TSD_BEFORE_COMPLETE`,
`BAG2_NONE_UNEXPLAINED`, `STOPS_AT_2TSD`, `DEEPEST_UNVERIFIED`, `DT_NOT_SDPCSPIN`, `SDPCSPIN_NOT_DT`,
`STICKSPIN_NEAR_NOT_2TSD`, and the measured-empty `BAG2_NONE_EXTRA_PIECE` / `_MOVED_PIECE`,
`PC_OFF_PAGE`, `BAG2_HANDEDNESS_MISMATCH`, `MULTI_COLOUR_RESOLVED_BY_BRANCH`, `COLOUR_DISAGREE` and
`PC_GARBAGE_IN_WINDOW`; demos `DEMO_UNBUILT` (the two illustrations, the board that draws its Z twice
and the two DT Cannon boards), `CLASSIFIER_PARENT_UNFILED`, `U_BEFORE_SUPPORT`, `DEMO_SPIN_LINES`,
`DEMO_SPIN_EXCEPTIONS` and `DEMO_PIECE_READINGS`. Sizes are read off the tests. The facts test's live mutants are `noMirror`,
`spinMirrorUnaware`, `spinClearStops`, `bag2Early`, `noGarbageStrip`, `noGarbageStop` and `noSwap`,
each with its symptom asserted; the hold-stage, PC/scope and `matchFromFilename` mutants are measured
EQUIVALENT on this corpus and named, so the day one stops being equivalent is a red build. In the
demos, `noRowMap`, `noReach`, `noSpinCheck` and `noUBefore` are mutants, `noSwapDeal` and
`ignoreConditions` are EQUIVALENT here (no demo holds; `3.third`'s S before O is forced by gravity),
and `no180` is a control.

**The TSDs the page fires BEFORE pieces its board draws are built since 2026-10-16, through one
explicit reading per node.** ~~Building the planner-unbuilt nodes would need a shared change … it is
an open item, not done.~~ The shared change is `DemoProfile.uFiresBefore` (`route-profile.ts`): a
map from node id to the pieces the T fires before, and `BagSpec.uBefore` in `route-demos.ts`, which
lets the U go before exactly those pieces and makes them wait for it (「要等 T(U)」); the order reading
records `u_before:<pieces>`. It is a profile reading per node, **never a search fallback** — a
fallback would also build nodes other openers name as unbuilt, and stick spin's two SDパフェ
patterns are the obvious candidates for a later, deliberate reading. SDPC Spin names eight boards
(`route-profile-sdpcspin.ts`); the sets are the pieces each board forces after its TSD — the one over
the slot, plus, in the three Z-and-J boards, the Z that only rests on that J (`U_BEFORE_SUPPORT`) —
and the test 「measured: each uFiresBefore TSD fires before the pieces the profile names, and no
fewer」 re-measures each set as minimal with the engine's own `reach()`. The drawing never stands at
any lock of such a demo, so it is checked as the last bag's kept-rows composite in both
implementations (`route-demo-checks.ts` and `route_page._demo_end`): the U is the bag's one U, a T,
with the drawn spin and lines, followed by exactly the named pieces, and the classifier must file NO
snapshot for the node; a test sets a node's drawing to its sibling's and must see the composite check
fail. Their matchable children whose parent is never filed are named in `CLASSIFIER_PARENT_UNFILED`.
The shared edit moved every sibling's artefacts in their md5 lines only and none of their pages
(no sibling profile names a `uFiresBefore` node, so `noUBefore` cannot reach them).

## 中盤手法頁（STSD、STMB Cave、インペリアルクロス、ダブルダガー、BT砲、千鳥格子、社畜トレイン、欄干、階段のドネイト、途中DT砲、基本的なドネイト）— every mid-game technique page, quarantined like the route pages

shiwehi.com's 「中盤テンプレ・ドネイト」 pages draw a technique on a PARTIAL stack, at whatever lock it
happens, which the route machinery cannot express: `route-facts.ts` compares whole boards (at most 8
rows, bottom-aligned) at fixed lock counts from an empty board, behind a bag-1 gate. So the technique
pages are a SIBLING framework that imports the route code and edits none of it — no route artefact's
hash line and no route page moved when it landed. STSD (`template/stsd.php`) is the first page,
STMB Cave (`template/stmbcave.php`) the second, インペリアルクロス (`template/imperialcross.php`) the third and
ダブルダガー (`template/doubledagger.php`) the fourth, BT砲 (`template/btcannon.php`) the fifth, 千鳥格子 (`template/cutcopy.php`) the sixth, 社畜トレイン (`template/shachikutrain.php`) the seventh, 欄干 (`template/parapet.php`) the eighth, 階段のドネイト (`template/kaidansetup.php`) the ninth, 途中DT砲 (`template/dtcannon.php`) the tenth and 基本的なドネイト (`template/basicdonating.php`) the eleventh (each later one has a ### below); a later technique whose shape the window
predicate can express is a data addition (a transcription
module + JSON, a facts profile, a demos profile, a page profile + prose, one registry line per side,
two tests, three CI steps, one `TECHNIQUE_SITES` entry).

| piece | where |
|---|---|
| transcription | `pipeline/openers/stsd-technique.json` (schema `technique-shapes/1`, named `*-technique.json` so no `*-routes.json` glob sees it), held as a literal in `extract_stsd_shapes.py` and gated by the shared `technique_transcription.py`; raw-HTML snapshot, fetched like 山岳積み2号's, re-checked with `--html-dir` |
| matcher + artefact | `pipeline/sim/technique-facts.ts` (rules), `technique-profile.ts` (types), `technique-profile-stsd.ts` (data), `techniques.ts` (registry, unhashed) → `analysis/stsd-facts.json` |
| facts test | `pipeline/openers/stsd.test.ts` (+ `technique-facts-checks.ts`) |
| demos | `pipeline/sim/technique-demos.ts` (planner), `technique-demo-profile.ts` / `technique-demos-stsd.ts` → `analysis/stsd-demos.json`; test `stsd-demos.test.ts` |
| pages | `pipeline/technique_page.py` (renderer + audit) bound by `stsd_page.py` + `stsd_prose.json` → `docs/stsd.html`, `docs/stsd-demos.html`, rendered by `bin/build-docs` from `TECHNIQUE_SITES` under a 中盤手法 index group after 定式路線 |

**Every hit links to the moment, not the round start** (since 2026-10-20): the case row's link is
`<date>-replay.html#m<pos>r<round>@p<n>`, where `<n>` indexes the replay page's MERGED lock order (both players' locks by frame,
`replay_section.round_payload`'s `order`, which `replay_player.js` steps through), set to the position just before the hit's T —
`n` locks placed, so the page shows the board the T went into and one step plays it. `technique_page.replay_href` computes it from
the session's `replay-facts.json` and `facts.json`; the overview audit re-reads every link from the other side
(`audit_replay_links`): the position's next step, decoded from an empty board with `replay_section.decode_boards`, must be the hit
player's lock at the hit's lock index, a T with a full spin clearing the variant's lines. The page selftest plants a link one
position late, one early, at the player's previous lock and at the round's start, and each is caught. Only the hrefs and the
`cases_note` sentence moved on the nine pages.

**The predicate is anchored on the T, not on a column range.** The lock's four cells must equal the
variant's drawn T cells under one translation (mirrored: columns reflected inside the window), which
fixes orientation too; every other cell of the window the transcription carries must be filled
(any piece or garbage — garbage is FILLED) or empty as drawn; colour is never compared, and nothing
outside the window is read. The cleared rows' cells right of the window are deliberately not tested:
they are entailed by the clear (the `NaiveClauseForced` lesson), and the gate's window rule that no
piece letter sits outside the window is what makes leaving them out safe. The window is written
TWICE — `windowMatch` in TS and `window_fires` in the gate — and the facts test holds the two to one
answer over every board of every committed `*-routes.json` (the cross-source: harddrop's SDPC Spin
page fires it as drawn and mirrored; one 山岳積み2号 board fires it unlabelled and is named, not
explained).

**The denominator is the scored TSD, and the loop that scores it is a THIRD COPY.** A T lock with an
engine spin credit that cleared lines, inside the verified prefix, passing the reconstruction check —
the same loop as `emit-opener-facts.ts`'s donation / cave pass and `dualVerdict`, kept as a copy so
that emitter is not edited. `stsd.test.ts` holds its scored count to `opener-facts.json`'s
`donation.check` in every session and for every player, which is the gate on the duplication.
Opener / mid-game is the 0-based `lock <= WINDOW_PIECES` convention (see the lock-numbering note in
「C-Spin 同 DT 砲」), and the artefact says which one it uses.

**No headline without its controls**, and the page audit enforces it: the same window under TSS, TST
and the mini spins, three ablations (no must-empty clause, no roof, the T merely overlapping the
window) and the orientation baseline, each 「N / M」 beside the headline. One ablation EQUALS the
headline on this corpus — the roof never decides a match — and is recorded as a finding, not
dropped. The follow-up (the second TSD the page promises) carries the slot through every clear and
garbage insertion to the next T, each step verified against the engine's own next board, and every
miss has a named reason. Every figure is read off the artefact and the tests; none is typed here.

**The cross-route counts only what it measured, inside the drawn continuation.** It takes the SDPC
Spin rounds that reached the STMB Cave node and asks whether an STSD hit follows in the bag harddrop
draws it in (`continuationLastLock`, re-derived by the test from `sdpcspin-routes.json`). A hit later
in the round is recorded as `later_hit_lock` and never counted — an unbounded 「any later hit」 once
counted one 74 locks after the cave as corroboration of the drawing. A round whose node the route
reached past its verified prefix (`verified: false` in the route artefact), or whose continuation runs
past the prefix with no hit inside it, is named in `cross_route_unscored` and kept out of M: a scan
for T-spins between the node and a prefix that ends before it is empty by construction, so its 「no
T-spin」 was never a measurement. The artefact's reasons are outcome codes with counts; the page words
each one in Cantonese from the prose, never by printing the English list line.

**Readings and discrepancies are the transcription's and are printed on the page:** `B` an EMPTY
garbage-hole cell, muted upper case the rows a spin clears, the three terrains the page never draws
DERIVED by subtracting its pieces (checked), the after board drawn with the right side stacked up
(`basic.after:after`), and the misfire's J drawn three cells (`misfire.spin:colour`).

**Demos are BUILT from an empty board, never seeded**, because every decoder in this repo (the TS
one, `replay_section.decode_boards`, the inlined player) starts empty and a timeline can insert only
one-hole garbage rows. The planner enumerates exact covers of the terrain's grey cells by non-T
pieces, then searches placement orders the engine can play, then fires the stood T at the one T
placement where `windowMatch` matches, fills the follow-up's rows with pieces OUTSIDE the window
columns where the drawing assumes them, and fires the follow-up. Two T-spins in a row need two T's
close together, so the dealing is one scheme: bag 1's T dealt last and held, bag 2's first piece
placed in its stead, bag 2's T swapped for the held one, the follow-up T swapped out when the next
piece arrives — whole 7-bags throughout. The engine is the arbiter (`runDemo` + `assertRoundTrip`),
the page re-decodes every embedded demo with its own decoder, and a terrain the planner cannot build
is published unbuilt with the planner's MEASURED reason (an ODD cell count, which is a proof rather
than a planner limit — each lock adds 4 cells and each line clear removes 10, so a board built from
empty always holds an even count; an even count that is not a multiple of four is worded as THIS
planner's limit, since it never clears a line; the garbage boards because a constructed demo has no
opponent). `noSpinCheck` is a
measured EQUIVALENT mutant — both T slots are reachable only by a spin — and `no180` changes a path
and no check. Named lists and their sizes live in the two tests, never here.

**What would move every technique artefact's hash line:** a new `anchor` value (a technique the
window predicate cannot express) is an edit to `technique-facts.ts`, which every technique artefact's `emitter_md5`
hashes — loud, and the cost to name when it happens. The live case is アンカーセット (Anchor Set, `template/anchorset.php`):
a J or L placement with no T-spin, whose drawings agree on no rectangle holding both the anchor and the overhang, so
matching it needs an anchor on a non-spin lock AND a window that is not a rectangle (ROADMAP.md, with the measured
reasons). 階段のドネイト was the example this sentence used to give (「a staircase over several locks」), and it was wrong:
measured, its shape sits in the rows the TSD clears and the two rows under them, all on one board at the TSD's lock, so no
sequence of locks is needed (the window counts no steps and cannot tell a staircase from a flat stack). `technique-profile-stsd.ts` also lists `route-facts.ts` among its hashed files,
because the emitter imports from it; the demos hash `route-demos.ts` for the same reason. The reverse
direction is clean: no route artefact hashes a technique file.

**欄干 is the change that moved them, and it moved nothing else.** Its payoff (in place of a follow-up) and its
per-variant opportunity are edits to `technique-facts.ts`, and the payoff variant's demo ending on the stood T is an
edit to `technique-demos.ts`; so every one of the seven earlier technique artefacts re-emitted with a new
`emitter_md5` (facts), `planner_md5` and `classifier_md5` (demos), which `git diff` was checked to show before any 欄干
file was written. The same pass moved one more hash line in six of them, for a different reason:
`transcription_md5` in BT砲's, 千鳥格子's and 社畜トレイン's facts and demos, because the wikitext-discovery change
rewrote the `snapshot_note` of those three transcriptions (their harddrop records are refetched weekly now). STSD's,
STMB Cave's, インペリアルクロス's and ダブルダガー's moved in the three md5 lines above and nothing else; no earlier
artefact moved outside its hash lines. The Python halves (`technique_transcription.py`'s rule (d') and the per-variant
external drawings, `technique_page.py`'s `more_variants`) are unhashed and default-preserving: every earlier gate's
plain, `--selftest` and `--html-dir` output and every earlier `*_page --selftest` output was byte-compared against the
pre-edit run, and `bin/build-docs --check` passed with no earlier page moved (only `docs/index.html` gains the card).

**階段のドネイト changed no shared RULE file, and then one docstring moved every hash line, on purpose.** Its files were added
and every earlier technique artefact re-emitted byte-identical (the zero-shared-change control), with one exception that is data,
not code: 社畜トレイン's `other_windows` (complete both ways over every committed technique window) now records the
drawn T's of its harddrop page at which the Kaidan window fires, so its transcription and its two artefacts' `transcription_md5`
moved, and its gate's plain, `--selftest` and `--html-dir` output did not. Every earlier gate's output and every earlier page
was byte-compared against 6844978 and is identical. Only then was `technique-profile.ts`'s docstring corrected (it repeated the
false 「staircase over several locks」 example); that file is hashed, so all nine facts artefacts' `emitter_md5` and all nine
demos' `classifier_md5` moved, and `git diff` shows those lines and nothing else. One shared TEST module was added too:
`pipeline/openers/technique-donation-checks.ts` (`H`, `W`, `scored`, `donationVerdict`) is `parapet.test.ts`'s donation helper
moved verbatim so `kaidan.test.ts` can import it, and `parapet.test.ts` imports it now; no artefact hashes it.

### STMB Cave

The same deliverable for `template/stmbcave.php` (「2021-03-23更新」): `pipeline/openers/stmbcave-technique.json`
(held as a literal in `extract_stmbcave_shapes.py`, gated by the shared `technique_transcription.py`),
`technique-profile-stmbcave.ts` → `analysis/stmbcave-facts.json` (`stmbcave.test.ts`),
`technique-demos-stmbcave.ts` → `analysis/stmbcave-demos.json` (`stmbcave-demos.test.ts`), and
`docs/stmbcave.html` + `docs/stmbcave-demos.html` from `stmbcave_page.py` + `stmbcave_prose.json`, the
second card under 中盤手法. Every figure is read off the artefacts and tests, never typed here.

**The spin is a TSD and the anchor is the T's cells, as STSD's — the T laid flat, nub down — so the
window predicate expresses it and the matcher (`technique-facts.ts`) is untouched.** What did not fit
was the GATE's window rule: STSD's window is the bounding box of the T, every filled cell above it and
the follow-up slot, and this page's one complete TSD is drawn on a stacked board whose J, Z, L and O
above the T are no part of the shape (each other drawing has different cells there). So a variant may
now declare `window_basis: agreement` (opt-in; STSD's gate output is byte-identical with or without the
change, compared by running both): the window is the box on which every drawing of the shape agrees —
the page's own three, and harddrop's positive STMB_Cave diagrams from `wiki-tspin-techniques.json` (the
spec's `external_drawings`) — checked from BOTH sides: every drawing fires it exactly once, at its
declared slot and hand, and widening it by a row or a column on any side meets a disagreement or leaves
a drawing. Every piece letter left outside is named in `untested_drawn`, both ways. The same pass made
the follow-up rule compare the after board BOTTOM-aligned (this page draws it a row shorter than the
spin board; STSD draws them the same height, so its shift is zero).

**What the window can discriminate is one row.** Its top two rows are the rows the TSD clears, so at
the opportunity every filled cell in them is entailed by the clear (`NaiveClauseForced`), the nub row
being the cave's roof (`RoofForced` / `RoofCannotDiscriminate`) — no roof test is added, and the test
MEASURES that the cave row alone, with the T anchored, gives exactly the headline. The page's own roof
(the stood Z over the T's back arm) is outside the box: on the stacked board the cell beside it is the L
that roofs the NEXT TSD, which no other drawing has, and a rectangle cannot keep one without the other.
Because a flat T is symmetric, the must-empty cells are what tell the two hands apart: the `noMustEmpty`
mutant makes a lock match both, and the matcher refuses it (the test asserts the throw).

**Cross-checks, each stated in the test as agreement or named differences.** (1) The opener metric
(`opener-facts.json` `stmb_cave`, harddrop's ≥3-wide gap overlapping the T): `stmbcave.test.ts`
re-implements `caveAt` (importing `emit-opener-facts.ts` runs a session) and reproduces every session's
per-player `width_ge_3`, `min_depth_ge_2`, `in_opener` and `mid_game` exactly; every hit is one of its
caves, and every cave that is not a hit is named in `CAVE_METRIC_ONLY` with a re-derived geometric
reason (`centred`: the gap is the T's own columns; `arm_only`: the gap reaches under one arm, the nub on
a filled cell; `wall`: the cells behind the nub leave the board). (2) SDPC Spin: every round whose route
reached `3.first.cave` with the node verified is a hit at its next T lock (`SDPC_CAVE_HITS`), the rest
named. (3) The gate's `cross:` rule over every routes board: harddrop's SDPC Spin cave fires; the same
author's stick spin cave is over a FOUR-wide gap and is named, not fitted (the agreement box's far wall
is filled on every drawing in the agreement set).

**`window_off_board` is a count with a property check, not a list.** The window holds the row under the
nub, so every TSD on the floor, and every one hard against a wall, leaves the board — far too many to list
(the size is the artefact's and the test's, never this file's). **A window cell past the side or the floor is
"leaves the board", never "filled"**, for every technique: the drawings draw stack in those cells, and the wall
is not read as standing in for it, so a shape built flush against the wall is not a hit. That is a definition,
not a measurement, and `stmbcave.test.ts` names the cave it costs (`CAVE_METRIC_ONLY`, reason `wall`). The test pins the count per player and checks every entry is a flat nub-down T whose window leaves the
board in at least one hand and is not a hit — not an exact re-derivation, because the matcher returns
"off board" only when no in-board cell failed first (iteration order; the `garbageEmpty` mutant moves
entries out of that list and no hit, which is its asserted symptom).

**No demo is built, and every board says why.** The planner stops each chain at its first failing
check — the basic form's terrain is even but not a multiple of four (a planner limit), the complete
TSD's J is two lower-case cells (its third is muted in the cleared row), the similar form's S is a Z's
shape — and `stmbcave-demos.test.ts` re-derives each, with the facts behind them (two of the three
terrains have an ODD cell count, a proof; the basic form's T completes one row, so it is a local sketch,
not a full TSD). Two shared-file edits came with that, both in unhashed Python and default-preserving:
`technique_page.py`'s selftest skips its demo-island plants when there is no demo (and plants a dropped
unbuilt block instead), and the board it drops is the profile's `selftest_board` (default STSD's).
Named lists and their sizes live in the two tests, never here.

### インペリアルクロス（Imperial Cross）

The same deliverable for `template/imperialcross.php` (「2020-06-20更新」): `pipeline/openers/imperialcross-technique.json`
(held as a literal in `extract_imperialcross_shapes.py`, gated by the shared `technique_transcription.py`),
`technique-profile-imperialcross.ts` → `analysis/imperialcross-facts.json` (`imperialcross.test.ts`),
`technique-demos-imperialcross.ts` → `analysis/imperialcross-demos.json` (`imperialcross-demos.test.ts`), and
`docs/imperialcross.html` + `docs/imperialcross-demos.html` from `imperialcross_page.py` +
`imperialcross_prose.json`, the third card under 中盤手法. Every figure is read off the artefacts and tests,
never typed here.

**The spin is a TSD and the anchor is the T's cells — the T STOOD UP, nub right (mirrored: nub left) — so
the window predicate expresses it and the matcher (`technique-facts.ts`) is untouched.** The T goes into a
cross-shaped hole and clears the cross's top and bottom rows, which are NOT adjacent; the engine credits a
full TSD either way, and nothing in the matcher assumes the cleared rows touch (the follow-up's row map
counts the cleared rows below each slot cell). The row between them keeps the cross's far arm EMPTY, and that
cell is what tells this T from STSD's (whose nub fills it): `imperialcross.test.ts` re-derives, from both
transcriptions, that anchored on the same stood T the two windows disagree on a cell, and measures the two hit
sets disjoint.

**The window is the agreement box (`window_basis: agreement`, STMB Cave's opt-in), and the reason is the
page's own build.** The bounding box of T, roof and follow-up reaches a column whose top cell is empty on the
spin board, FILLED on the page's TSD-shape build (its stood Z) and drawn `B` on the basic form. So the window
is the box every drawing agrees on — the page's basic form and three builds, and ガムシロ積み's two Imperial
Cross boards (`gamushiro-routes.json`, the spec's `external_drawings`, their slots declared in the extract
module and checked by the agreement rule). `B` here is dark grey the page leaves open: read as EMPTY
(`empty_letters`), and `extra_checks` measures that the window reads no `B` cell where it fires. The cross
check (`cross:`) fires on harddrop's SDPC Spin `3.third.imperial` (independent) and on stick spin's
`2.sd.imperial.spin` (same author, `also`), both nub left.

**One gate change, in unhashed Python, default-preserving: the opt-in `followup.drawn_lines`.** The page draws
its after board BEFORE the stack beside the second slot is built, so the follow-up T fills one row of the
drawing while the TSD the page promises clears two. Rule (d) now takes the drawn count from `drawn_lines`
when present (fewer than `lines`, with a `drawn_note`), else `lines` as before; STSD's and STMB Cave's gate,
selftest and `--html-dir` output were compared byte for byte with and without the change. The matcher still
scores the follow-up as a full TSD.

**What discriminates is measured, and either half is enough on this corpus.** The cross's top and bottom rows
are entailed by the clear; with only the cross's filled cells and the T anchored the window admits more TSDs
than the headline (the count is pinned in the test), while the `no_roof` ablation (the cross with its empty
arm) and the `no_must_empty` one (every filled cell, the overhang's included) each give the headline exactly —
so `noMustEmpty` and `noRoof` are measured EQUIVALENT mutants, named and asserted byte-identical.

**Cross-checks against the route artefacts:** no corpus round reached any route page's Imperial Cross node
(named, empty — the scan reads every string of every case, not one field, and `snapshots` is required, never
defaulted); every SDPC Spin round that reached its parent `3.third` is measured over bag 4 (the bag harddrop
draws the Imperial Cross in, re-derived from `sdpcspin-routes.json`) and named with what happened
(`SDPC_THIRD_ROUNDS`; how many is the test's).

**No demo is built, and every board says why** (`imperialcross-demos.test.ts` re-derives each): the basic
form and the bare cross have an ODD cell count (a proof); the TSD-shape terrain has no tiling by tetrominoes
at all (an exact-cover search over all seven kinds, with a control that finds tilings where there are some),
so only line clears could reach it; the cross-shape build's terrain is even but not a multiple of four (a
planner limit). The page's sentence for its TST board holds 来, which the page audit's simplified-glyph check
cannot tell from the simplified character, so that board's caption is not rendered (`caption_note` says so;
the quote is still checked against the snapshot). Named lists and their sizes live in the two tests.

### ダブルダガー（Double Dagger）

The same deliverable for `template/doubledagger.php` (「2020-06-20更新」): `pipeline/openers/doubledagger-technique.json`
(held as a literal in `extract_doubledagger_shapes.py`, gated by the shared `technique_transcription.py`),
`technique-profile-doubledagger.ts` → `analysis/doubledagger-facts.json` (`doubledagger.test.ts`),
`technique-demos-doubledagger.ts` → `analysis/doubledagger-demos.json` (`doubledagger-demos.test.ts`), and
`docs/doubledagger.html` + `docs/doubledagger-demos.html` from `doubledagger_page.py` + `doubledagger_prose.json`,
the fourth card under 中盤手法. Every figure is read off the artefacts and tests, never typed here.

**The spin is a TSD and the anchor is STMB Cave's flat, nub-down T, so the window predicate expresses it and NO
shared file changed** — not the matcher, not the gate, not the renderer: the transcription, the two profiles,
the page profile and prose, one registry line per side, one `TECHNIQUE_SITES` entry. Two TSD slots are stacked
one directly on the other, the upper roofed over one end; the TSD's clear drops the overhang onto the lower
slot, which is the second TSD. The window is STSD's default bounding box (T, roof, follow-up slot): no other
drawing disagrees with the spin board inside it, so the opt-in agreement box was not needed. It does NOT reach
the lower slot's far wall, which the follow-up table answers instead.

**What the shared rules could not say lives in `extra_checks`, under its own tags** (`mirror:`, `line:`,
`pink:`, `B:`, `imperial:`, each with a selftest mutant): the page draws most of its Double Daggers MIRRORED,
and the shared rule (e) takes only as-drawn boards, so `fires_mirrored` is checked there (once, mirrored, at a
two-row placement; spin boards read with their spin piece taken out — the tetris feature spins an I). Its second
feature, a line between the two slots, is a Double Dagger the window does not express: `not_expressed` records
it, and the gate measures both halves (no fire as drawn; with the line row taken out, one fire at the drawn T).
`p` (the page's pink cell, 「屋根の反対側」) is read as empty and measured to be the build's J cell, outside the
window, so the corpus never tests that build condition. `max_rows` is 10 (the tetris feature).

**Cross-sources, both measured.** harddrop's SDPC Spin page (another author) draws this shape in its second
C-Spin build's bag-5 boards — the T in the slot the build makes, directly over the C-Spin's residue slot — and
the gate's `cross:` rule finds them; no routes board is LABELLED ダブルダガー. shiwehi.com's own インペリアルクロス
page draws a Double Dagger as its `dagger` miss and this page draws an インペリアルクロス (`cross.imperial`): the
`imperial:` rule measures each window firing only on the other page's drawing (same author: corroboration).
Every SDPC Spin round that reached that build is measured over bag 5 in the test and named (`SDPC_SECOND_ROUNDS`; how many is the test's).

**What discriminates is measured per window part** (`doubledagger.test.ts`, `PART_ONLY`): with the T anchored,
the lower slot alone gives exactly the headline, while the cleared rows (entailed) and the overhang row (which a
TSD slot nearly always has) admit almost every full TSD — so the `no_roof` ablation equals the headline. The
overhang is still not decoration: it is half of what tells the two HANDS apart, and both `noRoof` and
`noMustEmpty` make a lock match both hands, which the matcher refuses (both asserted to throw). The hit sets of
this window and STMB Cave's (the same flat T) are disjoint and the two windows clash on a cell in every pairing
of hands, both re-derived in the test.

**No demo is built, and every board says why** (`doubledagger-demos.test.ts` re-derives each): the TSD-shape
build's terrain and the bare cross have an ODD cell count (a proof); the basic form, the cross-shape build's
terrain and the three feature boards are even but not multiples of four (a planner limit); and the cross-shape
build is drawn mirrored, so the as-drawn window the planner fires would not fit it even built (measured). The
two sentences naming the build pieces draw them as mino icons the page text drops; they are quoted as the text
reads (`icons`) and not used as captions. Named lists and their sizes live in the two tests.

### BT砲（途中BT, mid-game BT Cannon）

The same deliverable for `template/btcannon.php` (「2021-07-03更新」): `pipeline/openers/btcannon-technique.json` (held as a
literal in `extract_btcannon_shapes.py`, gated by the shared `technique_transcription.py`), `technique-profile-btcannon.ts`
→ `analysis/btcannon-facts.json` (`btcannon.test.ts`), `technique-demos-btcannon.ts` → `analysis/btcannon-demos.json`
(`btcannon-demos.test.ts`), and `docs/btcannon.html` + `docs/btcannon-demos.html` from `btcannon_page.py` +
`btcannon_prose.json`, the fifth card under 中盤手法. Every figure is read off the artefacts and tests, never typed here.

**It is a technique page although BT Cannon is also an opener.** The page is the MID-GAME form (途中BT, built from 欄干 or
72積み), matched on a partial stack at any lock; the opener of the same name (開幕BT砲) is the same shape, so a hit inside
the opener window is counted in the artefact's `in_opener` column, never filtered out.

**The spin is a TSD and the anchor is the flat, nub-down T (STMB Cave's and ダブルダガー's), so the matcher is untouched; the
follow-up is a TST.** The TST slot runs up the wall beside the T's left end and on under the clear: before the TSD its four
cells are split by the two cleared rows, and the row map (which counts the cleared rows below each slot cell) joins them.
`followup.lines` 3 is read by the matcher's existing `followupKind`, so `technique-facts.ts` and every hash line stayed put.

**The window is the agreement box, and its external drawings are harddrop's own BT_Cannon page.** STSD's bounding box would be
the whole board (the TSD board draws the stack right of the slots as filled rows above the T). No committed routes board
draws a BT (the gate measures the window fires on none), and the opener catalogue's BT fields are four-row bag-1 boards the
seven-row window cannot be placed on, so the independent drawings come from harddrop's `BT_Cannon` page, pinned the way SDPC
Spin's wikitext is (oldid, MediaWiki's revision sha1, our sha256 and byte count, fetched by urllib through `api.php`) and
recorded in the transcription's `cross_source.harddrop`: every board on that page whose drawn T the window fires on (its
「Mid-game BT Cannon」 section among them), and every board with no T drawn on which it fires. `--html-dir` re-reads the
wikitext beside the page and checks both lists COMPLETE as well as letter for letter. That record is not a `*-routes.json`, and
until 2026-10-19 nothing re-read it weekly; `check_wikitext_sources` now discovers it (see ### SDPC Spin) and re-runs the
extractor's `--wikitext-dir` (`wikitext_checks`, the same function as `html_checks`) over the refetched revision. The shiwehi
page is still re-read only by a person with `--html-dir`. **Re-pinned 2026-10-24 from 41529 to 44634**, the weekly job's first red on it: the new
revision only APPENDS (its first 1850 lines are 41529's byte for byte) the OBT Cannon and Mechanical Heart sections, two of whose
boards stand outside any table — `_tabled` wraps each in a one-board table, so every earlier (table, board) holds. Its two
firing drawings are table 5 board 2's TSD board again, so the window and the corpus hits did not move; the artefacts moved in
`transcription_md5` only.

**Three opt-in edits to the shared gate, in unhashed Python, each checked default-preserving** (the gate, selftest and
`--html-dir` output of STSD, STMB Cave, インペリアルクロス and ダブルダガー were compared byte for byte before and after): a
`spin_piece: U` board is read as a T (the page draws the T it places in the renderer's `U`); an empty `cross_source.fires` is
allowed only with `routes_fire_none` and an agreement window with external drawings (rule (g) firing the window on each of
them is then the independent check); and `TechniqueSpec.html_checks` extends `--html-dir`. A fourth, in `technique_page.py`:
its selftest plants an invented hit row when the case index is empty (it assumed at least one hit); the other four pages'
selftest output is byte-identical.

**The test pins the hit list as a named list, and proves the predicate could have fired** (whether the corpus
holds a hit is that list's, never this file's). `btcannon.test.ts` pins every named list, and runs the TS `windowMatch` (the Python predicate's twin) on every recorded harddrop drawing (once, at its drawn T, in
its recorded hand, nowhere else), on its no-T boards and on the page's own drawings. What discriminates is measured per window
part: the rows above the T alone admit no full TSD of the corpus, so `noMustEmpty`, `garbageEmpty` and the follow-up mutants are
EQUIVALENT on the corpus (named, asserted byte-identical), while `noRoof` turns the `below` part into the headline. The
follow-up search therefore runs nowhere on the corpus, so the test runs it on the page's own TSD → TST as a two-lock digest
(`basic.spin`, its clear, the T into `tst.spin`'s slot), as drawn and mirrored: it fires, and each follow-up mutant breaks it
there. The window clashes with STMB Cave's and ダブルダガー's on a cell in every pairing of hands.

**harddrop's drawings are not chosen by the window.** The agreement drawings taken from harddrop are the boards whose drawn
T the window fires on, which alone would let the window pick its own evidence. So `drawn_t_not_fired` records every OTHER
board on that page with a drawn T — its lie, the rows it clears and why the window misses it (not the window's T, the window
leaves the board, or a cell disagrees), measured by the gate, with a note read off the page — and `--html-dir` fails unless
every drawn T on the page is in one list or the other. A drawing of the shape the window misses is a red build to name.

**No demo is built and no chain is planned**: the shared planner reads a build's page pieces as its lower-case letters, and
this page's 72積み builds draw them upper case (the 72積み stack lower case) while the 欄干 build's terrain carries a lower-case L
of its own. Every board carries the profile's reason with the cell count `btcannon-demos.test.ts` re-derives; one 72積み terrain
is a multiple of four and is stopped by that reading alone, which its reason says. Teaching the planner a per-profile page-letter
set would move every demo artefact's `planner_md5`, so it was not done here. Named lists and their sizes live in the two tests.

### 千鳥格子（Cut Copy）

The same deliverable for `template/cutcopy.php` (「2020-10-14更新」): `pipeline/openers/cutcopy-technique.json` (held as a literal
in `extract_cutcopy_shapes.py`, gated by the shared `technique_transcription.py`), `technique-profile-cutcopy.ts` →
`analysis/cutcopy-facts.json` (`cutcopy.test.ts`), `technique-demos-cutcopy.ts` → `analysis/cutcopy-demos.json`
(`cutcopy-demos.test.ts`), and `docs/cutcopy.html` + `docs/cutcopy-demos.html` from `cutcopy_page.py` + `cutcopy_prose.json`, the
sixth card under 中盤手法. Every figure is read off the artefacts and tests, never typed here.

**NO SHARED FILE CHANGED when it landed** — not the matcher, the planner, the gate or the renderer: the transcription and its
extract module, the two profiles, the page profile and prose, one registry line per side, one `TECHNIQUE_SITES` entry, three CI
steps. Every pre-existing artefact and page was byte-identical; `docs/index.html` gained the card. **2026-10-20's pass changed two
shared Python files and no hashed one.** Two of its edits are opt-in and default-preserving: the gate's `external` nodes (below)
and the renderer's `external_note` (only read when a node is external). A third, in the same renderer, is NOT: the case links now
open a replay position (`replay_href` / `audit_replay_links`, the paragraph on case links above), which re-rendered every technique
page's case hrefs and its cases note. Every other technique's gate output and artefact is unchanged; their pages moved by that one
edit and nothing else.

**The spin is a TSD and the anchor is the flat, nub-down T (STMB Cave's, ダブルダガー's and BT砲's); the follow-up is a second TSD
whose cells the first one's clear splits.** Two TSD slots are interleaved one column apart: the T goes into the inner one (its arms
one row, its nub the row under), and its two cleared rows join the outer slot's arms row (above them) to its nub cell (under them).
That is BT砲's split slot again, which the matcher's row map already joins, so `followup.lines` 2 and the pre-clear cells are data.
The page writes 「縦向きに入れて」 (upright) and draws the T flat: read as the T dropping in upright and turning into the slot; the
window reads the drawing.

**The window is the agreement box, against four sources.** STSD's bounding box would be the whole board (the spin board draws the
stack beside the slots as filled rows above the T). The agreement drawings are the page's three (the basic form, and its T-hole and
third-column builds, both drawn MIRRORED, so `extra_checks` fires them under `mirror:` as ダブルダガー's do), harddrop's Cut_copy
page's (the page the source cites as its reference; pinned like BT砲's BT_Cannon page — oldid, MediaWiki's revision sha1, our sha256
and bytes, urllib through `api.php` — and recorded with every OTHER drawn T on it in `drawn_t_not_fired` and its no-T boards the
window fires on in `fires_without_slot`, so the window does not choose its evidence), and the Cut Copy harddrop's BT_Cannon page
draws, read by (table, board) out of `btcannon-technique.json`, whose own note names it. harddrop draws one board with three T's
(yakine's repeating pattern), which BT砲's one-T-per-board completeness check cannot read, so this module partitions every board's
drawn cells into T's (`hd_slots`; a board with no unique partition is a red build) and records each T as its own `slot`; the
harddrop reading itself (`hd_cell`, `_sections`) is imported from BT砲's module, one reading. The fourth source is Tetrisちゃんねる's
千鳥格子 page (`cross_source.tetrisch`, added 2026-10-20): its ten images are committed under `spec/fixtures/tetrisch-cutcopy/` and
read with the jp-forecast sampler (欄干's route), and its basic terrain and its 江戸城 board are agreement drawings. The window is
four rows by six columns: the outer slot's arms row with its wall and the inner roof, the two cleared rows, the outer slot's nub row. No routes
board fires (`routes_fire_none`), and none of the other technique transcriptions' boards does (`extra_checks`, under `cross:`).
Like BT砲's, the harddrop record is refetched weekly by `check_wikitext_sources` and re-checked with `--wikitext-dir`; the shiwehi
page is not.

**The outer slot's overhang must stand before the first TSD, and that is yachi's reading, not the page's** (2026-10-22). The page
says 「(Z)は1回目のT-spinを打った後に置いても構いません」; the window refuses it. The overhang is the one cell of the row above the
box the window reads, as drawn and mirrored with the box: the variant's opt-in `window_extra` (`cells` outside the box, a `note`),
read by `technique-facts.ts`'s `prepare`, the gate's `window_cells` and the own-design search's `candidates`. Every drawing in the
agreement set fills it, so the agreement rule checks it like a box cell and no drawing moved; the cells beside it in its row
disagree between drawings, which is why it is not a row of the box. Before it, the corpus window admitted Cut Copies whose
overhang went in between the two T-spins, and most corpus hits were that (the old and new hit lists are in git, never here).
Two of that Z's cells (`decides`) are the overhang and the outer slot's wall, so the T-hole build with its Z left out fires
nowhere (`not_expressed`, measured and required, never defaulted; the piece left out must be the sentence's own mino icon,
`later:`; the selftest drops the overhang and reads it one cell over, and both are caught). `technique-facts.ts` is hashed, so
every technique artefact moved in its `emitter_md5` / `classifier_md5` lines and nothing else; check that with `git diff` when
`window_extra` is touched. The cold-clear self-play artefact was re-derived WITHOUT the bot's JSONL, by monotonicity: the window
only got stricter, so every new hit is an old hit and every old hit is in a committed game; each committed game was re-scanned on
its own and cut to what `select()` commits. Its `scan` counts other than `hits` are unchanged and are still the JSONL's.

**What discriminates is measured per window part** (`cutcopy.test.ts`, `PART_ONLY`): the cleared rows (entailed by the clear) admit every flat,
nub-down full TSD whose window is on the board, and the row above (with the overhang) and the row below each cut that down without reaching the headline alone, so both are
doing work; the `no_roof` ablation is the `below` part (it drops the overhang with the row above). `followupUnmirrored` and `followupAnyT` are
EQUIVALENT on the corpus since the overhang rule (named, asserted byte-identical) and killed on the page's own two-lock digest. For the first type, unlike ダブルダガー's, neither `noMustEmpty` nor `noRoof`
makes a lock match both hands: both are live mutants whose hits are their ablations'. Since the second variant landed, a full
`noMustEmpty` build throws (that variant's window less its must-empty cells is symmetric about the T, ダブルダガー's case), so the
test asserts the throw and measures the first type's symptom on a transcription holding it alone. The first type's window clashes
with STMB Cave's, ダブルダガー's and BT砲's on a cell in every pairing of hands and no lock is a hit of two of them. Garbage reads as filled, and the page itself says the shape is
mostly built when garbage rises, so `garbage_in_window` is a large share of the hit list — a fact about the corpus, read off the test.

**No demo is built, and every board says why** (`cutcopy-demos.test.ts` re-derives each): the third-column terrain has an ODD cell
count (a proof); the T-hole terrain is a multiple of four with no tiling by tetrominoes AT ALL (the hole cuts it into two parts,
neither a multiple of four — the planner's own words, 「no cover under its dealing」, are true and weaker); the basic form is even
but not a multiple of four (a planner limit); and both builds are drawn mirrored, so the as-drawn window the planner fires would
not fit them even built (measured). Named lists and their sizes live in the two tests.

**A second variant, harddrop's (`uncut`), added 2026-10-20 by measurement.** harddrop's page draws two generic Cut Copies; the
second, 「Uncut copy」, saves the WHOLE second TSD slot under the first T (one column toward the open side) rather than its bottom
half. shiwehi.com draws only the first. A single-T window expresses it: the agreement box of every harddrop drawing of it (its
Generic Structures board, the S/Z/J variation of fumen #3, the same variation again beside its STMB Cave comparison, the repeat's
two T's, one T of yakine's pattern, the mix's second T, the T under an STSD; the test pins how many), five rows by six columns — the row above the T, the two cleared rows, the second slot's two rows. Its board is
harddrop's own drawing transcribed as an `external` node (`external: harddrop`, never in `page_order`, which is shiwehi.com's page;
the gate's one opt-in for it), in occupancy only, beside harddrop's drawn after board, and `extra_checks` holds both to the harddrop
record (`external:`). Its follow-up is unsplit, so `followupNoRowmap` is measured EQUIVALENT on it (asserted on a two-lock digest of
harddrop's own drawing, where the other follow-up mutants break it). The two variants' windows clash on a cell; the second type and
STMB Cave are a RELATION, not a clash — in OPPOSITE hands their windows agree on every shared cell, and the STMB Cave page's own
「連続してTSD」 board fires the second type's window mirrored (`cross_source.also_technique`, measured both ways; harddrop says the
second type 「could be easily mistaken with STMB Cave」, and its own STMB Cave comparison, its cave two rows deep, is no hit). The
corpus hits of both are a named list (`STMBCAVE_ALSO_UNCUT`). What was decided NOT to be a variant, by measurement, stays in
`drawn_t_not_fired` with its reason: the deeper-hole S variation is already a drawing of the first type; the stood T after the
Parapet comparison is a Parapet TSS (欄干's TSS window fires at exactly that T, `other_window`, checked); yakine's other two T's
are read on a board that never stands; the Donation boards are donations. The `harddrop` record's `drawings` and
`fires_without_slot` now name the variant each belongs to, and its completeness check runs over both windows.

**Tetrisちゃんねる's 江戸城 is ONE Cut Copy, not a third shape** (measured in `_check_tetrisch` and the TS twin; it read 「two Cut
Copies in a row」 until the overhang rule): the window fires once on 009 at its innermost T; on the board that TSD leaves it fires
nowhere, because the middle T's outer slot has no overhang, and read WITHOUT `window_extra` it fires MIRRORED at exactly the carried
follow-up slot (the gate records `hits: 1` and checks both halves); that T's own follow-up is the last TSD, which leaves nothing. The
page's own 「交互にずれている」 is the alternation of hands. A hit whose follow-up lock is itself a hit is still published as
`followup_is_a_hit` (a named list in the test). Its other images: 002 and 005 draw the T UPRIGHT before 003 and 006 draw it flat
about the same centre (checked), which is shiwehi.com's 「縦向きに入れて」 drawn by a second site; 008 is 001's board coloured by
which TSD each row belongs to (same occupancy, checked); 010 is an annotation the sampler refuses. `--html-dir` re-reads the page and
the images beside the shiwehi snapshot (Pillow; without it one named `pillow:` failure); the weekly wikitext job does not.

**Declined, recorded in `source.declined`**: howtotetris.com's Cut Copy lesson and four.lol state that all rights are reserved and
nothing may be reproduced without permission, so nothing of theirs is transcribed, committed or published; the page says so in a
sentence. A `declined:` rule requires each entry's url, date and reason.

**精選 (since 2026-10-20): the corpus examples are picked by a RULE, never by eye.** `TechniqueSiteProfile.showcase` (opt-in,
千鳥格子 only; every other page is byte-identical) draws, before the case index, EVERY hit of the primary variant with no garbage in
its window and its follow-up fired, at four moments read from the replay (`replay_section.decode_boards`, the hit player's board
only): before the T with its cells dashed, after the first TSD, before the second T, after it. The audit checks the set is the
rule's, in artefact order, and re-reads each first board with `technique_transcription.window_fires` — the Python twin of the TS
matcher that found the hit. How many qualify is a figure (`showcase`), never typed here.

**Own designs (since 2026-10-20): boards nobody drew, found by a search and played by the engine.** The demo planner builds none of
the source drawings, so `pipeline/sim/technique-own.ts` asks the other way round, deterministically (no clock, no random draw): the
variant's window, as drawn, on the floor at every column offset in `technique-own-cutcopy.ts`; outside it the rows the stood T clears
full and the rest, plus two rows above, optional; every cover of the must-fill cells by non-T pieces the planner's two-bag dealing
allows (each of IJLOSZ once or twice, at most four second-bag pieces), smallest first; each handed to the SHARED planner
(`technique-demos.ts`'s `build`, which gained two opt-in options, an in-memory transcription and `maxSteps`, a step COUNT cap so an
over-budget candidate is reported the same on every machine; with both unset it is the emitter's byte for byte, and the nine demo
artefacts moved in `planner_md5` only); stop at an offset after `pick` builds. `emit-technique-own.ts` → `analysis/cutcopy-own.json`
(`report_eligible: false`, `constructed: true`, `own: true`), with every TRIED candidate's outcome counted by kind and how many were
never tried. `cutcopy-own.test.ts` re-derives the candidate lists, re-plans every published board byte for byte, decodes each demo on
its own (board, window, two full TSDs, `reachProblems`), checks no published board is a transcribed drawing, and checks the md5s;
the outcome counts are re-derived only by the full search (`OWN_FULL=1`, or the emitter), which takes long. The demo page plays them
after the drawn boards (`own_rel`), and re-checks each embedded one with `reach_problems` and `window_fires`. Against a wall
(offsets 0 and 4) the search finds no candidate: a count of THIS search (no T in the terrain, the window on the floor), not a
claim about the technique, and the page says so.

**`reach()` caches its whole search (since 2026-10-20).** The BFS never reads the target — it only filters by it at the
end — so `route-demos.ts` keeps, per (board as the engine holds it, piece, `no180`), every resting placement's paths in
discovery order with `reach()`'s own per-spin dedup, and answers each target from that (copies, so a caller cannot
mutate the cache). Entries are keyed by how the engine was built (`newEngine`'s options and date; an engine built
anywhere else keys by its own identity) and dropped least-recently-used past a fixed cap. Nothing it returns changed:
every route demo, technique demo and own-design artefact re-emitted with only its `planner_md5` line moved, and no
page moved. Measured on 2026-10-20 by re-running the own-design emitter and by timing `planOwn` over offset 2's
first 100 candidates against a scratch copy of the old file, with identical results; the timings were not committed
anywhere, so re-measure rather than quote one.

**A second implementation behind the own designs, for REACHABILITY only: the original cold-clear (since 2026-10-20).** `cutcopy-own-cc.test.ts` decodes
every published demo from empty and, on the board just before the stood T and before the follow-up T, asks the `cc-oracle` binary
(`CC_ORACLE_MOVES=1`, `find_moves` ZeroGComplete, `cross-movegen`'s protocol) whether that exact T placement is reachable, then
classifies it with cold-clear's `rotate()` rule (`cc-tspin.ts`; the binary's movegen line carries cells, not a spin status) under
EVERY kick index, since the timeline does not record which one our engine used, and counts the rows the four cells complete on that
board. It found cold-clear reaching both T's of every committed design and calling each a full T-spin clearing two whatever the
kick, because both front corners are filled. Only the reachability half is the Rust binary; the spin half is this repo's own
TypeScript port of cold-clear's rule, so it is not an independent implementation of the spin and must not be read as one. A placement cold-clear's mover does not reach would be its documented
mid-height-tuck asymmetry, named in `CC_UNREACHED` with its reason (measured empty), never a bound. It skips without the binary and
runs beside the cross tests in verify.yml's `oracle-image` job (the flake builds `cc-oracle` for aarch64 only).

**cold-clear's own Cut Copies, played on the demo page after our design (since 2026-10-20): bot games, not corpus, not drawn,
not ours.** The pilot in `tools/cc-coach/FINDINGS-cutcopy-selfplay.md` had cold-clear (the pinned rev, the cc-coach patch and
harness, `COACH_MODE=selfplay`) play alone with no garbage; its replay core is now `pipeline/sim/cc-selfplay.ts` (the tools
script imports it; its output on the pilot's JSONL was compared by hand with the pilot's on 2026-10-20 and was identical
apart from the input path, a one-off check nothing re-runs). `emit-cutcopy-selfplay.ts --games <jsonl> --coach-seed
<n>` scans every game through the engine and the corpus classifier unchanged (`cutcopy-selfplay.ts`), then commits, INSIDE
`analysis/cutcopy-selfplay.json` (`report_eligible: false`, `constructed: true`, `selfplay: true`), each hit game's own
placements up to the last lock deciding a hit's follow-up plus `tail` more, and the engine's timeline of them; the bot's whole
JSONL is not committed (its md5 and the run's settings are in `provenance`). `cutcopy-selfplay.test.ts` rebuilds the artefact
from the committed placements byte for byte (`--rebuild` does the same), pins the hits as a named list, decodes every timeline on
its own (cold-clear's cells at every lock, the window in the hit's hand, both TSDs full and clearing two) and checks the md5s,
the cold-clear harness files among them. What it cannot re-derive is the `scan` summary, which needs the JSONL: re-run the
emitter. The page (`technique_page.py`'s opt-in `selfplay_rel`, default off) draws each game with each hit's board and a link
to the position before its T, prints the scan sentence and the quarantine sentences (their cut-off from the artefact's `tail`) and requires both, and re-checks every embedded game with
`decode_boards` and `window_fires`; it also holds each hit's words (variant, hand, follow-up) to the artefact; its selftest deletes a quarantine sentence, swaps a
hit's hand words, drops a game, moves a hit's T, moves a hit link and reads a hit in the
other hand. The board drawn per hit is not re-read by the audit; `bin/build-docs --check` byte-compares it with the renderer. These games say nothing about how often a person, or the bot under garbage, builds one.

### 社畜トレイン（Shachiku Train）

The same deliverable for `template/shachikutrain.php` (「2020-10-31更新」): `pipeline/openers/shachikutrain-technique.json` (held as a
literal in `extract_shachikutrain_shapes.py`, gated by the shared `technique_transcription.py`), `technique-profile-shachikutrain.ts`
→ `analysis/shachikutrain-facts.json` (`shachikutrain.test.ts`), `technique-demos-shachikutrain.ts` →
`analysis/shachikutrain-demos.json` (`shachikutrain-demos.test.ts`), and `docs/shachikutrain.html` + `docs/shachikutrain-demos.html`
from `shachikutrain_page.py` + `shachikutrain_prose.json`, the seventh card under 中盤手法. Every figure is read off the artefacts and
tests, never typed here.

**NO SHARED FILE CHANGED**, as for 千鳥格子: the transcription and its extract module, the two profiles, the page profile and
prose, one registry line per side, one `TECHNIQUE_SITES` entry, three CI steps. Every pre-existing artefact and page is
byte-identical; `docs/index.html` gains the card.

**The spin is a TSD and the anchor is the flat, nub-down T (STMB Cave's, ダブルダガー's, BT砲's and 千鳥格子's); the follow-up is a
second TSD whose cells the first one's clear splits.** An S one column off a wall and an L hung over its far end make the slot,
roofed over its near end; the two cleared rows drop the row above the slot (the second slot's arms) onto the cell beside the S's
foot (its nub), and the page roofs it with a Z before the second T. The matcher's row map joins the split slot, so `followup` is
data.

**This page draws its spins UNMUTED, and that decided the node kinds.** The shared `spin:` rule requires every cell of a row the
spin clears to be upper case; this page draws the T as `U` and leaves the cleared rows in their colours. So no board here is a
gate `spin` board: each board with a T drawn is a `build` adding its `U` on a DERIVED board (the drawing less the `U`, letter for
letter), and the module's own `tsd:` rule checks what the spin rule would (one T, exactly two rows cleared, the board less it the
derived one). The agreement drawings and `fires_on` boards are those derived boards, slot empty. `r` is the renderer's pale S
(`pale:` checks it is one S); upper case is an earlier piece drawn muted, which the page does inconsistently (two `:colour`
discrepancies name the lone lower-case L cell it leaves; a third names DT社畜's three-cell L, cut by the drawing's bottom edge).

**The window is the agreement box** of the page's five drawings of the shape (the basic form, the 4x2 build, the two 2x2-hole builds
and DT社畜, drawn mirrored and fired under `mirror:`) and harddrop's own Shachiku_Train page, which the source does not cite (pinned
like 千鳥格子's Cut_copy page: oldid, MediaWiki's revision sha1, our sha256 and bytes, urllib through `api.php`; every OTHER drawn T on
it recorded in `drawn_t_not_fired` with why the window misses, so the window does not choose its evidence; `hd_cell`/`_sections`
from BT砲's module, `hd_slots` from 千鳥格子's). Four rows by six columns: the row above the T, the two cleared rows, the row under
them; the second slot's Z roof is outside. The window fires on one routes board, the same author's stick spin `2.sd`, recorded in
`cross_source.also` (`routes_fire_none` says no board by another author does); on no other technique transcription's board.
`other_windows` records, measured and complete both ways, every other technique window that fires on a drawn T of harddrop's page —
EVERY variant of each other file (千鳥格子's `uncut` and 欄干's `parapet_tss` included), which until 2026-10-20 read only each file's
first; an entry names its `variant` only when it is not the file's first, and a selftest plants a second variant that fires.

**Per variant, measured (`extra_checks`):** the basic form and the 4x2 build — the T the page draws next is exactly the window's
follow-up slot re-anchored at the build's T (`second:`); the boards between the two TSDs are what the first TSD leaves plus the Z
(and the I), measured. The two 2x2-hole builds (「STSDの地形が現れます」 and the TST terrain) — the first TSD is the window's, but the
page's next step is the STSD or TST in the hole, so they are `not_expressed` past the first spin: the cell under the follow-up's
nub is open, the follow-up T fills one row of the drawn after board (`fills`), and STSD's own window fires nowhere on it. DT社畜 —
the window fires once, mirrored; the DT砲 hole it keeps under the follow-up's nub is not drawn past that and is `not_expressed`.
The rule ties `not_expressed` to the open cell under the nub, both ways (`later:`).

**STMB Cave, measured, not assumed.** harddrop's STMB_Cave page (the revision wiki-tspin-techniques.json pins, checked equal; its
caption equal to that file's quoted sentence) says a variation 「has the same shape and steps as Shachiku Train」. Its table 17
draws that variation (an O base: a cave three wide under the T), the Shachiku Train it compares (a J base) and the second TSD.
This window fires on the J base only and STMB Cave's (`stmbcave-technique.json`) on the O base only (`stmb:`); the bases differ
only in the row under the nub row, and the two windows, anchored on the same flat T, clash at TWO cells there: the cell under the
nub and its neighbour under one arm (the right as drawn, the left mirrored), recorded as `clash` and re-measured by the gate
(`stmb:`) and the test. harddrop's own Shachiku_Train page draws the same comparison (its tables 10 and 11; the gate holds the
boards equal). So 「the same shape」 holds in the cleared rows, where both windows read and agree, and fails at those two cells;
STMB Cave's window does not read the row above the T (`rows_both_read`), so nothing compares the two there. This paragraph
said 「the cell under the nub」 and 「holds above the T」 until an audit anchored both windows: the test's `toContain` could not
see the second cell, and the row above the T was never read by both.

**What discriminates is measured per window part** (`shachikutrain.test.ts`, `PART_ONLY`), as for 千鳥格子: neither part above or
below the cleared rows reaches the headline alone, and `noMustEmpty` and `noRoof` are live mutants whose hits are their ablations'.
The window clashes with STMB Cave's, ダブルダガー's, BT砲's and 千鳥格子's in every pairing of hands, and no lock is a hit of two.

**The window says the SHAPE stood; `qualify` says whether it was BUILT** (since 2026-10-23, rules agreed with yachi
reviewing the hit list). `pipeline/sim/shachikutrain-qualify.ts` is the profile's opt-in `qualify` hook (`technique-profile.ts`),
read by `assemble`: a hit qualifies only if the cells `basic.spin` draws as its S and L are each a cell of a piece with all four
cells still on the board (`fragment` otherwise), none is garbage (`garbage_in_shape`), the Kaidan window does not fire at the same
T (`kaidan_window`: the two windows clash on no cell, so a lock both fire on is read as a Kaidan), and the board is not emptied
within `DPC_LOCKS` locks before or after the T (`dpc`: the DPC setup, a TSD built from the pieces a Perfect Clear left, into a
second one). A failing hit stays in `hits` with `qualifies: false` and every rule it fails. Piece ownership runs through the
digest's row map and is checked cell for cell against the board the matcher read (a mismatch throws). The first version counted
`dpc` only AFTER the T; yachi then read the hits that passed every rule as DPCs, and measured, each had emptied the board a few
pieces before its T, so the rule covers both sides. How many qualify is the artefact's and `shachikutrain.test.ts`'s
(`QUALIFIED_HITS`, `DPC_ONLY`, `QUALIFY_BY_PLAYER`), never this file's. **The page prints that count and nothing else of the corpus** (since 2026-10-23, yachi's
call: no hit qualifies, and a page opening on the window's hits, its follow-up table and its case index read as the technique
being played). The profile's opt-in `corpus_qualified_only` (`technique_page.py`) keeps the boards, the window and the rules, prints
one figure, the qualifying count, drops the headline, controls and follow-up, and lists only the qualifying hits as cases (none
today, so no case table; the selftest flips one to qualifying and must see it listed with its replay link). The index card counts
the qualifying hits too. The artefact and its tests still hold every hit; every other technique page is byte-identical. The hook's TYPE lives in `technique-profile.ts` and its call in `technique-facts.ts`, both hashed, so every
technique artefact moved in its `emitter_md5` / `classifier_md5` lines and nothing else.

**No demo is built, and every board says why** (`shachikutrain-demos.test.ts` re-derives each): the basic form's and the TST build's
terrains have ODD cell counts (a proof); the STSD build's terrain has tilings but none under the planner's dealing; DT社畜's L is
three cells; the 4x2 terrain has no tiling at all (two parts of six), a profile reason, because given that chain the planner stops
first at the pale S, which it reads as a piece R (measured in the test). Like BT砲's and 千鳥格子's, both harddrop records
(`cross_source.harddrop` and `cross_source.stmb_cave`) are refetched weekly by `check_wikitext_sources` and re-checked with
`--wikitext-dir`; the shiwehi page is not. Named lists and their sizes live in the two tests.

### 欄干（Parapet）

The same deliverable for `template/parapet.php` (「2021-03-23更新」): `pipeline/openers/parapet-technique.json` (held as a literal in
`extract_parapet_shapes.py`, gated by the shared `technique_transcription.py`), `technique-profile-parapet.ts` →
`analysis/parapet-facts.json` (`parapet.test.ts`), `technique-demos-parapet.ts` → `analysis/parapet-demos.json`
(`parapet-demos.test.ts`), and `docs/parapet.html` + `docs/parapet-demos.html` from `parapet_page.py` + `parapet_prose.json`, the
eighth card under 中盤手法. Every figure is read off the artefacts and tests, never typed here.

**It is a donation, and the first technique page whose payoff is not a second T-spin.** An L stood on end, shifted one column
(the page: 「%Lを1列ずらして立てて置き」 — it says nothing about the wall, and BT砲's page draws the L against it), its foot under the
slot's left end, a roof over its right end: the flat, nub-down T clears the T's arm and the L's foot, and the column under that arm
opens from the top to the floor. harddrop and Tetrisチャンネル draw the next step as a Tetris into that well (harddrop: an I on the
fumen's next page; Tetrisチャンネル: its 4-deep sequence ends on one). shiwehi names a Tetris only as its reason to fire the TSS
rather than the TSD (「TSDではなくTSSを打つ理由…打後の地形が1段高くなるためその後テトリスを送りやすい」), never as what follows the
TSD, and the prose attributes it that way. So the variant carries a `payoff` (`well_quad`) in place of a `followup` — exactly one of the two, refused otherwise by the matcher and by
the gate's `grammar:`. `wellPayoff` (`technique-facts.ts`) carries the WELL CELL through every clear and garbage insertion, verified
step by step as the follow-up slot is, to the first later lock with a cell in its column: fired iff that lock is inside the verified
prefix, has a cell at or below the carried cell, is an I and cleared four (else `past_verified`, `well_covered`, `well_filled_not_i`,
`i_in_well_not_quad`, `rowmap_unverified`, `slot_off_board`, `round_ended`). **What the window entails is not reported as a
payoff**: that the column re-opens and that the well is at least two deep are decided inside the window (its must-empty well cells
and its cleared rows), so a check on either could never fail — the NaiveClauseForced screening question, asked before writing the
payoff. Each hit carries `well_depth` (the empty cells under the well cell before the spin, garbage filled), and
`well_depth_lt4` names the shallow ones. The gate's rule (d') checks the payoff on the DRAWING: the payoff board is the spin
board's after board, the well column is empty top to bottom there, and every filled cell of it on the spin board is in a row the
spin clears (harddrop's re-opening clause, on the page's own boards).

**Two variants on one terrain, each measured at its own spin.** `parapet` is the TSD; `parapet_tss` the TSS the page draws on the
same terrain (the T stood, nub right, clearing only the foot's row, the well kept one row higher). The matcher reads a variant's
opportunity off its transcription's `spin`/`lines` (checked against each other, and required to be the profile's `opportunity` or
one of its `controlSpins`); under the TSS variant the TSD takes the TSS's place among the controls. For the seven earlier techniques
(one TSD variant each) this is the identity, which is why their artefacts moved only in their hash lines. Three TSS controls are
STRUCTURAL zeros the test re-derives from the window, not measurements: `no_roof` equals the TSS headline (no window cell lies above
its T), and a TSD (flat T) or a TST (every T row but the cleared one holds a must-empty cell) cannot hit the TSS window; nor a TST
the TSD window. The page renders both variants (`technique_page.py`'s opt-in `more_variants`: the TSS's figures keyed
`parapet_tss:<key>`, its headings from the prose's `more_variants.parapet_tss`).

**The window is the agreement box** (rows 1-5, columns 1-5 of `tsd.spin`, the same box for both variants) of the page's two basic
forms and four external drawings, each per variant: BT砲's page's Parapet (`btcannon-technique.json`'s `parapet`, same author, the L
against the wall — which is what puts column 0 outside); harddrop's Parapet page (Chopin's; ONE fumen and no pfrow table, decoded
once with knewjade's tetris-fumen 1.1.3 and recorded page by page — the board page 9 locks its T into, the T and the I locks; the
decode is NOT re-run in CI, an open item); and Tetrisチャンネル's two Parapet boards (the page this page cites; its sixteen JPEGs
are committed under `spec/fixtures/tetrisch-parapet/` and read with the jp-forecast sampler, which reads fifteen and refuses the
annotation 008). The TSS slots on the external drawings are OUR READING (they draw only the TSD). The gate's external drawings now
may name the `variant` they are drawings of (`technique_transcription.external_for`; one that names none is a drawing of every
variant, so the earlier techniques' are unchanged). Tetrisチャンネル draws the plain TSD on both terrains beside its Parapet, the T's
nub plugging the well — its own control — and `tetrisch:` measures the windows never fire there, nor on the bare terrains;
`after_spin` of each spin image is its after image; 015 less its I is 014 and the I clears four in the well column; the wells are 2
and 4 deep where drawn. The TSD window fires on two same-author 山岳積み2号 boards (`cross_source.also`; 9-row boards the route
artefact cannot match, so no cross-route) and, measured by `bt:`, on BT砲's page's Parapet and its 途中BT build (「実は欄干を組む形から
BT砲にすることができます」: the BT is built on this terrain). That is a relation, not a clash: in the same hand BT砲's window and this
one agree on every cell they share, so the test names their common hits (`BTCANNON_ALSO_PARAPET`) rather than asserting none;
against STMB Cave, ダブルダガー, 千鳥格子 and 社畜トレイン the windows clash in every pairing of hands and the hit sets are disjoint.
Of the three external records only harddrop's is a pinned MediaWiki revision, so `check_wikitext_sources` discovers it and refetches
it weekly (the spec's `wikitext_checks`, the harddrop half of `--html-dir`, with a `synthetic_wikitext` holding its quote and its one
fumen; the selftest plants a fumen edit where a pfrow page loses a cell). The shiwehi page and the Tetrisチャンネル page and images are
not re-read weekly: an open item. `--html-dir` re-reads all three (Pillow for the images; without it one named `pillow:`
failure and the hashes only).

**Donation, cross-checked.** `parapet.test.ts` re-implements `donationCols` at its shipped clauses (importing `emit-opener-facts.ts`
runs a session), reproduces every session's per-player `donation.players[].donations` exactly, and names every hit that is not a
donation at its well column in `HIT_NOT_DONATION` with the re-derived clause it fails: only `filled_above_window` (a filled cell over
the slot in the well column, outside the window), `cavity_lt4` and, since 2026-10-25, `incomplete` (a plug cell in the cleared rows
that is garbage or a fragment, read off the digest's ownership grid) occur — never the walls, which the window itself decides.

**What discriminates is measured per window part, per variant** (`PART_ONLY`): the rows above the cleared rows, the cleared rows,
and the well rows under them; no part reaches the headline alone, and the well rows cut the most. The TSD's `no_roof` ablation is
exactly its `below` part. Mutants: `payoffAnyPiece` and `payoffNoQuad` (new, shared) and the follow-up mutants `followupUnmirrored`
and `followupNoRowmap` (honoured by the well) each move only payoffs on the corpus, and the test also builds two-lock digests from
Tetrisチャンネル's 4-deep sequence and harddrop's fumen, as drawn and mirrored, on which the payoff fires and each payoff mutant breaks
it (`followupNoRowmap` needs garbage under the well to matter: a spin's own clear is always above the well cell).

**The window says the SHAPE stood; `qualify` says whether it was BUILT** (since 2026-10-23, at yachi's request:
社畜トレイン's rules carried over). `pipeline/sim/parapet-qualify.ts` is the profile's `qualify` hook: the six cells both
builds draw as a piece of their own inside the window (the stood L and the two roof cells, mirrored with the window) must
each be a cell of a complete piece and never garbage (`fragment`, `garbage_in_shape`), the L's four cells one piece
(`l_not_one_piece`, the page's 「%Lを1列ずらして立てて置き」), and no Perfect Clear within `DPC_LOCKS` locks either side of
the T (`dpc`). 社畜トレイン's Kaidan rule does not apply: the two windows clash in every pairing of hands. Ownership is
`shachikutrain-qualify.ts`'s exported `owners`, checked cell for cell against the board the matcher read. The page is
`corpus_qualified_only`: it prints how many hits of either variant qualify and lists those alone, with their replay
links; the report's region, chart, strip and the replay labels drop the rest, as for 社畜トレイン. Every 建議 tagged item
that cited the old 欄干 hit counts was deleted or cut to its other technique on the same pass (they described shape-only
hits). The counts and named lists are `parapet.test.ts`'s (`QUALIFIED_HITS`, `ONLY`, `QUALIFY_BY_PLAYER`), never this
file's. Exporting `owners` moved 社畜トレイン's facts `emitter_md5` and demos `classifier_md5` and nothing else of it.

**No demo is built, and every board says why** (`parapet-demos.test.ts` re-derives each): the O-roof terrain is a multiple of four
with no tiling AT ALL (the well and the L's stem cut it into two parts, neither a multiple of four — 「no cover under its dealing」
is true and weaker), and the Z-roof terrain is even but not a multiple of four (a planner limit), the four boards drawn on it
standing on it. The shared planner gained one branch — a payoff variant's demo ends on the stood T, with nothing swapped out of the
hold for a second T — which no committed chain reaches, so the demos test runs it on a SYNTHETIC copy of the transcription (the
O-roof terrain widened until it tiles; a temporary file, never committed or published): the engine arbiter accepts it and it ends on
one full TSD. Named lists and their sizes live in the two tests.

### 階段のドネイト（Kaidan Setups）

The same deliverable for `template/kaidansetup.php` (「2021-03-23」): `pipeline/openers/kaidan-technique.json` (held as a literal in
`extract_kaidan_shapes.py`, gated by the shared `technique_transcription.py`), `technique-profile-kaidan.ts` →
`analysis/kaidan-facts.json` (`kaidan.test.ts`), `technique-demos-kaidan.ts` → `analysis/kaidan-demos.json` (`kaidan-demos.test.ts`),
and `docs/kaidan.html` + `docs/kaidan-demos.html` from `kaidan_page.py` + `kaidan_prose.json`, the ninth card under 中盤手法. Every
figure is read off the artefacts and tests, never typed here.

**No shared RULE file changed** — not the matcher, the planner, the gate or the renderer. Three shared files did move, and
are named in the 中盤手法 paragraph above: `technique-profile.ts`'s docstring (hashed, so every technique artefact's
`emitter_md5` / `classifier_md5`), 社畜トレイン's transcription (its `other_windows` data), and the new shared test helper
`technique-donation-checks.ts` lifted out of `parapet.test.ts`.

A staircase, a Z stood on end on its lowest step at the wall, a roof over the slot's end away from the wall: the flat,
nub-down T (STMB Cave's, ダブルダガー's, BT砲's, 千鳥格子's, 社畜トレイン's and 欄干's anchor) makes a full TSD that clears the two rows the
Z's top half is in, and the column beside the Z's foot opens from the top to the floor. So the variant is 欄干's shape of record: one
TSD and a `well_quad` payoff, which the matcher, the planner, the gate and the renderer already carried. The window counts no steps
and does not see the Z: the page's four-step form and its three-step S and J forms are one window. harddrop builds the same edge
from other pieces and from line clears, but those drawings carry no T and the window fires on none of them, so that it fires once
they are completed is reasoned from its reading occupancy only, not measured.

**The payoff is harddrop's, and the page and the artefact say so.** shiwehi.com names no Tetris after a Kaidan (its next step is
ST積み or よしひろ積み, which nothing measures); harddrop's Kaidan_Setups page says the column should be open again and its Anchor_Set page
draws the I clearing four into it (`payoff:` checks that drawing: one vertical I in the re-opened column, four rows filled). The
page draws its well three deep, so the facts test's payoff digest on the page's own board gives `i_in_well_not_quad`, and the board
on which the payoff fires is CONSTRUCTED (the bottom row repeated once) and says so.

**The window is the agreement box, and it holds the one choice.** Over the page's three builds and two DT砲 boards (mirrored),
harddrop's four Kaidan_Setups drawings, Anchor_Set's Kaidan (mirrored) and the Kaidan BT砲's harddrop record holds (mirrored,
read from `btcannon-technique.json`), there are three maximal boxes on which every drawing agrees: the cleared rows alone, the
cleared and well rows (no roof), and the window, which is the only one holding the roof. The facts test measures the other two as
controls (`OTHER_MAXIMAL_BOXES`) and asserts nothing about them. Both harddrop pages are pinned revisions (`revision_sha1`), read
with `kd_cell` (blank/`-`/`--` empty; a digit filled; `P`/`SP` the T; `'X` the next piece, empty before it; every other code
`hd_cell`'s), and `check_wikitext_sources` discovers both by structure and re-reads them weekly with `--wikitext-dir`; the
shiwehi page is re-read only by a person with `--html-dir`. harddrop STMB_Cave's last table (a Kaidan beside an STMB Cave
variation) is recorded by pointer to 社畜トレイン's pin, not re-pinned: its window leaves that board.

**Relations, measured both ways (`other:`).** This window over every board of every other committed technique transcription,
and every other technique window over every drawing this one holds, are recorded complete both ways. With 社畜トレイン's window,
anchored on the same flat T in the same hand, it clashes on NO cell: the Kaidan window fires on 社畜トレイン's 2x2-hole builds'
first TSD, on its DT社畜 (mirrored) and on several of harddrop's Shachiku_Train drawings of the shape itself (every board listed
in `other_windows`), and cannot tell them apart, and the common corpus hits are a named list (`SHACHIKUTRAIN_ALSO_KAIDAN`), never asserted
absent. STMB Cave, ダブルダガー, BT砲, 千鳥格子 and 欄干 clash in every pairing of hands and their hit sets are disjoint;
STSD's and インペリアルクロス's T stands up. The hits are checked against harddrop's Donation predicate (`technique-donation-checks.ts`,
lifted out of `parapet.test.ts` and shared): every hit that is not a donation fails only a clause outside the window.

**No demo is built, and every board says why** (`kaidan-demos.test.ts` re-derives each): the four-step staircase has an ODD
cell count (a proof); the three-step staircases tile, but never without a T, and the planner's dealing keeps the T's for the spin
(its 「no cover by non-T pieces」 is the measurement, not a proof); the DT砲 boards are even but not multiples of four and drawn
mirrored, so the as-drawn window would not fit them even built (measured). Named lists and their sizes live in the two tests.

### 途中DT砲（mid-game DT Cannon）

The same deliverable for `template/dtcannon.php` (「2024-08-29更新」): `pipeline/openers/dtcannon-technique.json` (held as a
literal in `extract_dtcannon_shapes.py`, gated by the shared `technique_transcription.py`), `technique-profile-dtcannon.ts` →
`analysis/dtcannon-facts.json` (`dtcannon.test.ts`), `technique-demos-dtcannon.ts` → `analysis/dtcannon-demos.json`
(`dtcannon-demos.test.ts`), and `docs/dtcannon.html` + `docs/dtcannon-demos.html` from `dtcannon_page.py` + `dtcannon_prose.json`,
the tenth card under 中盤手法 (yachi's pick, 2026-10-24). Every figure is read off the artefacts and tests, never typed here.

**No shared RULE file changed**: the flat, nub-down T into a TSD whose follow-up is a TST standing on its nub column is BT砲's
shape of record (`followup.lines` 3, the slot split by the two cleared rows and joined by the row map). The one shared edit is a
`dtcannon` entry in `technique-qualify.ts`'s `QUALIFY_OPTIONS` (and a docstring clause naming it), which every technique
artefact hashing that module re-emitted for: the eight facts and demos moved in their hash lines only, and `cutcopy-own.json` /
`cutcopy-selfplay.json` in `classifier_md5` only. Like BT砲 it is also an opener (開幕DT砲), so a hit in the opener window is a
column, never filtered; the opener hits are exactly the rounds `DT_ORDER_IN_OPENER` already names as DT Cannon first bags, which
`dtcannon.test.ts` checks against `ordering.per_round`.

~~**Its snapshot is MARKDOWN, not HTML, and it is the weakest pin of any technique.** … An open item: refetch the raw HTML and
pin harddrop's DT_Cannon revision once a session can reach them.~~ **Closed 2026-10-24.** The snapshot is the page's raw HTML
(`dtcannon.html`, fetched with curl and the YE2 intermediate, TLS verification on, as 山岳積み2号's), and its renderer's colour map
(`column-exp.js`, hashed in `source.renderer`) was read: `p` is #ff33ff and `y` the pale Z, the mirror partner of `r`. Every board
and quoted sentence is the markdown transcription's, letter for letter; the one metadata fix was the page's created date. harddrop's
DT_Cannon is a redirect to Double Triple Cannon Setups, whose revision is pinned in `cross_source.harddrop` (oldid,
`revision_sha1`, sha256, bytes; read with urllib through `api.php`), so `check_wikitext_sources` discovers it and refetches it
weekly with `--wikitext-dir`. Its drawings the window fires on are agreement drawings, every other drawn T on it is in
`drawn_t_not_fired` with why the window misses, its no-T boards the window fires on in `fires_without_slot`, and the boards that
nearly fire in `near_misses` (the DT STSD form differs at exactly the cell harddrop draws empty; the Higher Notch board leaves the
window off-board) — all complete both ways, measured by the gate. The window and the corpus hits did not move; the artefacts moved
in `transcription_md5` only.

**The window is the agreement box** of the page's eight drawings and the two SDPC Spin boards. It reads no `B`; `p` (pink) and `y`
are read from the page's renderer. One measured relation the gate's miss rule does not see: `dtdt.tst` draws the first DT's TST
with the second DT already stacked above it, and the window fires there, as drawn, at that second DT's TSD slot —
`dtcannon.test.ts` pins it (`SECOND_DT`). **Qualify**: the key cell is the overhang over the TST stem alone, the one window cell
every build places as a piece. `noRoof` makes a lock match both hands and is refused (asserted to throw); `followupAnyT` is
measured equivalent and named. **No demo is built**: odd cell counts (a proof), boards even but not multiples of four (a planner
limit), the DTDT residue boards, and のそみ砲's illustrations, which do not separate terrain from page pieces (a reading, not a
measurement); `dtcannon-demos.test.ts` re-derives each.

### 基本的なドネイト（basic donating）

The same deliverable for `template/basicdonating.php` (「脱初心者のための基本的なドネイト」, 2024-10-07 版; yachi's 「下一個中盤」,
2026-10-24): `pipeline/openers/basicdonating-technique.json` (held as a literal in `extract_basicdonating_shapes.py`, gated by the
shared `technique_transcription.py`), `technique-profile-basicdonating.ts` → `analysis/basicdonating-facts.json`
(`basicdonating.test.ts`), `technique-demos-basicdonating.ts` → `analysis/basicdonating-demos.json`
(`basicdonating-demos.test.ts`), and `docs/basicdonating.html` + `docs/basicdonating-demos.html` from `basicdonating_page.py` +
`basicdonating_prose.json`, the eleventh card under 中盤手法. Raw-HTML snapshot, fetched like 途中DT砲's; some boards are indented
with a tab, which the opt-in `snapshot_indented` reads. Every figure is read off the artefacts and tests, never typed here.

**It teaches a PRINCIPLE over many terrains, so its window is the principle, not a box.** 「TSDで消える2列だけを埋める」: a piece
laid over a hole fills exactly the two rows a flat, nub-down T's TSD clears, so the hole opens again; the page draws holes 1 to 6
columns from the T's near arm, and no two of its terrains agree between the T and the hole, so neither the bounding box nor the
agreement box can hold them. So there are six variants, `k1`..`k6`, under a new opt-in `window_basis: well`: the T's own 2 × 3 box
plus four cells in the hole's column (above the donation empty, the two donated cells filled, the hole under them empty), checked by
the gate's `well_window` and held to every drawing on the page BOTH ways by `well_accounting` (every firing is a recorded drawing or
a `well_fires_other` entry; every spin board no window fires on is a `well_not_fired` entry — the page's own L-fills-three-rows
mistake is the one). The payoff is 欄干's `well_quad`, and it is harddrop's (the Donation page), not the page's, which says only
that the hole stays open. Two further opt-ins in the shared gate, both default-preserving (every earlier gate's plain, `--selftest`
and `--html-dir` output compared byte for byte): `snapshot_indented` (also in `route_transcription.page_boards`) and
`muting_slips`, which lets a spin board whose muted cells do not equal its cleared rows be a named `:muting` discrepancy.

**Every named donation is one of these windows plus more, so the qualify rules give a T to the page that names it.**
`pipeline/sim/basicdonating-qualify.ts`: the shared rules on the two donated cells (`fragment`, `garbage_in_shape`, `dpc`), then
`other_page` (any variant of any other technique window fires at the same T, either hand), `nearer_well` (a smaller-k window fires
at the same T: the T counts once, at its nearest hole) and `well_covered` (a filled cell above the window in the hole's column, so
the clear does not re-open it). Measured in `basicdonating.test.ts`: `other_page` agrees with membership in another technique
artefact's hits on every hit; 階段のドネイト's and 社畜トレイン's hits are contained whole in this page's, STMB Cave's are not (the
test pins the counts in `COMMON`), and no two qualifying hits share a lock. The other gates' `other_windows` records were extended
to this window (kaidan, parapet, shachikutrain), so their transcriptions and both artefacts' `transcription_md5` moved and nothing
else; 社畜トレイン's `emitter_md5` / `classifier_md5` moved too, because it hashes kaidan's transcription.

**A seventh variant, `nub` (2026-10-24, yachi's 「好」 to a corpus-mining finding): the hole under the T's OWN nub.** The page
draws holes 1 to 6 columns from the arm; harddrop draws the T's nub plugging a Tetris hole straight under it (its
Shachiku_Train page, table 16 board 1, 「Donation T-Spin Double」), which is the Donation page's definition with k = 0. The
board is an `external: harddrop` node (`nub.hd`), read BY POINTER from 社畜トレイン's pinned record
(`cross_source.harddrop.drawn_t_not_fired`; `_check_external` holds it equal in occupancy), never re-pinned. Its window
(`well.side: nub`, offset 0) is the T's box plus the cell above its centre empty, two empty cells under the nub and the four
wall cells beside them filled: a one-cell hole fires on STMB Cave boards and C-Spin / DT TST setups, a two-deep walled one
on none of them. It is SYMMETRIC about the T, so `technique-facts.ts`'s `prepare` drops a mirror whose cells equal the drawn
window's (a hit is recorded as drawn; the gate still records both hands), which is the one change to a hashed rule file and
moved every technique artefact's `emitter_md5` / `classifier_md5` (and `dpc-facts.json`'s) and nothing else. Qualify: it has
no donated cells (`keyCells: []`, which `technique-qualify.ts` now accepts only when given EXPLICITLY), so
`garbage_in_shape` reads its whole window instead — most of its window hits sit on a garbage well and fail — and its offset
0 makes every k hit the nub window also fires at a `nearer_well`. **A nub hit also needs at least 4 empty cells
under the nub** (`shallow_well`, since 2026-10-24, after yachi asked why the page listed so many examples): the window
asks for 2, which any TSD over a dent meets, and most nub window hits were 2 or 3 deep; harddrop's Donation page, the
variant's source, draws a cavity of 4 or more. A shallow nub window claims no k hit (`nearer_well` skips it), so the
farther hole counts. The k variants keep the page's own depth: its boards are cropped under the hole. The 途中DT砲 TSD's nub sits over the TST slot, so the
two pages share hits, which `other_page` gives to 途中DT砲 (`COMMON` in the test). Counts are the test's. A `t_covers_hole`
rule that failed every nub hit (a hole under the T is no donation) lived for one day and was reverted on 2026-10-25, when
yachi chose harddrop's definition with complete pieces: the T is a complete piece by definition, so the nub plug counts.

**The report region and the replay labels see seven variants**, labelled 「窿離 T k 欄」 (and 「窿喺 T 尖下面」 for the nub) in
`routes_techniques_section._variant_name` (a branch on `well`; every other technique's label is unchanged). **No demo is built**: odd cell counts (a proof), even counts not
multiples of four (a planner limit), and most boards drawing the donated pieces and the T in one diagram with no board of the
pieces placed before the T; `basicdonating-demos.test.ts` re-derives each reason by kind. Named lists and sizes live in the tests.

### 用完整方塊砌出嚟先算 — the shared `qualify` hook of the other seven pages

STSD, STMB Cave, インペリアルクロス, ダブルダガー, BT砲, 千鳥格子, 階段のドネイト and 途中DT砲 carry the same build rules as 社畜トレイン
and 欄干 (yachi, 2026-10-23: 「睇埋其他中盤」), through ONE module, `pipeline/sim/technique-qualify.ts`
(`techniqueQualifier`, `QUALIFY_OPTIONS`), gated by `pipeline/openers/technique-qualify.test.ts`. A hit qualifies iff each of
its variant's KEY cells is a cell of a complete piece and never garbage (`fragment`, `garbage_in_shape`), a piece the page
names as one is one piece (階段のドネイト's 「Zを縦置き」: `z_not_one_piece`), and no Perfect Clear lies within `DPC_LOCKS`
locks either side of the T (`dpc`); `ownership_unverified` as for the other two. The key cells default to the transcription's
`roof_cells` + `window_extra` (the pieces above the cleared rows, which every page draws as what it builds); STSD, STMB Cave,
千鳥格子's `uncut` and 階段のドネイト name theirs in `QUALIFY_OPTIONS`, each with its reading beside it. The cleared rows and
the stack under them are NOT required to be fresh: measured on 2026-10-23, fragments there are the ordinary old stack every
page draws grey, while the cells above the cleared rows were whole pieces in almost every hit — so requiring the whole window
fresh would have failed hits nobody would call accidental. No overlap rule was added: of the window relations the pages
name (BT砲 / 欄干, 千鳥格子 uncut / STMB Cave, 階段 / 社畜), BT砲 and uncut hold no corpus hit and the last is excluded on
社畜's side. The test pins each artefact's per-player tally and, where few fail, every failing hit by name; re-derives every
committed verdict from the digests; and turns each rule off to see it qualify exactly the hits failing only that rule, and
requires each rule live somewhere in the corpus. Every one of the eight pages is `corpus_qualified_only`; on 千鳥格子 the
精選 set is drawn from qualifying hits only. Which hits fail, and how many, is the test's, never this file's — only that
階段のドネイト is the page where most fail (its Z split by a clear, or garbage in its steps). Editing `technique-qualify.ts`
moves all eight pages' facts and demos hash lines (and `cutcopy-own.json` / `cutcopy-selfplay.json`'s `classifier_md5`); 社畜トレイン's and 欄干's artefacts do not hash it.

## DPC 頁 — what the first T-spin after a Perfect Clear was built on

harddrop's six DPC pages (DPC Setups and Extra S/Z, O, I, J/L, T) are transcribed into
`pipeline/openers/dpc-setups.json` (named `*-setups.json`; `extract_dpc_setups.py` gates it, and
`check_wikitext_sources` discovers its six pinned revisions like a technique file's and re-runs it
with `--wikitext-dir`). `pipeline/sim/dpc-facts.ts` → `analysis/dpc-facts.json` takes every PC
point and the first full or mini T-spin that clears within 15 locks after it and before the next
PC, strips complete garbage rows from the bottom, and compares the board before that T with every
drawn setup by occupancy, as drawn and mirrored, with the T's own cells. `docs/dpc.html` from
`pipeline/dpc_page.py` + `dpc_prose.json` is the 中盤手法 group's last card. Same quarantine as the
technique pages: no claim id, no ✓, no demo.

Two things the wording must keep. **The PC points are anchored**: per player-round the simulator's
board-empty count must equal `clears.allclear` (twice-extracted), and the artefact refuses to
build otherwise. **The board after a PC is mostly past the verified prefix**, because the game
sends that PC's attack in packets the oracle sends as one; every case says whether it is verified,
and the page prints both counts. It is NOT in `TECHNIQUE_SITES` (`replay_labels` and the report's
routes section read that list); `bin/build-docs` renders it in its own loop. Counts, the named
`MATCHED` list and the Shachiku cross-check live in `dpc.test.ts`, never here.

## Front-end traps in report.html (each one shipped a silent bug)

- **A generated section's `<style>` is injected into the body, so at equal specificity it beats
  the report's own stylesheet.** 全場之最 defined `.rec-grid` for its tile grid; 建議 had used
  `.rec-grid` for its two-column layout since long before, and the coaching columns silently
  collapsed into narrow auto-fit ones — the new section itself looked perfect, which is why
  eyeballing the section you just added does not cover this. Name generated classes with a
  section-specific prefix (`sr-`, `rt-`) and scope the rules under the section id.
  `pipeline/check_generated_css.py` is the gate: it fails any selector that could match an
  element outside its own region.
- `--accent` is defined **only** on `.match-card[data-winner=…]`. It resolves to an empty
  string everywhere else, which silently invalidates any `color-mix()` using it — that
  painted invisible bars and an unstyled card border. The round-table section carries its
  own `--rt-accent`.
- **Sticky cells must be fully opaque.** The player tints are translucent; a translucent
  sticky cell lets the scrolling columns show through, printing stat values on top of the
  pinned player name. Paint the tint as `background-image` over an opaque `background-color`.
- **`data-v` must be computed before any markup is wrapped around a cell value**, or the sort
  key becomes the markup — this broke sorting and the summary means on the four barred columns.
- Build the column-name→index map from **one** header row. Querying across all tables lets the
  last table's indices win, putting every lookup past the end of a row.
- Scores render in **player order** (`players[0] : players[1]`), never champion-first — that
  reversed the meaning on the site index once.
- **An unresolved badge is indistinguishable from a pending one.** `check_badge_links.py`
  is now the gate, and it reads `expandShorthandBadges`' regex out of the report rather
  than assuming one, because the failure was that regex being narrower than the prose.
  Both mutants are killed: a typo'd `data-claim`, and the expander narrowed back to
  `[CR]\d{3}`. It renders `⏳ G014` linked
  to an anchor that does not exist, which reads as "still being proved". Two ways that
  happened on 07-28, the first session whose prose cites generated claims: the claims island
  listed only the hand ledgers, and `expandShorthandBadges` matched `[CR]\d{3}` so `<b>G004</b>`
  in match-card copy stayed literal text. `appendix._rows` now includes every ledger the
  session's committed `claims-proof-map.json` covers — a rule that leaves 07-22 at 54 rows and
  07-24 at 52 while giving 07-28 all **96** — its `claims-proof-map.json` holds 96 entries, its
  appendix 96 data rows (`<tr>` in the region, less the header) and its island 96 claims, which is
  the rule holding exactly. It said 83 until 2026-08-17, and 83 was correct when written: the proof
  map held 83 entries that day. The rule is "every ledger the proof map covers", so its output
  tracks the map and a number written beside it does not — and `claim_cards.load` falls back to
  that map when a
  ledger has no `<stem>-proof-map.json` of its own, which is what made the round table's
  verdict cards show 待證 for claims the verifier had proved. Counting `.badge[data-status]`
  in the DOM does **not** catch either one; both were found by reading a screenshot.
- The `.ttrm` files are single-line JSON; `.gitattributes` marks them `-diff linguist-vendored`.

## 一個 quantizer,三條規則 —— 邊條規則有數撐住,係度出嚟嘅

**印出嚟嘅數要縮短,縮短就要有規則,而條規則淨係得一樣嘢守住:corpus 入面有個值令兩條規則
答案唔同。** 冇咁嘅值,條規則就係一句 comment —— 換咗佢,byte-identity gate、ledger 重生、
report 重 render 全部照綠,因為佢出嘅嘢一個 byte 都冇變。`forecast_section` 用 `:.0f`
(round-half-even)印一個周圍都 floor 嘅 ratio,冇人見到,就係因為冇一個 ratio 啱啱落喺半格上面。

`pipeline/check_rounding.py` 逐個 site 答兩條問題,第二條先係之前冇人問嘅:

1. **條規則有冇被行使過?** 把每一個記低咗嘅 call 用另外兩條規則重播。有 call 出唔同嘅字,
   就係 corpus 分得開,條規則有 artefact 撐住。
2. **條規則有冇宣告過?** `fmt.quant` 收 rule 做參數,所以每個 call 都講明自己要邊條。冇宣告
   嘅 site 根本查唔到,而 `_uncovered` 當佢係 failure,唔係當佢唔存在。

**佢做唔到嘅嘢,照直講** —— 佢分唔到一條**宣告咗嘅方向啱唔啱**。「27 locks against 81」有規則、
一致地applied、方向錯。佢報邊啲 site 有數撐住、邊啲係靠信,揀方向仍然係人手判斷,寫喺 call
旁邊。

七個 helper,一個 quantizer:`quant`(x1000 整數)、`quantf`(float,弱啲,因為個 input 已經
甩咗 bit)、`permille`(num/den 出 x1000)、`mean_x1000`,加上 `r1`/`r2`/`r3`/`bound2`/`pct1`。
**呢個 rule 之前有六份 copy** —— `fmt.r1`/`r2`、`generators._one_dp`/`_two_dp`、
`intense_round._r1`/`_r2`、三份一模一樣嘅 `_pct`、`build_round_table.ratio`/`pct`、
`opener_section._share` —— 每份自己 spell `x // 100 / 10`。Copy 就係點解條 convention 只可以
被記錄、唔可以被 enforce:一條規則住喺六個地方就有六個 site,而佢哋一致與否冇嘢守住。全部
consolidate 之後七份 artefact、七份 report 同 ledger **全部 byte-identical**,呢個就係 control。

一次 sweep 行晒全部 session,行到 **<!--round:figures-->38610<!--/round:figures--> 個
quantized figure、<!--round:sites-->41<!--/round:sites--> 對 (site, helper)**:
<!--round:enforced-->30<!--/round:enforced--> 個有 corpus 撐住,
<!--round:ontrust-->11<!--/round:ontrust--> 個至少有一對規則分唔開。四個 `_pct` 兩個方向都靠信,
而且係**結構性**咁靠信 —— 餵入去嘅 per-mille 已經 floor 咗,所以第二次 quantize 係精確嘅,
條規則永遠行使唔到:呢五對唔會因為多幾個 session 而變。

**2026-10-11 嘅 攻擊由邊度嚟 section 加咗 18 對 (site, helper),全部嚟自 `attack_section`,唔係因為
加咗 session。** 14 對有 corpus 撐住；4 對(`app`、`apl`、`lpp`、`app_w` 嘅 `quant`)靠信,原因同
上面幾個 `_pct` 一樣:`permille` 已經 floor 咗,再 `quant` 去三個位係精確嘅,所以呢四對都係結構性
咁靠信,多幾個 session 都唔會變。上面嗰幾個 fragment 由 22 / 15 / 7 跳到而家嘅數,就係呢 18 對。

**但第六對會,而且已經變咗五次 —— 呢個先係「有冇數撐住」點解要度而唔係估。** `records._dp1`
喺七個 session 之下分得開 floor 同 ceil(當時 14 個 call),分唔開 floor 同 round(0 個
call)。冇人郁過一行 code,一路加 session 落去,兩欄都郁:ceil 嗰欄而家係
<!--round:dp1-split-->19 個 call<!--/round:dp1-split-->,而 round 嗰欄行過
0 → 10 → 24 → 0 → 14 → 15 → 0 → <!--round:dp1-round-->19 個 call<!--/round:dp1-round-->。

**第十三個 session 將佢由 enforced 打返落「靠信」,第十四個又推返上去——同一個 site,兩個方向,
三次。** 「真正 enforced,唔再係靠一欄撐住」嗰句喺十二個 session 之下係啱嘅:當時 round 嗰欄
係 24,兩條 alternative 都逐個 call 分得開。09-19 加咗 150 局之後 round 嗰欄歸零,即係話 corpus
入面再冇一個 `_dp1` 嘅 call 令 floor 同 round 出唔同嘅字;09-18 加多 127 局,佢又返到十幾個
call。所以「有一個 alternative 分得開」唔算數,**每一個 alternative 都要分得開**先報 ok ——
而一個今日靠信嘅 site,唔代表佢永遠靠信,反之亦然,呢句嘅**兩個方向而家都有實例**,而且係同
一個 site 來回行咗兩轉:條 rule 一路都係嗰條,郁嘅係啲數。

**兩次之間仲有樣嘢要分開睇:郁嘅係邊個 session,唔係「幾多局」。** 09-19 一百五十局令佢跌落靠信,
09-18 一百二十七局令佢升返,兩晚大細差唔多而方向相反 —— 所以呢一欄唔係「局數夠多就分得開」,
係嗰批數啱啱好落喺半格上面定唔落,而咁樣嘅嘢冇得預。

**第十五個 session(10-03)冇郁到佢嘅類別:round 欄 14 → 15,enforced 16、靠信 6 同十四個
session 一樣。**點解佢
咁易郁:`_dp1` 嘅 call 全部係 `records.py` 嘅 `sd_short` 同 `sd_long` 兩個 **corpus-wide** 數,
每份 report 嘅 footnote 印一次,所以 30 個 call 其實係 15 個 session × 同一對數。成欄由兩個數
話事,即係個 SD 啱唔啱好落喺半格兩邊;邊一晚、幾多局都唔係原因。上面「郁嘅係邊個 session」
嗰句應該咁讀:郁嘅係 corpus 加咗嗰晚之後嘅兩個 SD。

**第十六個 session(10-09)又將佢打返落靠信 —— 同一個 site 第四次轉類別。** round 欄 15 → 0,
enforced 16 → 15,靠信 6 → 7;ceil 欄 30 → 32 個 call,即係 16 個 session × 同一對數。上面嗰段
講嘅機制完全照用:加咗 10-09 之後 corpus-wide 嘅 `sd_short` 同 `sd_long` 啱啱好冇一個落喺
floor 同 round 會出唔同字嘅半格上面,所以成欄一齊歸零。102 局唔係原因,10-09 本身亦唔係;
係個 SD 郁咗,而 SD 係成個 corpus 嘅。

**第十七個 session(10-12)又將佢推返上 enforced —— 同一個 site 第五次轉類別。** round 欄
0 → 17,enforced 29 → 30,靠信 11 → 10;ceil 欄 32 → 34 個 call,即係 17 個 session × 同一對數。
(29 同 11 已經包埋上面 2026-10-11 加嘅 18 對,所以同 10-09 嗰段嘅 16 / 15 / 7 唔可以直接比。)
17 啱啱好係 34 嘅一半:加咗 10-12 之後 `sd_long` 係 13.8603,floor 出 13.8、round 出 13.9,而
`sd_short` 嘅 62.9311 兩條規則都係 62.9 —— 即係每份 footnote 嗰對數入面一個分得開、一個分唔開。
55 局,大細得 10-09 一半左右,照樣將佢推返上去:又一次唔係局數,係個 SD 落喺半格邊一邊。

**第十九個 session(10-22)將 `_dp1` 拆開做兩個 site,所以上面條鏈最後一格同之前嘅格唔係同一樣嘢。**
加咗 10-22 之後 footnote 嗰對數係 63.7 同 14.1(floor),而 63.7 / 14.1 floor 出 4.5,大過未
round 嘅 4.4948 —— `_check_sd_ratio` 拒絕咗份 footnote,因為「足足細咗 4.5 倍」講多咗。分母係
跌勢嘅細嗰頭,floor 佢就係誇大個跌幅,所以而家 `sd_long` 行 `records._dp1_up`(ceil,14.2),
`sd_short` 留喺 `records._dp1`(floor)。即係話 `_dp1` 由「19 個 session × 一對數」變成
「19 個 session × 一個數」:佢兩欄而家都係 19,全部分得開,所以 enforced;新嘅 `_dp1_up` 嘅
round 欄係 0(14.1x 嘅 ceil 同 round 都出 14.2),入咗靠信,呢個就係 site 數 40 → 41、靠信
10 → 11 嘅來源。之前嘅 0 → 10 → … → 18 係嗰對數合埋嘅紀錄,唔可以同最後嗰個 19 直接比。

**同一個 session 入面,兩個 gated 嘅數一個 byte 都冇郁,而佢哋數緊嗰個 set 換咗兩個成員 ——
呢個先係今次最值得記低嘅嘢。** 上面段嗰兩個 fragment(enforced 同 ontrust)十二同十三個
session render 出嚟嘅字一個 byte 都冇分別,兩個都有 renderer、都有 byte-compare、都綠。
但入面換咗兩個成員:`records._dp1` 由 enforced 跌落靠信,而 `forecast_pooled.homogeneity_p`
由靠信升上 enforced(佢個 round 欄由 0 變到分得開)。一減一加,個總數啱啱好唔郁。

**而第十四個 session 郁法又唔同:enforced 嗰個加一,靠信嗰個冇郁,而 (site, helper) 嘅總數
加一。** 兩件事一齊發生:`records._dp1` 由靠信升返上 enforced(即係上面講嗰個第三次反覆),
而**多咗一個之前冇出現過嘅 site —— `forecast_section._num`**。佢一直都喺 code 入面,不過
之前十三個 session 冇一個嘅數據行到嗰條 path;09-18 嘅 forecast section 印到嗰個數,佢先第一次
有 call(得兩個,兩條 alternative 都分唔開,所以佢入咗靠信嗰欄)。一升一新,所以 enforced 加一
而靠信維持原數。

**呢個係第三種郁法,而頭兩種都估佢唔到。** 十三個 session 嗰次係 set 換咗成員而總數唔郁;
十四個 session 呢次係 set 多咗一個成員,而嗰個成員係新嘅 —— 唔係邊個 site 轉咗類,係
corpus 第一次行到嗰個 site。所以「個總數郁唔郁」同「個 set 郁唔郁」之外,仲有第三個問題:
**個 set 嘅範圍本身會唔會大咗**,而一個 site 有幾多個 call 係數據話事,唔係 code 話事。
三種都唔可以由嗰兩個數字讀返出嚟,所以要知邊幾個 site,唯一嘅路仍然係行 `check_rounding`
睇逐個 site 嘅 `ok` / `--`。

(順帶一提,寫呢一段嘅第一稿喺呢度再抄多次嗰兩個數,即刻俾 `check_rounding` 打回頭——
「exactly one pair per document」。即係話「一個量得一個屋企」呢條規則,喺講緊「個數唔夠睇」
嘅段落自己身上都要守,而且今次係 gate 而唔係人捉到。)

呢個正正就係 `check_equiv_coverage` 用 **verdict SET** 而唔用百分比嘅理由,原文寫喺嗰個 gate
自己嘅 docstring:「a scalar gate of ANY shape — a floor, a byte-compared percentage, a delta
bound — is structurally blind to the exact edit that motivated this work」。嗰度講嘅係 hand-claim
coverage,今次同一件事發生喺呢一節自己嘅 fragment 上面。可以做嘅嘢:讀呢兩個數嘅時候,唔好當佢
哋係「邊幾個 site 有數撐住」嘅答案,佢哋淨係個數;要知邊幾個,行 `check_rounding` 睇佢逐個
site 嘅 `ok` / `--`。要 gate 住個 set 就要 emit 個 set,而呢個未做。

**呢一段自己中過一次同款嘅招,而且係第十個 session 先照出嚟。** 上面兩個數本來得一個
fragment(`round:dp1-split`),render 出嚟嘅係 **ceil** 嗰欄,但包住佢嗰句講嘅係 **round** 嗰
對——即係話個 fragment 有 gate、有 renderer、每次都啱,而佢隔籬嗰句描述緊另一個量。八個 session
嗰陣 round 嗰欄仲係 0,兩句都啱得晒,睇唔出;第十個 session 一到,round 變 10 而 ceil 變 20,
嗰句就靜靜咁攞住 20 去講一件 10 嘅事。呢個就係 CLAUDE.md 自己寫過嘅
「a fragment pair whose sentence asserts a relation between them is not made safe by both
fragments being gated」,不過今次連「pair」都冇——係一個 fragment 頂兩個位。而家兩欄各自有 fragment,
一句講邊欄就印邊欄。

**個 key 一定要係 (site, helper) 而唔係 site。** `build_round_table.ratio` quantize 兩次(一次
per-mille、一次 quant),同一個 site 名;淨係用 site 做 key 嘅話第二次會冚咗第一次,個 summary
就報 7 954 而個 trace 有 11 554 —— **靜靜咁跌咗自己已經記低嘅 3 600 個 call**,而個數字讀落
完全正常。

**個 scanner 自己中過同一個窿,而且係第一次行就中。** 條 pattern 本來係 `//\s*\d`,讀落似
「integer division」但唔係:`opener_section._share` 用 `num * 1000 // den` floor,除嘅係一個
**名**,所以個 scan 報咗嗰個 module 乾淨,而成個 約 convention 靠住嗰個 floor 完全冇睇過。
而家係淨一個 `//`,over-report,每個 index 減半同每個毫秒轉換都要入 `EXCUSED` 連理由 ——
**over-report 先係佢應該壞嘅方向**。`EXCUSED` 用**函數名**做 key 唔用行入面嘅 substring:
一個 substring excuse 會靜靜咁擴大(寫嚟 excuse 一個 `// 1000` 嘅,連之後任何人加嘅
`// 1000` 都一齊 excuse 埋),而**一條配唔到任何嘢嘅 excuse 都係 failure**,因為一份開始講大話
嘅 list 同一份冇講大話嘅睇落一模一樣。

## 約 means the floored value — everywhere, and it is gated

`pipeline/fmt.py` floors; every generator uses it. Hand-written text is where a *rounded*
figure gets in, and it did: for weeks 約262.6 (C009/C010) and 約262.5 (G017) were the same
`vs_x1000 == 262582`, in one report. 45 figures across both sessions were rewritten on
2026-07-26 — Cantonese, `english_gloss` (which ships inside the claims island, so it is just
as published), and the prose typed straight into `report.html`.

`pipeline/check_prose_figures.py` is now the gate: it resolves every 約 / `~` / `≈` figure
against `facts.json` and fails when no datum *floors* to it but one *rounds* to it. Run it on
any session whose prose changed:

```bash
python3 -m pipeline.check_prose_figures sessions/<date>/report
```

Notes for future prose: a figure the checker cannot resolve is reported, not failed — sums and
differences legitimately print values no single datum produces. Figures in minutes are skipped
(a different divisor). `check_claims` will never catch this class, because every predicate
compares the integer, not the printed text.

**The gate used to skip the generated ledger, on the grounds that the generators floor by
construction. They did not.** Several families formatted the Cantonese with `_one_dp`/`_two_dp`
and the `english_gloss` with a bare `:.1f`, so one claim published 約167.9 and "VS 168.0" for
the same datum across all three sessions; the flat-rate family printed "差距唔夠 0.01 / under
0.01" for a bound its lemma only proved at 0.015 — a sentence strictly stronger than its proof.
Fixed 2026-07-28: every printed figure goes through a helper, and `_bound_dp` **ceils** because
an upper bound is the one figure that must round the other way. `check_prose_figures` now scans
every ledger, and its datum pool includes the derived quantities a generator can legitimately
print (per-round means, and the won/lost per-piece rates) — without them a correctly floored
rate resolves against no datum, collides with some unrelated datum's rounded rendering, and the
gate cries wolf at exactly the figures it just added.

## Perturbation is in place now, and that trade needs a guard

Two gates ask *"if I change this one datum, which claims flip?"* — `claims/equiv.py` 4 440
times per session (7 019 on 07-22) and `check_rate_coverage.py` up to 164 times. Both used
to answer it with `copy.deepcopy(facts)`, rebuilding a 300-480 KB object graph to write one
integer: 76.5 million deepcopy calls per `equiv` run, 88 % of its wall clock.

`pipeline/perturb.py` replaces that with **make/unmake** — write in place, evaluate, write
the old value back. Same mutants, O(1) instead of O(|facts|). `equiv` went 51.8 s → 13.9 s
on 07-22, output byte-identical.

**What it costs is the one thing deepcopy gave for free: the original cannot be corrupted.**
A sweep that restores 4 439 of 4 440 sites leaves every later mutant on a wrong baseline,
prints a plausible coverage figure and exits 0 — and for `check_rate_coverage` the drift is
in the direction that makes the gate *pass*, hiding a hole rather than inventing one. So
both callers fingerprint the tree either side of the sweep and assert it came back, and
`pipeline/test_perturb.sh` plants a disabled restore to prove that assertion fires. Do not
delete the fingerprint because it "obviously can't happen" — it is the only thing standing
where deepcopy's structure used to.

Preconditions, neither enforced at runtime: the code inside the `with` must not mutate
`facts` (both callers `eval` a pure comparison), and a write must name a container and key
that already exist.

`equiv.py`'s truth vectors are **bitmaps**, not lists — `defined` and `value`, one bit per
mutant, so three-valued logic survives (`defined ^ value` is "decided and False"). The
pair-coverage search is O(|hand| × |gen|²), which was 167 M interpreter steps in one
generator expression; as `&` over ~110 machine words it is free. `implies`, `==` and the
conjunction all changed representation — anything new that consumes a truth vector must go
through `Vec`, which is why the old list-shaped `truth_vector()` was deleted rather than
left for reuse.

**`equiv` evaluates only the claims that can observe a mutant — the relevance index.**
Every mutant used to evaluate every claim, and most of those evaluations provably return
the pristine verdict: the mutant writes no key the predicate spells. **How many is printed by
every run, per mode and corpus-wide (`equiv.evals_line`), and typed nowhere** — the share this
paragraph first carried was a guess, wrong by a factor of two on the evaluated side, with three
more copies in the code; a share is exactly the figure 冇第二份 says to point at, not to type. `pipeline/claims/readset.py`
labels each write by the key it writes (a score-dict write by `score`), maps each label to the
claims whose predicate subscripts it, and the sweep evaluates only those; every other bit is
the pristine verdict, and a vector is built from the sparse exceptions (`Vec.from_sparse`).
Exact under four premises — pure deterministic predicates whose pristine run cannot raise; a
field slot observable only through `Subscript(Constant k)`; every `python_check ==
spec.to_python(spec)`; a control-flow change moves which PLAYER is read, never which key — and
each is checked on every run: **G1** the renderer equality, **G2** an AST kind system
(`readset.audit`) under which a container may only be subscripted, iterated, `.values()`-ed or
`len()`-ed, **G3** every write label in a closed set and never a player name, **G4** pristine
verdicts are bools, **G5** a stratified shadow sample that evaluates every claim and fails if
one outside the index moved. **A predicate outside the whitelist is a build error, not a slow
path** — a new spec operator fails `IndexUnsound` until `audit` and its selftest admit it.
G5 is a tripwire and not the proof; the proof is `python3 -m pipeline.claims.equiv --selftest`,
which runs `equiv_reference.py` — the exhaustive sweep, frozen verbatim and never optimised —
against the indexed one and requires the whole result dict AND every claim's `Vec` to be
identical, then plants defects (a dropped label, a raw score key, a dropped reader, an
inverted pristine fill, an off-by-one move offset, a dropped chunk, a disabled restore, two
out-of-grammar predicates, a hand-reformatted one) and fails unless every one is killed. Both
CI jobs run it first. Sessions are measured as one deterministic process pool
(`equiv.measure_many`: one task per single-value sweep, two-site families cut into
contiguous chunks the parent proves tile the family); `--jobs` changes the schedule, never a
byte. Its per-process session cache is keyed by a digest of the input files' CONTENT (a
path-only key silently re-measured a stale ledger on a second call in one process), and the
timings it prints are `process_time` CPU, not summed wall intervals labelled as CPU. The cost figures live in `equiv-coverage.yml`'s timeout comments, with what produced
them — not here.

**`check_dead_consts` tokenises once instead of searching per const** (9.1 s → 0.04 s, 206×).
It was `re.search(rf"\b{n}\b", body)` for each of ~4 700 names over ~600 KB. Aho-Corasick
(CACM 18(6), 1975) is the general answer, but every pattern here is `\b<word>\b` over `\w+`,
and `\b` *is* a token boundary — so a `set` of `re.findall(r"\w+", body)` gives the identical
answer in one pass. The hazard is that a tokeniser which is too generous prints exactly what
a clean run prints, so `--selftest` plants prefix and suffix substrings (`abc` against
`abcd`) that a naive containment check would wave through. It runs before the gate in CI.

**A profiler share is not a wall-clock share.** `cProfile` said deepcopy was 68 % of
`check_rate_coverage`; removing it gained 1.4×, because per-call instrumentation inflates
millions of tiny recursive `deepcopy` calls far more than it inflates one `eval`. Profile to
find *where* the time goes, then time the change to find out *how much*.

## Relevant skills

- `dataviz` (bundled) — its palette validator is authoritative: run
  `node scripts/validate_palette.js "<hex,hex>" --mode light|dark`. The yachi/pinglamb pair
  passes all six checks in both modes, so colour is not the thing to change.
- `html-skills:html-data-explorer` (installed from `f-labs-io/agent-html-skills`) — the round
  table follows its structure: row count, live summary, detail drawer, export, URL hash, plus
  its mandatory secret-scan-before-embedding rule.
- `web-artifacts-builder` is a **bad fit** here: it pulls React + Tailwind + shadcn (~150KB)
  for interactivity already delivered by ~20KB of vanilla JS, and the reports are deliberately
  single-file with zero external requests.

## Known remaining work

1. One `innerHTML` assignment left in `report.html`, and it is the legitimate one: the
   match-card body expands authored prose carrying badge shorthand (`<b>C001</b>`). The other
   two are gone — the match-card score builds nodes, and the appendix row builder was deleted
   with the section it served. Re-verify after touching anything near them by running the gate —
   `python3 -m pipeline.check_badge_links sessions/<date>/report` — which resolves every citation
   against the claims island and prints its own counts. **Not by comparing a badge count**: the
   "110" that used to sit here matched no report on any measure, and there are two measures that
   disagree by design. `data-claim` *occurrences* in the document run 77 / 88 / 96 / 111 / 119 / 119
   over the first six sessions — 08-19 is not on that list because its prose is still being written,
   which is exactly why the list is not the instruction
   (`grep -o 'data-claim=' report.html | wc -l`; `grep -c` counts lines, and
   this file puts many on one). The gate counts **distinct cited ids** and prints 43 / 40 / 49 / 55 /
   56 / 57 badge plus 20 / 23 / 27 / 33 / 31 / 48 shorthand `<b>C001</b>` citations — lower because a
   claim cited three times is one id. No single number was ever right for more than one session, so
   the instruction is to re-run the gate, not to match a figure. The appendix's 54 / 52 rows for
   07-22 / 07-24 do check out (`<tr>` inside the appendix region, less its header).
2. ROADMAP P5. **The report body is fully generated** (`pipeline/build_report.py`,
   CI-gated with `--check`): hero/scoreboard, 戰況, 數據對決, 關鍵時刻, 全場之最, 建議, the
   appendix, and the `chart-data`, `match-copy` and `claims-data` islands, plus the round
   table from its own generator. That sentence was first written while 戰況 was still
   hand-written — it had been checked by counting `SECTIONS` entries rather than by
   scanning the document. `pipeline/check_report_shell.py` now scans the document, so the
   claim is enforced instead of asserted.

   **P5 is done.** `bin/new-session` emits the report too (`pipeline/skeleton.py`): raw
   replays in, a complete rendering report out, with every generated region filled and
   TODO prose files to write into. A session no longer starts by copying the previous
   one's report.html — which is what had been silently propagating stale constants
   between sessions. Step 7 never touches an existing report.html, and step 4 never touches the Dafny or proof map of a session that has hand claims.

   What a person still writes by hand: the five `prose/*.json` files, `narrative-beats.md`
   / `recommendations.md`, `hand_claims.py`, and the `<title>` — the only string in the
   document no generator owns.

   **Nothing in the pipeline is bound to the players' names any more.** The last one was
   `build_round_table.py`, whose `tr[data-who="yachi"]` bar-tint and filter rules matched
   nothing for any other pair — the bars fell back to grey `--muted` and no gate noticed,
   because the table still rendered. Those four rules are derived per session now
   (`player_css`), and the filter classes are positional `f-p1` / `f-p2`. The colour
   tokens stay `--yachi` / `--pinglamb`: the shell defines them as aliases of `--p1` /
   `--p2`, and pointing at the slots directly would break the four committed reports whose
   `:root` predates the aliases — the `--accent` trap again. `report.html` carries the shell and marker pairs, nothing
   else. What remains of P5 is the skeleton, so `bin/new-session` emits a report instead of
   expecting one copied from the previous session.

   **Moving prose into a file can narrow a checker.** `check_prose_figures` enumerated
   `hero.json` and `matches.json` by name, so lifting 關鍵時刻 into `prose/moments.json`
   took its figures out of the scan — the region left behind is generated and therefore
   skipped, and the new file was on nobody's list. The count went 102 → 98 and nothing
   said so. It now walks `prose/*.json` and every string leaf in them, which also picked
   up fields nobody had enumerated. When adding a prose file, check the figure count goes
   UP. Add each as a new entry in `SECTIONS`; the marker region and the
   drift gate come for free.

   A `SECTIONS` entry may keep pre-existing markers instead of the standard pair — the
   `claims-data` island does, because things locate it by those comments (`check_prose_figures`
   skips it by them).

   A section that cites claims uses `pipeline/claim_cards.py` — one loader for ledger + proof
   map, so every section agrees on what "verified" means. `round_operand()` reads a figure out
   of the claim's own spec (the operands of the proved equality) rather than re-deriving it
   from `facts.json`; a spec of another shape returns None so the section skips the claim
   instead of inventing a number. Number formatting lives in `pipeline/fmt.py` and **floors**,
   because 約 has to mean "at least this much" everywhere.

   The split every section follows: numbers from `facts.json`, words from
   `<report_dir>/prose/*.json`. Prose is inserted as raw HTML because it legitimately contains
   `<span class="hl-y">` and badge spans — derived values are escaped, prose is trusted, and
   each loader runs the same simplified-glyph check as the claim generator.

   Editorial constants belong in prose, not in the script: `hero_match` (which card gets the
   spotlight) and `score_claim` (the badge on every card's score) were `m.index === 7` and a
   literal `data-claim="C026"` inside each report's inline JS, which is a large part of why the
   script could not be shared between sessions.

   **The inline script is still player-hardcoded** — ~110 occurrences of `yachi`/`pinglamb` in
   colours, keys and labels. The card renderer and the small multiples now read `CD.players`
   by position; the rest is the report-skeleton step's job, not something to chip at.
3. `sessions/2026-07-24/proof/` is a *second, lighter* report with its own 20-claim proof layer.
   It is a cross-check, not a published report — every fact in it is covered by that session's
   full report. Keep it gated by CI; do not resurrect it onto the site.

   **What made it a cross-check was unenforced until 2026-08-16.** `bin/verify-session` takes ONE
   artefact directory and every gate it runs is internal to that directory, so `proof/` and
   `report/` both went green while describing the same night differently — and the only thing
   keeping them together was somebody remembering to re-extract `proof/` whenever `report/` moved
   (most recently for the apm/pps/vs change on 2026-08-15; it was remembered, and nothing would
   have said so otherwise). `pipeline/check_cross_artefact.py` is the gate: 6 012 shared values,
   globbed over `sessions/*` so a second artefact anywhere is covered without an edit, and no pair
   at all is a failure rather than a quiet pass. The two schemas genuinely differ — `report/`
   carries 30 per-player fields `proof/` never had — so the gate **names** every uncompared field
   instead of silently intersecting, and separates a FIELD on one side only (tolerated, named)
   from a RECORD on one side only (a missing match, round, player or garbage event — a failure).
