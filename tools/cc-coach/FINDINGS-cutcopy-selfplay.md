# Pilot: does cold-clear, playing alone, build Cut Copies (千鳥格子)?
Research only, in the same tier as the rest of tools/cc-coach. Nothing here feeds facts.json or a claim. Since 2026-10-20 the hit games (cold-clear's placements up to each hit's follow-up) are committed in analysis/cutcopy-selfplay.json and played on docs/cutcopy-demos.html, re-derived there by pipeline/openers/cutcopy-selfplay.test.ts; the replay core is pipeline/sim/cc-selfplay.ts. The other figures below are still this note's alone. Every figure is one run's output, copied by hand on 2026-10-20. No committed artefact re-derives them, so re-run the commands to get them back and never copy them into anything published.

## Method
1. **Self-play** (`COACH_MODE=selfplay`). cold-clear 279edd7 with the patch and Standard::default plays alone from an empty board, with no garbage. The queue is a seeded 7-bag: the current piece plus 5 previews are visible, and one more is revealed per placement. A game is exactly the harness's rollout from that empty position. Same id, seed, CC_NODES and COACH_SEED give byte-identical output; seed 48 re-run alone matched.
2. **Replay through the repo's engine** (cutcopy-selfplay.ts): the vendored Triangle engine, TL ruleset, g = 0, the queue spliced in as runDemo does. Each placement's path comes from the planner's `reach` (a BFS over the engine's own moves, SRS+, 180 allowed) and `inputsOf`.
   - The engine's lock is what gets scored.
   - Wrong piece after a hold, no engine path, or different lines or cells: counted, and the game is cut.
   - Spin-credit disagreements are counted, and the engine's credit is used.
   - Each completed game's final board is compared with cold-clear's final_field.
3. **The corpus matcher, unchanged**: TechDigests (no garbage, every lock inside the prefix) go to `classify(CUTCOPY, …)`. That covers the scored-T-spin rule, the reconstruction check, both variants and both hands, and the matcher's own follow-up in the carried slot.
4. **Positive control** (`--control`): own.3.482 from analysis/cutcopy-own.json gives 1 cutcopy hit, as drawn, at lock 9, with the follow-up fired at lock 12. All 13 of 13 placements are reproduced and the final board is equal.
5. **Near-miss diagnostic** (pilot only, not the matcher): at each full TSD whose T is the window's flat, nub-down T, the number of window cells that disagree, taking the smaller over the two hands. A count of 0 matched every hit.

## Commands
```
git clone https://github.com/MinusKelvin/cold-clear cc && cd cc && git checkout 279edd7c3177ff8077f6a930193397814b281f27
git apply ~/tetrio-replay-report/tools/cc-coach/cold-clear-coach.patch
mkdir -p bot/src/bin && cp ~/tetrio-replay-report/tools/cc-coach/cc-coach.rs bot/src/bin/ && cp ~/tetrio-replay-report/tools/cc-coach/Cargo.lock .
cargo build --release -p cold-clear --bin cc-coach && cd ..
python3 -c "import json;[print(json.dumps({'id':f'sp-{s}','seed':s,'pieces':200})) for s in range(1,201)]" > games-in.jsonl
CC_NODES=40000 COACH_MODE=selfplay COACH_SEED=0 cc/target/release/cc-coach < games-in.jsonl > games-40k.jsonl
bun ~/tetrio-replay-report/tools/cc-coach/cutcopy-selfplay.ts games-40k.jsonl result-40k.json
bun ~/tetrio-replay-report/tools/cc-coach/cutcopy-selfplay.ts --control
```
- Speed: about 0.16 s per piece per core at 40k nodes. 200 games × 200 pieces took 29 min 39 s wall on 4 cores.
- Replay plus classify took 2.5 min, and two runs gave identical output.
- md5 of games-40k.jsonl: 654bbe48bd2ea5df0ef192911aeb3aa7. md5 of result-40k.json: 237379e5687e1c0d12756484d2181de4.

