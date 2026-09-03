# 2026-09-03 — narrative beats

Six matches, 46 rounds. pinglamb takes the series 5-1 [G001] on a round split of 27-19 [G002].
Every match was first-to-5 [G003].

## The shape of the night — it breaks in half at m3

yachi won only match 3 [C001]. But the scoreline reads wider than the night was: **through the
first three matches the round count is 13-12 to yachi**, and over the last three it is 6-15
[C010]. Two matches went to a deciding final round [G010] and pinglamb took both — m1 on a VS
of ~122.1 against ~112.9 [G057], m2 on ~134.3 against ~74.2 [G058]. The first was taken, the
second was a collapse.

pinglamb's longest run is six rounds, spanning m1 into m2 [G011].

## The finding — the half that broke is not the half a reader expects

The obvious explanation for a 13-12 becoming a 6-15 is that pinglamb started hitting harder.
He did not. Attack per piece, by window:

    m1-m3   yachi .5785   pinglamb .6303   →  +8.95%
    m4-m6   yachi .5685   pinglamb .6269   → +10.27%

Both players' APP is flat to within two percent of itself and the gap widens by about one and a
third points [C011], while the round split inverts by ten. **The one column that changes sign at
the break is downstacking**:

    m1-m3   yachi .1983   pinglamb .1880   →  pinglamb at 94.8% of yachi
    m4-m6   yachi .1858   pinglamb .2145   →  pinglamb at 115.4% of yachi

C012 pins that crossover. Two things must be said with it or the section overclaims:

1. **It is a description of the second half, not its cause.** The same rounds carry both facts,
   and one session is one observation. What C012 buys is narrower and still worth having: the
   collapse *cannot* be told as an attacking story, because C011 shows the attacking columns
   did not move.
2. **It is stated as two cross-multiplied bounds, never as a single "+20 points".** The four
   rates have four different denominators; a difference of ratios would be a number no lemma
   here proves.

## The volume route — fifth failure, and the session that breaks its ordering

yachi threw 207 more pieces for 120 fewer lines of attack [C005]. The surplus is 4.75% of
pinglamb's count, so the route can return 4.75 pp [C009] against a 9.54 pp gap [C004] — a
shortfall of 4.79 pp.

**This is the first session added since the corpus's shortfall ordering was written down, and it
does not land in its slot.** Ranked by shortfall, the eight previous sessions ranked identically
by attack difference. A shortfall of 4.79 sits between 2026-08-14's 4.61 (−206 lines) and
2026-08-19's 6.89 (−236), so the ordering predicts an attack difference in that band. Measured:
**−120**, which is outside it on the other side — where a shortfall near 3 belongs. Spearman
falls from 1.000 to 0.950 (exact permutation p = 0.0002).

So the relationship survives as a strong monotone one and the *perfect* ordering does not. That
distinction is the whole of the correction: the route still works, the shortfall still predicts
the outcome better than the surplus does, and the claim that the ranking is exact was a
statement about eight points that the ninth refutes. Nothing in this session's ledger states a
position in that ordering — C005 and C009 pin the arithmetic only, because the ordering is a
corpus-level claim and this ledger covers one session.

## What did NOT reproduce

**The per-match separation.** 2026-08-19 and 2026-08-25 each ordered their matches by pinglamb's
APP advantage and had the match winner fall out perfectly. Here it interleaves: yachi's single
win (m3, +6.61%) sits between pinglamb's m4 (+0.58%) and m2 (+7.98%). Two of nine sessions
separate and seven do not; this is one of the seven, which refutes nothing that the six earlier
interleaving sessions had not already established. There is deliberately no C007 this session —
a weakened version that "nearly" separates would be fitting a claim to data that does not carry
it.

## The two regimes

Split every round by who won it and pool attack over pieces:

    rounds won     yachi 1231/1945 = .6329    pinglamb 1773/2602 = .6814   →  +7.7%
    rounds lost    yachi 1391/2623 = .5303    pinglamb  969/1759 = .5509   →  +3.9%

Ceilings apart, floors close [C002] — the reverse of 2026-08-25's shape (+5.0 / +17.5) and of
the corpus's most common one. Read against the whole corpus this is not a new shape but the
mildest form of an existing one: at +3.8 points of difference between the two gaps it sits
beside 2026-07-24 (+3.5) in the "roughly level" group. What still does not happen in any of the
nine sessions is the shape a reader keeps expecting — both gaps large together.

Within each player, both separate their own won rounds from their lost ones [C003]: yachi by
+19.3%, pinglamb by +23.7%. pinglamb is the wider of the two, ending the two-session run in
which yachi was.

## The flat columns

**Keypresses per piece is the flattest it has been in the corpus**: yachi 3.619, pinglamb 3.609,
under 0.3% apart [C008], and neither player's KPP moves by 0.06 between his won and lost rounds
[G067][G068].

**So is the death tally.** Seven rounds ended in a topout, 3 yachi's and 4 pinglamb's [C006] —
against 9:4 the session before. The full series is now y:p = 8:3 · 4:4 · 5:4 · 6:2 · 0:4 · 11:2 ·
4:3 · 9:4 · 3:4. Nine values with no run of three in one direction: this column swings every
session and predicts nothing, which is what the corpus already said at eight.

## Records and the rest

- The most intense qualifying round is m1r7, combined VS ~302.8 [G059]. pinglamb won it while
  trailing on three axes — PPS, maxspike and lines [G081] — and led on both per-piece rates:
  attack ~0.958 against ~0.699 [G082], downstack ~0.268 against ~0.252 [G083].
- Longest round: m3r6 at ~210 s, and the same round is the session's highest line count at 198
  [G018][G019]. yachi survived it, in the one match he won.
- Shortest: m4r3 at ~13 s [G020], which is also the unqualified APM peak at ~101.0 — a 13-second
  round, so not a record [G073].
- VS decides all 46 rounds with no exception [G022], the ninth session running. Kills equal round
  wins by construction and are not a second signal [G036].
- Perfect Clears: pinglamb 6, yachi 4 [G035]. In the 2 rounds where only yachi had one he lost
  none [G076]; in the 4 where only pinglamb did he lost one [G078].
- Clear-type split: yachi's Quads 203 against 167 [G032], pinglamb's T-spin doubles 224 against
  185 [G033] and triples 43 against 28 [G034]. Spike runs the other way — yachi's ceiling 16
  against 12 [G049], and 11 rounds over 12 lines against 7 [G052].
