"""最癲一局 重播 — an animated replay of ONE round, quarantined like the forecast and opener sections.

    python3 -m pipeline.build_report sessions/2026-10-03/report      # writes the region
    python3 -m pipeline.check_replay_section sessions/2026-10-03/report   # its drift gate

Renders the round `generators._intense_round` selects — the SAME selector 最癲一局 (`intense_round.py`)
and its proved claims use, imported rather than copied, so the replay and the trust-chain section
cannot describe different rounds — out of the session's `sim/replay-facts.json` (written by
`pipeline/sim/emit-replay.ts`). Returns None when the session has no such artefact, or no qualifying
round; `build_report.render` then refuses a leftover region rather than leaving it stale.

QUARANTINE. Every board drawn here comes from ONE engine (the vendored Triangle engine) replaying the
recorded inputs. The `.ttrm` holds no board snapshot, so no board is ever compared with the game cell
for cell, and there is no second independent implementation. So: no claim ids, no ✓ badges, no
`data-claim` anywhere inside the region, and the artefact must say `report_eligible: false` or this
module refuses to render it. `check_replay_section.py` holds the region to all of that.

WHAT IS AND IS NOT FROM THE SIMULATOR. The piece sequence, the per-lock boards, holds, queue, clears,
spins, attack and the garbage rows inserted are the engine's. The incoming-garbage meter combines
the receiver's RECORDED `garbage_events` (facts.json, twice-extracted — the queued 射埋 amounts,
before cancellation) with the engine's own cancellation (attack − sent) and insertion, so the meter is
pending = queued so far − cancelled − inserted. That is never negative on any of the corpus's 2314
player-rounds (measured when this module was written), and `_meter_check` makes a negative value a
build error rather than a clamped zero — a clamp would turn the one sign of a mis-join into a
plausible empty meter.

THE THREE BOUNDARY STATES, per player, from the artefact's `prefix` (the existing verified-prefix
gate): locks up to `verified_to` sit on boards whose attacks matched the opponent's recorded incoming
garbage; after that the round is either "no evidence either way" (the attacks ran out — most rounds)
or "check failed at lock N". The seek bar draws all three, and the method note explains them. Two
flags make a visible 「模擬盤面喺呢度可能同真實唔同」: a round whose whole-round totals fail the
artefact's admission check, and a player whose engine knock-out disagrees with `gameoverreason`.

FIGURES. Python prints integer counts only (lock indices, piece counts); every rate is computed in
the browser and FLOORED there, like `fmt` floors, because 約 means "at least" in this report. The
player's script lives in `replay_player.js` and is inlined verbatim, so the drift gate's re-render
covers it too.
"""
import html
import json
import os
import re

from pipeline.claims import generators
from pipeline.claims.build_claims import SIMPLIFIED

FACTS_REL = os.path.join("sim", "replay-facts.json")
SECTION_ID = "round-replay"
DATA_ID = "rp-data"
JS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "replay_player.js")

# Key-moment thresholds. A key moment is a marker on the seek bar and a ↑/↓ stop, so it has to be
# rare enough to be navigable; these are drawing choices, not findings, and nothing is counted from
# them anywhere else in the report.
BIG_ATTACK = 6       # lines of attack from one lock (not already a T-spin or a perfect clear)
BIG_GARBAGE = 4      # garbage rows inserted on one lock
NEXT_SHOWN = 5       # hold + next-5, as emit-replay.ts NEXT_SHOWN emits `seq` long enough for

# The sentences the quarantine rests on. Named so `check_replay_section` demands each one and its
# selftest deletes each one; a control with no mutant proving it fires is a comment, not a gate.
EYEBROW = "模擬器推導 · 唔屬於信任鏈"
TITLE_MARK = "（未經證明）"
NO_CLAIM = "冇 claim 編號、冇 ✓ 標記"
DROP_SENTENCE = ("每粒方塊淨係記低最後落咗喺邊；方塊跌落去嗰條路線係畫出嚟嘅，"
                 "<strong>唔係玩家真實嘅按鍵操作</strong>。")
