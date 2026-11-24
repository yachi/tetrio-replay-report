#!/usr/bin/env python3
"""Which dealt orders of bag 2 build each (ranked card, live class) of docs/tst-openers.html ->
analysis/tst-openers-tp-orders.json (constructed, quarantined, like analysis/tst-openers-tp.json).

  python3 pipeline/sim/emit-tst-orders.py [--out analysis/tst-openers-tp-orders.json] [--check]

For every ranked card and every live class, every tiling of that class holding the card's board is fed to
`pipeline/sim/tst-build-rs` with `ORDERS=1`: per dealt order of bag 2 (the i-th permutation of IOTSZJL as
`tst2bag-tp-rs`'s `perms()` builds them) the least bag-2 soft-drop cost with which a player with one hold slot, bag 1
already on the board and the kind bag 1 left out in the hold, builds that tiling and fires the TST. The class's string is
the per-order least over its tilings.

Before anything is written, every board's `cum` in analysis/tst-openers-tp.json is reproduced from these strings and the
board's bag-1 vector (analysis/tst-openers-tp-b1.json), at every class and every budget:
cum_b[k] = sum_s n_s * #(orders whose least cost over the live classes 0..k is <= b - s). A mismatch is a build error.
That pins the cumulative least over classes 0..k, which is the counter's figure; a class's own count for k > 0 on orders
an earlier class already builds is not pinned by it. The pair counts depend on which order index i is, so the binary
prints its own table (`PERMS=1`) and this script refuses to run unless it equals `perms()` below.

Per key `<card>#<class>` the artefact keeps `n` (orders that build it with bag-2 soft drops <= 0, 1, 2, any) and `pairs`:
for each pair (A, B) of IJLOSTZ in that order, how many of the orders that build it at any cost deal A before B (the
other side is n_inf minus it) and `w` (the set itself: bit i is order i, little-endian bytes, base64). Per card, `plans`
holds a decision list (yachi 2026-11-23: 「呢個組合先就砌呢個形，其他組合就砌另個形」): which class to build for which
dealt orders, read best PC rate first; see `plan()`. A rule is a conjunction of at most RULE_MAX precedences "A dealt
before B", minimal (no precedence can be dropped and it still hand only orders that build the class), picked by a greedy
cover. Since 2026-11-24 (schema /5, yachi: 「make sure 其他地方都冇呢個bug class」) a rule is checked against EVERY order
not yet decided, the ones no class builds included, and those orders are decided first by `nr` rules (→ 砌唔到): before,
rules were checked only against the buildable orders, so a rule or the else step could cover orders that build nothing.
The list is exact where `open` and `none_open` are 0. `no180` repeats `n`, `w` and `plans` with the binary run under `NO180=1`
(the engine's search without the 180 rotation, for every bag-2 piece; bag 1 stands on the board as before), checked to be
a subset of the 180 orders and never cheaper; the cum check does not apply to it. Nothing here is a corpus figure. `--check` re-runs it and fails unless the committed
artefact is byte-identical.
"""
import argparse, base64, hashlib, itertools, json, subprocess, sys, zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline import tst_openers_tp_page as TP  # noqa: E402

SIM = ROOT / "pipeline" / "sim"
CRATE = SIM / "tst-build-rs"
OUT = ROOT / "analysis" / "tst-openers-tp-orders.json"
JOBS = 4
KINDS = "IJLOSTZ"
PAIRS = list(itertools.combinations(KINDS, 2))
BUDGETS = (("0", 0), ("1", 1), ("2", 2), ("inf", 99))
RULE_MAX = 3
FULL = (1 << 5040) - 1


def perms():
    """IOTSZJL's permutations in `tst2bag-tp-rs`'s order (remove the i-th of the rest, recurse)."""
    out = []

    def r(p, rest):
        if not rest:
            out.append("".join(p))
            return
        for i in range(len(rest)):
            c = rest.pop(i)
            p.append(c)
            r(p, rest)
            p.pop()
            rest.insert(i, c)
    r([], list("IOTSZJL"))
    return out