## Numbers (seeds 1-200, 200 pieces each, 40k nodes, COACH_SEED=0)
- **Games:** 200 played, 198 completed on the engine. 40 000 pieces placed by cold-clear, 39 971 replayed.
- **Engine disagreements:** 2 games cut, both no_engine_path for a flat I on the bottom row (seed 136 lock 190, seed 177 lock 181).
- **Checks:** spin-credit disagreements 0; final-board mismatches 0; row map unverified 0; reconstruction disagreements 0.
- **Scored full TSDs:** 3 194, the same as cold-clear's own tsd count. 314 in the opener window, 2 880 mid-game. TSS 172, TST 56.
- **cutcopy hits: 11** (5 as drawn, 6 mirrored). Follow-up fired in 10; the other was slot_filled_before_t.
- **uncut hits: 1**, as drawn, follow-up fired.
- Hits in the opener window: 2.
- cutcopy ablations (no must-empty / no roof / T overlap): 82 / 37 / 18.
- Near-miss for cutcopy (cells off: TSDs): 0: 11, 1: 56, 2: 459, 3: 1 105, 4: 139. 23 TSDs were not a flat, nub-down T.

| seed | lock | variant | hand | follow-up |
|---|---|---|---|---|
| 48 | 81 | cutcopy | as drawn | fired at lock 86 |
| 65 | 19 | cutcopy | mirrored | fired at lock 23 |
| 83 | 58 | cutcopy | mirrored | fired at lock 59 |
| 87 | 11 | cutcopy | mirrored | fired at lock 13 |
| 118 | 131 | cutcopy | mirrored | fired at lock 134 |
| 118 | 144 | cutcopy | as drawn | fired at lock 149 |
| 136 | 83 | uncut | as drawn | fired at lock 84 |
| 173 | 193 | cutcopy | mirrored | fired at lock 196 |
| 176 | 80 | cutcopy | as drawn | fired at lock 88 |
| 186 | 27 | cutcopy | as drawn | not fired: slot_filled_before_t (lock 28) |
| 193 | 26 | cutcopy | as drawn | fired at lock 32 |
| 195 | 135 | cutcopy | mirrored | fired at lock 141 |

To replay a hit, feed `{"id":"sp-<seed>","seed":<seed>,"pieces":200}` with CC_NODES=40000 and COACH_SEED=0.

## Reading
- **Yes, rarely, and it finishes them.** 11 Cut Copies in 3 194 TSDs (about 1 in 290), in 10 of the 200 games, with the second TSD fired in 10 of the 11. Every placement up to each hit was reproduced by the engine and checked by the row map.
- **It is not something cold-clear aims at.** Its evaluator knows TSD slots, not this shape. Close misses are common: 56 TSDs are one window cell off and 459 are two cells off, against 11 exact. Read the hits as a by-product of TSD-slot play.
- **This does not test the source's claim**, which is that Cut Copies mostly arise with rising garbage; self-play has none.
  - For orientation only: analysis/cutcopy-facts.json (read 2026-10-20) has 109 cutcopy hits in 10 058 scored TSDs, 95 of them with garbage in the window. That leaves 14 garbage-free corpus hits in 10 058, against cold-clear's 11 in 3 194.
  - The two are not comparable populations: no clock, no opponent, one search sample per game, and an unconverged budget (the README says the 40k pick equals the 640k pick only 185 of 300 times). And 11 is a small count. This is a pilot reading, not a measurement.
- **uncut appears once** (seed 136, lock 83) where the corpus has none. One event: recorded, not read.
- **The two engine disagreements** are flat bottom-row I placements with no SRS+ path. The likely cause is that cold-clear uses SRS for the I while the engine uses SRS+ (the README's residual table); not investigated further. Neither game was near a hit.

## Caveats a review raised
- **"Reconstruction disagreements 0" cannot fail here.** In the corpus the cleared rows come from the engine's own records; this script computes them from the same pre-lock board and lock cells the check re-derives from, so agreement holds by construction. The checks that can fail are the row map (predicted board against the engine's board) and the line count against cold-clear's.
- **Spin credit is partly chosen.** For a T, the script takes the first engine path whose spin matches cold-clear's and falls back to the first path only when none does. So "spin-credit disagreements 0" says some engine path gives the same credit, not that cold-clear's own path does.
- **The two no-path I placements are unexplained.** SRS against SRS+ is a guess; a limit of the planner's move search is just as possible. Untested.
- **The near-miss counts** treat a window cell off the board as disagreeing, where the matcher calls the window off the board. A diagnostic, not the matcher.

