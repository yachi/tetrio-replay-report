# cc-coach — your mid-game positions, replayed by cold-clear

**Question:** can we take the mid-game positions out of a `.ttrm`, hand them to the cold-clear bot,
and learn something from where it disagrees with the human? **Yes**, and this directory does it end to
end. It is a research tool in the same tier as `tools/triangle-oracle`: nothing here feeds `facts.json`,
mints a claim, or runs in CI. Every figure it produces is a **one-engine** figure (cold-clear's opinion),
never a verified one.

First run: all 20 exports of the night of 2026-10-03 (`replay-2026-10-03-01..20.ttrm`, 292 player-rounds,
27 868 placements), results in [`FINDINGS-2026-10-03.md`](FINDINGS-2026-10-03.md). The published
`sessions/2026-10-03` holds only exports 16-20 (5 matches), so its report and this tool's figures cover
different sets of matches and must not be compared as if they were one session.

## Pipeline

```fish
set -x REPLAY_DIR /path/to/session/replays      # a directory of .ttrm
set W (mktemp -d); cd $W

# 1. every decision point, through the repo's reference board source (vendored Triangle engine)
OUT=positions.jsonl bun ~/tetrio-replay-report/tools/cc-coach/extract-positions.ts
python3 ~/tetrio-replay-report/tools/cc-coach/validate-boards.py      # board_i + cells_i + garbage_i == board_{i+1}
bun ~/tetrio-replay-report/tools/cc-coach/validate-attack.ts          # TETR.IO attack re-priced == replay's own

# 2. cold-clear, pinned rev 279edd7 (the same rev as nix/cold-clear-oracle), plus this patch + harness
git clone https://github.com/MinusKelvin/cold-clear cc && cd cc && git checkout 279edd7c3177ff8077f6a930193397814b281f27
git apply ~/tetrio-replay-report/tools/cc-coach/cold-clear-coach.patch
cp ~/tetrio-replay-report/tools/cc-coach/cc-coach.rs bot/src/bin/ && cp ~/tetrio-replay-report/tools/cc-coach/Cargo.lock .
cargo build --release -p cold-clear --bin cc-coach && cd ..

# 3a. per-move grading (mid-game = lock >= 21, verified prefix only)
python3 -c "import json;[print(l,end='') for l in open('positions.jsonl') if (lambda p:p['lock']>=21 and p['verified'])(json.loads(l))]" > mid.jsonl
CC_NODES=40000 COACH_DUEL=80000 cc/target/release/cc-coach < mid.jsonl > grade-mid.jsonl
python3 ~/tetrio-replay-report/tools/cc-coach/grade-analyze.py grade-mid.jsonl

# 3b. 14-piece rollouts from the same positions, same pieces, same received garbage
python3 ~/tetrio-replay-report/tools/cc-coach/build-rollouts.py
CC_NODES=40000 COACH_MODE=rollout cc/target/release/cc-coach < rollouts.jsonl > rollouts-40k.jsonl
bun ~/tetrio-replay-report/tools/cc-coach/analyze-rollouts.ts rollouts.jsonl rollouts-40k.jsonl
python3 ~/tetrio-replay-report/tools/cc-coach/window-analysis.py rollouts-40k.priced.jsonl
```

Runtime on 4 cores: extraction 30 s; grading ~0.6 s per position per core; a 40k-node 14-piece
rollout ~5 s per window per core.

## What each piece of evidence rests on

| step | how it is checked | result on 2026-10-03 |
|---|---|---|
| board reconstruction | whole round: engine piece count and line count == replay `results.stats` | 292 / 292 rounds |
| piece sequence / bag | every aligned 7-block of the reconstructed sequence is a permutation | 292 / 292 |
| decision records | start field + played cells → clear → recorded garbage (amount, hole column) reproduces the next decision's field | 27 576 / 27 576 transitions |
| attack pricing | the vendored engine's own `garbageCalcV2` with re-derived b2b/combo counters == replay's pre-cancel `rawGarbage` | 27 866 / 27 868 locks (2 straddle a garbage-multiplier step) |
| b2b / combo counters | recomputed counters == engine's next-state counters | 27 868 / 27 868 |
| attack-row prefix | the repo's `verifiedIndex(..., 'frame+row')` | 24 268 of 27 868 decisions inside it; only those are graded |
| reachability | the human's placement is among cold-clear's root candidates (`ZeroGComplete` movegen) | 18 341 of 18 356 graded mid-game moves (15 are 180° / SRS+ placements cold-clear cannot generate; they are still scored, through the duel) |

## Cold-clear's search is random; this harness makes it reproducible

Cold-clear picks which line to explore by WEIGHTED RANDOM SAMPLING (the Monte-Carlo leaf choice in
`dag.rs`), from the unseeded thread rng, and its move generator returns placements in `HashMap`
order, which differs per process. So the unpatched bot gives a different answer every run — measured:
one 14-piece rollout came out 14, 9 and 4 lines of attack on three runs. The patch replaces the rng with
a thread-local `StdRng` the harness reseeds before every search (FNV of position id + purpose, xor
`COACH_SEED`), and sorts the move list. Same inputs + same `COACH_SEED` is now byte-identical output;
another `COACH_SEED` is an independent sample. The first run's figures (FINDINGS) were made before this
patch, i.e. from one unseeded sample per position; re-run with seeds 1 and 2 over 300 of yachi's
windows, cold-clear's APP was 0.906 (original), 0.908 and 0.921 against the human's 0.629 — the
headline is a property of the positions, not of one draw.

## Three measurement decisions, each made because the obvious version was wrong

**1. Cold-clear is not converged, so a single "it would have played X" is weak evidence.** Over 300
calibration positions its 40k-node pick equals its own 640k-node pick only 185 times. A per-move verdict
therefore needs a noise floor, and that is measured, not assumed (`calib.py`, `duelcal.py`).

**2. Values read off the main tree are biased against the human.** Root candidates carry backed-up
MAXIMA, and cold-clear's favourite is searched far deeper than the human's move, so its max is drawn
from more samples. The **duel** removes this: each of the two placements gets its own reward plus an
independent fresh search of the same budget from the board it leaves (`COACH_DUEL`). Regret is
`duel(cc pick) − duel(human)` and can be negative — the human beats cc's pick in ~40% of positions.

**3. A threshold is a calibration, not a taste.** A "clear mistake" is duel regret ≥ 600, which is
above the 95th percentile of a deliberately weakened cold-clear (10k nodes) judged by the same duel.
Reproducibility of a single flag at 600, re-judged with 4× the budget: ~75%. So individual examples
shown to a player are **re-verified at higher budget** before being shown, and the headline numbers
are aggregates.

## Rollouts: what "same position" means

From a mid-game decision, cold-clear plays the next 14 pieces (two bags). It sees exactly what the
human saw: the same field, hold, b2b/combo state, the 5-piece preview, and the true future sequence
revealed one piece per placement. Garbage is **pressure-matched**: the rows the human actually
received at step *j* (amount and hole column) are inserted under cold-clear's board at the SAME step
*j*, right after its lock — unless that lock cleared lines, in which case they wait for its next lock
that clears nothing (TETR.IO only tanks on a lock that clears nothing, which is also why the human
received them on that step). Two independent re-derivations in the clip workflow found an earlier
wording of this rule ambiguous by one step; the code has always done the above.
Cold-clear gets no cancellation credit for its own attack, and both sides' attack is the TETR.IO
pre-cancel figure priced by the same `garbageCalcV2`.

Received garbage is ENDOGENOUS (a human who attacks less cancels less and receives more), so it is
never used as a stratifier; pressure is stratified by what is fixed at the window's start (garbage rows
already on the board, garbage already queued).