def md5(b):
    return hashlib.md5(b).hexdigest()


def crate_md5():
    fs = [CRATE / "Cargo.toml"] + list((CRATE / "src").rglob("*.rs")) + list((SIM / "oracle-rs" / "src").rglob("*.rs"))
    h = hashlib.md5()
    for p in sorted(fs, key=lambda p: p.relative_to(SIM).as_posix()):
        h.update(f"{p.relative_to(SIM).as_posix()}\0{md5(p.read_bytes())}\n".encode())
    return h.hexdigest()


def enc(ps):
    return ";".join(f"{k}:{','.join(map(str, sorted(cs)))}" for k, cs in ps)


def lines(art, cat):
    """`<card>#<class>#<tiling>|bag1|bag2|tst` for every tiling of every live class of every ranked card, in order."""
    out = []
    for r, _ in TP.ranked(art, cat):
        bs = TP.piece_set(r["pieces"])
        for i in TP.live(r):
            si, left, p5 = r["classes"][i]
            s = cat[r["shapes"][si]]
            tst = ",".join(str(y * 10 + x) for x, y in sorted(s["tst"]))
            got = 0
            for j, t in enumerate(s["til"]):
                if not (t["B"] > 0 and t["left"] == left and t["p5"] == p5 and bs <= t["set"]):
                    continue
                b1 = [p for p in t["pieces"] if (p[0], tuple(sorted(p[1]))) in bs]
                b2 = [p for p in t["pieces"] if (p[0], tuple(sorted(p[1]))) not in bs]
                assert len(b1) == len(bs), f"{r['name']} class {i}: the tiling does not hold the board"
                out.append(f"{r['name']}#{i}#{j}|{enc(b1)}|{enc(b2)}|{tst}")
                got += 1
            assert got, f"{r['name']} class {i}: a live class with no tiling holding the board"
    return out


