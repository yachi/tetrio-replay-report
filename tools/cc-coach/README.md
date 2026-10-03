# cc-coach — your mid-game positions, replayed by cold-clear

**Question:** can we take the mid-game positions out of a `.ttrm`, hand them to the cold-clear bot,
and learn something from where it disagrees with the human? **Yes**, and this directory does it end to
end. It is a research tool in the same tier as `tools/triangle-oracle`: nothing here feeds `facts.json`,
mints a claim, or runs in CI. Every figure it produces is a **one-engine** figure (cold-clear's opinion),
never a verified one.

First run: the 2026-10-03 session (20 matches, 292 player-rounds, 27 868 placements), results in
[`FINDINGS-2026-10-03.md`](FINDINGS-2026-10-03.md).

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
player; clip, step and seed counts from `clips-chosen.json`; the frame count, the number of checker
agents and the caption refute history from `<player>/proof-record.json` (and `refute-history.json`
where that is kept per round). It refuses to render if the proof record does not cover every clip and
frame, if the refute loop did not end dry, or if the page text addresses the reader or uses a
gendered pronoun — the pages are public and name the player in the third person.

```fish
python3 build-anim.py --player pinglamb --other yachi --data $W/pinglamb \
    --rollouts $W/rollouts-40k.priced.jsonl --captions pinglamb/captions-final.json \
    --proof pinglamb/proof-record.json --out ../pages/cc-pinglamb.html
python3 build-anim.py --player yachi --other pinglamb --data $W/yachi \
    --rollouts $W/rollouts-40k.priced.jsonl --captions yachi/captions-final.json \
    --proof yachi/proof-record.json --refute yachi/refute-history.json --out ../pages/cc-yachi.html
```

`bin/build-docs` copies both pages into `docs/` verbatim and `--check` compares them byte for byte,
exactly as it does `tools/analyzer.html`; the index cards say they are simulator output and not in
the proof chain. The rendered pages are committed; the work-directory inputs are not, so a re-render
needs the work directory from a pipeline run.

The captions in `<player>/captions-final.json` are the output of two workflow passes per player,
recorded so the claims on the page have provenance:
1. four agents, one per batch of three clips, wrote their OWN checkers (`<player>/verify-batch-*.py`,
   kept here) from the raw sources and re-derived all 336 placements (12 clips × 14 pieces × 2 sides)
   — shape, empty cells, support, clears, garbage, TETR.IO attack / b2b / combo, board continuity;
2. every caption item (title, summary, step claims) was refuted by two lenses (numbers/geometry and
   wording/overclaim) in a loop until dry.

| | frames re-derived | frame mismatches | caption checks refuted, by round |
|---|---|---|---|
| yachi | 336 / 336 | 0 (the only flag was an ambiguous one-step wording of the garbage rule, now fixed in the text above) | 13 of 190, then 3 of 128, 2 of 48, 0 of 16 (`yachi/refute-history.json`) |
| pinglamb | 336 / 336 | 0, none unresolved | 10 of 192, then 2 of 112, 1 of 32, 0 of 16 (`pinglamb/proof-record.json`, per batch: 4→0 · 0 · 3→1→1→0 · 3→1→0) |

pinglamb's first-pass checker outputs (not committed) listed mismatches on clips 6, 9 and 11, mostly
garbage timing; the final record (`pinglamb/proof-record.json`) is what the workflow settled on after
re-checking, and it holds 0 mismatches and 0 unresolved items. Batch 2 also kept a supplementary T-spin
corner check (`verify-batch-2-extra.py`).
