"""開局 / 中盤手法 標記 — the replay pages' opener and mid-game technique key moments.

    python3 -m pipeline.replay_labels --selftest     # its refusals, each planted

The whole-night replay page (`replay_page`, `docs/<date>-replay.html`) lists a round's key moments
under the player: T-spins, big attacks, garbage, the check boundary. This module adds two kinds,
read out of artefacts that already exist and are already gated:

* `opener` — from each opener route site's corpus artefact (`analysis/<opener>-facts.json`, the
  classifier `route-facts.ts`): the bag-1 board, the bag-1 T-spin, the bag-2 board, every later
  snapshot board and a drawn Perfect Clear, each at the lock the classifier matched it.
* `technique` — from each mid-game technique site's artefact (`analysis/<technique>-facts.json`,
  `technique-facts.ts`): every hit, at the merged position just BEFORE its T, i.e. on the board the
  T went into, which is where the technique pages' own case links open.

The sites are `pipeline.sites`' lists, the same ones `bin/build-docs` renders the pages from, and
every round's labels link to those pages.

WHAT A LABEL SAYS, AND WHAT IT DOES NOT. 「對到」 means the board equals a transcribed drawing by
occupancy (a route page) or the technique's window fires (a technique page). It is never a claim
about what the player meant to build, and no label is no evidence that a player did not play an
opener: only these pages' drawings are compared, exactly. One board can match several pages (stick
spin and SDPC Spin share bag 1; Kaidan and Shachiku Train share hits), and then every match is
listed, joined in one moment — nothing is chosen between them.

ONLY INSIDE THE VERIFIED PREFIX. A route stage past `verified_to` is not labelled: the board there
is the simulator's with nothing checking it. Every technique hit is inside the prefix by
construction (its denominator is the scored T-spins).

RE-DERIVED, NOT COPIED. Every label is re-checked against the replay page's OWN decode
(`replay_section.decode_boards`, the decoder the page's player mirrors), not the TS digest the
classifier read: a route board must equal the node's drawing by occupancy in the recorded hand, a
bag-1 T-spin must put a T with a full spin into the drawing's U cells, a Perfect Clear must empty the
board, and a technique's window must fire (`technique_transcription.window_fires`, the Python twin
of the TS matcher) on the board before the T, in the hit's hand, with the T a full spin clearing the
variant's lines. A label that fails is a build error, never a dropped label, so `bin/build-docs
--check` re-runs every one of these on every push. `--selftest` plants each kind of wrong label and
fails unless every one is refused.

QUARANTINE. Same tier as the page: simulator output, no claim ids, no ✓. The artefacts must say
`report_eligible: false`, and every artefact must cover the session it labels — a session missing
from one is a refusal (the artefact is stale), never a round with fewer labels.
"""
import argparse
import json
import os
import re
from types import SimpleNamespace

from pipeline import replay_section as RS

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAG_WORDS = "零一二三四五六七八九"

# One template per label shape; phrases sharing a (player, lock, side, template) are joined into ONE
# moment, which is how several pages matching one board are listed without choosing between them.
T_BOARD = "{user} 盤面對到 {x}嘅圖"
T_SPIN = "{user} 呢粒 T 落喺 {x}圖上嘅 T-spin 位"
T_PC = "{user} 嘅全消對到 {x}嘅全消圖"
T_TECH = "{user} 落 T 之前個形對到 {x}"
JOIN = "／"
SPIN_WORDS = {(1, "TSS"): "TSS", (2, "TSD"): "TSD", (3, "TST"): "TST"}

# The page's method note carries this; `replay_page.audit` demands it whenever the page has a label.
SENTENCE = ("「開局對到」同「個形對到」嘅標記，嚟自定式路線頁同中盤手法頁："
            "淨係喺已核範圍入面、盤面同嗰版畫嘅圖逐格一樣（中盤手法就係個窗口全中）先會標，"
            "同一個盤對到幾版就全部列晒，唔會揀邊個。<strong>冇標唔代表冇打</strong>，"
            "只係同呢幾版畫嘅樣唔一樣；標咗亦唔係講玩家心入面想砌乜。")
LINKS_LEAD = "呢局對到嘅頁："
_HREF = re.compile(r"^[a-z0-9-]+\.html$")


def _need(cond, msg):
    if not cond:
        raise SystemExit(f"replay_labels: {msg}")


# ---------------------------------------------------------------- sources