# Says what the hole column IS (the engine's seeded RNG), what it is consistent with (the game's own
# counters) and that it was never observed. It deliberately says nothing about the column recorded
# in the replay's garbage events: whether those agree is a separate, unsettled question
# (research §2.3), and this sentence must not answer it in either direction.
HOLE_SENTENCE = ("垃圾行個窿喺邊一欄，係<strong>引擎用種子亂數揀嘅</strong>："
                 "同遊戲自己嘅計數（清咗幾多垃圾、消咗幾多行）對得上，"
                 "但<strong>從來冇直接觀察過</strong>。")
BOUNDARY_SENTENCE = (
    "時間軸上面兩條幼帶係每個玩家嘅核對界線，有三個狀態："
    "<strong>實色＝已核</strong>（嗰段時間引擎打出嘅攻擊，同對手 replay 記錄收到嘅垃圾"
    "逐下對得上，時間、行數、行位都啱）；"
    "<strong>斜紋＝最後一次攻擊之後，冇證據話啱定唔啱</strong>（攻擊用晒，之後冇嘢可以核，"
    "唔係錯，係核唔到）；<strong>紅斜紋＝核對失敗</strong>（由嗰粒開始，"
    "盤面可能同真實唔同）。")
FLAG_WORDS = "模擬盤面喺呢度可能同真實唔同"
MORE_LINK = "睇成晚每一局"      # the region's link to the per-session replay page
REQUIRED = (EYEBROW, TITLE_MARK, NO_CLAIM, DROP_SENTENCE, HOLE_SENTENCE, BOUNDARY_SENTENCE,
            FLAG_WORDS)

SPIN_NAMES = {(2, 1): "T-spin Single", (2, 2): "T-spin Double", (2, 3): "T-spin Triple",
              (2, 4): "T-spin Quad", (1, 1): "Mini T-spin Single", (1, 2): "Mini T-spin Double",
              (1, 3): "Mini T-spin Triple"}
ENDING_WORDS = {"topout": "頂爆", "garbagesmash": "俾垃圾逼爆"}
KNOCKOUT = set(ENDING_WORDS)


def facts_path(report_dir):
    """`<session>/sim/replay-facts.json` for the session owning `report_dir`."""
    return os.path.join(os.path.dirname(os.path.abspath(report_dir)), FACTS_REL)


def load(report_dir):
    """The session's replay facts, or None when it has none."""
    path = facts_path(report_dir)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _need(cond, msg):
    if not cond:
        raise SystemExit(f"replay_section: {msg}")


# ---------------------------------------------------------------- decoder (mirror of emit-replay.ts)

def _place_cells(shapes, width, rows, piece, place):
    if isinstance(place, list):
        return list(place)
    cells_n = width * rows
    shape_list = shapes.get(piece)
    _need(shape_list is not None, f"no shapes for piece {piece!r}")
    k, a = divmod(place, cells_n)
    _need(0 <= k < len(shape_list), f"bad place {place} for {piece}")
    ay, ax = divmod(a, width)
    return [(ay + dy) * width + ax + dx for dx, dy in shape_list[k]]


def queue_states(seq, locks, shown):
    """Port of emit-replay.ts `queueStates`: (piece placed, hold box) per lock."""
    cur, ptr, hold = seq[0], 1, ""
    out = []
    for lk in locks:
        if lk[5]:
            if hold == "":
                hold, cur = cur, seq[ptr]
                ptr += 1
            else:
                hold, cur = cur, hold
        _need(ptr + shown <= len(seq), "seq too short for the next queue")
        out.append((cur, hold))
        cur = seq[ptr] if ptr < len(seq) else None
        ptr += 1
    return out


def decode(data, seq, locks, shown):
    """Per lock: (piece, cleared row count, board empty afterwards). Mirrors `decodeTimeline` and
    throws on the same disagreement it does (full rows != the lock's `lines`)."""
    b = data["board"]
    width, rows = b["width"], b["rows"]
    shapes = data["shapes"]
    board = [[None] * width for _ in range(rows)]
    out = []
    for lk, (piece, _hold) in zip(locks, queue_states(seq, locks, shown)):
        _dframe, place, lines, _spin, garbage = lk[0], lk[1], lk[2], lk[3], lk[4]
        for column, amount in garbage:
            new = []
            for _ in range(amount):
                row = ["G"] * width
                row[column] = None
                new.append(row)
            board[0:0] = new
            del board[rows - amount - 1:rows - 1]
        for c in _place_cells(shapes, width, rows, piece, place):
            y, x = divmod(c, width)
            board[y][x] = piece
        full = [y for y in range(rows) if all(v is not None for v in board[y])]
        _need(len(full) == lines, f"decoder found {len(full)} full rows, lock says {lines}")
        for y in reversed(full):
            del board[y]
            board.append([None] * width)
        empty = all(v is None for row in board for v in row)
        out.append((piece, lines, empty))
    return out