def run(ls, no180=False):
    subprocess.run(["cargo", "build", "--release", "--locked", "--manifest-path", str(CRATE / "Cargo.toml")], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    exe = str(CRATE / "target" / "release" / "tst-build")
    chunks = [ls[i::JOBS] for i in range(JOBS)]
    env = {"ORDERS": "1", "PATH": "/usr/bin:/bin", **({"NO180": "1"} if no180 else {})}
    go = lambda c: subprocess.run([exe], input="\n".join(c) + "\n", text=True, capture_output=True, check=True,
                                  env=env).stdout
    with ThreadPoolExecutor(JOBS) as ex:
        outs = list(ex.map(go, chunks))
    got = subprocess.run([exe], input="", text=True, capture_output=True, check=True,
                         env={"PERMS": "1", "PATH": "/usr/bin:/bin"}).stdout.split()
    assert got == perms(), "the binary's dealt-order table is not perms(): the pair counts would be read against the wrong orders"
    by = {}
    for o in outs:
        for l in o.splitlines():
            if l.strip():
                g = json.loads(l)
                by[g["id"]] = g["v"]
    assert set(by) == {l.split("|", 1)[0] for l in ls}, "the binary did not answer every line"
    return by


def cost(c):
    return 10 ** 6 if c == "." else int(c)


def least(a, b):
    return "".join(x if cost(x) <= cost(y) else y for x, y in zip(a, b))


def b1_vector(name):
    v = B1["vectors"][name]
    return zlib.decompress(base64.b64decode(v)).decode()


def check_cum(r, per_class):
    """Reproduce the board's cum from the class strings and its bag-1 vector (see the module docs)."""
    v1 = b1_vector(r["name"])
    assert len(v1) == 5040, f"{r['name']}: bag-1 vector length"
    ns = [v1.count(str(s)) for s in range(10)]
    nfeas = sum(ns)
    u = "." * 5040
    for k in range(len(r["classes"])):
        if k in per_class:
            u = least(u, per_class[k])
        for bk, b in BUDGETS:
            if bk == "inf":
                want = nfeas * sum(c != "." for c in u)
            else:
                want = sum(ns[s] * sum(c != "." and int(c) <= b - s for c in u) for s in range(b + 1))
            assert r["cum"][bk][k] == want, f"{r['name']} class {k} budget {bk}: cum {r['cum'][bk][k]} but the orders give {want}"


def prec_sets(P):
    """(A, B) -> bitmask of the orders that deal A before B, for every ordered pair of distinct kinds."""
    out = {}
    for a in KINDS:
        for b in KINDS:
            if a != b:
                out[a + b] = sum(1 << k for k, o in enumerate(P) if o.index(a) < o.index(b))
    return out


def conj(pre, c):
    m = FULL
    for p in c:
        m &= pre[p]
    return m


def terms_of(pre):
    """Every conjunction of at most RULE_MAX precedences that some order satisfies, as (precedences, bitmask)."""
    out = []
    for n in range(1, RULE_MAX + 1):
        for c in itertools.combinations(list(pre), n):
            m = conj(pre, c)
            if m:
                out.append((c, m))
    return out


def pc(x):
    return bin(x).count("1")


def cover(pre, terms, R, ok, tgt):
    """Greedy rules over R, the orders not yet decided: each a conjunction of at most RULE_MAX precedences every order of
    R it matches is in `ok` (no exception, buildable or not), the one taking the most orders of `tgt` (fewest precedences,
    then first, on a tie), cut to a minimal conjunction, until none takes any. Returns (rules, R left)."""
    rs = []
    while tgt:
        best, bn = None, 0
        for c, m in terms:
            if m & R & ~ok:
                continue
            g = pc(m & tgt)
            if g > bn or (g == bn and g and len(c) < len(best[0])):
                best, bn = (c, m), g
        if not best:
            break
        c = list(best[0])
        for p in list(c):
            d = [q for q in c if q != p]
            if d and not conj(pre, d) & R & ~ok:
                c = d
        m = conj(pre, c)
        rs.append([sorted(c), pc(m & tgt)])
        R &= ~m
        tgt &= ~m
    return rs, R


def plan(pre, terms, ws):
    """The card's decision list over its live classes `ws` = [(class index, w), ...] in the artefact's class order (best
    PC rate first), read top to bottom over R, the orders no earlier step has decided (all 5040 at the start). First the
    orders no class builds: rules (`nr`) every order of R they match builds nothing. Then each class in turn: when every
    order in R builds it, it is the last step ("else") and the list ends; otherwise rules every order of R they match
    builds the class. A rule never matches an order of R that does not do what it says, buildable or not (until
    2026-11-24 a rule was checked only against the buildable orders, so it could match orders nothing builds). A rule is
    [precedences, how many orders of R it decides]; a step is [class index, rules, its total]. open is the buildable
    orders no step decides, none the orders no class builds, none_open those of them no `nr` rule decides."""
    B = 0
    for _i, w in ws:
        B |= w
    nb = FULL & ~B
    nr, R = cover(pre, terms, FULL, nb, nb)
    steps, els = [], None
    for i, w in ws:
        if not R & B:
            break
        if not R & ~w:
            els = [i, pc(R)]
            R = 0
            break
        rs, R = cover(pre, terms, R, w, w & R)
        if rs:
            steps.append([i, rs, sum(n for _c, n in rs)])
    return {"nr": nr, "steps": steps, "else": els, "open": pc(R & B), "none": pc(nb), "none_open": pc(R & nb)}


def build():
    art, cat = TP.load_inputs(str(ROOT))
    ls = lines(art, cat)
    P = perms()
    pos = [{c: i for i, c in enumerate(o)} for o in P]

    def classes(by):
        cls = {}
        for l in ls:
            card, i, _j = l.split("|", 1)[0].split("#")
            key = (card, int(i))
            cls[key] = least(cls.get(key, "." * 5040), by[l.split("|", 1)[0]])
        return cls
    cls = classes(run(ls))
    cls0 = classes(run(ls, no180=True))
    pre = prec_sets(P)
    terms = terms_of(pre)
    orders, plans, orders0, plans0 = {}, {}, {}, {}
    for r, _ in TP.ranked(art, cat):
        per = {i: cls[(r["name"], i)] for i in TP.live(r)}
        check_cum(r, per)
        for i, s in per.items():
            W = [k for k, c in enumerate(s) if c != "."]
            n = [sum(c != "." and int(c) <= b for c in s) for _bk, b in BUDGETS]
            pairs = [sum(pos[k][a] < pos[k][b] for k in W) for a, b in PAIRS]
            w = sum(1 << k for k in W)
            orders[f"{r['name']}#{i}"] = {"n": n, "pairs": pairs,
                                         "w": base64.b64encode(w.to_bytes(630, "little")).decode()}
        plans[r["name"]] = plan(pre, terms, [(i, int.from_bytes(base64.b64decode(orders[f"{r['name']}#{i}"]["w"]), "little"))
                                             for i in sorted(per)])
        per0 = {i: cls0[(r["name"], i)] for i in TP.live(r)}
        for i, s in per0.items():
            # without the 180 the engine reaches a subset of the cells, so an order can only get dearer or be lost
            assert all(cost(a) >= cost(b) for a, b in zip(s, per[i])), f"{r['name']} class {i}: no-180 cheaper than with 180"
            W = [k for k, c in enumerate(s) if c != "."]
            w = sum(1 << k for k in W)
            orders0[f"{r['name']}#{i}"] = {"n": [sum(c != "." and int(c) <= b for c in s) for _bk, b in BUDGETS],
                                          "w": base64.b64encode(w.to_bytes(630, "little")).decode()}
        plans0[r["name"]] = plan(pre, terms, [(i, int.from_bytes(base64.b64decode(orders0[f"{r['name']}#{i}"]["w"]), "little"))
                                              for i in sorted(per0)])
    with open(ROOT / "analysis" / "tst-openers-tp.json", "rb") as f:
        tp = md5(f.read())
    return {
        "schema": "tst-openers-tp-orders/5",
        "report_eligible": False,
        "constructed": True,
        "about": ("Per ranked card and live class of docs/tst-openers.html: of the 5040 dealt orders of bag 2 (bag 1 on the "
                  "board, the kind it left out in the hold, one hold slot), how many build a tiling of that class and fire "
                  "the TST with bag-2 soft drops <= 0, 1, 2 and any (n), and per pair (A, B) of IJLOSTZ how many of the "
                  "orders that build it at any cost deal A before B (pairs). Reproduces analysis/tst-openers-tp.json's cum "
                  "at every class and budget with the board's bag-1 vector. w is that set (bit i = order i of the pairs' "
                  "order table, little-endian, base64). plans holds per card a decision list over its live classes, best PC "
                  "rate first: each step a class and rules (minimal conjunctions of at most 3 precedences 'A dealt before "
                  "B') under which, among the orders some class builds and no earlier step decided, every order builds "
                  "that class, each with how many such orders it hands the class; else the class every order still "
                  "undecided builds; open the buildable orders no step decides; none the orders no class builds. no180 "
                  "holds the same orders (n, w) and plans with the engine's 180 rotation removed for every bag-2 piece "
                  "(bag 1 stands on the board as before); its orders are a subset of the 180 ones and never cheaper."),
        "rule_max": RULE_MAX,
        "budgets": [bk for bk, _ in BUDGETS],
        "pairs": ["".join(p) for p in PAIRS],
        "md5": {"crate": crate_md5(), "tst_openers_tp": tp},
        "orders": orders,
        "plans": plans,
        "no180": {"orders": orders0, "plans": plans0},
    }


def dump(a):
    return json.dumps(a, ensure_ascii=False, separators=(",", ":"), sort_keys=False) + "\n"


with open(ROOT / "analysis" / "tst-openers-tp-b1.json", encoding="utf-8") as _f:
    B1 = json.load(_f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    s = dump(build())
    if a.check:
        if Path(a.out).read_text(encoding="utf-8") != s:
            sys.exit(f"{a.out} is stale: re-run pipeline/sim/emit-tst-orders.py")
        print(f"{a.out} is current")
        return
    Path(a.out).write_text(s, encoding="utf-8")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