def _read(repo, rel):
    with open(os.path.join(repo, rel), encoding="utf-8") as fh:
        return json.load(fh)


def load_sources(repo=REPO):
    """Every site's artefact and drawings, read once: (route sources, technique sources)."""
    from pipeline.sites import ROUTE_SITES, TECHNIQUE_SITES   # late: the sites import replay_page
    routes = []
    for site in ROUTE_SITES:
        art = _read(repo, site.FACTS_REL)
        tr = _read(repo, site.ROUTES_REL)
        _need(art.get("report_eligible") is False, f"{site.FACTS_REL} must declare report_eligible: false")
        strip = str(art["rules"].get("bag2_garbage", "")).startswith("strip")
        routes.append(SimpleNamespace(
            name=site.PROSE["opener_name"], href=site.OVERVIEW, rel=site.FACTS_REL, art=art, strip=strip,
            nodes={n["id"]: n for n in tr["nodes"]}, sessions=set(art["sessions"])))
    techs = []
    for site in TECHNIQUE_SITES:
        art = _read(repo, site.p.facts_rel)
        tr = _read(repo, site.p.transcription_rel)
        _need(art.get("report_eligible") is False, f"{site.p.facts_rel} must declare report_eligible: false")
        techs.append(SimpleNamespace(
            name=site.PROSE["technique_name"], href=site.OVERVIEW, rel=site.p.facts_rel, art=art, tr=tr,
            variants={v["id"]: v for v in tr["variants"]}, sessions=set(art["sessions"])))
    for s in routes + techs:
        _need(_HREF.match(s.href), f"{s.name}: page name {s.href!r} is not a plain docs page")
    return routes, techs


# ---------------------------------------------------------------- the page's own boards

class Round:
    """One round as the replay page decodes it: per player, per lock the piece, its cells (y-UP
    indices), the board after it (a copy) and the lock's raw fields."""

    def __init__(self, data, rr):
        self.locks, self.boards, self.cells, self.pieces = {}, {}, {}, {}
        b = data["board"]
        self.width, self.rows = b["width"], b["rows"]
        for p in rr["players"]:
            u = p["user"]
            # decode_boards yields ONE live grid: copy it at each lock, before the next step moves it
            dec = [(piece, [list(r) for r in board])
                   for piece, _f, board in RS.decode_boards(data, rr["seq"], p["locks"], RS.NEXT_SHOWN)]
            self.locks[u] = p["locks"]
            self.pieces[u] = [piece for piece, _b in dec]
            self.boards[u] = [board for _p, board in dec]
            self.cells[u] = [set(RS._place_cells(data["shapes"], self.width, self.rows, piece, lk[1]))
                             for lk, piece in zip(p["locks"], self.pieces[u])]

    def board_after(self, user, i):
        """The y-UP board after lock `i`; before lock 0 it is empty."""
        if i < 0:
            return [[None] * self.width for _ in range(self.rows)]
        return self.boards[user][i]


def _occ_rows(board):
    """A y-UP board as occupancy rows, top first, empty top rows trimmed ('.' empty, 'G' garbage, '#')."""
    rows = ["".join("." if v is None else ("G" if v == "G" else "#") for v in row) for row in reversed(board)]
    while rows and set(rows[0]) == {"."}:
        rows.pop(0)
    return rows


def _drawn(node, mirrored):
    """A route drawing's occupancy, top first, trimmed — the classifier's rule: '-' and 'U' empty."""
    rows = ["".join("." if ch in "-U" else "#" for ch in r) for r in node["rows"]]
    if mirrored:
        rows = [r[::-1] for r in rows]
    while rows and set(rows[0]) == {"."}:
        rows.pop(0)
    return rows


def board_matches(board, node, mirrored, strip):
    """The decoded board equals the drawing by occupancy, bottom-aligned, in the given hand. With
    `strip`, complete garbage rows come off the bottom first and no garbage may remain; without it the
    board may hold no garbage at all (the classifier never compares one that does)."""
    rows = _occ_rows(board)
    if strip:
        while rows and "G" in rows[-1] and set(rows[-1]) <= {".", "G"}:
            rows.pop()
    if any("G" in r for r in rows):
        return False
    return rows == _drawn(node, mirrored)