## Next step
Test the source's claim by giving self-play a received-garbage schedule (the rollout already inserts rows), or by grading the corpus's garbage-in-window hits with cold-clear. Using several COACH_SEEDs per game would turn the single draw into a sampled rate.

## With received garbage (2026-10-20)
Research only, like the rest of this note: nothing below is on any page, in any artefact under analysis/, or in a claim. Every figure is one run's output, copied by hand on 2026-10-20; re-run the commands to get them back.

The source page says Cut Copies are mostly built when garbage rises, and the no-garbage run above found few. This run gives cold-clear the same 200 queues (seeds 1-200, 200 pieces, CC_NODES=40000, COACH_SEED=0) plus a received-garbage schedule.

### The garbage rule (ours, not TETR.IO's)
- **Schedule** (`selfplay-garbage-input.py`, seeded by `random.Random("cc-garbage-<seed>")`): the first attack arrives at a piece drawn from 4-10 (1-based), then one every 4-10 pieces. Each attack is 1-4 rows with one hole column drawn from 0-9, the same column for every row of that attack.
  - That is an attack every 7 pieces and 2.5 rows on average, about 0.36 rows per piece offered.
  - For orientation only: the corpus's materialised received garbage (facts.json `garbagereceived` over `pieces`, all sessions) measured about 0.43 rows per piece on 2026-10-20.
