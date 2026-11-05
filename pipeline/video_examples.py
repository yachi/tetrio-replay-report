"""The 「影片實戰例子」 section: the boards read off one match video (`pipeline/openers/video-examples.json`), drawn on
the DPC page and on each technique page that has one, beside the source drawings and never mixed into them.

    python3 -m pipeline.video_examples --selftest   # plant the corruptions the audit must catch

`section(page)` renders the section for one page key (`dpc`, or a technique page's prefix) and returns no lines
when the page has no example. `audit(html, page)` checks a rendered page: the section's sentences are there,
every example filed under the page is drawn exactly once (`data-vexample`) with its own video link, and nothing
else is. The data is gated by `pipeline/openers/check_video_examples.py` and `video-examples.test.ts`; this
module only draws it. Strings are in `video_examples_prose.json`.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "pipeline", "openers", "video-examples.json")
PROSE_PATH = os.path.join(REPO, "pipeline", "video_examples_prose.json")
SETUPS = os.path.join(REPO, "pipeline", "openers", "dpc-setups.json")
_EX = re.compile(r'data-vexample="([^"]+)"')


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _esc(s):
    return html.escape(str(s), quote=True)


def mmss(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def link(doc, t):
    return f"https://youtu.be/{doc['source']['video']}?t={max(0, int(t) - 3)}"


def board_rows(b, extra=()):
    """The board as `board_svg` rows, cropped: from one row over the stack (or the T) down to two rows under the
    lowest non-garbage cell, the cleared rows and the cells named in `extra`."""
    rows, lock = b["rows"], {tuple(x) for x in b["t_cells"]}
    top = min([r for r in range(20) if rows[r].strip(".?")] + [min(r for r, _ in lock)])
    low = max([r for r in range(20) if set(rows[r]) - set(".?G")] + list(b["cleared"])
              + [r for r, _ in lock] + [r for r, _ in extra])
    out = []
    for r in range(max(0, top - 1), min(20, low + 3)):
        out.append("".join("U" if (r, c) in lock else "-" if ch in ".?" else "c" if ch == "G" else ch.lower()
                           for c, ch in enumerate(rows[r])))
    return out


def examples_for(doc, page):
    if page == "dpc":
        return [(f"{e['board']}/dpc", e) for e in doc["dpc_examples"]]
    return [(f"{e['board']}/{e['page']}/{e['variant']}", e) for e in doc["technique_examples"] if e["page"] == page]


def _card(doc, P, ex_id, b, head, tags, extra=()):
    from pipeline import route_page as RT
    name = f"{P['side'][b['side']]} · {mmss(b['t'])} · {P['spin'][str(b['lines'])]}"
    bits = [f'    <div class="scp-node" data-vexample="{_esc(ex_id)}"><h4 class="scp-name">{_esc(name)}</h4>',
            RT.board_svg(board_rows(b, extra), f"{name} {head}", RT.PIECE_CLASS)]
    bits += [f'<p class="scp-tag">{_esc(t)}</p>' for t in tags]
    bits.append(f'<p class="scp-tag"><a href="{_esc(link(doc, b["t"]))}">{_esc(P["link"].format(mmss=mmss(b["t"])))}</a></p></div>')
    return "".join(bits)


def section(page, doc=None, P=None):
    doc = doc or _load(DATA)
    P = P or _load(PROSE_PATH)
    exs = examples_for(doc, page)
    if not exs:
        return []
    boards = {b["id"]: b for b in doc["boards"]}
    S = P["sentences"]
    out = ['  <section class="scp-sec" id="video-examples">', f'    <h2>{_esc(P["title"])}</h2>']
    out += [f"    <p>{_esc(S[k])}</p>" for k in ("source", "quarantine", "approx", "unread")]
    if page == "dpc":
        out.append(f"    <p>{_esc(P['dpc_sentence'])}</p>")
        names = {s["id"]: s["heading"][0] for s in _load(SETUPS)["setups"]}
        for kind in ("matched", "near", "new", "late"):
            mine = [(i, e) for i, e in exs if e["kind"] == kind]
            if not mine:
                continue
            out += [f'    <h3>{_esc(P["dpc_head"][kind])}</h3>', '    <div class="scp-grid">']
            for i, e in mine:
                b = boards[e["board"]]
                tags = [P["pc"].format(pc=mmss(e["pc_t"]), gap=e["gap_s"])]
                hits = e["setups"] or e["near_setups"]
                if hits:
                    tags.append(P["setups"] + "、".join(dict.fromkeys(
                        names[s] + (f"（{P['mirrored']}）" if m else "") for s, m in hits)))
                if e.get("note"):
                    tags.append(e["note"])
                if e["pc_after"]:
                    tags.append(P["pc_after"])
                out.append(_card(doc, P, i, b, P["dpc_head"][kind], tags))
            out.append("    </div>")
    else:
        for verdict in ("qualifies", "rejected"):
            mine = [(i, e) for i, e in exs if e["verdict"] == verdict]
            if not mine:
                continue
            out += [f'    <h3>{_esc(P["technique_head"][verdict])}</h3>', '    <div class="scp-grid">']
            for i, e in mine:
                b = boards[e["board"]]
                nm = P["variants"].get(e["variant"], P["pages"][e["page"]])
                tags = [nm + (f" · {P['mirrored']}" if e["mirrored"] else "")]
                if e["reasons"]:
                    tags.append("；".join(P["reasons"][r] for r in e["reasons"]))
                others = [P["variants"].get(o["variant"], P["pages"][o["page"]]) for o in doc["technique_examples"]
                          if o["board"] == e["board"] and o is not e]
                if others:
                    tags.append(P["also"] + "、".join(others))
                out.append(_card(doc, P, i, b, P["technique_head"][verdict], tags,
                                 [tuple(x) for x in e["key_cells"]]))
            out.append("    </div>")
    out.append("  </section>")
    return out


def audit(page_html, page, doc=None, P=None):
    doc = doc or _load(DATA)
    P = P or _load(PROSE_PATH)
    want = sorted(i for i, _ in examples_for(doc, page))
    got = sorted(html.unescape(x) for x in _EX.findall(page_html))
    bad = []
    if got != want:
        bad.append(f"the video section does not draw each of this page's {len(want)} examples exactly once "
                   f"({len(got)} drawn)")
    if want:
        for k, s in P["sentences"].items():
            if _esc(s) not in page_html:
                bad.append(f"the video section's {k} sentence is missing")
        boards = {b["id"]: b for b in doc["boards"]}
        for i, e in examples_for(doc, page):
            m = re.search(r'data-vexample="' + re.escape(_esc(i)) + r'">.*?</div>', page_html, re.S)
            if m and f'href="{_esc(link(doc, boards[e["board"]]["t"]))}"' not in m.group(0):
                bad.append(f"{i}: drawn without its video link")
    return bad


def selftest():
    doc, P = _load(DATA), _load(PROSE_PATH)
    pages = ["dpc"] + sorted({e["page"] for e in doc["technique_examples"]})
    fails = []
    for pg in pages:
        h = "\n".join(section(pg, doc, P))
        if audit(h, pg, doc, P):
            print(f"  control FAILED on {pg}: {audit(h, pg, doc, P)}")
            return 1
    h = "\n".join(section("stmbcave", doc, P))
    first = _EX.search(h).group(1)
    card = re.search(r'    <div class="scp-node" data-vexample="' + re.escape(first) + r'">.*?</div>', h, re.S).group(0)
    m = re.search(r"\?t=(\d+)", card)
    cases = [
        ("an example dropped", "stmbcave", h.replace(card, "")),
        ("an example drawn twice", "stmbcave", h.replace(card, card + "\n" + card)),
        ("a video link one second off", "stmbcave", h.replace(card, card.replace(m.group(0), f"?t={int(m.group(1)) + 1}"))),
        ("a sentence deleted", "stmbcave", h.replace(_esc(P["sentences"]["quarantine"]), "")),
        ("one page's section on another page", "stsd", h),
        ("the section on a page with no example", "doubledagger", h),
    ]
    for label, pg, x in cases:
        caught = bool(audit(x, pg, doc, P))
        print(f"  {'caught' if caught else 'SURVIVED'}: {label}")
        if not caught:
            fails.append(label)
    print(f"{len(fails)} survivor(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(selftest())
    sys.exit("usage: python3 -m pipeline.video_examples --selftest")