def spin_matches(rnd, user, i, node, mirrored, lines):
    """Lock `i` is a T with a full spin clearing `lines`, into the drawing's U cells (in the hand),
    and the board before it equals the drawing with its U cells empty."""
    lk = rnd.locks[user][i]
    if rnd.pieces[user][i] != "T" or lk[3] != 2 or lk[2] != lines:
        return False
    if not board_matches(rnd.board_after(user, i - 1), node, mirrored, False):
        return False
    h = len(node["rows"])
    want = set()
    for k, r in enumerate(node["rows"]):
        for c, ch in enumerate(r):
            if ch == "U":
                want.add((h - 1 - k) * rnd.width + (rnd.width - 1 - c if mirrored else c))
    return bool(want) and rnd.cells[user][i] == want


def pc_matches(rnd, user, i):
    return rnd.locks[user][i][2] > 0 and all(v is None for row in rnd.boards[user][i] for v in row)


def technique_matches(rnd, user, i, tr, var, mirrored):
    """Lock `i` is a T with a full spin clearing the variant's lines, and the variant's window fires
    on the board it went into, anchored on its cells, in the hit's hand."""
    from pipeline.openers.technique_transcription import window_fires
    lk = rnd.locks[user][i]
    if rnd.pieces[user][i] != "T" or lk[3] != 2 or lk[2] != var["lines"]:
        return False
    before = rnd.board_after(user, i - 1)
    H, W = rnd.rows, rnd.width
    rows = ["".join("-" if before[y][x] is None else "#" for x in range(W)) for y in range(H - 1, -1, -1)]
    lock = {(H - 1 - c // W, c % W) for c in rnd.cells[user][i]}
    spec = SimpleNamespace(empty_letters="")
    return window_fires(tr, var, spec, rows, lock, mirrored, filled=lambda R, C: rows[R][C] != "-") is True


# ---------------------------------------------------------------- the labels

_MV = re.compile(r"^(\S+)( \(mirrored\))? @(\d+)$")


def _bag(n):
    _need(0 < n < len(BAG_WORDS), f"bag {n} has no word")
    return f"第{BAG_WORDS[n]}巡"


def route_items(src, c, rnd):
    """(lock, before, template, phrase) for one route case, each re-checked on `rnd`."""
    user, v, out = c["player"], c["verified_to"], []
    where = f"{src.name} {c['session']} {c['file']} r{c['round_index0']} {user}"

    def node(nid):
        _need(nid in src.nodes and src.nodes[nid].get("rows"), f"{where}: no drawing for node {nid!r}")
        return src.nodes[nid]

    b1 = c["bag1"]
    m = _MV.match(b1["matched_variants"][0]) if b1["matched_variants"] else None
    _need(m is not None, f"{where}: bag 1 names no matched drawing")
    nid, mir, n = m.group(1), bool(m.group(2)), int(m.group(3))
    _need(mir == b1["mirrored"], f"{where}: the bag-1 drawing's hand disagrees with the case's")
    if n - 1 <= v:
        _need(board_matches(rnd.board_after(user, n - 1), node(nid), mir, False),
              f"{where}: the board after lock {n - 1} is not {nid} ({'mirrored' if mir else 'as drawn'})")
        out.append((n - 1, False, T_BOARD, f"{src.name} {_bag(node(nid)['bag'])}"))
    sp = b1.get("spin")
    if sp and sp.get("node") and b1["lock"] <= v:
        sn = node(sp["node"])
        _need(spin_matches(rnd, user, b1["lock"], sn, b1["mirrored"], sp["lines"]),
              f"{where}: lock {b1['lock']} is not a T-spin into {sp['node']}'s U cells")
        out.append((b1["lock"], False, T_SPIN, f"{src.name} {_bag(sn['bag'])}"))
    b2 = c.get("bag2")
    if b2 and b2.get("node") and b2["lock"] <= v:
        strip = b2.get("garbage_rows_stripped", 0) > 0
        _need(not strip or src.strip, f"{where}: garbage stripped on an opener that never strips")
        _need(board_matches(rnd.board_after(user, b2["lock"]), node(b2["node"]), b2["mirrored"], strip),
              f"{where}: the board after lock {b2['lock']} is not {b2['node']}")
        out.append((b2["lock"], False, T_BOARD, f"{src.name} {_bag(node(b2['node'])['bag'])}"))
    for s in c["snapshots"]:
        if not s["verified"]:
            continue
        _need(s["lock"] <= v, f"{where}: snapshot {s['node']} is marked verified past verified_to")
        _need(board_matches(rnd.board_after(user, s["lock"]), node(s["node"]), s["mirrored"], src.strip),
              f"{where}: the board after lock {s['lock']} is not {s['node']}")
        out.append((s["lock"], False, T_BOARD, f"{src.name} {_bag(node(s['node'])['bag'])}"))
    pc = c.get("pc")
    if pc and pc.get("node") and pc["verified"]:
        _need(pc_matches(rnd, user, pc["lock"]), f"{where}: lock {pc['lock']} is not a Perfect Clear")
        out.append((pc["lock"], False, T_PC, src.name))
    return out


def technique_items(src, h, rnd):
    """(lock, before, template, phrase) for one technique hit, re-checked on `rnd`."""
    where = f"{src.name} {h['session']} {h['file']} r{h['round_index0']} {h['player']} lock {h['lock']}"
    var = src.variants.get(h["variant"])
    _need(var is not None, f"{where}: no variant {h['variant']!r}")
    _need(h["lock"] <= h["verified_to"], f"{where}: a hit past the verified prefix")
    _need(technique_matches(rnd, h["player"], h["lock"], src.tr, var, h["mirrored"]),
          f"{where}: the window does not fire on the board before the T, or the T is not its spin")
    words = SPIN_WORDS.get((var["lines"], var["spin"]))
    _need(words is not None, f"{where}: no words for a {var['spin']} clearing {var['lines']}")
    if src.art.get("qualify") and not h["qualifies"]:
        # 社畜トレイン's `qualify`: the window fired but the hit fails a build rule, so the shape
        # stood and the technique was not built. It gets no key moment at all (the technique page's
        # case index still lists it, with a link to the moment); the checks above still ran.
        return []
    return [(h["lock"], True, T_TECH, f"{src.name}（{words}）")]


def for_session(data, facts, sources):
    """{(mi, ri): {"marks": [(user, lock, before, kind, label)], "links": [(name, href)]}} for every
    round of the session holding a label. `sources` is `load_sources()`."""
    routes, techs = sources
    session = data["session"]
    for s in routes + techs:
        _need(session in s.sessions, f"{s.rel} does not cover {session}: re-emit it before rendering")
    at = {(m["file"], fr["index"]): (mi, ri) for mi, m in enumerate(facts["matches"])
          for ri, fr in enumerate(m["rounds"])}
    by_round = {(rr["file"], rr["round"]): rr for rr in data["rounds"]}
    cache = {}

    def rnd(file, r0):
        if (file, r0) not in cache:
            _need((file, r0) in by_round, f"{session} {file} r{r0}: no replay round")
            cache[(file, r0)] = Round(data, by_round[(file, r0)])
        return cache[(file, r0)]

    items = {}   # (mi, ri) -> {(user, lock, before, template): [phrases]}, links
    links = {}

    def add(file, r0, user, kind, src, got):
        key = at.get((file, r0))
        _need(key is not None, f"{session} {file} r{r0}: not a round of facts.json")
        for lock, before, tpl, phrase in got:
            grp = items.setdefault(key, {}).setdefault((user, lock, before, kind, tpl), [])
            if phrase not in grp:
                grp.append(phrase)
        if got and (src.name, src.href) not in links.setdefault(key, []):
            links[key].append((src.name, src.href))

    for src in routes:
        for c in src.art["cases"]:
            if c["session"] == session:
                add(c["file"], c["round_index0"], c["player"], "opener", src,
                    route_items(src, c, rnd(c["file"], c["round_index0"])))
    for src in techs:
        for h in src.art["hits"]:
            if h["session"] == session:
                add(h["file"], h["round_index0"], h["player"], "technique", src,
                    technique_items(src, h, rnd(h["file"], h["round_index0"])))
    out = {}
    for key, grp in items.items():
        marks = sorted((u, lock, before, kind, tpl.format(user=u, x=JOIN.join(ph)))
                       for (u, lock, before, kind, tpl), ph in grp.items())
        out[key] = {"marks": marks, "links": links[key]}
    return out


# ---------------------------------------------------------------- selftest

def _selftest():
    """Each planted wrong label must be refused by the re-derivation; a control must pass."""
    import copy
    from pipeline import replay_page as RP
    session = "2026-10-20"
    data, facts = RP.load(os.path.join(REPO, "sessions", session))
    routes, techs = load_sources()

    def pick(srcs, field, pred):
        for s in srcs:
            for x in s.art[field]:
                if x["session"] == session and pred(x):
                    return s, x
        raise SystemExit(f"replay_labels selftest: no {field} on {session} to plant")

    rs, case = pick(routes, "cases", lambda c: c.get("bag2") and c["bag2"]["lock"] <= c["verified_to"])
    ss, scase = pick(routes, "cases", lambda c: (c["bag1"].get("spin") or {}).get("node")
                     and c["bag1"]["lock"] <= c["verified_to"])
    ts, hit = pick(techs, "hits", lambda h: True)

    def with_case(src, field, obj, edit):
        s2 = copy.copy(src)
        s2.art = dict(src.art)
        o2 = copy.deepcopy(obj)
        edit(o2)
        s2.art[field] = [o2 if x is obj else x for x in src.art[field]]
        return s2

    def run(rr, tt):
        return for_session(data, facts, (rr, tt))

    def mv_shift(c):
        mv = c["bag1"]["matched_variants"]
        mv[0] = re.sub(r"@(\d+)$", lambda m: f"@{int(m.group(1)) + 1}", mv[0])

    cases = [
        ("control: every label of the night", routes, techs, None),
        ("a bag-1 board one lock late", [with_case(rs, "cases", case, mv_shift) if s is rs else s for s in routes], techs, "is not"),
        ("a bag-2 board one lock early", [with_case(rs, "cases", case, lambda c: c["bag2"].__setitem__("lock", c["bag2"]["lock"] - 1)) if s is rs else s for s in routes], techs, "is not"),
        ("a bag-2 board in the other hand", [with_case(rs, "cases", case, lambda c: c["bag2"].__setitem__("mirrored", not c["bag2"]["mirrored"])) if s is rs else s for s in routes], techs, "is not"),
        ("a bag-1 T-spin one lock late", [with_case(ss, "cases", scase, lambda c: c["bag1"].__setitem__("lock", c["bag1"]["lock"] + 1)) if s is ss else s for s in routes], techs, "T-spin"),
        ("a technique hit one lock late", routes, [with_case(ts, "hits", hit, lambda h: h.__setitem__("lock", h["lock"] + 1)) if s is ts else s for s in techs], "window"),
        ("a technique hit in the other hand", routes, [with_case(ts, "hits", hit, lambda h: h.__setitem__("mirrored", not h["mirrored"])) if s is ts else s for s in techs], "window"),
        ("an artefact that does not cover the night", routes, [SimpleNamespace(**{**vars(techs[0]), "sessions": set()})] + techs[1:], "does not cover"),
    ]
    ok = True
    for name, rr, tt, want in cases:
        try:
            got = run(rr, tt)
            good = want is None and bool(got)
            msg = f"accepted ({sum(len(v['marks']) for v in got.values())} labels)"
        except SystemExit as e:
            good = want is not None and want in str(e)
            msg = f"refused: {str(e)[:90]}"
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {msg}")
    # A hit that fails its artefact's `qualify` rules gets no key moment; the same hit marked as
    # qualifying does, so the drop is the rule and not a hit the night never had.
    qs = [s for s in techs if s.art.get("qualify")]
    shape = [(s, h) for s in qs for h in s.art["hits"] if h["session"] == session and not h["qualifies"]]
    if not shape:
        raise SystemExit(f"replay_labels selftest: no shape-only hit on {session} to check")
    qsrc, qhit = shape[0]

    def n_marks(tt):   # labels naming the technique: a hit can share a mark with another one's
        return sum(m[4].count(qsrc.name) for v in run(routes, tt).values() for m in v["marks"])

    base = n_marks(techs)
    flipped = n_marks([with_case(qsrc, "hits", qhit, lambda h: h.__setitem__("qualifies", True))
                       if s is qsrc else s for s in techs])
    good = flipped == base + 1
    ok &= good
    print(f"  {'ok ' if good else 'BAD'} a shape-only {qsrc.name} hit has no key moment: "
          f"{base} labels, {flipped} with it marked as qualifying")
    print(f"{'ok ' if ok else 'FAIL'} replay_labels selftest: {len(cases) - 1} wrong labels, "
          f"{'all refused' if ok else 'SOME ACCEPTED'}")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    ap.error("nothing to do: pass --selftest (the labels are rendered and checked by bin/build-docs)")


if __name__ == "__main__":
    raise SystemExit(main())