## Residual differences from TETR.IO, and which way each one biases

| difference | effect | direction |
|---|---|---|
| no clock: cold-clear thinks ~0.2 s per piece unpressured, the human plays at ~2 PPS | cc is advantaged | overstates the gap; the 4k-node rollouts are the "fast bot" check |
| cold-clear's evaluator is tuned for PPT, values b2b as a boolean, knows nothing of TETR.IO's b2b chain levels or combo multiplier | cc plays sub-optimally for TETR.IO scoring | understates the gap |
| no 180° rotation, SRS instead of SRS+ for I | cc's move set is a subset of the human's | understates the gap |
| no cancellation credit for cc in rollouts | cc faces at least the garbage the human let through | understates the gap |
| cold-clear's own T-spin / mini rule prices cc's spins | small; minis are rare in both | either |
| spawn rule `Row19Or20`, lock-out pruning above row 20 | cc declares positions near topout dead earlier than TETR.IO | rollouts where cc topped out are reported, and excluding them raises the gap |

## Animated clips (`clips/`, published as `pages/cc-<player>.html`)

One page per player, built by the same pipeline with the player as a parameter. Run it from the work
directory the pipeline above left behind (it reads `positions.jsonl`, `positions.jsonl.rounds.json`,
`mid.jsonl`, `grade-mid.jsonl` and `rollouts-40k.priced.jsonl` from the cwd, and writes `./<player>/`):

