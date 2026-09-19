# 2026-09-18 · 兩邊都喺狀態嗰三場 — drafting notes

**This artefact is a FILTERED SUBSET, not a session report.**

## What the filter is

Of the 18 matches played on 2026-09-18, these are the 3 where BOTH players' pooled
per-match VS sat above that player's own median across the 12 committed sessions
(96 matches): yachi > 113.05, pinglamb > 116.36.

Pooled per-match VS = `100 * sum(garbage_attack + garbage_cleared) / sum(T)`, where
`T = round(60 * pieces / pps) / 60` seconds — the frame-count route. `finaltime_ms`
does NOT yield the frame count (CLAUDE.md, `stat:floor-wrong`).

| here | real night | file | pooled VS y / p |
|---|---|---|---|
| m1 | m1 | replay-2026-09-18-01.ttrm | 118.8 / 120.5 |
| m2 | m3 | replay-2026-09-18-03.ttrm | 114.9 / 123.6 |
| m3 | m5 | replay-2026-09-18-05.ttrm | 116.7 / 127.1 |

Matches are renumbered by position on extraction (CLAUDE.md: `index` is the position
in the artefact, not the export number). The original identity survives in `file`.

## What must not be said about it

- **The 3:0 [G001] is the subset's, not the night's.** The full 18-match night was
  pinglamb 11:7 in matches, 69:58 in rounds.
- **[G019] "in all 24 rounds the winner had the higher VS" is not a finding here.**
  The filter selects on VS, so this is the selection showing through. Corpus-wide the
  same statement is independently true (VS 100% in every session's AUC block), which
  is why it is worth citing at all — but not as evidence produced by this subset.
- **Nothing here is evidence about either player's level.** Three matches chosen on a
  VS criterion is not a sample.

## Why it is not under sessions/

`analysis/stat_sources.py` globs `sessions/*/*.ttrm` and `pipeline/corpus-membership.ts`
calls any directory holding `.ttrm` a session. Placing these three replays under
`sessions/` would add 48 player-rounds to every corpus-wide figure — the gated
`stat:corpus` family, the rate-records artefact, the donation bands, the equiv-coverage
and leave-one-out tables — while those same rounds also belong to the (not yet added)
real 2026-09-18 session, so the corpus would count them twice.

## Beats used

1. m1 is the only one reaching a deciding round [G007]; that round is 106.6 vs 85.2 [G054].
2. m2r7 is the subset's peak: combined VS 304.5 [G055], and its VS [G010] and APM [G009] maxima.
3. m3r5 is the biggest comeback: 50 queued attack against 41 [G020].
4. Pieces are near-level (2236 vs 2216 [G023]) while attack is not (1489 vs 1332 [G024]).
5. Both players' attack per piece is higher in rounds won than lost [G066][G060][G061] —
   the corpus's standing "APP is the lever" conclusion, reproduced here but not evidenced by here.