# ---------------------------------------------------------------- the payload

def select(facts):
    """(mi, ri, round) of the session's most intense round, or None — the shared selector."""
    best = generators._intense_round(facts)
    if best is None:
        return None
    mi, ri, r, _tot = best
    return mi, ri, r


def _meter_check(where, locks, ge):
    """pending = queued (recorded) − cancelled − inserted, at every lock, must stay >= 0."""
    t, inc, out, k = 0, 0, 0, 0
    for i, lk in enumerate(locks):
        t += lk[0]
        while k < len(ge) and ge[k][0] <= t:
            inc += ge[k][1]
            k += 1
        out += (lk[6] - lk[7]) + sum(a for _c, a in lk[4])
        _need(inc - out >= 0, f"{where}: incoming-garbage meter goes negative at lock {i} "
                              f"({inc} queued, {out} cancelled+inserted) — the recorded events and "
                              "the engine's locks are not describing the same round")


def page_name(session):
    """The per-session replay page's file name under docs/ — ONE definition, read by this region's
    link, by `replay_page` and by `bin/build-docs`, so the link and the page cannot disagree."""
    _need(re.fullmatch(r"\d{4}-\d{2}-\d{2}", session or "") is not None,
          f"session {session!r} is not a date")
    return f"{session}-replay.html"


def check_artefact(data):
    """Refuse an artefact this module must not render: one that claims trust-chain standing, or
    one in a schema the decoder was not written for."""
    _need(data.get("report_eligible") is False,
          "replay-facts.json must declare report_eligible: false — simulator boards are not "
          "trust-chain data")
    _need(data.get("schema") == "replay-facts/1", f"unknown schema {data.get('schema')!r}")


def payload(data, facts):
    """The JSON the player reads for the 最癲一局 round, or None when there is none to replay."""
    if data is None:
        return None
    check_artefact(data)
    sel = select(facts)
    if sel is None:
        return None
    mi, ri, _fr = sel
    return round_payload(data, facts, mi, ri)