- **Tanking** (the harness's existing rollout rule): an attack at piece j is in the incoming meter for piece j and joins the pending list after lock j. Pending rows enter, front first, on the first lock that clears nothing, at most 8 rows per lock. cold-clear's `pick_move` is told the rows arriving at that piece plus the rows still waiting.
- **What is left out**: cold-clear sends nothing back, so nothing cancels. There is no garbage delay in frames, no messiness within an attack, and no opponent.

### What changed in the tools
- **`cc-coach.rs`**: selfplay accepts an optional `"garbage": [{"after_piece", "lines", "col"}]`. With it, each step also carries its board after the lock and garbage (`field`) and the hole columns inserted on that lock (`garbage_cols`), and the schedule is echoed in the output.
  - Without the key, the output is unchanged: seeds 7, 48, 65 and 136, and in a separate review 83, 118 and 195, re-run with the rebuilt binary were byte-identical to games-40k.jsonl (one-off hand checks, not a gate).
  - The file is in `analysis/cutcopy-selfplay.json`'s `harness_md5`, so that artefact was rebuilt (`--rebuild`), and only that md5 line moved.
- **`cutcopy-selfplay-garbage.ts`**: the replay. It is a copy of `pipeline/sim/cc-selfplay.ts`'s replay, kept separate because that file is hashed by the committed artefact.
  - It re-derives the insertion from the echoed schedule and inserts the rows with the engine's own `board.insertGarbage` after each lock.
  - After every placement it checks that the inserted columns equal cold-clear's `garbage_cols` and that the engine's board equals cold-clear's `field`.
  - Any disagreement cuts the game with a named reason (`garbage_mismatch`, `board_mismatch`, `garbage_spawn_overlap`, plus the replay's own cuts). Nothing is ignored.
  - Each lock's digest carries its garbage rows, so `classify(CUTCOPY, …)` runs unchanged and `garbage_in_window` is the matcher's own.
- **Mutants planted by hand on a 4-game, 4k-node trial**:
  - a hole column changed → `garbage_mismatch`
  - one row of a cold-clear board changed → `board_mismatch`
  - an attack moved 1, 2 or 3 pieces earlier → `garbage_mismatch` each time
  - one attack moved a piece LATER was not detected, and that is correct: the lock it moved off cleared lines, so the rows waited for the next lock either way (an equivalent mutant).

### Commands
```
cd /tmp/claude-0/ccpilot   # the cc/ build from the Commands section, rebuilt with the patched cc-coach.rs
python3 ~/tetrio-replay-report/tools/cc-coach/selfplay-garbage-input.py 1 200 200 > games-garbage-in.jsonl
# 4 processes, 50 seeds each (in-k.jsonl holds the lines with NR%4==k, NR 1-based), RAYON_NUM_THREADS=1:
for k in 0 1 2 3; do awk -v k=$k 'NR%4==k' games-garbage-in.jsonl > in-$k.jsonl; done
for k in 0 1 2 3; do RAYON_NUM_THREADS=1 CC_NODES=40000 COACH_MODE=selfplay COACH_SEED=0 cc/target/release/cc-coach < in-$k.jsonl > out-$k.jsonl & done; wait
# merged and sorted by seed into games-garbage-40k.jsonl, then
bun ~/tetrio-replay-report/tools/cc-coach/cutcopy-selfplay-garbage.ts games-garbage-40k.jsonl result-garbage-40k.json
```
- **Time**: 27 min wall on 4 cores; replay plus classify 1 min 53 s. Two classify runs gave identical output, and seed 7 re-run alone matched its line in the merged file.
- **md5**: games-garbage-in.jsonl 507e06cc764f96db48150df6ca261a1a; games-garbage-40k.jsonl b3149e02fea6516c162a018f7eeaab6d; result-garbage-40k.json 31b5a700a8e693f6d5ce4d088b2f98f0. All are kept in /tmp/claude-0/ccpilot/g, not in the repo.

### Numbers
- **Games**: 200 played, 200 completed on the engine, none dead. 40 000 pieces placed and replayed.
- **Garbage**: 14 138 rows offered, 14 113 inserted (the rest were still pending when the games ended), about 0.35 rows per piece.
- **Checks**: no game cut; garbage mismatches 0; board mismatches 0; spin-credit disagreements 0; row map unverified 0 of 40 000.
- **Scored full TSDs**: 2 550, equal to cold-clear's own tsd count. 298 in the opener window, 2 252 mid-game. TSS 277, TST 38.
- **cutcopy hits: 48**, in 45 of the 200 games.
  - 42 of the 48 have garbage in the window.
  - Follow-up fired in 30; 17 were slot_filled_before_t and 1 was next_t_elsewhere.
  - 8 are in the opener window, every one at lock 11 or later, so after the first attack had arrived (it lands by piece 10); 7 of those 8 have garbage in the window.
- **uncut hits: 0.**
- **cutcopy ablations** (no must-empty / no roof / T overlap): 338 / 168 / 54.

| | no garbage | with garbage |
|---|---|---|
| scored full TSDs | 3 194 | 2 550 |
| cutcopy hits | 11 (about 1 in 290 TSDs) | 48 (about 1 in 53 TSDs) |
| of which garbage in window | 0 (there is none) | 42 |
| hits with no garbage in window | 11 | 6 |
| games with a hit | 10 | 45 |
| follow-up fired | 10 of 11 | 30 of 48 |
| uncut hits | 1 | 0 |

For orientation only: the corpus (analysis/cutcopy-facts.json, read 2026-10-20) has 109 cutcopy hits in 10 058 scored TSDs, 95 of them with garbage in the window, and follow-up fired in 54.

### Reading
- **The direction matches the source's claim.** On the same queues, garbage raised cold-clear's Cut Copy rate about fivefold per scored TSD, with fewer TSDs. 42 of the 48 hits have garbage in the window, near the corpus's 95 of 109.
- **The share is weaker evidence than the rate.** At about 0.35 rows per piece the bottom of the board is mostly garbage, so a window near the floor can contain garbage cells whether or not garbage made the shape. This run does not measure how often a scored TSD's window holds garbage when it is NOT a hit, so it does not separate "garbage builds the shape" from "garbage is everywhere".
- **The follow-up fires less often with garbage** (30 of 48, against 10 of 11). Most misses are slot_filled_before_t, which is also the corpus's most common reason (the corpus fires 54 of 109).
- **The 6 garbage-free hits against 11 without garbage** is one sample of small counts; not read.

### Caveats
- **A bot is not a human.** cold-clear's evaluator knows TSD slots, not this shape. Everything here is about how often that search stumbles into the window, one search sample per game (COACH_SEED=0), at a budget the README shows is not converged.
- **The garbage rule is ours.** It is not TETR.IO's exact behaviour: no cancellation, no frame delay, no opponent, one hole per attack, and our own rate and size distribution. A different rule could give a different rate.
- **A few hundred games.** 200 games and 48 hits; a pilot reading, not a measurement. Several COACH_SEEDs, or another garbage rule, would be needed to put an interval on it.
- **The replay is not independent of the matcher.** The garbage insertion and the board are checked against cold-clear's own output after every placement, but the hit decision is the same TypeScript classifier the corpus artefact uses.
- **The near-miss diagnostic from the no-garbage run was not run here.**
