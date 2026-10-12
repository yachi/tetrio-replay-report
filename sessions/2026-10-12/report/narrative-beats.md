# 2026-10-12 — narrative beats

Eight matches, 55 rounds. The seventeenth session, in date order and in arrival.

## The scoreboard

* pinglamb 5-3 in matches [C001][G001], 30-25 in rounds [C010][G002]. Every match went to
  whoever reached five first [G003], and **no match went to a ninth round** — the scores
  [G058] are 0-5, 5-2, 5-0, 1-5, 3-5, 3-5, 5-3, 3-5. 09-11 is the only other session with none.
* **A 5-0 each way** [G012]: pinglamb in m1, yachi in m3. 09-18 and 10-03 are the two earlier
  sessions with a shutout in both directions.
* yachi won nine rounds in a row across m2 and m3 [G013].

## The night in three stretches — C010

    matches  1-3    10-7    (17 rounds)   two of three yachi's — series 2-1
    matches  4-6     7-15   (22)          all three pinglamb's  <- his worst rate of the three windows
    matches  7-8     8-8    (16)          one each

[C010] pins the counts and the order of the rates by cross-multiplication — the stretches differ
in size, so the raw counts are never compared across them. [C001] pins the match winners. **The
whole margin of the series is m4-m6**: m4 went 1-5 after 1-1 [C014], m5 3-5 after yachi clawed
back from 1-4 to 3-4 [C015], m6 3-5 after yachi led 3-0 and lost five straight [C016].

## The per-match ordering SEPARATES — C007

Order the eight by pinglamb's per-piece advantage:

    m3 -28.02 Y   m7 +3.13 Y   m2 +4.54 Y   |   m5 +11.97 P   m4 +15.34 P   m6 +20.12 P
    m8 +29.45 P   m1 +30.99 P

yachi's three wins are the three smallest gaps (each under +5%), pinglamb's five the five
largest (each over +11%) [C007]. Three wins among eight fall that way by chance with
probability **1/C(8,3) = 1 in 56** — the intermediate tier, between 09-17's 1 in 21 and 08-19's
1 in 120, and far below 10-03's 1 in 38 760. Filed by its probability, not its win count. The
count of separating sessions becomes five of seventeen (08-19, 08-25, 09-17, 10-03, 10-12). The
cut falls between +4.54% and +11.97%, a void 7.4 points wide; a different place again from the
other four cuts, so there is still no corpus-wide threshold.

**The sign is not what separates** [C019][C020]. pinglamb's attack per piece is higher in seven of
the eight; in m2 and m7 that higher side lost, because yachi placed more pieces and landed more
attack. **The higher attack total won all eight** [C019]. So 「pinglamb leads every match」 fails
here — once, in m3 — and m3 is a 38%-plus yachi lead [C020], **the largest per-match lead yachi
holds anywhere in the corpus** (the next is 09-18's m4, where pinglamb's per-piece rate is 18.26%
below his).

## The volume route — C004, C005, C009

[C004] Session APP gap +13.50% (third-largest of seventeen, behind 09-17 and 08-09). [C009] yachi
threw 9.92% more pieces — 468 more [C005]. A surplus buys back exactly 100·(surplus/other − 1)
points of APP gap, so it bought 9.92 against 13.50: **shortfall about 3.58**, between 07-24's
2.66 and 08-25's 3.82. The attack total finished **102 lines, 3.15% of pinglamb's total**, in
pinglamb's favour [C005] — between 07-24's −2.42% and 08-25's −3.42% on the rate axis, and
between −72 and −176 on the raw axis, so in its slot on both. `check_loo` puts the attack
difference at `rel` 0.343 (m8r7 → −67), under THRESHOLD; it is not a published annotation.

In-game score is pinglamb 1 016 804 against 1 011 945 [G064]. That difference is NOT read as a
finding: leave-one-out moves it by 10 707 (m2r4), more than twice its size.

## The regimes — ceilings close, floors apart

    attack per piece   won rounds    yachi .6814   pinglamb .7301   ->   +7.14%
                       lost rounds   yachi .5402   pinglamb .6237   ->  +15.44%

[C002] Ranked in their own columns over seventeen sessions the won-gap is **10th** (median
+7.66) and the lost-gap **4th** (median +6.39). Won/lost ratio 0.46 — the 07-22 shape
(+5.8/+12.8, 0.45), with 08-19 and 08-25. `check_loo`: won-gap 0.318 (m5r7), lost-gap 0.156
(m8r5), session gap 0.093 — none crosses THRESHOLD.

Within a player [C003]: yachi +26.11%, pinglamb +17.05% — yachi the wider, his second-widest of
seventeen behind 08-09's +31.5.

## Topouts [C006]

4 yachi, 4 pinglamb — 8 of 55 rounds. The second even split in the corpus, after 07-24's 4:4.
47 rounds ended in a garbage smash [G063].

## The night's rounds

* 最癲一局 is **m8r5** [G061], combined VS ~308.7 — yachi won it while trailing on max spike
  [G083] and on attack per piece (0.648 against 0.787 [G084]); he was faster and cleared more
  [G081][G082][G085].
* Longest round **m5r7 at ~231 s** [G021], yachi's 229 lines the session high [G020]; yachi
  survived. Shortest **m4r1 at ~11 s** [G022].
* yachi's biggest spike of 21 (m5r5) [G016] and B2B of 11 (m6r1) [G018]; pinglamb's combo of 9
  (m8r1) [G017].
* 11 All Clears, 6 yachi 5 pinglamb [G037]. Rounds where only yachi cleared: 4, lost 2 [G078];
  only pinglamb: 3, lost 1 [G080].
* KPP: yachi 3.591, pinglamb 3.683, pinglamb 2.54% above [C008].