```fish
set -x REPLAY_DIR /path/to/session/replays
bash ~/tetrio-replay-report/tools/cc-coach/clips/clip-pipeline.sh pinglamb   # CC=… overrides the harness path
```

| stage | script | what it does |
|---|---|---|
| 1 | `pick-candidates.py <player> <out>` | the player's per-move clear misses (duel regret ≥ 600) at stack heights 5-15, top 10 per category (`grade-analyze.py`'s categories) |
| 2 | harness at 160k nodes / 320k duel, then `choose-examples.py <out>` | keep candidates that are still ≥ 600 at 4× the budget; take the largest confirmed miss per category, distinct rounds, with a full 14-piece window after it — 7 examples |
| 3 | `build-clips-p.py <player> <out>` | the 7 examples plus 5 "typical" windows from the 40k rollouts at the 50th/75th/80th/85th/90th percentile of the player's gap; same pieces, preview and received-garbage schedule |
| 4 | harness rollout × `COACH_SEED=0..7`, `build-frames-p.ts` per seed | per-piece frames for both sides; fails loudly if the human's frames do not reproduce the recorded boards or cold-clear's do not end on the harness's own final field |
| 5 | `finalize-clips.py <out>` | per clip, the LOWER-median seed — one rule for every clip, never the run that flatters cold-clear — plus each human move's verified-prefix flag and graded loss; `clips-chosen.json` and readable `clipdump/` |
| 6 | `build-anim.py` | renders `anim-template.html` into `../pages/cc-<player>.html` |

`build-anim.py` derives every number on the page from its inputs: the histogram, the window count,
the topped-out count and the "matched or beat" count from `rollouts-40k.priced.jsonl` filtered to the
player; the percentile of each typical clip is its **mid-rank** among the player's windows (windows
with the same gap count half; Python's `round`, i.e. half to even — under strict-less-than the same
clips read several points lower, so the page names the method); the node budget from
`--rollout-nodes` (40000, the `CC_NODES` of the rollout command above); clip, step and seed counts
and the biggest-miss clips' own 14-piece gaps from `clips-chosen.json`; the frame count, the
checkers and how each of their mismatch lines was resolved from `<player>/adjudication.json`; and
the caption refute history from `<player>/refute-history.json`. It refuses to render if the
adjudication does not cover every clip and frame, if a typical clip is not a charted window, if the
refute loop did not end dry, or if the page text addresses the reader or uses a gendered pronoun —
the pages are public and name the player in the third person.

The 7 "biggest miss" clips are **not** drawn from the histogram: they are chosen per move (stage 2,
graded loss of one placement) and start at that move, so the page says so and prints their own gaps.

```fish
python3 build-anim.py --player pinglamb --other yachi --data $W/pinglamb \
    --rollouts $W/rollouts-40k.priced.jsonl --rollout-nodes 40000 --captions pinglamb/captions-final.json \
    --verify pinglamb/adjudication.json --refute pinglamb/refute-history.json --out ../pages/cc-pinglamb.html
python3 build-anim.py --player yachi --other pinglamb --data $W/yachi \
    --rollouts $W/rollouts-40k.priced.jsonl --rollout-nodes 40000 --captions yachi/captions-final.json \
    --verify yachi/adjudication.json --refute yachi/refute-history.json --out ../pages/cc-yachi.html
```

