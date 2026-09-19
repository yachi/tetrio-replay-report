# 2026-09-19 — narrative beats

Twenty matches, 150 rounds. **The largest session the corpus has, by 1.79x on rounds and
1.82x on matches**, and that size is the story rather than the scoreline.

## The scoreboard

* pinglamb 15-5 in matches [C001][G001], 91-59 in rounds [C010][G002].
* Every match went to whoever reached five rounds first — no exceptions in twenty [G003].
* 60.67% of the night's rounds are pinglamb's. That is **third** in the corpus, behind
  09-11's 62.75% and 09-17's 61.22% and above 08-09's and 08-19's 60.00%. In MATCHES its
  75.00% ties 07-28 for **fourth**, behind 08-09's sweep, 09-11's 85.71% and 09-03's
  83.33%. The two measures disagree, as they did on 09-11, so any sentence calling this
  the most one-sided night has to say which one it means — and on neither is it close to
  first.
* The night has no act structure. First ten matches 28-47, last ten 31-44, **over exactly
  75 rounds each** [C010]. Two windows of the same size, so the raw counts compare without
  cross-multiplying — the one case the repo's window rule allows. yachi trailed from match
  1 and closed the second half a little better than the first. Not 09-03's late collapse
  and not 09-11's early decision: a constant rate.

## The regimes — back to the middle

    attack per piece   won rounds    yachi .6478   pinglamb .6856   ->  +5.84%
                       lost rounds   yachi .5418   pinglamb .5765   ->  +6.39%

[C002] Ranked in their own columns over thirteen sessions the won-gap is **10th** (median
+7.66) and the lost-gap is **7th, the median exactly**. Ratio 0.91.

This is the 「roughly level」 class, with 07-24, 07-28 and 08-01 — and at 150 rounds it is
the best-powered instance that class has. **What it settles is 09-17.** That session was
the first with both gaps large (ranks 2 and 3) and was filed explicitly as one instance
that a thirteenth session could not promote to a class. The thirteenth session is this one
and it does not reproduce it.

Within a player [C003]: yachi +19.55%, pinglamb +18.93%. yachi wider, so seven of thirteen.
The two are **six-tenths of a point apart, the second-closest this column has been** —
07-28's 23.19 against 23.08 is closer at 0.11 — and its extremes are 24.7 points apart.

## The volume route, a ninth time — and the trap in reading it

[C005][C009] yachi threw **714 more pieces** and landed **476 fewer lines of attack**.
Session APP gap +11.16% [C004]; the surplus is 5.20% of pinglamb's count, so the route
covered under half the hole. Shortfall 5.96 pp.

Both 714 and 476 are the largest raw numbers the route has produced. **Both are largest
because the night is longest.** As rates the session is unremarkable: −5.36% of pinglamb's
attack total puts it 5th of thirteen, mid-table. C005 pins the percentage beside the count
for exactly that reason.

The same trap sits in the death tally [C006]: **15 topouts is the largest raw count any
player has recorded**, past 08-14's eleven — and 15 of 150 rounds is 10.0% against 08-14's
13.1%. The raw record and the rate disagree about whether this was a bad night for him.
The session's 24 in 150 is 16.0%, which ties 07-24 for mid-table.

## What does not happen

* **The per-match ordering does not separate.** yachi's five wins sit at −6.19%, −5.24%,
  +8.07%, +10.96%, +14.89%; pinglamb's fifteen run +2.43% to +24.36%. Three of yachi's are
  above six of pinglamb's. No C007 is minted and the slot is left empty, following 09-10
  and 09-11. The corpus count stays 3 of 13.
* **yachi leads attack per piece outright in m3 and m16**, so 「pinglamb leads every match」
  is false here; it holds in 7 of the 13 sessions.
* **No figure needs a 「得一局撐住」 annotation**, and this session sets the corpus minimum
  on that measurement — max `rel` 0.150, under 09-17's 0.226. Four of its five figures are
  the quietest version of themselves ever measured. That is NOT because the session is
  long: over thirteen sessions the rank correlation between round count and max `rel` is
  −0.06. It is because none of its five figures sits near zero.

## The night's rounds

* 最癲一局 is **m5r6** [G075], combined VS ~305.7. yachi won it and **led on every axis**
  [G097] — 08-09's and 08-19's shape — trailing only on the non-axis 清走 column. His APP
  in it is 0.909 against 0.697 [G098], and his DS/piece 0.252 against 0.281 [G099].
* Longest round **m18r2 at ~258 s** [G034], also the session's 236-line high [G033] — and
  pinglamb survived it.
* Shortest **m19r9 at ~11 s** [G035].
* m11 is the night's only 5-0 [G024][G067]; four matches went to a last round [G025].
* Longest run of rounds is pinglamb's seven, spanning m12 into m13 [G026].
* 32 All Clears, 18 pinglamb 14 yachi [G050] — and the PC column still does not decide a
  round: 25 rounds had exactly one player with a perfect clear and that player lost 7
  [G092][G094].

## The corpus finding this session produces

**CLAUDE.md's shortfall ordering ranks a RAW LINE COUNT against a RATE, and twelve sessions
within a factor of 1.8 of each other could not show it.** 09-19 is 1.79x the largest and
3.26x the smallest, and it breaks the raw ordering four ways at once while landing exactly
in its slot on the rate version. Measured both ways over all thirteen:

| axis | rho(12) | rho(13) | discordant pairs at 13 |
|---|---|---|---|
| raw lines | 0.9720 | **0.9231** | **7** |
| % of pinglamb's attack | 0.9930 | **0.9945** | **1** |

The rate axis had **zero** discordant pairs at nine, ten and eleven sessions, where the raw
axis already had two — both of them 09-03's, the miss the document has carried since. So
09-03 never missed its slot; the y-axis did. The single remaining discordant pair on the
rate axis is 08-09/09-17, the 0.03 pp adjacent swap the document already says the ordering
cannot resolve.

This is a units correction and not a re-fit: the x-axis is a rate, so the y-axis must be;
the percentage is **already written beside every raw figure** in the same paragraphs; and it
was strictly better on the old data, before this session existed.