def round_payload(data, facts, mi, ri):
    """The player's JSON for match `mi`, round `ri` (both 0-based list positions in facts.json).
    The caller has run `check_artefact`."""
    m = facts["matches"][mi]
    fr = m["rounds"][ri]
    hits = [r for r in data["rounds"] if r["file"] == m["file"] and r["round"] == fr["index"]]
    _need(len(hits) == 1, f"replay-facts.json holds {len(hits)} entries for {m['file']} "
                          f"round {fr['index']} (the 最癲一局 round); expected exactly one")
    rr = hits[0]
    _need(rr["match"] == m["index"], f"match position {rr['match']} != facts.json's {m['index']}")

    order_users = list(facts["players"])
    by_user = {p["user"]: p for p in rr["players"]}
    _need(set(by_user) == set(order_users),
          f"replay players {sorted(by_user)} != facts players {sorted(order_users)}")
    shown = NEXT_SHOWN
    players, moments, flags = [], [], []
    abs_frames = []
    for slot, user in enumerate(order_users):
        p = by_user[user]
        fp = fr["players"][user]
        ge_raw = fp["garbage_events"]               # required: KeyError rather than a default
        ge = sorted([e["frame"], e["amt"]] for e in ge_raw)
        where = f"{m['file']} r{fr['index']} {user}"
        locks = p["locks"]
        _need(len(locks) > 0, f"{where}: no locks")
        _need(p["ending"] == fp["gameoverreason"],
              f"{where}: ending {p['ending']!r} != facts gameoverreason {fp['gameoverreason']!r}")
        _meter_check(where, locks, ge)
        dec = decode(data, rr["seq"], locks, shown)
        t = 0
        frames_abs = []
        for i, (lk, (piece, lines, empty)) in enumerate(zip(locks, dec)):
            t += lk[0]
            frames_abs.append(t)
            spin = lk[3]
            if lines and empty:
                moments.append([slot, i, "pc", f"{user} 全消（Perfect Clear）"])
            elif spin and lines:
                name = SPIN_NAMES.get((spin, lines))
                _need(name is not None, f"{where}: spin {spin} with {lines} lines has no name")
                moments.append([slot, i, "tspin", f"{user} {name}，攻擊 {lk[6]} 行"])
            elif lk[6] >= BIG_ATTACK:
                moments.append([slot, i, "attack", f"{user} 一下攻擊 {lk[6]} 行"])
            ins = sum(a for _c, a in lk[4])
            if ins >= BIG_GARBAGE:
                moments.append([slot, i, "garbage", f"{user} 食咗 {ins} 行垃圾"])
        if p["ending"] in KNOCKOUT:
            moments.append([slot, len(locks) - 1, "end",
                            f"{user} {ENDING_WORDS[p['ending']]}，局完"])
        abs_frames.append(frames_abs)
        ko = p["engine_knockout"]
        if not ko["agrees"]:
            flags.append([slot, ko["lock"] if ko["lock"] is not None else 0, "knockout"])
        if not p["admission"]["ok"]:
            flags.append([slot, 0, "admission"])
        pre = p["prefix"]
        _need(pre["after"] in ("end", "no_evidence", "check_failed"),
              f"{where}: unknown prefix state {pre['after']!r}")
        # the boundary is a key moment too: the first lock past what was checked
        if pre["after"] == "check_failed":
            _need(isinstance(pre["failed_at"], int)
                  and pre["verified_to"] < pre["failed_at"] < len(locks),
                  f"{where}: check_failed needs verified_to < failed_at < locks")
            moments.append([slot, pre["failed_at"], "boundary",
                            f"{user} 第 {pre['failed_at'] + 1} 粒嘅攻擊對唔上（核對失敗）"])
        elif pre["after"] == "no_evidence" and pre["verified_to"] + 1 < len(locks):
            moments.append([slot, pre["verified_to"] + 1, "boundary",
                            f"{user} 由呢粒起冇證據話啱定唔啱（攻擊用晒）"])
        players.append({
            "user": user, "slot": slot, "ending": p["ending"], "frames": p["frames"],
            "pieces": fp["pieces"], "locks": locks, "ge": ge,
            "verified_to": pre["verified_to"], "after": pre["after"], "failed_at": pre["failed_at"],
        })

    # one shared frame clock: every lock of both players, by (frame, slot, index)
    events = sorted((f, s, i) for s, fl in enumerate(abs_frames) for i, f in enumerate(fl))
    order = "".join(str(s) for _f, s, _i in events)
    pos = {(s, i): n + 1 for n, (_f, s, i) in enumerate(events)}   # merged position AFTER the lock
    moments = sorted([pos[(s, i)], s, kind, label] for s, i, kind, label in moments)
    flags = sorted([pos[(s, i)], s, kind] for s, i, kind in flags)
    return {
        "session": data["session"], "file": m["file"], "match": m["index"], "round": ri + 1,
        "label": f"m{m['index']}r{ri + 1}", "winner": fr["winner"], "seq": rr["seq"],
        "shapes": data["shapes"], "width": data["board"]["width"], "rows": data["board"]["rows"],
        "visible": data["board"]["visible_rows"], "next": shown,
        "order": order, "players": players, "moments": moments, "flags": flags,
        "flag_words": FLAG_WORDS,
    }


# ---------------------------------------------------------------- markup