`bin/build-docs` copies both pages into `docs/` verbatim and `--check` compares them byte for byte,
exactly as it does `tools/analyzer.html`; the index cards say they are simulator output and not in
the proof chain. The rendered pages are committed; the work-directory inputs are not, so a re-render
needs the work directory from a pipeline run.

### Provenance of the frames and captions

1. Four agents, one per batch of three clips, wrote their OWN checkers (`<player>/verify-batch-*.py`,
   kept here) from the raw sources — shape, empty cells, support, clears, garbage, TETR.IO attack /
   b2b / combo, board continuity. `run-verifiers.sh <player> <data-dir>` re-runs all four and saves
   what they print in `<player>/verify-out/batch-N.txt`; then `adjudicate.py` rebuilds every frame of
   both sides from the frames alone (continuity, support, clears, one-hole garbage rows, and Cold
   Clear's garbage-waiting rule against the player's own inserted rows) and classifies every saved
   mismatch line. It explains only one class — a checker comparing rows *inserted* with rows
   *received* — and only when its own rebuild of that clip is clean; anything else stays
   `unresolved` and the page prints it. Planted mutants (wrong garbage count, a floating piece, a
   garbage row inserted on a clearing step) each produce rebuild problems and flip the verdicts.
2. Every caption item (title, summary, step claims) was refuted by two lenses (numbers/geometry and
   wording/overclaim) in a loop until dry.

| | frames rebuilt | checker mismatch lines (saved re-runs) | caption checks refuted, by round |
|---|---|---|---|
| yachi | 336 / 336, 0 problems | 0 | 13 of 190, then 3 of 128, 2 of 48, 0 of 16 (`yachi/refute-history.json`, with every refutation's reason and fix) |
| pinglamb | 336 / 336, 0 problems | 4, all `verify-batch-3.py` comparing inserted with received rows on clips 9 and 11; all explained, 0 unresolved | 10 of 192, then 2 of 112, 1 of 32, 0 of 16 (`pinglamb/refute-history.json`, per batch only) |

Four things this record used to blur, kept here so they are not blurred again:

- **The checkers' outputs were not saved the first time**, and the per-player `proof-record.json` that
  stood in for them said "0 mismatches" while the two outputs that *were* kept (pinglamb batches 2
  and 3) listed some. Both files are deleted; `verify-out/` and `adjudication.json` replace them.
  The batch-2 mismatches in that early output (clips 6-8, a cascade from one garbage-timing step)
  do not reproduce with the committed `verify-batch-2.py`, which is the script that was revised after
  them.
- **`verify-batch-1.py` is run with `CC_GARBAGE_MODE=early`.** Its default reading delivers the
  player's step-N rows to Cold Clear only after Cold Clear's step-N piece, which is not the rule the
  clips were built with or the page states; under that default it reports pinglamb's clips 3 and 4
  and yachi's clip 4 as mismatches, at exactly the steps where the two readings differ. `run-verifiers.sh` says this at the top.
- **pinglamb's refute history is per batch and per round counts only** — the verification workflow
  returned counts, not the individual refutations, unlike yachi's file. The counts are the workflow's
  record; nothing here can re-derive them.
- **After the refute loop, "the human" in yachi's captions (28 places) and pinglamb's (1) was replaced
  by the player's name** so both pages read alike. That substitution is mechanical and was not put
  back through the skeptics.

## Habits page (`habits/`, published as `pages/cc-habits.html`)

One page, both players, every night: for each recurring habit (six per player) the night's rate next
to Cold Clear's rate on the same positions, a strip of that measure over all 15 nights, and typical
example plays replayed side by side with Cold Clear from the identical position, queue, hold and
received garbage. The habits are the ones that survived two skeptic re-derivations over the 15-night
corpus (narrowed where a skeptic narrowed them); the page's header says what it shows and what Cold
Clear is not. yachi's view says "you"; pinglamb is always named.

The scripts expect one work directory, `$CC_WORK`, laid out as the run that produced the page was:
`corpus/` (per-night positions, `mid.jsonl`, `grade.jsonl`, the seed-1 and weak-bot grades,
`sub4000.jsonl`), `scen/` (`habits/lib/*.py` here), `scen/habits/` (`habits/detectors/*.py`) and
`scen/hclips/` (`habits/clips/*`), plus `attack.ts` at its root (`frames.ts` imports
`../../attack.ts`). Every hard-coded work path was replaced by `$CC_WORK`; nothing else was edited.
The detectors also read the skeptics' cached row files (`scen/holes_rows.pkl` from `holes_build.py`,
`scen/b2b_hold.pkl` from `b2b_hold_load.py`).

