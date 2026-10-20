"""中盤手法頁 — the shared MID-GAME TECHNIQUE PAGES renderer: for one shiwehi.com technique page (STSD,
…) one overview and one constructed-demo page, each audited before it is returned.

    python3 -m pipeline.stsd_page --out-dir /tmp/stsd   # STSD's pages, through its profile module
    python3 -m pipeline.stsd_page --selftest            # its audit's mutants

ONE RENDERER, ONE AUDIT. A `TechniqueSite` is this module bound to one technique's
`TechniqueSiteProfile` (file names, schemas, the variant, the board letters) and its prose file. It is
a SIBLING of `route_page.py`, not a profile of it: a technique page has no bags, no route tree and no
per-node case pages, so it imports the route renderer's low-level pieces (`board_svg`, the page CSS,
the island and tail, the source line, `demo_slug`, `PAGE_JS`) and edits none of them — no route page
moves because a technique exists.

Inputs, all committed: the technique's transcription (`pipeline/openers/<x>-technique.json`, gated by
`technique_transcription.py`), its corpus artefact (`technique-facts.ts`) and its demo artefact
(`technique-demos.ts`). Pure Python, so `bin/build-docs` renders it in the `docs` job, which has no
bun. The overview embeds no replay: each case links to its night's `<date>-replay.html#m<pos>r<round>@p<n>`,
an anchor that page already reads, where `<n>` is the round's MERGED lock position (both players' locks in
the replay page's frame order, `replay_section.round_payload`'s `order`) just before the hit's T: the page
opens on the board the T went into, and stepping once plays the T. The audit re-reads every link from the
other side — the lock the position's next step plays is decoded with `replay_section.decode_boards` and must
be the hit player's T, at the hit's lock index, with a full spin clearing the variant's lines.

QUARANTINE. Simulator output, the replay pages' tier: no claim ids, no ✓, no `data-claim`, and both
artefacts must say `report_eligible: false` (the demos `constructed: true` as well). The audit reuses
`replay_page.audit_quarantine` / `audit_player` — one copy of each rule — and adds its own:

* every transcribed board appears exactly once on the overview, and exactly once on the demo page
  (reached by a demo, or unbuilt with its reason);
* every hit is indexed exactly once;
* every figure (`data-figure`) is the artefact's, and the hit-derived ones are RE-COUNTED from the
  hit list rather than read from the aggregates the renderer printed, so the two halves of the
  artefact must agree for the page to render;
* the control sentence is present whenever the headline table is (a shape test printed without its
  controls reads as a finding);
* the only `%` are inside quoted source text, and no simplified glyph anywhere;
* each embedded demo is decoded again with `replay_section.decode_boards` (a second implementation
  of the bun test's `reachProblems`) and must stand on every board it claims.

FIGURES. Counts only, rendered from the artefacts, always 「N / M」 with the denominator. No rate is
computed, so no rounding rule is exercised.
"""
import argparse
import html
import json
import os
import re
from dataclasses import dataclass, field

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline import route_page as RT
from pipeline.claims.build_claims import SIMPLIFIED

HERE, REPO = RT.HERE, RT.REPO
_esc, _src, board_svg, demo_slug = RT._esc, RT._src, RT.board_svg, RT.demo_slug
DATA_ID, TEMPLATE_ID = RT.DATA_ID, RT.TEMPLATE_ID

_FIGURE = re.compile(r'data-figure="([^"]+)">([^<]*)<')
_BOARD = re.compile(r'data-board="([^"]+)"')
_CASE = re.compile(r'data-case="([^"]+)"')
_CASE_LINK = re.compile(r'<tr data-case="([^"]+)">.*?<a href="([^"]+)">')
_REPLAY_HREF = re.compile(r'^(\d{4}-\d{2}-\d{2})-replay\.html#(m\d+r\d+)@p(\d+)$')
_DEMO_BLOCK = re.compile(r'data-demo-node="([^"]+)" data-demo="(built|unbuilt)"')
_REACH = re.compile(r'data-reach="([^"]+)"')
_SRC_QUOTE = re.compile(r'<q class="scp-src">.*?</q>', re.S)
_TAG = re.compile(r"<[^>]+>")


@dataclass
class TechniqueSiteProfile:
    """One technique's half of the pages. Every reader-visible string is in the prose file."""
    module: str
    #: docs file prefix: `<prefix>.html` and `<prefix>-demos.html`
    prefix: str
    transcription_rel: str
    facts_rel: str
    demos_rel: str
    prose_path: str
    transcription_schema: str
    facts_schema: str
    demos_schema: str
    #: the variant every figure is about, and the denominators key of its opportunity
    variant: str
    opportunity: str
    #: board letters beyond route_page.PIECE_CLASS, and the CSS for them
    cell_classes: dict = field(default_factory=dict)
    extra_css: str = ""
    max_page_bytes: int = 0
    #: the board the selftest drops from the overview (any id the transcription draws)
    selftest_board: str = "basic.after"
    #: further variants the overview prints, each `(variant id, denominators key of its opportunity)` (欄干: its
    #: TSS). Their figures are keyed `<id>:<key>`, their sections take `more_variants.<id>.sections` from the prose
    more_variants: tuple = ()
    #: opt-in: a 精選 section before the primary variant's cases, every hit of it with no garbage in the window and
    #: the follow-up fired, drawn from the replay at four moments (千鳥格子)
    showcase: bool = False
    #: opt-in: boards of OURS found by `technique-own.ts`'s search, played on the demo page after the drawn boards'
    #: demos (千鳥格子). Empty: no own-design section, and the page is byte for byte what it was
    own_rel: str = ""
    own_schema: str = "technique-own/1"
    #: opt-in: games cold-clear played ALONE in which the corpus classifier finds a hit (`cutcopy-selfplay.ts`),
    #: played on the demo page after the own designs (千鳥格子). Empty: no self-play section, and the page is byte
    #: for byte what it was
    selfplay_rel: str = ""
    selfplay_schema: str = "technique-selfplay/1"


def case_key(h):
    return f"{h['session']} m{h['match']}r{h['round']} {h['player']} lock {h['lock']}"


def _nn(n, m):
    return f"{n} / {m}"


