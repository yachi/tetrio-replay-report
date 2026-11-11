"""The SDPC loop video read (`pipeline/openers/sdpc-loop.json`): the gate, and the reader that made it.

    python3 -m pipeline.openers.check_sdpc_loop                 # the gate (CI)
    python3 -m pipeline.openers.check_sdpc_loop --selftest      # its mutants (CI)
    python3 -m pipeline.openers.check_sdpc_loop --video <mp4>   # re-read every frame; the reads must be the committed ones

JayKob's video plays an SDPC loop: stick spin's SDパフェ (bag 1 with the T laid flat into a T-spin Single, the
SD bag-2 TSD, an 8-line Perfect Clear) and then とんぼ's くるまDPC (the piece left over is the O; a TSD into a
4-line Perfect Clear), over and over. Both halves are boards this repo already transcribes, so the video adds
NO board: it adds the times. The reader compares the bottom 8 rows of every frame with those transcriptions by
occupancy, exactly (all 80 cells), so a read is never a guess; the Perfect Clear times are read by eye and say so.

What the gate checks, against the committed transcriptions:

* every read names a real board (`stickspin:<node>` of the loop, or `dpc:<setup>[+T]` of a real setup);
* reads are in frame order, each in the stretch its frame falls in between two Perfect Clears;
* no stretch holds both halves, and inside one the reads follow the route (bag1.left, bag1.pc, 2.sd,
  2.sd.after; a DPC setup before its T, in one hand);
* the arithmetic of the loop from the transcriptions themselves: the SDPC half clears 8 lines (its TSS, its
  TSD, an 8-row-less-3 Perfect Clear) = 20 pieces, one short of three bags, and the DPC half 6 lines = 15
  pieces, so the two are 35 pieces, five bags, and the board is empty at the start of a bag again.

VIDEO TIER. Nothing here is corpus data and nothing enters a count; the page says so.
"""
import argparse
import copy
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, "sdpc-loop.json")
STICKSPIN = os.path.join(HERE, "stickspin-routes.json")
DPC = os.path.join(HERE, "dpc-setups.json")
SPIN_LINES = {"TSS": 1, "TSD": 2}
ROUTE = ("bag1.left", "bag1.pc", "2.sd", "2.sd.after")
NR = 8


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def transcriptions():
    with open(STICKSPIN, encoding="utf-8") as f:
        st = json.load(f)
    with open(DPC, encoding="utf-8") as f:
        dp = json.load(f)
    return st, dp


def segment(pcs, frame):
    """The stretch a frame falls in: how many Perfect Clears came before it."""
    return sum(1 for t in pcs if t < frame / 60)


def kind(board):
    return board.split(":", 1)[0]


# ------------------------------------------------------------------ the boards a read can name

def _occ(rows):
    n = len(rows)
    return {(n - 1 - i, c) for i, r in enumerate(rows) for c, ch in enumerate(r) if ch not in ".-"}


def targets(st, dp):
    """{(board, mirrored): frozenset of (row from the bottom, column)} for every board a read may name. A
    DPC setup equal to an earlier one by occupancy is not added again: the first id names it (the video's
    p01.000 is also p08.000 and p10.000)."""
    nodes = {n["id"]: n for n in st["nodes"]}
    out, seen = {}, set()

    def put(name, cells):
        for m in (False, True):
            key = frozenset((r, 9 - c if m else c) for r, c in cells)
            if name.startswith("dpc:") and (key in seen):
                continue
            if name.startswith("dpc:"):
                seen.add(key)
            out[(name, m)] = key
    for k in ROUTE:
        put(f"stickspin:{k}", _occ(nodes[k]["rows"]))
    for s in dp["setups"]:
        n = len(s["base"])
        base = _occ(s["base"])
        put(f'dpc:{s["id"]}+T', base | {(n - 1 - r, c) for r, c in s["t_cells"]})
        put(f'dpc:{s["id"]}', base)
    return {k: v for k, v in out.items() if all(r < NR for r, _ in v)}


# ------------------------------------------------------------------ the reader