```fish
set -x CC_WORK /path/to/work
# 1. detectors: <ID>.nights.json (per-night rates, verbatim on the page) + <ID>.occ.jsonl (occurrences)
cd $CC_WORK/scen/habits
python3 Y6_prep.py   # Y6 only: positions outside grade.jsonl, then grade them:
CC_NODES=20000 COACH_DUEL=20000 COACH_SEED=0 cc/target/release/cc-coach < Y6.extra-in.jsonl > Y6.extra-grade.jsonl
for h in Y1 Y2 Y3 Y4 Y5 Y6 P1 P2 P3 P4 P5 P6; python3 $h.py; end
# 2. clips: pick typical windows, roll Cold Clear out from each start with seeds 0-4, rebuild and check frames
cd $CC_WORK/scen/hclips
python3 select.py                       # candidates.json, windows.jsonl, rollin.jsonl, select-log.json
for s in 0 1 2 3 4
  CC_NODES=40000 COACH_MODE=rollout COACH_SEED=$s cc/target/release/cc-coach < rollin.jsonl > roll-s$s.jsonl
  bun frames.ts $s                      # frames-s$s.json + frames-check-s$s.json (fails loudly on a mismatch)
end
python3 finalize.py                     # $CC_WORK/scen/habit-clips.json
# 3. the page, then publish
python3 ~/tetrio-replay-report/tools/cc-coach/clips/build-habits.py \
    --clips $CC_WORK/scen/habit-clips.json --out ~/tetrio-replay-report/tools/cc-coach/pages/cc-habits.html
bin/build-docs; bin/build-docs --check
```

(`frames.ts` reads `HCD` instead of `$CC_WORK/scen/hclips` when set; `mut/` held the mutant inputs.) The committed `finalize.py`, run against the original work
directory, reproduces `habit-clips.json` byte for byte.

What the clip stage checks, per start position and per seed: the player's board after each of the
4 shown pieces equals the next recorded decision's field (garbage included); the player's attack, re-priced
with each file's own options and the lock-time garbage multiplier, equals the replay's raw attack;
Cold Clear's rebuilt lines and inserted garbage match the harness at every step, and its final board
equals the harness's `final_field`. Planted mutants (a +1 attack, a changed tank, a changed final field,
a shifted garbage hole on a window that has garbage) each fail a check. Selection: verified
occurrences only, misdrop-shaped moves excluded except for Y1, P1 and Y6 (misdrop-shaped by
definition), the occurrence whose graded cost is nearest that night's pool median, distinct rounds.
The shown Cold Clear run is the median of the five seeds by 4-piece attack, then holes; the page
says how many of the five chose the same first move, and flags the clips whose shown first move does
not meet the habit's own contrast test.

`build-habits.py` prints every rate straight from each habit's per-night entry (the detector's
`nights.json`, carried verbatim in `habit-clips.json`). The one derived figure is Y6's all-nights row,
which its detector did not pool: it is summed from the per-night counts and the build asserts each sum
against the figures in Y6's own comparison text. The build refuses a page with an external URL, a
gendered pronoun or a model identifier. Like the two replay pages, it is simulator and bot output and
not in the proof chain; `bin/build-docs` copies it verbatim and `--check` compares it byte for byte.
