#!/usr/bin/env python3
"""Emit analysis/tst-openers-tp-replay.json: which bag-1 board each player really built in every round, against what the
TST opener ranking (analysis/tst-openers-tp.json) says is best for the bag-1 order that round dealt. Constructed,
quarantined: the replays are the corpus's, but the verdicts (a board's chance of a bag-3 Perfect Clear) come from the
constructed ranking, so the artefact says `report_eligible: false`, carries no claim id and no badge.

  python3 pipeline/sim/emit-tst-opener-choices.py [--out analysis/tst-openers-tp-replay.json] [--check]

Pure Python (no numpy; CI's docs job has none), a few seconds. `--check` rebuilds and fails unless the committed artefact
is byte-identical.

METHOD, per player-round of every `sessions/*/sim/replay-facts.json`:

  order     o = the position of `seq[:7]` in `itertools.permutations('IOTSZJL')`, the counter's first-bag recursion order,
            the index the b1 vectors (`analysis/tst-openers-tp-b1.json`) are laid out by.
  board     the first six locks decoded with `replay_section.decode_boards` (`queue_states` gives the hold). Matched when
            no lock of the six cleared a line or took garbage, the six placed pieces plus the held one are the seven
            bag-1 pieces, and the six placed pieces' cells equal a KEPT board of the ranking exactly (this hand: no mirror).
  chance    J(board, o) = the board's soft-drop-cost table `j_tables` at the cost `vec[board][o]` (the least soft drops
            building the board from that order, `.` = cannot); J / 5040^2 is the chance that a random bag 2 finishes a
            two-bag TST shape and bag 3 then clears a Perfect Clear. It says nothing about who won the round: it
            assumes the player is going for TST then a bag-3 PC.
  best      three comparisons, each over J at the budget (a hit is EQUAL J, so two boards with the same chance tie):
            repertoire = the best of the boards that player built at least `REPERTOIRE_MIN` times in the whole corpus
            (and the board actually built, so the actual is never below the best); global = the best of every kept board
            (a ceiling, never a miss); family = the best hold-swap variant of the layouts the built board is a variant
            of (`families.list`).

Every player-round gets exactly one STATUS and the statuses partition the total:

  matched              the board is a kept board (the only status with figures)
  not_kept             a six-piece board with the seventh held and no clear or garbage, not among the kept boards: below
                       the 36% prune or holding no TST shape, and the two cannot be told apart from here
  garbage_or_clear     a line clear or garbage inside the first six locks
  seven_placed_no_hold all seven bag-1 pieces placed in seven clean locks with the hold empty; matched by LAYOUT
                       against `families.list` (`f` is the family index, null when no listed family holds it)
  hold_not_bag1        the hold was empty after six locks and the seventh piece was held, or went with a clear or garbage
                       or the round ended: no board the ranking can read
  short_round          fewer than six locks

Rows store integers only (J numerators out of 5040^2); totals, means and hits are derived by the page and the test.
"""
import argparse, hashlib, importlib.util, itertools, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline import replay_section as RS  # noqa: E402

SIM = ROOT / "pipeline" / "sim"
OUT = ROOT / "analysis" / "tst-openers-tp-replay.json"
SCHEMA = "tst-openers-replay/1"
REPERTOIRE_MIN = 3
NEAR_DEN = 50                   # near = 0 < loss <= N2 / NEAR_DEN (2 points; at budget 2 no miss is under 1)
FIRST = 6
SHOWN = 5
BKEYS = ["0", "1", "2", "inf"]
STATUSES = ["matched", "not_kept", "garbage_or_clear", "seven_placed_no_hold", "hold_not_bag1", "short_round"]
COLUMNS = ["actual", "rep_j", "rep_board", "glob_j", "glob_board", "fam_j", "fam_board"]
QUARANTINE = ("the replays are the corpus's; every chance and every best board comes from the constructed T-placed ranking "
              "(analysis/tst-openers-tp.json): nobody played those boards, no claim id, no badge")
MEANS = ("one row per player-round: the bag-1 order dealt (index into itertools.permutations('IOTSZJL')), a status, the bag-1 "
         "board built when it is a kept board, and per soft-drop budget the integer chance numerators (out of 5040^2) of the "
         "built board, the best board of the player's own repertoire, the best kept board, and the best hold-swap variant of "
         "the built board's layouts; a chance assumes the player is going for a TST then a bag-3 Perfect Clear")