def read_video(path, d, st, dp):
    """Re-read the video the way the committed reads were made (`d["reader"]`)."""
    import numpy as np
    rd = d["reader"]
    vf = rd["crop"].split(", cell")[0]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-t", str(rd["seconds"]), "-i", path, "-vf", vf,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 63, 30, 3)[:, 1::3, 1::3].astype(int)
    pal = np.array(list(rd["palette"].values()))
    x = a[:, 21 - NR:, :][:, ::-1]
    filled = (((x[:, :, :, None, :] - pal[None, None, None]) ** 2).sum(-1).min(-1) < rd["threshold"])
    flat = filled.reshape(len(filled), -1)
    pcs = d["pcs"]["t"]
    reads = []
    for (name, m), cells in targets(st, dp).items():
        mask = np.zeros((NR, 10), bool)
        for r, c in cells:
            mask[r, c] = True
        for f in np.where((flat == mask.reshape(-1)).all(1))[0]:
            reads.append({"frame": int(f), "segment": segment(pcs, int(f)), "board": name, "mirrored": m})
    reads.sort(key=lambda r: r["frame"])
    out = []
    for r in reads:
        if not any(o["segment"] == r["segment"] and o["board"] == r["board"] and o["mirrored"] == r["mirrored"]
                   for o in out):
            out.append(r)
    return out


# ------------------------------------------------------------------ the gate

def loop_arithmetic(d, st, dp):
    """(sdpc pieces, dpc pieces, problems), every count from the transcriptions."""
    bad = []
    nodes = {n["id"]: n for n in st["nodes"]}
    spin_lines = SPIN_LINES
    pc_rows = {len([r for r in n["rows"] if r.strip("-")]) for n in st["nodes"] if n.get("list") == d["loop"]["sdpc"]["pc_list"]}
    if len(pc_rows) != 1:
        bad.append(f"the SD Perfect Clear patterns are not one height: {sorted(pc_rows)}")
    sd_lines = spin_lines[nodes["bag1.pc"]["spin"]] + spin_lines[nodes["2.sd"]["spin"]] + min(pc_rows)
    setup = [s for s in dp["setups"] if s["id"] == d["loop"]["dpc"]["setup"]][0]
    boards = {b["id"]: b for b in dp["boards"]}
    pc_lines = {sum(1 for r in boards[p]["rows"] if r.strip(".")) for p in setup["pcs"]}
    if len(pc_lines) != 1:
        bad.append(f"the DPC's Perfect Clears are not one height: {sorted(pc_lines)}")
    dpc_lines = setup["lines"] + min(pc_lines)
    if sd_lines * 10 % 4 or dpc_lines * 10 % 4:
        bad.append(f"a half's cells are not whole pieces: {sd_lines}, {dpc_lines} lines")
    sd, dc = sd_lines * 10 // 4, dpc_lines * 10 // 4
    if sd % 7 != 6:
        bad.append(f"the SDPC half is {sd} pieces, not one short of whole bags")
    if (sd + dc) % 7:
        bad.append(f"the loop is {sd + dc} pieces, not whole bags")
    if not setup["heading"][1].startswith("Oミノ残し"):
        bad.append("the DPC setup is not the one that leaves the O")
    return sd, dc, sd_lines, dpc_lines, bad


def check(d, st, dp):
    bad = []
    if d.get("schema") != "sdpc-loop/1":
        bad.append("schema is not sdpc-loop/1")
    if d.get("report_eligible") is not False:
        bad.append("report_eligible is not false")
    pcs = d["pcs"]["t"]
    if pcs != sorted(pcs) or len(set(pcs)) != len(pcs):
        bad.append("the Perfect Clear times are not strictly increasing")
    if pcs and pcs[-1] >= d["reader"]["seconds"]:
        bad.append("a Perfect Clear after the frames the reader reads")
    if d["source"]["end"]["t"] < d["reader"]["seconds"]:
        bad.append("the reader reads past the video's own end of the loop")
    tg = targets(st, dp)
    frames = [r["frame"] for r in d["reads"]]
    if frames != sorted(frames):
        bad.append("the reads are not in frame order")
    groups = {}
    for r in d["reads"]:
        if (r["board"], r["mirrored"]) not in tg:
            bad.append(f'frame {r["frame"]}: {r["board"]} is no transcribed board')
            continue
        if r["frame"] >= d["reader"]["seconds"] * 60:
            bad.append(f'frame {r["frame"]}: past the frames the reader reads')
        if r["segment"] != segment(pcs, r["frame"]):
            bad.append(f'frame {r["frame"]}: in stretch {segment(pcs, r["frame"])}, recorded as {r["segment"]}')
        groups.setdefault(r["segment"], []).append(r)
    for s, rs in groups.items():
        kinds = {kind(r["board"]) for r in rs}
        if len(kinds) > 1:
            bad.append(f"stretch {s} holds both halves")
            continue
        if kinds == {"stickspin"}:
            order = [ROUTE.index(r["board"].split(":")[1]) for r in rs]
            if order != sorted(order) or len(set(order)) != len(order):
                bad.append(f"stretch {s}: the stick spin reads are not in route order")
        else:
            ids = [r["board"].split(":")[1] for r in rs]
            if len({i.split("+")[0] for i in ids}) != 1 or len({r["mirrored"] for r in rs}) != 1:
                bad.append(f"stretch {s}: more than one DPC setup or hand")
            if ids != sorted(ids, key=lambda i: i.endswith("+T")) or len(set(ids)) != len(ids):
                bad.append(f"stretch {s}: the DPC setup after its T")
            if ids[0].split("+")[0] != d["loop"]["dpc"]["setup"]:
                bad.append(f"stretch {s}: a DPC setup that is not the loop's")
    bad += loop_arithmetic(d, st, dp)[-1]
    return bad