class TechniqueSite:
    """The pages of one technique: this module's renderer and audit bound to one profile."""

    def __init__(self, p: TechniqueSiteProfile):
        self.p = p
        self.OVERVIEW = f"{p.prefix}.html"
        self.DEMO_PAGE = f"{p.prefix}-demos.html"
        self.PROSE = self.load_prose(p.prose_path)
        PS = self.PS = self.PROSE["page_sentences"]
        self.PAGE_SENTENCES = (PS["source"], PS["midgame"], PS["window"], PS["garbage"], PS["our_reading"])
        self.OVERVIEW_REQUIRED = ((RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, RS.HOLE_SENTENCE)
                                  + self.PAGE_SENTENCES + (PS["control"],))
        self.DP = self.PROSE["demo"]
        DS = self.DP["sentences"]
        self.DEMO_SENTENCES = (DS["demo"], DS["engine"], DS["base"], DS["order"], DS["rule"])
        self.DEMO_REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, PS["source"]) + self.DEMO_SENTENCES
        self.CLASSES = {**RT.PIECE_CLASS, **p.cell_classes}
        self.OW = self.PROSE["own"] if p.own_rel else None
        self.SP = self.PROSE["selfplay"] if p.selfplay_rel else None
        #: every variant the pages print, the primary first: (variant id, its opportunity's denominators key)
        self.VARIANTS = ((p.variant, p.opportunity),) + tuple(p.more_variants)

    # ------------------------------------------------------------ inputs

    def _need(self, cond, msg):
        if not cond:
            raise SystemExit(f"{self.p.module}: {msg}")

    def _no_simplified(self, text, where):
        bad = sorted(set(text) & SIMPLIFIED)
        self._need(not bad, f"{where}: simplified glyph(s) {bad} — this report is traditional-character Cantonese")
        return text

    def load_prose(self, path):
        with open(path, encoding="utf-8") as fh:
            prose = json.load(fh)
        for s in RT._walk_strings(prose):
            self._no_simplified(s, os.path.basename(path))
        return prose

    def load_inputs(self, repo=REPO):
        """(transcription, facts artefact, demos artefact)."""
        out = []
        for rel in (self.p.transcription_rel, self.p.facts_rel, self.p.demos_rel):
            with open(os.path.join(repo, rel), encoding="utf-8") as fh:
                out.append(json.load(fh))
        return tuple(out)

    def check_inputs(self, tr, art, demos):
        self._need(tr.get("schema") == self.p.transcription_schema, f"unknown transcription schema {tr.get('schema')!r}")
        self._need(art.get("schema") == self.p.facts_schema, f"unknown facts schema {art.get('schema')!r}")
        self._need(demos.get("schema") == self.p.demos_schema, f"unknown demos schema {demos.get('schema')!r}")
        self._need(art.get("report_eligible") is False,
                   f"{os.path.basename(self.p.facts_rel)} must declare report_eligible: false — simulator boards "
                   "are not trust-chain data")
        self._need(demos.get("report_eligible") is False and demos.get("constructed") is True,
                   f"{os.path.basename(self.p.demos_rel)} must declare report_eligible: false and constructed: true")
        for vid, _opp in self.VARIANTS:
            self._need(vid in art["variants"], f"the facts artefact has no variant {vid!r}")

    def variant(self, tr, vid=None):
        vid = vid or self.p.variant
        v = [x for x in tr["variants"] if x["id"] == vid]
        self._need(len(v) == 1, f"the transcription has {len(v)} variants {vid!r}")
        return v[0]

    def _key(self, vid):
        # a variant's figure-key prefix: none for the primary, so a one-variant page is unchanged
        return "" if vid == self.p.variant else vid + ":"

    def name(self, nid):
        names = self.PROSE["names"]
        self._need(nid in names, f"no Cantonese name for board {nid!r} in the prose file")
        return names[nid]

    # ------------------------------------------------------------ figures

    def figures(self, art):
        """Every figure the overview prints, by key, from the artefact's AGGREGATES."""
        out = {}
        for vid, opp in self.VARIANTS:
            out.update({self._key(vid) + k: x for k, x in self._figures(art, vid, opp).items()})
        cr = art.get("cross_route")
        if cr:
            out["cross"] = _nn(cr["with_hit"], cr["rounds_scored"])
        if self.p.showcase:
            out["showcase"] = _nn(len(self.showcase_hits(art)), len([h for h in art["hits"] if h["variant"] == self.p.variant]))
        return out

    def _figures(self, art, vid, opp):
        v = art["variants"][vid]
        den = art["denominators"]
        out = {}
        for u in sorted(den):
            h = v["hits_by_player"][u]
            for k in ("all", "in_opener", "mid_game"):
                out[f"hits.{u}.{k}"] = _nn(h[k], den[u][opp][k])
            out[f"mirrored.{u}"] = _nn(h["mirrored"], h["all"])
            out[f"garbage.{u}"] = _nn(h["garbage_in_window"], h["all"])
            f = v["followup_by_player"][u]
            out[f"fired.{u}"] = _nn(f["fired"], h["all"])
            for r, n in f["not_fired"].items():
                out[f"reason.{u}.{r}"] = _nn(n, h["all"])
            c = v["controls"]
            for kind, by in c["under"].items():
                out[f"under.{kind}.{u}"] = _nn(by[u], den[u][kind]["all"])
            for ab, by in c["ablation"].items():
                out[f"ablation.{ab}.{u}"] = _nn(by[u], den[u][opp]["all"])
            out[f"baseline.{u}"] = _nn(c["orientation_baseline"][u], den[u][opp]["all"])
        return out

    def recount(self, art):
        """The hit-derived figures again, RE-COUNTED from the hit list (the audit's half): the
        renderer prints the aggregates, so the page renders only when the two agree."""
        out = {}
        for vid, opp in self.VARIANTS:
            out.update({self._key(vid) + k: x for k, x in self._recount(art, vid, opp).items()})
        cr = art.get("cross_route")
        if cr:
            out["cross"] = _nn(sum(r["outcome"] == "hit" for r in cr["by_round"]),
                               sum(r["outcome"] in ("hit", "no_hit") for r in cr["by_round"]))
        if self.p.showcase:
            prim = [h for h in art["hits"] if h["variant"] == self.p.variant]
            out["showcase"] = _nn(sum(not h["garbage_in_window"] and h["followup"]["fired"] for h in prim), len(prim))
        return out

    def _recount(self, art, vid, opp):
        v = art["variants"][vid]
        den = art["denominators"]
        hits = [h for h in art["hits"] if h["variant"] == vid]
        out = {}
        for u in sorted(den):
            mine = [h for h in hits if h["player"] == u]
            out[f"hits.{u}.all"] = _nn(len(mine), den[u][opp]["all"])
            out[f"hits.{u}.in_opener"] = _nn(sum(h["in_opener"] for h in mine), den[u][opp]["in_opener"])
            out[f"hits.{u}.mid_game"] = _nn(sum(not h["in_opener"] for h in mine), den[u][opp]["mid_game"])
            out[f"mirrored.{u}"] = _nn(sum(h["mirrored"] for h in mine), len(mine))
            out[f"garbage.{u}"] = _nn(sum(h["garbage_in_window"] for h in mine), len(mine))
            out[f"fired.{u}"] = _nn(sum(h["followup"]["fired"] for h in mine), len(mine))
            for r in sorted({h["followup"]["reason"] for h in mine if not h["followup"]["fired"]}):
                out[f"reason.{u}.{r}"] = _nn(sum(h["followup"]["reason"] == r for h in mine), len(mine))
            c = v["controls"]
            for kind, by in c["under"].items():
                out[f"under.{kind}.{u}"] = _nn(by[u], den[u][kind]["all"])
            for ab, by in c["ablation"].items():
                out[f"ablation.{ab}.{u}"] = _nn(by[u], den[u][opp]["all"])
            out[f"baseline.{u}"] = _nn(c["orientation_baseline"][u], den[u][opp]["all"])
        return out

    # ------------------------------------------------------------ replay positions

    def _replay_round(self, session, file, round_index0):
        """One round of a night's replay page, read the way that page reads it: its label, its merged lock
        order, its players in slot order, and per player each lock's (piece, lines, spin). Cached."""
        rounds = self.__dict__.setdefault("_rounds", {})
        sessions = self.__dict__.setdefault("_sessions", {})
        key = (session, file, round_index0)
        if key in rounds:
            return rounds[key]
        if session not in sessions:
            data, facts = RP.load(os.path.join(self._repo, "sessions", session))
            self._need(data is not None, f"{session} has no replay facts, so a hit cannot be linked to its moment")
            RS.check_artefact(data)
            sessions[session] = (data, facts)
        self._sessions_cache = sessions
        data, facts = sessions[session]
        at = [(mi, ri) for mi, m in enumerate(facts["matches"]) if m["file"] == file
              for ri, fr in enumerate(m["rounds"]) if fr["index"] == round_index0]
        self._need(len(at) == 1, f"{session} {file} round {round_index0}: {len(at)} rounds in facts.json")
        pl = RS.round_payload(data, facts, *at[0])
        locks = {}
        for p in pl["players"]:
            dec = RS.decode_boards(data, pl["seq"], p["locks"], RS.NEXT_SHOWN)
            locks[p["user"]] = [(piece, len(full), lk[3]) for lk, (piece, full, _b) in zip(p["locks"], dec)]
        rounds[key] = {"label": pl["label"], "order": pl["order"],
                       "users": [p["user"] for p in pl["players"]], "locks": locks}
        return rounds[key]

    def _round_boards(self, h):
        """The hit player's boards through the round, read the way the replay page reads them: per lock the
        piece, its cells (y-UP cell indices) and a copy of the board after it. Cached."""
        boards = self.__dict__.setdefault("_boards", {})
        key = (h["session"], h["file"], h["round_index0"], h["player"])
        if key not in boards:
            self._replay_round(h["session"], h["file"], h["round_index0"])
            data, facts = self._sessions_cache[h["session"]]
            at = [(mi, ri) for mi, m in enumerate(facts["matches"]) if m["file"] == h["file"]
                  for ri, fr in enumerate(m["rounds"]) if fr["index"] == h["round_index0"]]
            pl = RS.round_payload(data, facts, *at[0])
            p = [p for p in pl["players"] if p["user"] == h["player"]][0]
            b = data["board"]
            out = []
            for lk, (piece, _full, board) in zip(p["locks"], RS.decode_boards(data, pl["seq"], p["locks"], RS.NEXT_SHOWN)):
                cells = RS._place_cells(data["shapes"], b["width"], b["rows"], piece, lk[1])
                out.append((piece, sorted(cells), [list(r) for r in board]))
            boards[key] = out
        return boards[key]

    def showcase_hits(self, art):
        """THE RULE: every hit of the primary variant with no garbage in its window and its follow-up fired."""
        return [h for h in art["hits"] if h["variant"] == self.p.variant and not h["garbage_in_window"]
                and h["followup"]["fired"]]

    @staticmethod
    def _rows_of(board, mark, height):
        """A y-UP board as rows top first, `height` rows from the floor, piece letters lower case, garbage
        grey, the cells in `mark` drawn as the dashed slot."""
        rows = []
        for y in range(height - 1, -1, -1):
            line = ""
            for x in range(len(board[0])):
                v = board[y][x]
                c = y * len(board[0]) + x
                line += "U" if c in mark else ("-" if v is None else ("c" if v == "G" else v.lower()))
            rows.append(line)
        return rows

    def showcase_moments(self, h):
        """The four boards of one showcased hit: before its T (the T's cells dashed), after it, before the
        follow-up T (its cells dashed), after it."""
        bs = self._round_boards(h)
        k, f = h["lock"], h["followup"]["lock"]
        before = bs[k - 1][2] if k else [[None] * 10 for _ in range(40)]
        moments = [(before, set(bs[k][1])), (bs[k][2], set()), (bs[f - 1][2], set(bs[f][1])), (bs[f][2], set())]
        top = max([y + 1 for b, m in moments for y in range(len(b)) if any(v is not None for v in b[y])]
                  + [c // 10 + 1 for _b, m in moments for c in m])
        return [self._rows_of(b, m, top + 1) for b, m in moments]

    def _showcase(self, tr, art):
        PR = self.PROSE
        SC = PR["showcase"]
        hits = self.showcase_hits(art)
        out = ['  <section class="scp-sec">', f'    <h2>{_esc(SC["title"])}</h2>',
               f'    <p>{_esc(SC["note"])}</p>',
               f'    <p class="scp-count" data-figure="showcase">{_esc(self.figures(art)["showcase"])}</p>']
        for h in hits:
            ck, rnd = case_key(h), f"m{h['match']}r{h['round']}"
            out += [f'    <div data-showcase="{_esc(ck)}">',
                    f'    <h3>{_esc(SC["case"].format(date=h["session"], round=rnd, player=h["player"], lock=h["lock"], followup=h["followup"]["lock"]))}'
                    f'（<a href="{_esc(self.replay_href(h))}">{_esc(SC["link"])}</a>）</h3>',
                    '    <div class="scp-grid">']
            for words, rows in zip(SC["moments"], self.showcase_moments(h)):
                out.append(f'    <div class="scp-node"><h4 class="scp-name">{_esc(words)}</h4>'
                           f'{board_svg(rows, f"{ck} {words}", self.CLASSES)}</div>')
            out += ["    </div>", "    </div>"]
        out += ["  </section>"]
        return out

    def audit_showcase(self, page, tr, art):
        """The showcase is the rule's set, in artefact order, and each first board fires the window — read by
        the Python twin of the matcher (`technique_transcription.window_fires`), not by the TS one that found
        the hit — at the dashed T, in the hit's hand."""
        from types import SimpleNamespace
        from pipeline.openers.technique_transcription import window_fires
        bad = []
        want = [case_key(h) for h in self.showcase_hits(art)]
        got = [html.unescape(x) for x in re.findall(r'data-showcase="([^"]+)"', page)]
        if got != want:
            bad.append(f"the showcase lists {got}, the rule gives {want}")
        spec = SimpleNamespace(empty_letters=tr.get("empty_letters", ""))
        v = self.variant(tr)
        for h in self.showcase_hits(art):
            rows = self.showcase_moments(h)[0]
            lock = {(r, c) for r, line in enumerate(rows) for c, ch in enumerate(line) if ch == "U"}
            board = [line.replace("U", "-") for line in rows]
            if window_fires(tr, v, spec, board, lock, h["mirrored"]) is not True:
                bad.append(f"{case_key(h)}: the window does not fire on the board drawn before its T")
        return bad

    def replay_href(self, h):
        """The hit's link: its night's replay page, its round, at the merged position just BEFORE its T lock
        (the replay page's `@p<n>`: n locks of both players placed, so the hit player's next lock is the T)."""
        r = self._replay_round(h["session"], h["file"], h["round_index0"])
        self._need(r["label"] == f"m{h['match']}r{h['round']}",
                   f"{case_key(h)}: the replay page labels this round {r['label']}")
        self._need(h["player"] in r["users"], f"{case_key(h)}: {h['player']} is not in the replay round")
        slot = str(r["users"].index(h["player"]))
        mine = [n for n, s in enumerate(r["order"]) if s == slot]
        self._need(0 <= h["lock"] < len(mine), f"{case_key(h)}: lock {h['lock']} is past the round's locks")
        return f'{h["session"]}-replay.html#{r["label"]}@p{mine[h["lock"]]}'

    def audit_replay_links(self, page, tr, art):
        """Every case row's link, read back from the replay side: the position's next step must be the hit
        player's lock at the hit's lock index, and that lock (decoded from an empty board) a T with a full
        spin clearing the variant's lines."""
        bad = []
        hits = {case_key(h): h for h in art["hits"]}
        lines = {v["id"]: v["lines"] for v in tr["variants"]}
        for ck, href in _CASE_LINK.findall(page):
            ck, href = html.unescape(ck), html.unescape(href)
            h = hits.get(ck)
            m = _REPLAY_HREF.match(href)
            if h is None or not m:
                bad.append(f"{ck}: the case link {href!r} is not a replay link at a position")
                continue
            if m.group(1) != h["session"] or m.group(2) != f"m{h['match']}r{h['round']}":
                bad.append(f"{ck}: the case link {href!r} names another night or round")
                continue
            r = self._replay_round(h["session"], h["file"], h["round_index0"])
            n = int(m.group(3))
            if n >= len(r["order"]):
                bad.append(f"{ck}: position {n} is past the round's {len(r['order'])} locks")
                continue
            slot = r["order"][n]
            k = r["order"][:n].count(slot)
            user = r["users"][int(slot)]
            piece, cleared, spin = r["locks"][user][k]
            if user != h["player"] or k != h["lock"]:
                bad.append(f"{ck}: position {n} steps into {user}'s lock {k}, not the hit's T")
            elif piece != "T" or spin != 2 or cleared != lines[h["variant"]]:
                bad.append(f"{ck}: position {n} steps into a {piece} (spin {spin}, {cleared} lines), not a full "
                           f"T-spin clearing {lines[h['variant']]}")
        if len(_CASE_LINK.findall(page)) != len(_CASE.findall(page)):
            bad.append("a case row carries no replay link")
        return bad

    # ------------------------------------------------------------ page shell

    def _head(self, title, desc, users, with_player):
        css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), RT.PAGE_CSS.strip("\n")]
        if self.p.extra_css:
            css.append(self.p.extra_css.strip("\n"))
        if with_player:
            css += [RS._color_css([{"user": u} for u in users]), RS.CSS.strip("\n")]
        return [
            "<!doctype html>",
            '<html lang="zh-HK">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_esc(title)}</title>",
            f'<meta name="description" content="{_esc(desc)}">',
            "<style>",
            "  " + "\n".join(css),
            "</style>",
            "</head>",
            "<body>",
            '<div class="wrap-wide">',
        ]

    def _nav(self, other_href, other_words):
        return ['  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a>'
                f'<a href="{_esc(other_href)}">{_esc(other_words)}</a></nav>']

    def _window_rows(self, tr, v, mirrored):
        rows = [n for n in tr["nodes"] if n["id"] == v["board"]][0]["rows"]
        empties = tr.get("empty_letters", "")
        (r0, r1), (c0, c1) = v["window"]["rows"], v["window"]["cols"]
        tcells = {(r, c) for r, c in v["t_cells"]}
        out = []
        for r in range(r0, r1 + 1):
            line = ""
            for c in range(c0, c1 + 1):
                ch = rows[r][c]
                line += "U" if (r, c) in tcells else ("-" if ch == "-" or ch in empties else "c")
            out.append(line[::-1] if mirrored else line)
        return out

    def _thumb(self, tr, v, h):
        """A hit's window before the T, its letters as the artefact records them, the T's cells as the
        dashed slot (mirrored with the window)."""
        (r0, _r1), (c0, c1) = v["window"]["rows"], v["window"]["cols"]
        w = c1 - c0
        tcells = {(r - r0, (w - (c - c0)) if h["mirrored"] else (c - c0)) for r, c in v["t_cells"]}
        rows = []
        for r, line in enumerate(h["window_letters"]):
            s = ""
            for c, ch in enumerate(line):
                if (r, c) in tcells:
                    s += "U"
                elif ch == ".":
                    s += "-"
                elif ch == "G":
                    s += "c"
                else:
                    s += ch.lower()
            rows.append(s)
        return board_svg(rows, case_key(h), self.CLASSES)

    # ------------------------------------------------------------ the overview

    def render_overview(self, tr, art, demos):
        PR, T, S = self.PROSE, self.PROSE["table"], self.PROSE["sections"]
        fig = self.figures(art)
        users = sorted(art["denominators"])
        title = f"{PR['title']}{RS.TITLE_MARK}"
        out = self._head(title, PR["desc"], users, False)
        out += self._nav(self.DEMO_PAGE, self.DP["title"])
        out += ['  <header class="scp-head">',
                f'    <div class="eyebrow">{RS.EYEBROW}</div>',
                f'    <h1 class="section-title">{_esc(title)}</h1>',
                f'    <p>{_esc(PR["lede"])}</p>',
                RT._source_line(tr, PR.get("source_credit")),
                '  </header>',
                '  <div class="method-note">',
                '    <p><strong>呢版唔屬於信任鏈。</strong>每個盤面都係<strong>一個 replay 模擬器</strong>'
                '（Triangle 引擎）重跑操作記錄推導出嚟，冇第二份獨立實作；邊一下 TSD 對到呢個形亦係由佢推出嚟。'
                f'所以呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
        out += [f"    <p>{s}</p>" for s in self.PAGE_SENTENCES]
        out += [f"    <p>{RS.HOLE_SENTENCE}</p>", "  </div>"]

        # 1. the boards, page order then the derived terrains
        quotes = {q["id"]: q["verbatim"] for q in tr["quotes"]}
        disc = {d["id"].split(":")[0]: d["id"] for d in tr["known_discrepancies"]}
        order = list(tr["page_order"]) + [n["id"] for n in tr["nodes"] if n["id"] not in tr["page_order"]]
        by_id = {n["id"]: n for n in tr["nodes"]}
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["boards"])}</h2>',
                f'    <p class="scp-quote">{_esc(S["boards_note"])}</p>', '    <div class="scp-grid">']
        for nid in order:
            n = by_id[nid]
            bits = [f'<div class="scp-node" data-board="{_esc(nid)}">', f'<h4 class="scp-name">{_esc(self.name(nid))}</h4>']
            if n.get("caption_quote"):
                bits.append(f'<p class="scp-jp">原頁：{_src(quotes[n["caption_quote"]])}</p>')
            bits.append(board_svg(n["rows"], self.name(nid), self.CLASSES))
            if n.get("derived"):
                bits.append(f'<p class="scp-tag">{_esc(PR["derived_note"])}</p>')
            if n.get("external"):
                # opt-in: a board another site draws, transcribed into the file (千鳥格子's harddrop variant)
                bits.append(f'<p class="scp-tag">{_esc(PR["external_note"])}</p>')
            if nid in disc:
                bits.append(f'<p class="scp-tag">{_esc(PR["discrepancies"][disc[nid]])}</p>')
            bits.append("</div>")
            out.append("    " + "".join(bits))
        out += ["    </div>", "  </section>"]

        # 2-5, per variant (the primary's here, then the cross-source, then its cases; a further
        # variant's sections and cases after the primary's)
        parts = {vid: self._variant_sections(tr, art, vid, opp, fig, users) for vid, opp in self.VARIANTS}
        out += parts[self.p.variant][0]

        # 6. the cross-source
        cr = art.get("cross_route")
        if cr:
            out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["cross"])}</h2>',
                    f'    <p>{_esc(S["cross_note"])}</p>',
                    f'    <p class="scp-count" data-figure="cross">{_esc(fig["cross"])}</p>',
                    '    <div class="scp-index-wrap"><table class="scp-table">',
                    f'    <tr><th>{_esc(T["cross_round"])}</th><th>{_esc(T["cross_node"])}</th>'
                    f'<th>{_esc(T["cross_hit"])}</th><th>{_esc(T["reason"])}</th></tr>']
            CR = PR["cross_reasons"]
            for r in cr["by_round"]:
                fields = dict(r, last=cr["continuation"]["last_lock"], first=r["node_lock"] + 1)
                words = CR[r["outcome"]].format(**fields)
                if r["outcome"] == "no_hit" and r["first_tsd"] is not None:
                    words += CR["first_tsd"].format(**fields)
                if r["later_hit_lock"] is not None:
                    words += CR["later_hit"].format(**fields)
                out.append(f'    <tr data-outcome="{_esc(r["outcome"])}"><td>{_esc(r["round"])}</td><td>{r["node_lock"]}</td>'
                           f'<td>{"—" if r["hit_lock"] is None else r["hit_lock"]}</td>'
                           f'<td>{_esc(words)}</td></tr>')
            out += ["    </table></div>", "  </section>"]

        if self.p.showcase:
            out += self._showcase(tr, art)
        out += parts[self.p.variant][1]
        for vid, _opp in self.VARIANTS[1:]:
            out += parts[vid][0] + parts[vid][1]
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["demos"])}</h2>',
                f'    <p><a href="{_esc(self.DEMO_PAGE)}">{_esc(S["demos_link"])}</a></p>', '  </section>']
        out += RT._tail({"figures": fig})
        return "\n".join(out)

    def _variant_sections(self, tr, art, vid, opp, fig, users):
        """One variant's window, headline, controls and follow-up (the first list) and its case index (the
        second). The primary reads the prose's `sections` and `table`; a further variant overlays its own
        `more_variants.<id>` on them, and its figure keys carry its prefix."""
        PR = self.PROSE
        MV = PR.get("more_variants", {}).get(vid, {}) if vid != self.p.variant else {}
        S = {**PR["sections"], **MV.get("sections", {})}
        T = {**PR["table"], **MV.get("table", {})}
        control = MV.get("control", self.PS["control"])
        pre = self._key(vid)
        v = self.variant(tr, vid)
        out = []
        # 2. the window
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["window"])}</h2>',
                f'    <p>{_esc(S["window_note"])}</p>', '    <div class="scp-grid">']
        for mirrored, words in ((False, S["window_drawn"]), (True, S["window_mirrored"])):
            out.append(f'    <div class="scp-node"><h4 class="scp-name">{_esc(words)}</h4>'
                       f'{board_svg(self._window_rows(tr, v, mirrored), words, self.CLASSES)}</div>')
        out += ["    </div>", "  </section>"]

        # 3. the headline, with the control sentence beside it
        cell = lambda k: f'<td data-figure="{_esc(pre + k)}">{_esc(fig[pre + k])}</td>'
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["headline"])}</h2>',
                f'    <p>{_esc(S["headline_note"].format(pieces=art["window_pieces"] + 1, last=art["window_pieces"]))}</p>',
                f'    <p>{control}</p>',
                '    <div class="scp-index-wrap"><table class="scp-table">',
                f'    <tr><th>{_esc(T["player"])}</th><th>{_esc(T["all"])}</th><th>{_esc(T["in_opener"])}</th>'
                f'<th>{_esc(T["mid_game"])}</th><th>{_esc(T["mirrored"])}</th><th>{_esc(T["garbage"])}</th></tr>']
        for u in users:
            out.append(f"    <tr><th>{_esc(u)}</th>" + "".join(cell(k) for k in (
                f"hits.{u}.all", f"hits.{u}.in_opener", f"hits.{u}.mid_game", f"mirrored.{u}", f"garbage.{u}")) + "</tr>")
        out += ["    </table></div>"]

        # 4. controls
        ctl = art["variants"][vid]["controls"]
        out += [f'    <h3>{_esc(S["controls"])}</h3>', '    <div class="scp-index-wrap"><table class="scp-table">',
                f'    <caption>{_esc(T["denominator_note"])}</caption>',
                f'    <tr><th>{_esc(T["row"])}</th>' + "".join(f"<th>{_esc(u)}</th>" for u in users) + "</tr>"]
        for kind in ctl["under"]:
            out.append(f'    <tr><th>{_esc(T["under"].format(kind=PR["spin_kinds"][kind]))}</th>'
                       + "".join(cell(f"under.{kind}.{u}") for u in users) + "</tr>")
        for ab in ctl["ablation"]:
            out.append(f'    <tr><th>{_esc(T["ablation"][ab])}</th>' + "".join(cell(f"ablation.{ab}.{u}") for u in users) + "</tr>")
        out.append(f'    <tr><th>{_esc(T["baseline"])}</th>' + "".join(cell(f"baseline.{u}") for u in users) + "</tr>")
        out += ["    </table></div>", "  </section>"]

        # 5. the follow-up
        reasons = sorted({k[len(pre):].split(".", 2)[2] for k in fig if k.startswith(pre + "reason.")})
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["followup"])}</h2>',
                f'    <p>{_esc(S["followup_note"])}</p>',
                '    <div class="scp-index-wrap"><table class="scp-table">',
                f'    <tr><th>{_esc(T["followup_head"])}</th>' + "".join(f"<th>{_esc(u)}</th>" for u in users) + "</tr>",
                f'    <tr><th>{_esc(T["fired"])}</th>' + "".join(cell(f"fired.{u}") for u in users) + "</tr>"]
        for r in reasons:
            out.append(f'    <tr><th>{_esc(PR["reasons"][r])}</th>' + "".join(
                cell(f"reason.{u}.{r}") if pre + f"reason.{u}.{r}" in fig else "<td>—</td>" for u in users) + "</tr>")
        out += ["    </table></div>", "  </section>"]

        # 7. the cases
        cases = ['  <section class="scp-sec">', f'    <h2>{_esc(S["cases"])}</h2>',
                 f'    <p>{_esc(S["cases_note"])}</p>',
                 '    <div class="scp-index-wrap"><table class="scp-table">',
                 f'    <tr><th>{_esc(T["date"])}</th><th>{_esc(T["round"])}</th><th>{_esc(T["player"])}</th>'
                 f'<th>{_esc(T["lock"])}</th><th>{_esc(T["phase"])}</th><th>{_esc(T["window_col"])}</th>'
                 f'<th>{_esc(T["followup_col"])}</th></tr>']
        for h in art["hits"]:
            if h["variant"] != vid:
                continue
            fu = h["followup"]
            fw = T["yes"].format(lock=fu["lock"]) if fu["fired"] else PR["reasons"][fu["reason"]]
            href = self.replay_href(h)
            cases.append(f'    <tr data-case="{_esc(case_key(h))}"><td>{_esc(h["session"])}</td>'
                         f'<td><a href="{_esc(href)}">m{h["match"]}r{h["round"]}</a></td><td>{_esc(h["player"])}</td>'
                         f'<td>{h["lock"]}{_esc(T["mirrored_mark"]) if h["mirrored"] else ""}</td>'
                         f'<td>{_esc(T["phase_opener"] if h["in_opener"] else T["phase_mid"])}</td>'
                         f'<td>{self._thumb(tr, v, h)}</td><td>{_esc(fw)}</td></tr>')
        cases += ["    </table></div>", "  </section>"]
        return out, cases

    # ------------------------------------------------------------ the demo page

    def reach_problems(self, d, demos, tr):
        """The page's own check of one demo, a second implementation of `technique-demos.ts`'s
        `reachProblems`: decoded from an empty board with `replay_section.decode_boards`."""
        by_id = {n["id"]: n for n in tr["nodes"]}
        v = self.variant(tr, d.get("variant"))
        empties = tr.get("empty_letters", "")
        b = demos["board"]
        width, rows_n = b["width"], b["rows"]
        try:
            steps = [(p, [list(r) for r in board]) for p, _f, board in
                     RS.decode_boards(demos, d["seq"], d["locks"], RS.NEXT_SHOWN)]
        except SystemExit as e:
            return [f"{d['node']}: does not decode: {e}"]

        def ok(board, rows, cols=None):
            h = len(rows)
            for y, line in enumerate(board):
                for x, val in enumerate(line):
                    ch = rows[h - 1 - y][x] if y < h else "-"
                    strict = cols is None or cols[0] <= x <= cols[1]
                    if ch == "-" or ch in empties:
                        if strict and val is not None:
                            return False
                    elif val is None:
                        return False
                    elif strict and ch.islower() and ch != "c" and val != ch.upper():
                        return False
            return True

        def cells(i):
            return sorted(RS._place_cells(demos["shapes"], width, rows_n, steps[i][0], d["locks"][i][1]))

        def drawn(rows, letters):
            h = len(rows)
            return sorted((h - 1 - i) * width + x for i, row in enumerate(rows) for x, ch in enumerate(row)
                          if ch in letters)

        bad = []
        for r in d["reaches"]:
            n, i, where = by_id.get(r["node"]), r["lock"], f"{d['node']} → {r['node']}"
            if n is None or not 0 <= i < len(steps):
                bad.append(f"{where}: no such board or lock")
                continue
            lk = d["locks"][i]
            if r["check"] == "board":
                if not ok(steps[i][1], n["rows"]):
                    bad.append(f"{where}: the board after lock {i + 1} is not the drawing")
            elif r["check"] == "spin":
                if steps[i][0] != "T" or lk[3] != 2 or lk[2] != n["lines"] or cells(i) != drawn(n["rows"], "Tt"):
                    bad.append(f"{where}: lock {i + 1} is not the drawing's T")
                elif not ok(steps[i - 1][1], by_id[n["spin_of"]]["rows"]):
                    bad.append(f"{where}: the board before lock {i + 1} is not {n['spin_of']}")
            elif r["check"] == "after":
                h = len(n["rows"])
                slot = sorted((h - 1 - row) * width + col for row, col in v["followup"]["t_cells_after"])
                cols = (v["window"]["cols"][0] + d["offset"]["dc"], v["window"]["cols"][1] + d["offset"]["dc"])
                if steps[i][0] != "T" or lk[3] != 2 or lk[2] != v["followup"]["lines"] or cells(i) != slot:
                    bad.append(f"{where}: lock {i + 1} is not the drawn follow-up")
                elif not ok(steps[i - 1][1], n["rows"], cols):
                    bad.append(f"{where}: the board before lock {i + 1} does not show the drawing")
            else:
                bad.append(f"{where}: unknown check {r['check']!r}")
        return bad

    def _demo_payload(self, d, name=None):
        moments = []
        for e in d["events"]:
            nm = RS.SPIN_NAMES.get((e["spin"], e["lines"]))
            self._need(nm is not None, f"{d['node']}: spin {e['spin']} with {e['lines']} lines has no name")
            moments.append([e["lock"] + 1, 0, "tspin", self.DP["spin"].format(n=e["lock"] + 1, name=nm)])
        return {"label": demo_slug(d["node"]), "title": self.DP["now"].format(name=name or self.name(d["node"])),
                "seq": d["seq"], "order": "0" * len(d["locks"]), "winner": None,
                "players": [{"user": self.DP["user"], "slot": 0, "ending": None, "frames": d["frames"],
                             "pieces": len(d["locks"]), "locks": d["locks"], "ge": [],
                             "verified_to": None, "after": None, "failed_at": None}],
                "moments": moments, "flags": [], "notes": [self._own_chain_words(d) if name else self._chain_words(d)]}

    def _chain_words(self, d):
        pieces = [q for q, _h in RS.queue_states(d["seq"], d["locks"], RS.NEXT_SHOWN)]
        roles = d["roles"]
        part = lambda code: "".join(p for p, r in zip(pieces, roles) if r == code)
        words = [self.DP["base_words"].format(n=d["base_locks"], pieces=part("b")),
                 self.DP["page_words"].format(pieces=part("p"))]
        if part("f"):
            words.append(self.DP["fill_words"].format(pieces=part("f")))
        return self.DP["chain"].format(chain="；".join(words))

    def _own_chain_words(self, d):
        pieces = [q for q, _h in RS.queue_states(d["seq"], d["locks"], RS.NEXT_SHOWN)]
        part = lambda code: "".join(p for p, r in zip(pieces, d["roles"]) if r == code)
        words = [self.OW["base_words"].format(n=d["base_locks"], pieces=part("b"))]
        if part("f"):
            words.append(self.DP["fill_words"].format(pieces=part("f")))
        return self.DP["chain"].format(chain="；".join(words))

    def own_name(self, b):
        return self.OW["name"].format(offset=b["offset"], n=b["candidate"])

    @staticmethod
    def own_tr(tr, own):
        """The transcription with every own board added, as the search handed it to the planner (the board
        and its terrain, two ids), so `reach_problems` reads them as it reads a drawn board."""
        extra = [n for b in own["boards"] for n in ({"id": b["id"], "rows": b["rows"]},
                                                     {"id": b["id"] + ".terrain", "rows": b["rows"]})]
        return dict(tr, nodes=list(tr["nodes"]) + extra)

    def own_problems(self, d, own, tr):
        """One own demo, checked by THIS page's implementations: `reach_problems` (decoded from an empty board),
        and the window read by `technique_transcription.window_fires`, the Python twin of the TS matcher the
        planner used, on the decoded board before the stood T; both T's must be full T-spins clearing the
        variant's lines."""
        from types import SimpleNamespace
        from pipeline.openers.technique_transcription import window_fires
        bad = self.reach_problems(d, own, self.own_tr(tr, own))
        v = self.variant(tr, own["search"]["variant"])
        b = own["board"]
        width, rows_n = b["width"], b["rows"]
        try:
            steps = [(p, [list(r) for r in board]) for p, _f, board in
                     RS.decode_boards(own, d["seq"], d["locks"], RS.NEXT_SHOWN)]
        except SystemExit as e:
            return bad + [f"{d['node']}: does not decode: {e}"]
        for i, lines in ((d["stood_lock"], v["lines"]), (d["followup_lock"], v["followup"]["lines"])):
            lk = d["locks"][i]
            if steps[i][0] != "T" or lk[3] != 2 or lk[2] != lines:
                bad.append(f"{d['node']}: lock {i + 1} is not a full T-spin clearing {lines}")
        i = d["stood_lock"]
        before = steps[i - 1][1]
        board = ["".join("-" if before[y][x] is None else "c" for x in range(width)) for y in range(rows_n - 1, -1, -1)]
        cells = RS._place_cells(own["shapes"], width, rows_n, "T", d["locks"][i][1])
        lock = {(rows_n - 1 - c // width, c % width) for c in cells}
        spec = SimpleNamespace(empty_letters=tr.get("empty_letters", ""))
        if window_fires(tr, v, spec, board, lock, False) is not True:
            bad.append(f"{d['node']}: the window does not fire on the board before lock {i + 1}")
        return bad

    @staticmethod
    def _own_rows(b, d, own):
        """An own board with the first T's cells drawn as the dashed slot (the T goes in where the window fires)."""
        w, n = own["board"]["width"], own["board"]["rows"]
        cells = RS._place_cells(own["shapes"], w, n, "T", d["locks"][d["stood_lock"]][1])
        h = len(b["rows"])
        rows = [list(r) for r in b["rows"]]
        for c in cells:
            y, x = divmod(c, w)
            rows[h - 1 - y][x] = "U"
        return ["".join(r) for r in rows]

    def _own_section(self, tr, own, rounds):
        OW = self.OW
        out = [f'  <h2 class="scp-sec" id="own">{_esc(OW["title"])}</h2>', f'  <p>{_esc(OW["note"])}</p>',
               '  <div class="scp-index-wrap"><table class="scp-table">',
               f'  <tr><th>{_esc(OW["offset_col"])}</th><th>{_esc(OW["candidates_col"])}</th><th>{_esc(OW["tried_col"])}</th>'
               + "".join(f"<th>{_esc(OW['outcomes'][k])}</th>" for k in OW["outcomes"]) + "</tr>"]
        for o in own["search"]["per_offset"]:
            out.append(f'  <tr data-own-offset="{o["offset"]}"><td>{o["offset"]}</td><td>{o["candidates"]}</td><td>{o["tried"]}</td>'
                       + "".join(f"<td>{o['outcomes'].get(k, 0)}</td>" for k in OW["outcomes"]) + "</tr>")
        out += ["  </table></div>", '  <div class="scp-grid scd-grid">']
        by_node = {d["node"]: d for d in own["demos"]}
        for b in own["boards"]:
            d = by_node[b["id"]]
            slug = demo_slug(d["node"])
            nm = self.own_name(b)
            rounds[slug] = self._demo_payload(d, nm)
            out.append("".join([
                f'    <div class="scp-node" id="{slug}" data-own-node="{_esc(b["id"])}">',
                f'<h4 class="scp-name">{_esc(nm)}</h4>',
                board_svg(self._own_rows(b, d, own), nm, self.CLASSES),
                f'<p><a class="scp-case" href="#{slug}" data-round="{slug}">{_esc(self.DP["play"])}</a></p>',
                f'<p class="scp-tag">{_esc(self._own_chain_words(d))}</p>',
                f'<p class="scp-cond">{_esc(self.DP["events"].format(events="，".join(m[3] for m in rounds[slug]["moments"])))}</p>',
                "</div>"]))
        out.append("  </div>")
        return out

    # ------------------------------------------------------------ cold-clear self-play (opt-in)

    def sp_name(self, g):
        return self.SP["name"].format(seed=g["seed"])

    def sp_scan_words(self, sp):
        s, pv = sp["scan"], sp["provenance"]
        return self.SP["scan"].format(games=s["games"], pieces=s["pieces_per_game"], rev=pv["rev"][:7],
                                      nodes=pv["cc_nodes"], coach_seed=pv["coach_seed"],
                                      complete=s["games_complete"], tsds=s["scored_tsds"], hits=len(s["hits"]),
                                      shown=len(sp["games"]))

    def sp_hit_words(self, h):
        SP = self.SP
        fu = h["followup"]
        follow = (SP["followup_fired"].format(n=fu["lock"] + 1) if fu["fired"]
                  else SP["followup_not"].format(reason=self.PROSE["reasons"].get(fu["reason"], fu["reason"])))
        return SP["hit"].format(n=h["lock"] + 1, variant=SP["variant_names"][h["variant"]],
                                hand=SP["hands"][h["hand"]], followup=follow)

    def _sp_steps(self, g, sp):
        b = sp["board"]
        return [(p, [list(r) for r in board]) for p, _f, board in
                RS.decode_boards(sp, g["seq"], g["locks"], RS.NEXT_SHOWN)], b["width"], b["rows"]

    def selfplay_problems(self, g, sp, tr):
        """One self-play game, checked by THIS page's implementations: decoded from an empty board with
        `replay_section.decode_boards`, every lock on cold-clear's own placement; at each hit, the window read by
        `technique_transcription.window_fires`, in the hit's hand, on the decoded board before its T, and the hit's
        T (and a fired follow-up's) a full T-spin clearing the variant's lines."""
        from types import SimpleNamespace
        from pipeline.openers.technique_transcription import window_fires
        node = g["node"]
        try:
            steps, width, rows_n = self._sp_steps(g, sp)
        except SystemExit as e:
            return [f"{node}: does not decode: {e}"]
        bad = []
        if len(steps) != len(g["placements"]):
            bad.append(f"{node}: {len(steps)} locks for {len(g['placements'])} placements")
        for i, ((piece, _b), pl) in enumerate(zip(steps, g["placements"])):
            cells = sorted(RS._place_cells(sp["shapes"], width, rows_n, piece, g["locks"][i][1]))
            want = sorted((rows_n - 1 - r) * width + x for x, r in pl["cells"])
            if piece != pl["piece"] or cells != want:
                bad.append(f"{node}: lock {i + 1} is not cold-clear's placement")
                break
        spec = SimpleNamespace(empty_letters=tr.get("empty_letters", ""))
        for h in g["hits"]:
            v = self.variant(tr, h["variant"])
            i = h["lock"]
            if not 0 < i < len(steps):
                bad.append(f"{node}: no lock {i + 1}")
                continue
            ts = [(i, v["lines"])]
            if h["followup"]["fired"]:
                ts.append((h["followup"]["lock"], v["followup"]["lines"]))
            for j, lines in ts:
                lk = g["locks"][j] if 0 <= j < len(steps) else None
                if lk is None or steps[j][0] != "T" or lk[3] != 2 or lk[2] != lines:
                    bad.append(f"{node}: lock {j + 1} is not a full T-spin clearing {lines}")
            before = steps[i - 1][1]
            board = ["".join("-" if before[y][x] is None else "c" for x in range(width)) for y in range(rows_n - 1, -1, -1)]
            cells = RS._place_cells(sp["shapes"], width, rows_n, "T", g["locks"][i][1])
            lock = {(rows_n - 1 - c // width, c % width) for c in cells}
            if window_fires(tr, v, spec, board, lock, h["hand"] == "mirrored") is not True:
                bad.append(f"{node}: the {h['variant']} window ({h['hand']}) does not fire on the board before lock {i + 1}")
        return bad

    def _selfplay_payload(self, g, name):
        SP = self.SP
        moments = []
        for h in g["hits"]:
            moments.append([h["lock"] + 1, 0, "tspin", SP["moment_hit"].format(
                n=h["lock"] + 1, variant=SP["variant_names"][h["variant"]])])
            if h["followup"]["fired"]:
                moments.append([h["followup"]["lock"] + 1, 0, "tspin",
                                SP["moment_followup"].format(n=h["followup"]["lock"] + 1)])
        return {"label": demo_slug(g["node"]), "title": SP["now"].format(name=name),
                "seq": g["seq"], "order": "0" * len(g["locks"]), "winner": None,
                "players": [{"user": SP["user"], "slot": 0, "ending": None, "frames": g["frames"],
                             "pieces": len(g["locks"]), "locks": g["locks"], "ge": [],
                             "verified_to": None, "after": None, "failed_at": None}],
                "moments": sorted(moments), "flags": [], "notes": [SP["notes"].format(n=len(g["locks"]))]}

    def _selfplay_section(self, tr, sp, rounds):
        SP = self.SP
        out = [f'  <h2 class="scp-sec" id="selfplay">{_esc(SP["title"])}</h2>',
               *[f"  <p>{_esc(x)}</p>" for x in SP["note"]],
               f'  <p class="scp-count" data-selfplay-scan="">{_esc(self.sp_scan_words(sp))}</p>',
               '  <div class="scp-grid scd-grid">']
        for g in sp["games"]:
            slug = demo_slug(g["node"])
            nm = self.sp_name(g)
            rounds[slug] = self._selfplay_payload(g, nm)
            steps, width, _rows_n = self._sp_steps(g, sp)
            bits = [f'    <div class="scp-node" id="{slug}" data-selfplay-node="{_esc(g["node"])}">',
                    f'<h4 class="scp-name">{_esc(nm)}</h4>']
            for h in g["hits"]:
                i = h["lock"]
                before = steps[i - 1][1]
                mark = set(RS._place_cells(sp["shapes"], width, sp["board"]["rows"], "T", g["locks"][i][1]))
                top = max([y + 1 for y in range(len(before)) if any(v is not None for v in before[y])]
                          + [c // width + 1 for c in mark])
                words = self.sp_hit_words(h)
                bits += [board_svg(self._rows_of(before, mark, top + 1), f"{nm} {words}", self.CLASSES),
                         f'<p class="scp-tag">{_esc(words)}</p>',
                         f'<p><a class="scp-case" href="#{slug}@p{i}" data-round="{slug}" data-selfplay-hit="{i}">'
                         f'{_esc(SP["play_hit"].format(n=i + 1))}</a></p>']
            bits += [f'<p><a class="scp-case" href="#{slug}" data-round="{slug}">{_esc(SP["play"])}</a></p>',
                     f'<p class="scp-cond">{_esc(SP["notes"].format(n=len(g["locks"])))}</p>', "</div>"]
            out.append("".join(bits))
        out.append("  </div>")
        return out

    def render_demo_page(self, tr, demos):
        bad = [x for d in demos["demos"] for x in self.reach_problems(d, demos, tr)]
        self._need(not bad, "; ".join(bad))
        DP = self.DP
        title = f"{DP['title']}{RS.TITLE_MARK}"
        shared = {"shapes": demos["shapes"], "width": demos["board"]["width"], "rows": demos["board"]["rows"],
                  "visible": demos["board"]["visible_rows"], "next": RS.NEXT_SHOWN, "flag_words": RS.FLAG_WORDS}
        by_id = {n["id"]: n for n in tr["nodes"]}
        with open(RT.PAGE_JS, encoding="utf-8") as fh:
            page_js = fh.read().rstrip()
        self._need("</script" not in page_js.lower(), "stray_cannon_page.js may not contain a closing script tag")
        out = self._head(title, DP["desc"], [DP["user"]], True)
        out += self._nav(self.OVERVIEW, self.PROSE["overview_title"])
        out += ['  <header class="scp-head">',
                f'    <div class="eyebrow">{RS.EYEBROW}</div>',
                f'    <h1 class="section-title">{_esc(title)}</h1>',
                f'    <p>{_esc(DP["lede"])}</p>',
                RT._source_line(tr, self.PROSE.get("source_credit")),
                '  </header>',
                '  <div class="method-note">',
                f'    <p><strong>呢版唔屬於信任鏈，亦唔係對局。</strong>所以呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
        out += [f"    <p>{s}</p>" for s in (self.PS["source"],) + self.DEMO_SENTENCES]
        out.append("  </div>")
        out += [f'  <section id="{RS.SECTION_ID}" aria-labelledby="rpg-now">',
                '    <h2 class="rpg-now" id="rpg-now" aria-live="polite"></h2>',
                f'    <p class="scp-idle">{_esc(DP["idle"])}</p>',
                '    <p class="rpg-notes"></p>',
                f'    <p class="rpg-flag" hidden>{RS.FLAG_WORDS}</p>',
                f'    <p class="rpg-missing" hidden>{_esc(self.PROSE["missing"])}</p>',
                '    <noscript><p>重播要開 JavaScript 先用到。</p></noscript>',
                '    <div class="rpg-host"></div>',
                f'    <template id="{TEMPLATE_ID}">',
                *["  " + line for line in RS.player_box("", [DP["user"]], bands=False)],
                '    </template>',
                '  </section>',
                '  <div class="scp-grid scd-grid">']
        rounds = {}
        for d in demos["demos"]:
            slug = demo_slug(d["node"])
            rounds[slug] = self._demo_payload(d)
            n = by_id[d["node"]]
            bits = [f'    <div class="scp-node" id="{slug}" data-demo-node="{_esc(d["node"])}" data-demo="built">',
                    f'<h4 class="scp-name">{_esc(self.name(d["node"]))}</h4>',
                    board_svg(n["rows"], self.name(d["node"]), self.CLASSES),
                    f'<p><a class="scp-case" href="#{slug}" data-round="{slug}">{_esc(DP["play"])}</a></p>',
                    f'<p class="scp-tag">{_esc(self._chain_words(d))}</p>',
                    f'<p class="scp-cond">{_esc(DP["events"].format(events="，".join(m[3] for m in rounds[slug]["moments"])))}</p>',
                    f'<p class="scp-cond">{_esc(DP["reaches"].format(boards=""))}'
                    + "、".join(f'<span data-reach="{_esc(r["node"])}">{_esc(self.name(r["node"]))}</span>'
                               for r in d["reaches"]) + "</p>",
                    "</div>"]
            out.append("".join(bits))
        out.append("  </div>")
        own = getattr(self, "_own", None)
        if own:
            bad = [x for d in own["demos"] for x in self.own_problems(d, own, tr)]
            self._need(not bad, "; ".join(bad))
            out += self._own_section(tr, own, rounds)
        sp = getattr(self, "_sp", None)
        if sp:
            bad = [x for g in sp["games"] for x in self.selfplay_problems(g, sp, tr)]
            self._need(not bad, "; ".join(bad))
            out += self._selfplay_section(tr, sp, rounds)
        out += [f'  <h2 class="scp-sec">{_esc(DP["unbuilt_title"])}</h2>', '  <div class="scp-grid">']
        for u in demos["unbuilt"]:
            n = by_id[u["node"]]
            out.append(f'    <div class="scp-node" data-demo-node="{_esc(u["node"])}" data-demo="unbuilt">'
                       f'<h4 class="scp-name">{_esc(self.name(u["node"]))}</h4>'
                       f'{board_svg(n["rows"], self.name(u["node"]), self.CLASSES)}'
                       f'<p class="scp-count">{_esc(DP["unbuilt"].format(reason=u["reason"]))}</p></div>')
        out.append("  </div>")
        island = {"shared": shared, "rounds": rounds, "cases": [{"case": k, "round": k} for k in rounds]}
        out += RT._tail(island, (RS.player_js(), page_js))
        return "\n".join(out)

    # ------------------------------------------------------------ audits

    def audit_text(self, page):
        bad = []
        vis = RT._visible(page)
        if set(page) & SIMPLIFIED:
            bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
        if "%" in _TAG.sub("", _SRC_QUOTE.sub("", vis)):
            bad.append("a % outside quoted source text — this page prints counts, never computed rates")
        return bad

    def audit_overview(self, page, tr, art):
        bad = RP.audit_quarantine(page, self.OVERVIEW_REQUIRED, DATA_ID) + self.audit_text(page)
        boards = _BOARD.findall(page)
        if sorted(boards) != sorted(n["id"] for n in tr["nodes"]):
            bad.append(f"the overview does not draw every board exactly once ({len(boards)} drawn, {len(tr['nodes'])} boards)")
        cases = _CASE.findall(page)
        vids = {vid for vid, _opp in self.VARIANTS}
        want = sorted(case_key(h) for h in art["hits"] if h["variant"] in vids)
        if len(set(want)) != len(want):
            bad.append("two variants' hits share a case key (one lock read as two variants)")
        if sorted(html.unescape(c) for c in cases) != want:
            bad.append(f"the case index does not list every hit exactly once ({len(cases)} rows, {len(want)} hits)")
        figs = {}
        for k, val in _FIGURE.findall(page):
            if k in figs:
                bad.append(f"figure {k} printed twice")
            figs[k] = html.unescape(val)
        rc = self.recount(art)
        if figs != rc:
            diff = sorted(k for k in set(figs) | set(rc) if figs.get(k) != rc.get(k))
            bad.append(f"the printed figures are not the artefact's, recounted: {diff[:4]}")
        if any(k.startswith("hits.") for k in figs) and self.PS["control"] not in page:
            bad.append("the headline is printed without the control sentence")
        if f'href="{self.DEMO_PAGE}"' not in page:
            bad.append("the overview does not link the demo page")
        if self.p.showcase:
            bad += self.audit_showcase(page, tr, art)
        return bad + self.audit_replay_links(page, tr, art)

    def audit_demo_page(self, page, tr, demos):
        bad = (RP.audit_quarantine(page, self.DEMO_REQUIRED, DATA_ID) + RP.audit_player(page)
               + self.audit_text(page))
        blocks = _DEMO_BLOCK.findall(page)
        seen = [nid for nid, _st in blocks]
        if len(seen) != len(set(seen)):
            bad.append("a demo block appears twice on the demo page")
        want = {d["node"]: "built" for d in demos["demos"]}
        want.update({u["node"]: "unbuilt" for u in demos["unbuilt"]})
        if dict(blocks) != want:
            bad.append("the demo page's blocks are not every demo and every unbuilt board")
        reached = _REACH.findall(page)
        cover = sorted(reached + [u["node"] for u in demos["unbuilt"]])
        if cover != sorted(n["id"] for n in tr["nodes"]):
            bad.append("the demo page does not account for every board exactly once (reached or unbuilt)")
        m = RT._ISLAND.search(page)
        if not m:
            return bad + ["no data island on the demo page"]
        island = json.loads(m.group(1))
        own = getattr(self, "_own", None)
        own_ids = [b["id"] for b in own["boards"]] if own else []
        sp = getattr(self, "_sp", None)
        sp_ids = [g["node"] for g in sp["games"]] if sp else []
        if sorted(island["rounds"]) != sorted([demo_slug(d["node"]) for d in demos["demos"] + (own["demos"] if own else [])]
                                              + [demo_slug(n) for n in sp_ids]):
            bad.append("the demo page does not embed every demo exactly once")
        if [html.unescape(x) for x in re.findall(r'data-selfplay-node="([^"]+)"', page)] != sp_ids:
            bad.append("the demo page does not draw every self-play game exactly once, in the artefact's order")
        if sp:
            links = re.findall(r'href="#(demo-[a-z0-9-]+)@p(\d+)" data-round="([^"]+)" data-selfplay-hit="(\d+)"', page)
            want = [(demo_slug(g["node"]), str(h["lock"]), demo_slug(g["node"]), str(h["lock"]))
                    for g in sp["games"] for h in g["hits"]]
            if links != want:
                bad.append("a self-play hit's link is not at its hit's lock, or a hit has no link")
            scan = re.findall(r'data-selfplay-scan="">([^<]*)<', page)
            if [html.unescape(x) for x in scan] != [self.sp_scan_words(sp)]:
                bad.append("the self-play scan sentence is not the artefact's")
            for g in sp["games"]:
                r = island["rounds"].get(demo_slug(g["node"]))
                if r is not None:
                    shown = dict(g, seq=r["seq"], locks=r["players"][0]["locks"])
                    bad += [f"embedded {x}" for x in self.selfplay_problems(shown, sp, tr)]
        if [html.unescape(x) for x in re.findall(r'data-own-node="([^"]+)"', page)] != own_ids:
            bad.append("the demo page does not draw every own board exactly once, in the artefact's order")
        if own:
            if sorted(d["node"] for d in own["demos"]) != sorted(own_ids):
                bad.append("the own-design artefact's boards and demos disagree")
            for d in own["demos"]:
                r = island["rounds"].get(demo_slug(d["node"]))
                if r is not None:
                    shown = dict(d, seq=r["seq"], locks=r["players"][0]["locks"])
                    bad += [f"embedded {x}" for x in self.own_problems(shown, own, tr)]
        for d in demos["demos"]:
            r = island["rounds"].get(demo_slug(d["node"]))
            if r is None:
                continue
            shown = dict(d, seq=r["seq"], locks=r["players"][0]["locks"])
            bad += [f"embedded {x}" for x in self.reach_problems(shown, demos, tr)]
        return bad

    def audit_all(self, pages, tr, art, demos):
        return (self.audit_overview(pages[self.OVERVIEW], tr, art)
                + self.audit_demo_page(pages[self.DEMO_PAGE], tr, demos))

    def render_all(self, repo=REPO, inputs=None):
        self._repo = repo
        tr, art, demos = inputs or self.load_inputs(repo)
        self.check_inputs(tr, art, demos)
        self._own = None
        if self.p.own_rel:
            with open(os.path.join(repo, self.p.own_rel), encoding="utf-8") as fh:
                own = json.load(fh)
            self._need(own.get("schema") == self.p.own_schema, f"unknown own-design schema {own.get('schema')!r}")
            self._need(own.get("report_eligible") is False and own.get("constructed") is True and own.get("own") is True,
                       f"{os.path.basename(self.p.own_rel)} must declare report_eligible: false, constructed: true "
                       "and own: true")
            self._own = own
        self._sp = None
        if self.p.selfplay_rel:
            with open(os.path.join(repo, self.p.selfplay_rel), encoding="utf-8") as fh:
                sp = json.load(fh)
            self._need(sp.get("schema") == self.p.selfplay_schema, f"unknown self-play schema {sp.get('schema')!r}")
            self._need(sp.get("report_eligible") is False and sp.get("constructed") is True and sp.get("selfplay") is True,
                       f"{os.path.basename(self.p.selfplay_rel)} must declare report_eligible: false, constructed: true "
                       "and selfplay: true")
            self._sp = sp
        self._need(self.figures(art) == self.recount(art),
                   "the facts artefact's aggregates disagree with its own hit list")
        pages = {self.OVERVIEW: self.render_overview(tr, art, demos), self.DEMO_PAGE: self.render_demo_page(tr, demos)}
        for name, page in pages.items():
            self._no_simplified(page, name)
            size = len(page.encode())
            self._need(not self.p.max_page_bytes or size <= self.p.max_page_bytes,
                       f"{name} is {size} bytes, over the profile's {self.p.max_page_bytes}")
        bad = self.audit_all(pages, tr, art, demos)
        self._need(not bad, "; ".join(bad))
        return pages

    # ------------------------------------------------------------ selftest

    def _selftest(self):
        inputs = self.load_inputs(REPO)
        tr, art, demos = inputs
        pages = self.render_all(REPO, inputs)
        ov, dp = pages[self.OVERVIEW], pages[self.DEMO_PAGE]
        first_case = _CASE.search(ov)
        fig = _FIGURE.search(ov)
        cases = [
            ("overview: a required sentence dropped", "ov", ov.replace(self.PS["midgame"], "")),
            ("overview: a badge", "ov", ov.replace("</body>", '<span data-claim="G001">✓</span></body>')),
            ("overview: an innerHTML", "ov", ov.replace("</body>", "<script>x.innerHTML=1</script></body>")),
        ]
        if first_case:
            case_line = [l for l in ov.split("\n") if first_case.group(0) in l][0]
            at = re.search(r'@p(\d+)"', case_line)
            cases += [
                ("overview: a hit row dropped", "ov", ov.replace(case_line + "\n", "")),
                ("overview: a hit row duplicated", "ov", ov.replace(case_line, case_line + "\n" + case_line)),
                ("overview: a replay link one position late", "ov",
                 ov.replace(case_line, case_line.replace(at.group(0), f'@p{int(at.group(1)) + 1}"'))),
                ("overview: a replay link one position early", "ov",
                 ov.replace(case_line, case_line.replace(at.group(0), f'@p{int(at.group(1)) - 1}"'))),
                ("overview: a replay link at the round's start", "ov",
                 ov.replace(case_line, case_line.replace(at.group(0), '"'))),
            ]
            # the same player's previous lock: right player, wrong lock (a link one T early in the round)
            h0 = next(h for h in art["hits"] if case_key(h) == html.unescape(first_case.group(1)))
            r0 = self._replay_round(h0["session"], h0["file"], h0["round_index0"])
            mine = [n for n, x in enumerate(r0["order"]) if x == str(r0["users"].index(h0["player"]))]
            if h0["lock"] > 0:
                cases.append(("overview: a replay link at the player's previous lock", "ov",
                              ov.replace(case_line, case_line.replace(at.group(0), f'@p{mine[h0["lock"] - 1]}"'))))
        else:
            # no hit (BT砲): the case index is empty, so a row the artefact does not hold must be caught
            cases.append(("overview: a hit row invented", "ov", ov.replace(
                f"<th>{_esc(self.PROSE['table']['followup_col'])}</th></tr>",
                f"<th>{_esc(self.PROSE['table']['followup_col'])}</th></tr>\n"
                '    <tr data-case="2026-01-01 m1r1 nobody lock 0"><td>x</td></tr>', 1)))
        cases += [
            ("overview: a figure changed", "ov",
             ov.replace(fig.group(0), f'data-figure="{fig.group(1)}">{fig.group(2)}0<', 1)),
            ("overview: the control sentence dropped", "ov", ov.replace(self.PS["control"], "")),
            ("overview: a board dropped", "ov", RT._drop_line(ov, f'data-board="{self.p.selftest_board}"')),
            ("overview: a %", "ov", ov.replace("</header>", "<p>12%</p></header>")),
            ("overview: a simplified glyph", "ov", ov.replace("</header>", "<p>这</p></header>")),
        ]
        for vid, _opp in self.VARIANTS[1:]:
            # a further variant's figures are keyed by its prefix: changing one must be caught as well
            vf = re.search(rf'data-figure="({re.escape(vid)}:[^"]+)">([^<]*)<', ov)
            cases.append((f"overview: a {vid} figure changed", "ov",
                          ov.replace(vf.group(0), f'data-figure="{vf.group(1)}">{vf.group(2)}0<', 1)))
        if demos["demos"]:
            isl = RT._ISLAND.search(dp)
            slug = demo_slug(demos["demos"][0]["node"])
            bad_island = json.loads(isl.group(1))
            bad_island["rounds"][slug]["players"][0]["locks"][0][1] += 1
            corrupt = dp.replace(isl.group(1), RT._island(bad_island))
            reach = _REACH.search(dp).group(0)
            cases += [
                ("demo: an embedded lock moved", "dp", corrupt),
                ("demo: a reach dropped", "dp", dp.replace(reach, "<span>", 1)),
                ("demo: a demo block dropped", "dp", RT._drop_line(dp, f'id="{slug}"')),
            ]
        else:
            # no demo was built: the page is its unbuilt blocks, so dropping one must be caught
            cases.append(("demo: an unbuilt block dropped", "dp",
                          RT._drop_line(dp, f'data-demo-node="{demos["unbuilt"][0]["node"]}"')))
        cases.append(("demo: a required sentence dropped", "dp", dp.replace(self.DS_rule(), "")))
        if self.p.showcase and self.showcase_hits(art):
            first = re.search(r'data-showcase="([^"]+)"', ov)
            cases.append(("overview: a showcase example dropped", "ov", ov.replace(first.group(0), "data-x=\"\"", 1)))
        own = getattr(self, "_own", None)
        if own and own["demos"]:
            isl = RT._ISLAND.search(dp)
            d0 = own["demos"][0]
            slug = demo_slug(d0["node"])
            moved = json.loads(isl.group(1))
            moved["rounds"][slug]["players"][0]["locks"][d0["stood_lock"]][1] += 1
            cases += [("demo: an own design's stood T moved", "dp", dp.replace(isl.group(1), RT._island(moved))),
                      ("demo: an own design dropped", "dp", RT._drop_line(dp, f'data-own-node="{d0["node"]}"'))]
        sp = getattr(self, "_sp", None)
        if sp and sp["games"]:
            isl = RT._ISLAND.search(dp)
            g0 = sp["games"][0]
            h0 = g0["hits"][0]
            slug = demo_slug(g0["node"])
            moved = json.loads(isl.group(1))
            moved["rounds"][slug]["players"][0]["locks"][h0["lock"]][1] += 1
            link = f'href="#{slug}@p{h0["lock"]}"'
            cases += [("demo: a self-play hit's embedded T moved", "dp", dp.replace(isl.group(1), RT._island(moved))),
                      ("demo: a self-play hit's link one lock late", "dp",
                       dp.replace(link, f'href="#{slug}@p{h0["lock"] + 1}"', 1)),
                      ("demo: a self-play hit lock moved", "dp",
                       dp.replace(f'data-selfplay-hit="{h0["lock"]}"', f'data-selfplay-hit="{h0["lock"] - 1}"', 1)),
                      ("demo: a self-play game dropped", "dp", RT._drop_line(dp, f'data-selfplay-node="{g0["node"]}"')),
                      ("demo: the self-play scan sentence changed", "dp",
                       dp.replace('data-selfplay-scan="">', 'data-selfplay-scan="">1', 1))]
        ok = True
        for name, which, page in cases:
            if page == (ov if which == "ov" else dp):
                print(f"  BAD {name}: the plant changed nothing")
                ok = False
                continue
            got = (self.audit_overview(page, tr, art) if which == "ov" else self.audit_demo_page(page, tr, demos))
            good = bool(got)
            ok &= good
            print(f"  {'ok ' if good else 'BAD'} {name}: {got[:1]}")
        # input-level refusals
        refused = 0
        for name, mutate in (
                ("facts not quarantined", lambda t, a, d: a.__setitem__("report_eligible", True)),
                ("demos not constructed", lambda t, a, d: d.__setitem__("constructed", False)),
                ("an aggregate disagrees with the hit list",
                 lambda t, a, d: a["variants"][self.p.variant]["followup_by_player"][sorted(a["denominators"])[0]]
                 .__setitem__("fired", a["variants"][self.p.variant]["followup_by_player"][sorted(a["denominators"])[0]]["fired"] + 1))):
            t2, a2, d2 = (json.loads(json.dumps(x)) for x in inputs)
            mutate(t2, a2, d2)
            try:
                self.render_all(REPO, (t2, a2, d2))
                good = False
            except SystemExit:
                good = True
            ok &= good
            refused += 1
            print(f"  {'ok ' if good else 'BAD'} refused: {name}")
        sp = getattr(self, "_sp", None)
        if sp and sp["games"]:
            # the window check itself: the first hit read in the other hand must not fire
            g0 = json.loads(json.dumps(sp["games"][0]))
            g0["hits"][0]["hand"] = "as_drawn" if g0["hits"][0]["hand"] == "mirrored" else "mirrored"
            got = self.selfplay_problems(g0, sp, tr)
            good = any("does not fire" in x for x in got)
            ok &= good
            refused += 1
            print(f"  {'ok ' if good else 'BAD'} refused: a self-play hit read in the other hand: {got[:1]}")
        print(f"{'ok ' if ok else 'FAIL'} {self.p.module} selftest: {len(cases) + refused} corruptions, "
              f"{'all caught' if ok else 'SOME MISSED'}")
        return 0 if ok else 1

    def DS_rule(self):
        return self.DP["sentences"]["rule"]

    def main(self, argv=None, doc=None):
        ap = argparse.ArgumentParser(description=(doc or __doc__).splitlines()[0])
        ap.add_argument("--out-dir")
        ap.add_argument("--selftest", action="store_true")
        a = ap.parse_args(argv)
        if a.selftest:
            return self._selftest()
        if not a.out_dir:
            ap.error("need --out-dir, or --selftest")
        os.makedirs(a.out_dir, exist_ok=True)
        for name, page in self.render_all(REPO).items():
            with open(os.path.join(a.out_dir, name), "w", encoding="utf-8") as fh:
                fh.write(page)
            print(f"wrote {os.path.join(a.out_dir, name)} ({len(page.encode())} bytes)")
        return 0


def site_card(site, art):
    """The index card's words and count for one technique (`bin/build-docs`)."""
    card = site.PROSE["index_card"]
    vids = {vid for vid, _opp in site.VARIANTS}
    return {"href": site.OVERVIEW, "cases": sum(h["variant"] in vids for h in art["hits"]),
            "kicker": card["kicker"], "title": site.PROSE["overview_title"], "blurb": card["blurb"]}