def _load_tp():
    spec = importlib.util.spec_from_file_location("emit_tst_openers_tp", SIM / "emit-tst-openers-tp.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def md5(b):
    return hashlib.md5(b).hexdigest()


def perm_index():
    return {"".join(p): i for i, p in enumerate(itertools.permutations("IOTSZJL"))}


def board_set(cells_by_kind):
    return frozenset((k, tuple(sorted(cs))) for k, cs in cells_by_kind.items())


def cells_of(board_rows):
    """{kind: [y * 10 + x]} of a decoded board ([y-UP][x] of a letter, 'G' or None); a garbage cell is returned under 'G'."""
    out = {}
    for y, row in enumerate(board_rows):
        for x, v in enumerate(row):
            if v:
                out.setdefault(v, []).append(y * 10 + x)
    return out


def classify(data, rnd, p, kept, layouts):
    """(status, board name | None, family index | None, seven-piece layout string | None) of one player-round."""
    seq, locks = rnd["seq"], p["locks"]
    if len(locks) < FIRST:
        return "short_round", None, None, None
    dec = list(RS.decode_boards(data, seq, locks[:FIRST], SHOWN))
    if any(full for _pc, full, _bd in dec) or any(lk[4] for lk in locks[:FIRST]):
        return "garbage_or_clear", None, None, None
    qs = RS.queue_states(seq, locks[:FIRST + 1], SHOWN)
    hold = qs[FIRST - 1][1]
    if hold:
        placed = [qs[i][0] for i in range(FIRST)]
        assert sorted(placed + [hold]) == sorted(seq[:7]), "six placed + hold must be the seven bag-1 pieces"
        cs = cells_of(dec[-1][2])
        assert sorted(cs) == sorted(placed)
        name = kept.get(board_set(cs))
        return ("matched", name, None, None) if name else ("not_kept", None, None, None)
    if len(locks) > FIRST:
        dec7 = list(RS.decode_boards(data, seq, locks[:FIRST + 1], SHOWN))
        if (not any(full for _pc, full, _bd in dec7) and not any(lk[4] for lk in locks[:FIRST + 1])
                and qs[FIRST][1] == "" and sorted(qs[i][0] for i in range(FIRST + 1)) == sorted(seq[:7])):
            cs = cells_of(dec7[-1][2])
            return ("seven_placed_no_hold", None, layouts.get(board_set(cs)),
                    "/".join(f"{k}:{','.join(map(str, sorted(v)))}" for k, v in sorted(cs.items())))
    return "hold_not_bag1", None, None, None


class Chances:
    """J(board, order, budget) and the three bests, from the committed ranking and first-bag vectors."""

    def __init__(self, tp, art, b1):
        self.art = art
        self.names = [b["name"] for b in art["boards"]]
        self.idx = {n: i for i, n in enumerate(self.names)}
        vec = tp.b1_vectors(b1)
        self.infeas = tp.INFEAS
        self.vec = [vec[n] for n in self.names]
        self.tab = []
        for b in art["boards"]:
            t = tp.j_tables(b, tp.solve_D(b["cum"], vec[b["name"]]))
            self.tab.append({bk: t[bk][0] for bk in BKEYS})
        self.fams_of = {}
        for fi, f in enumerate(art["families"]["list"]):
            for n in f["variants"]:
                self.fams_of.setdefault(self.idx[n], []).append(fi)
        self._glob = {}

    def j(self, bi, o, bk):
        return self.tab[bi][bk][self.vec[bi][o]]

    def best(self, o, bk, cands, actual):
        """(J, board index) of the best candidate; the actual board wins a tie, else the earlier board."""
        bj, bb = self.j(actual, o, bk), actual
        for c in sorted(cands):
            jc = self.j(c, o, bk)
            if jc > bj:
                bj, bb = jc, c
        return bj, bb

    def glob(self, o, bk):
        key = (o, bk)
        if key not in self._glob:
            bj, bb = -1, -1
            for bi in range(len(self.names)):
                jc = self.j(bi, o, bk)
                if jc > bj:
                    bj, bb = jc, bi
            self._glob[key] = (bj, bb)
        return self._glob[key]


def build(root=ROOT):
    tp = _load_tp()
    art_raw = (root / "analysis" / "tst-openers-tp.json").read_bytes()
    b1_raw = (root / "analysis" / "tst-openers-tp-b1.json").read_bytes()
    art, b1 = json.loads(art_raw), json.loads(b1_raw)
    assert art["schema"] == "tst-openers-tp/4" and art["report_eligible"] is False
    ch = Chances(tp, art, b1)
    pidx = perm_index()
    kept = {board_set({k: cs for k, cs in b["pieces"]}): b["name"] for b in art["boards"]}
    layouts = {frozenset((k, tuple(sorted(cs))) for k, cs in f["pieces"]): fi for fi, f in enumerate(art["families"]["list"])}
    rows, replay_md5, sessions = [], {}, []
    for path in sorted((root / "sessions").glob("*/sim/replay-facts.json")):
        raw = path.read_bytes()
        data = json.loads(raw)
        sess = data["session"]
        sessions.append(sess)
        replay_md5[sess] = md5(raw)
        for rnd in data["rounds"]:
            o = pidx["".join(rnd["seq"][:7])]
            for p in rnd["players"]:
                st, name, fam, lay = classify(data, rnd, p, kept, layouts)
                rows.append({"s": sess, "m": rnd["match"], "r": rnd["round"], "u": p["user"], "o": o, "st": st,
                             "b": name, "f": fam, "l": lay})
    # repertoire: the boards a player built at least REPERTOIRE_MIN times, this hand, over every matched round
    built = {}
    for r in rows:
        if r["st"] == "matched":
            d = built.setdefault(r["u"], {})
            d[r["b"]] = d.get(r["b"], 0) + 1
    rep = {u: sorted(ch.idx[n] for n, c in d.items() if c >= REPERTOIRE_MIN) for u, d in sorted(built.items())}
    for r in rows:
        if r["st"] != "matched":
            r["j"] = None
            continue
        a = ch.idx[r["b"]]
        fam = sorted({ch.idx[n] for fi in ch.fams_of.get(a, []) for n in art["families"]["list"][fi]["variants"]} - {a})
        # a board that was played must be buildable from the order it was dealt (checks the order index)
        assert ch.vec[a][r["o"]] != ch.infeas, f"{r['s']} m{r['m']}r{r['r']} {r['u']}: built a board its order cannot build"
        j = {}
        for bk in BKEYS:
            aj = ch.j(a, r["o"], bk)
            rj, rb = ch.best(r["o"], bk, rep[r["u"]], a)
            gj, gb = ch.glob(r["o"], bk)
            if gj == aj:
                gb = a
            fj, fb = ch.best(r["o"], bk, fam, a)
            j[bk] = [aj, rj, ch.names[rb], gj, ch.names[gb], fj, ch.names[fb]]
        r["j"] = j
    return {
        "schema": SCHEMA, "report_eligible": False, "constructed": True, "quarantine": QUARANTINE, "means": MEANS,
        "params": {"repertoire_min": REPERTOIRE_MIN, "near_den": NEAR_DEN, "first_locks": FIRST, "budgets": BKEYS,
                   "columns": COLUMNS, "statuses": STATUSES, "n2": 5040 * 5040},
        "md5": {"tp": md5(art_raw), "b1": md5(b1_raw), "emitter": md5((SIM / "emit-tst-opener-choices.py").read_bytes()),
                "replay_facts": replay_md5},
        "sessions": sessions,
        "repertoire": {u: [ch.names[i] for i in v] for u, v in rep.items()},
        "rows": rows,
    }


def text(art):
    return json.dumps(art, separators=(",", ":"), ensure_ascii=False, sort_keys=True) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    t = text(build())
    if a.check:
        if Path(a.out).read_text() != t:
            sys.exit(f"{a.out} is not what the emitter builds from the committed inputs (re-run without --check)")
        print(f"ok: {a.out} rebuilds byte for byte")
        return
    Path(a.out).write_text(t)
    import collections
    c = collections.Counter(r["st"] for r in json.loads(t)["rows"])
    print(f"wrote {a.out}: {sum(c.values())} player-rounds, {dict(c)}", file=sys.stderr)


if __name__ == "__main__":
    main()