def halves(d):
    """{stretch: 'sdpc' | 'dpc'} for every stretch holding a read."""
    out = {}
    for r in d["reads"]:
        out[r["segment"]] = "sdpc" if kind(r["board"]) == "stickspin" else "dpc"
    return out


def laps(d):
    """Stretches read as SDPC whose next stretch is read as the DPC: one whole loop each."""
    h = halves(d)
    return [s for s in sorted(h) if h[s] == "sdpc" and h.get(s + 1) == "dpc"]


# ------------------------------------------------------------------ selftest

def selftest():
    d, (st, dp) = load(), transcriptions()
    survived = killed = 0

    def expect(label, dd, want):
        nonlocal survived, killed
        bad = check(dd, st, dp)
        if bool(bad) == want:
            killed += want
            print(f'  {"killed" if want else "passed"}: {label}')
        else:
            survived += 1
            print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

    def mut(f):
        dd = copy.deepcopy(d)
        f(dd)
        return dd

    expect("the committed read (control)", d, False)
    expect("a Perfect Clear time out of order", mut(lambda x: x["pcs"]["t"].__setitem__(1, x["pcs"]["t"][0] - 1)), True)
    expect("a read naming no board", mut(lambda x: x["reads"][0].__setitem__("board", "stickspin:2.ideal")), True)
    expect("a read in the wrong stretch", mut(lambda x: x["reads"][0].__setitem__("segment", 5)), True)
    expect("the route out of order", mut(lambda x: x["reads"].__setitem__(slice(0, 2), [
        {**x["reads"][0], "board": "stickspin:bag1.pc"}, {**x["reads"][1], "board": "stickspin:bag1.left"}])), True)
    i = next(i for i, r in enumerate(d["reads"]) if r["board"].endswith("+T"))
    expect("a DPC T in the other hand", mut(lambda x: x["reads"][i].__setitem__("mirrored", not x["reads"][i]["mirrored"])), True)
    j = next(i for i, r in enumerate(d["reads"]) if r["board"].startswith("dpc:"))
    expect("a DPC read moved into an SDPC stretch",
           mut(lambda x: x["reads"][j].update(frame=x["reads"][j - 1]["frame"] + 1, segment=x["reads"][j - 1]["segment"])), True)
    expect("a read past the reader", mut(lambda x: x["reads"][-1].__setitem__("frame", 10 ** 6)), True)
    expect("another DPC setup", mut(lambda x: x["loop"]["dpc"].__setitem__("setup", "p07.000")), True)
    expect("report_eligible true", mut(lambda x: x.__setitem__("report_eligible", True)), True)
    print(f"selftest: {killed} killed, {survived} survived")
    return 1 if survived else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--video")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    d, (st, dp) = load(), transcriptions()
    bad = check(d, st, dp)
    if a.video:
        got = read_video(a.video, d, st, dp)
        if got != d["reads"]:
            bad.append(f"the video reads {len(got)} boards, not the committed {len(d['reads'])}: "
                       f"{[g for g in got if g not in d['reads']][:3]} / {[r for r in d['reads'] if r not in got][:3]}")
    sd, dc, sl, dl, _ = loop_arithmetic(d, st, dp)
    for b in bad:
        print(f"FAIL {b}", file=sys.stderr)
    print(f"sdpc loop: {len(d['pcs']['t'])} Perfect Clears, {len(d['reads'])} reads, {len(laps(d))} whole loops read; "
          f"SDPC {sl} lines = {sd} pieces, DPC {dl} lines = {dc} pieces" + (" (video re-read)" if a.video else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