CSS = """
    #round-replay .rp-player { margin: 1rem 0 .5rem; padding: .9rem; border: 1px solid var(--border-strong); border-radius: 10px; background: var(--bg-raised); }
    #round-replay .rp-player:focus { outline: none; }
    #round-replay .rp-player:focus-visible { outline: 2px solid var(--ink); outline-offset: 3px; }
    #round-replay .rp-focus-hint { font-size: .78rem; color: var(--muted); margin: 0 0 .6rem; }
    #round-replay .rp-boards { display: flex; gap: 1.2rem; justify-content: center; flex-wrap: wrap; }
    #round-replay .rp-side { display: grid; gap: .35rem; justify-items: center; min-width: 0; flex: 1 1 18rem; max-width: 26rem; }
    #round-replay .rp-name { font-weight: 700; font-size: .95rem; }
    #round-replay .rp-side[data-slot="0"] .rp-name { color: var(--rp-c0); }
    #round-replay .rp-side[data-slot="1"] .rp-name { color: var(--rp-c1); }
    #round-replay .rp-callout { height: 1.4em; line-height: 1.4; overflow: hidden; white-space: nowrap; font-weight: 700; font-size: .9rem; }
    #round-replay .rp-side[data-slot="0"] .rp-callout { color: var(--rp-c0); }
    #round-replay .rp-side[data-slot="1"] .rp-callout { color: var(--rp-c1); }
    #round-replay .rp-canvas { display: block; width: 100%; height: auto; border-radius: 6px; background: var(--bg-sunken); touch-action: manipulation; }
    #round-replay .rp-strip, #round-replay .rp-state { font: .78rem/1.45 var(--font-mono); color: var(--ink-secondary); text-align: center; font-variant-numeric: tabular-nums; }
    #round-replay .rp-state[data-state="no_evidence"] { color: var(--pending); }
    #round-replay .rp-state[data-state="check_failed"] { color: var(--rp-bad); }
    #round-replay .rp-flag { font-size: .8rem; color: var(--rp-bad); font-weight: 600; text-align: center; }
    #round-replay .rp-flag[hidden] { display: none; }
    #round-replay .rp-controls { display: flex; flex-wrap: wrap; gap: .45rem; align-items: center; margin-top: .9rem; }
    #round-replay .rp-btn { font: 500 .85rem var(--font-mono); padding: .4rem .7rem; min-width: 2.6rem; border: 1px solid var(--border-strong); border-radius: 6px; background: var(--bg); color: var(--ink); cursor: pointer; }
    #round-replay .rp-btn.rp-primary { background: var(--ink); color: var(--bg); border-color: var(--ink); }
    #round-replay .rp-speed { font: .85rem var(--font-mono); padding: .35rem; border: 1px solid var(--border-strong); border-radius: 6px; background: var(--bg); color: var(--ink); }
    #round-replay .rp-pos { font: .82rem var(--font-mono); color: var(--ink-secondary); font-variant-numeric: tabular-nums; }
    #round-replay .rp-seek-wrap { position: relative; margin-top: .6rem; padding-top: 2.1rem; }
    #round-replay .rp-seek { width: 100%; margin: 0; accent-color: var(--ink); }
    #round-replay .rp-band { position: absolute; left: 0; right: 0; height: 5px; border-radius: 3px; overflow: hidden; background: var(--border); }
    #round-replay .rp-band[data-slot="0"] { top: .2rem; }
    #round-replay .rp-band[data-slot="1"] { top: .55rem; }
    #round-replay .rp-seg { position: absolute; top: 0; bottom: 0; }
    #round-replay .rp-seg[data-state="verified"] { background: var(--good); }
    #round-replay .rp-seg[data-state="no_evidence"] { background: repeating-linear-gradient(45deg, var(--pending) 0 3px, transparent 3px 6px); }
    #round-replay .rp-seg[data-state="check_failed"] { background: repeating-linear-gradient(-45deg, var(--rp-bad) 0 2px, transparent 2px 4px); }
    #round-replay .rp-marks { position: absolute; left: 0; right: 0; top: 1rem; height: 1rem; }
    #round-replay .rp-mark { position: absolute; top: 0; width: 12px; height: 12px; margin-left: -6px; padding: 0; border-radius: 50%; border: 2px solid var(--bg-raised); cursor: pointer; background: var(--muted); }
    #round-replay .rp-mark[data-slot="0"] { background: var(--rp-c0); }
    #round-replay .rp-mark[data-slot="1"] { background: var(--rp-c1); }
    #round-replay .rp-mark[data-kind="pc"], #round-replay .rp-mark[data-kind="end"] { border-radius: 2px; }
    #round-replay .rp-mark[data-kind="garbage"] { border-style: dotted; }
    #round-replay .rp-mark:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
    #round-replay .rp-legend { display: flex; flex-wrap: wrap; gap: .3rem 1rem; font-size: .76rem; color: var(--muted); margin-top: .45rem; }
    #round-replay .rp-key { display: inline-block; width: 1.4rem; height: 5px; vertical-align: middle; margin-right: .3rem; border-radius: 2px; }
    #round-replay .rp-key[data-state="verified"] { background: var(--good); }
    #round-replay .rp-key[data-state="no_evidence"] { background: repeating-linear-gradient(45deg, var(--pending) 0 3px, transparent 3px 6px); }
    #round-replay .rp-key[data-state="check_failed"] { background: repeating-linear-gradient(-45deg, var(--rp-bad) 0 2px, transparent 2px 4px); }
    #round-replay .rp-moments { list-style: none; padding: 0; margin: .8rem 0 0; display: flex; flex-wrap: wrap; gap: .3rem .5rem; font-size: .8rem; }
    #round-replay .rp-moment { font: inherit; padding: .15rem .45rem; border: 1px solid var(--border); border-radius: 4px; background: transparent; color: var(--ink-secondary); cursor: pointer; }
    #round-replay .rp-moment[aria-current="true"] { border-color: var(--ink); color: var(--ink); }
    #round-replay .rp-help { margin-top: .7rem; font-size: .8rem; color: var(--ink-secondary); }
    #round-replay .rp-help[hidden] { display: none; }
    #round-replay .rp-help dl { display: grid; grid-template-columns: max-content 1fr; gap: .15rem .9rem; margin: .3rem 0 0; }
    #round-replay .rp-help dt { font-family: var(--font-mono); }
    #round-replay .rp-help dd { margin: 0; }
    #round-replay .rp-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
    #round-replay .rp-more { margin-top: .8rem; font-size: .88rem; color: var(--ink-secondary); }
    #round-replay .rp-more a { color: var(--ink); font-weight: 700; }
    #round-replay .rp-nojs { font-size: .85rem; color: var(--muted); }
    @media (max-width: 640px) {
      #round-replay .rp-player { padding: .6rem; }
      #round-replay .rp-side { flex-basis: 100%; }
    }
    @media print { #round-replay .rp-player { display: none; } }
"""

HELP_KEYS = [
    ("Space / K", "播放／暫停"),
    ("← / →", "上一粒／下一粒（兩個玩家合埋計，每次郁一粒）"),
    ("↑ / ↓", "上一個／下一個關鍵時刻"),
    ("J / L", "後退／前進 5 粒"),
    ("Home / End", "跳去局頭／局尾"),
    ("< / >", "慢啲／快啲（0.5×、1×、2×、4×）"),
    ("?", "開／收呢張快捷鍵表"),
]


def _no_simplified(markup):
    bad = sorted(set(markup) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"replay_section: simplified glyph(s) {bad} — this report is "
                         "traditional-character Cantonese")
    return markup


def _player_note(p, esc=html.escape):
    """One player's boundary state, in words. Integer lock numbers only (1-based for a reader).
    `esc` is html.escape for markup; the replay page passes `str` because it sets textContent."""
    u, v, n = esc(p["user"]), p["verified_to"], len(p["locks"])
    if v < 0:
        head = f"{u}：第一粒已經核唔到"
    else:
        head = f"{u}：核到第 {v + 1} 粒（全局 {n} 粒）"
    if p["after"] == "end":
        tail = "，一路核到局尾。"
    elif p["after"] == "no_evidence":
        tail = "；之後攻擊用晒，冇證據話啱定唔啱。"
    else:
        tail = (f"；第 {p['failed_at'] + 1} 粒嘅攻擊對唔上（核對失敗），"
                f"所以第 {v + 2} 粒起嘅盤面可能同真實唔同。")
    return head + tail


_CSS_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def _color_css(players):
    """Scoped colour tokens. The shell's positional `--p1`/`--p2` arrived after the first four
    reports were committed, whose `:root` still names the colours after the players (`--yachi`),
    so each slot falls back to the player-named token — the `--accent` trap otherwise: an unset
    custom property resolves to nothing and the board's names and markers draw in no colour. The
    red is the section's own because the shell defines no "bad" token."""
    out = []
    for slot, p in enumerate(players):
        fb = f", var(--{p['user']})" if _CSS_IDENT.match(p["user"]) else ""
        out.append(f"--rp-c{slot}: var(--p{slot + 1}{fb});")
    return ("    #round-replay { " + " ".join(out) + " --rp-bad: #d0453a; }\n"
            "    @media (prefers-color-scheme: dark) { :root:not([data-theme=\"light\"]) #round-replay "
            "{ --rp-bad: #ef6a5f; } }\n"
            "    :root[data-theme=\"dark\"] #round-replay { --rp-bad: #ef6a5f; }")


def player_box(label, users):
    """The `.rp-player` box the shared player mounts on — markup only, no data. The region and the
    replay page both emit THIS, so a control the player looks up cannot exist in one and not the
    other."""
    keys = "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd>" for k, v in HELP_KEYS)
    return [
        f'    <div class="rp-player" tabindex="0" role="group" '
        f'aria-label="{html.escape(label)} 模擬重播；撳 ? 睇快捷鍵" '
        f'aria-describedby="rp-hint">',
        '      <p class="rp-focus-hint" id="rp-hint">撳一下呢個框（或者 Tab 入嚟）先用到鍵盤：'
        'Space 播／停，← → 一粒一粒行，↑ ↓ 跳關鍵時刻，? 睇全部快捷鍵。由第一粒之前開始，唔會自己播。</p>',
        '      <noscript><p class="rp-nojs">重播要開 JavaScript 先睇到。</p></noscript>',
        '      <div class="rp-boards"></div>',
        '      <div class="rp-controls">',
        '        <button type="button" class="rp-btn" data-act="start" aria-label="跳去局頭">⏮</button>',
        '        <button type="button" class="rp-btn" data-act="back" aria-label="上一粒">◀</button>',
        '        <button type="button" class="rp-btn rp-primary" data-act="play" aria-label="播放">播放</button>',
        '        <button type="button" class="rp-btn" data-act="fwd" aria-label="下一粒">▶</button>',
        '        <button type="button" class="rp-btn" data-act="end" aria-label="跳去局尾">⏭</button>',
        '        <select class="rp-speed" aria-label="播放速度">'
        '<option value="0.5">0.5×</option><option value="1" selected>1×</option>'
        '<option value="2">2×</option><option value="4">4×</option></select>',
        '        <button type="button" class="rp-btn" data-act="letters" aria-pressed="false">字母</button>',
        '        <button type="button" class="rp-btn" data-act="help" aria-expanded="false" aria-controls="rp-help">?</button>',
        '        <span class="rp-pos" aria-hidden="true"></span>',
        '      </div>',
        '      <div class="rp-seek-wrap">',
        '        <div class="rp-band" data-slot="0" aria-hidden="true"></div>',
        '        <div class="rp-band" data-slot="1" aria-hidden="true"></div>',
        '        <div class="rp-marks" role="group" aria-label="關鍵時刻"></div>',
        '        <input type="range" class="rp-seek" min="0" value="0" step="1" aria-label="重播位置（粒）">',
        '      </div>',
        '      <div class="rp-legend" aria-hidden="true">'
        '<span><i class="rp-key" data-state="verified"></i>已核</span>'
        '<span><i class="rp-key" data-state="no_evidence"></i>最後一次攻擊之後，冇證據</span>'
        '<span><i class="rp-key" data-state="check_failed"></i>核對失敗</span>'
        '<span>上帶 = ' + html.escape(users[0]) + '，下帶 = '
        + html.escape(users[1]) + '</span></div>',
        '      <ul class="rp-moments" aria-label="關鍵時刻列表"></ul>',
        f'      <div class="rp-help" id="rp-help" hidden><strong>快捷鍵</strong>'
        f'（淨係喺呢個重播框有焦點嗰陣先生效）<dl>{keys}</dl></div>',
        '      <div class="rp-sr" aria-live="polite" aria-atomic="true"></div>',
        '    </div>',
    ]


def player_js():
    """`replay_player.js`, checked to be inlinable."""
    with open(JS_PATH, encoding="utf-8") as fh:
        js = fh.read()
    _need("</script" not in js.lower(), "replay_player.js may not contain a closing script tag")
    return js.rstrip()


# Mounts the shared player on this region. `replay_player.js` only defines `rpReplay.mount`; the
# replay page mounts the same function once per round the viewer picks.
BOOT = ("(function () {\n"
        "  var root = document.getElementById(\"" + SECTION_ID + "\");\n"
        "  var data = document.getElementById(\"" + DATA_ID + "\");\n"
        "  if (!root || !data || !window.rpReplay) return;\n"
        "  rpReplay.mount(root, root.querySelector(\".rp-player\"), JSON.parse(data.textContent),\n"
        "                 { hashPrefix: \"replay-\" });\n"
        "})();")


def section(pl):
    """The region's markup for payload `pl`, or None."""
    if pl is None:
        return None
    blob = json.dumps(pl, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    js = player_js()
    names = "、".join(html.escape(p["user"]) for p in pl["players"])
    flagged = bool(pl["flags"])
    flag_note = (
        f'      <p><strong>呢一局有標記：{FLAG_WORDS}。</strong>'
        '標記喺時間軸同盤面下面都有顯示：引擎個盤爆唔爆同遊戲記錄唔夾，'
        '或者成局嘅總數（粒數、行數、垃圾、T-spin、全消）同 facts.json 唔夾。</p>'
        if flagged else
        '      <p>呢一局兩個玩家嘅成局總數（粒數、消行、hold、清垃圾、攻擊、全消、每種 T-spin）'
        '都同 <code>facts.json</code> 對得上，引擎爆唔爆亦同遊戲記錄一致。'
        '對得上只係講總數，<strong>唔會</strong>令呢節入返信任鏈；如果有一項唔夾，'
        f'呢度會寫「{FLAG_WORDS}」。</p>')
    out = [
        f'<section id="{SECTION_ID}">',
        '  <style>\n' + _color_css(pl["players"]) + CSS.rstrip() + '\n  </style>',
        '  <div class="wrap-wide">',
        f'    <div class="eyebrow">{EYEBROW}</div>',
        f'    <h2 class="section-title">最癲一局 重播：{pl["label"]}{TITLE_MARK}</h2>',
        '',
        '    <div class="method-note">',
        f'      <p><strong>呢節唔屬於信任鏈。</strong>佢重播嘅係上面「最癲一局」嗰一局'
        f'（{html.escape(pl["file"])} 第 {pl["round"]} 局，{names}），由同一條揀局規則揀出嚟；'
        '但盤面係<strong>一個 replay 模擬器</strong>（Triangle 引擎）重跑操作記錄推導出嚟，'
        'replay 檔本身冇記錄過任何盤面，所以冇一格曾經同遊戲逐格對過，亦冇第二份獨立實作。'
        f'所以呢節<strong>{NO_CLAIM}</strong>。</p>',
        f'      <p>{DROP_SENTENCE}</p>',
        f'      <p>{HOLE_SENTENCE}</p>',
        '      <p>盤邊條直柱係<strong>射埋</strong>嘅垃圾：攞對手射過嚟、記錄喺 replay 嘅數'
        '（抵銷之前），減去引擎自己抵銷咗同塞咗落盤嘅行數。未必全部都會食到。</p>',
        f'      <p>{BOUNDARY_SENTENCE}</p>',
        f'      <p>{_player_note(pl["players"][0])}<br>{_player_note(pl["players"][1])}</p>',
        flag_note,
        '    </div>',
        '',
        *player_box(pl["label"], [p["user"] for p in pl["players"]]),
        f'    <p class="rp-more"><a href="{html.escape(page_name(pl["session"]))}#{pl["label"]}">'
        f'{MORE_LINK}</a>：同一個模擬器、同一套核對界線，成晚每一局都揀得，'
        '仲有一幅由 replay 記錄嘅射埋事件畫出嚟嘅攻擊圖。</p>',
        f'    <script type="application/json" id="{DATA_ID}">{blob}</script>',
        '    <script>\n' + js + '\n' + BOOT + '\n    </script>',
        '  </div>',
        '</section>',
    ]
    return _no_simplified("\n".join(out))


def build(facts, report_dir):
    """The region body for `report_dir`'s session, or None (no artefact, or no qualifying round)."""
    return section(payload(load(report_dir), facts))
