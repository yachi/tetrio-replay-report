"""數據對決 — the chart panels: authored captions around mount points the page fills.

Same split as the hero and 關鍵時刻: the *words* are hand-written Cantonese and live
in `<report_dir>/prose/stats.json`; anything derivable is derived. Here that is the
legend row, which is `facts["players"]` in order — the one thing in this section that
was retyped per report and could therefore disagree with the score above it.

What makes this section different from the others is that its markup is **load-bearing
for the inline script**. Every panel ends in an empty div whose id the page looks up
(`vs-small-multiples`, `clears-bar-chart`, `tape-chart`); the chart renders into that
div and nowhere else. Renaming or dropping one does not fail anything — the page loads,
the section reads correctly, and the chart is simply not there. So the ids are not free
text: `MOUNT_IDS` is the set the report's script knows how to fill, and a prose file
naming anything else is refused. Add to that set in the same commit that teaches the
page a new chart, never before.

The same is true of the `.scroll-x` wrapper (a wide chart has to scroll inside the
panel rather than the page) and of the mount's own class (`sm-grid` lays the small
multiples out). Both live in the prose next to the id they belong to, so a panel is
one object rather than a rule split between a JSON file and this module.

Insertion rules, the same everywhere in this pipeline:

  * **authored prose is raw HTML** — the lede, the captions and the footnote
    legitimately carry `<span class="badge" data-claim="...">`, `<strong>` and
    `<code>`. They are written by a person, not received as input.
  * **derived and display values are escaped** — the eyebrow, the title, each panel's
    `<h3>`, and the player names in the legend. They are short strings with no reason
    to become markup.
"""
import html
import json
import os

from pipeline.claims.build_claims import SIMPLIFIED

# The ids the report's inline script renders a chart into. A mount id outside this
# set is a blank panel that nothing reports, which is why it is an enum and not a
# free string.
MOUNT_IDS = {"vs-small-multiples", "clears-bar-chart", "tape-chart"}
# The legend's swatch classes, by position in facts["players"] — the stylesheet
# defines .dot.y and .dot.p and nothing else.
DOT_CLASSES = ("y", "p")

PANEL_KEYS = {"heading", "caps", "footnote", "mount"}
MOUNT_KEYS = {"id", "class", "scroll_x"}

SHAPE = ('  {"eyebrow": "...", "title": "...", "lede": "...", "panels": [\n'
         '     {"heading": "...", "caps": ["..."], "footnote": null,\n'
         '      "mount": {"id": "vs-small-multiples", "class": "sm-grid",'
         ' "scroll_x": false}}]}')


def load_prose(report_dir):
    """Read prose/stats.json, refusing anything that would silently degrade the page."""
    path = os.path.join(report_dir, "prose", "stats.json")
    if not os.path.exists(path):
        raise SystemExit(f"missing {path} — 數據對決's words are hand-written; "
                         f"write it as\n{SHAPE}")
    with open(path, encoding="utf-8") as fh:
        prose = json.load(fh)

    missing = [k for k in ("eyebrow", "title", "lede")
               if not str(prose.get(k) or "").strip()]
    if missing:
        raise SystemExit(f"{path}: missing or empty {', '.join(missing)}\n{SHAPE}")

    panels = prose.get("panels") or []
    if not panels:
        raise SystemExit(f"{path}: no panels — the section would render as a legend "
                         f"with nothing under it\n{SHAPE}")

    seen = {}
    for i, p in enumerate(panels, 1):
        unknown = sorted(set(p) - PANEL_KEYS)
        if unknown:
            raise SystemExit(f"{path}: panel {i} has unknown key(s) {unknown}; a "
                             f"misspelt key is dropped in silence — expected "
                             f"{sorted(PANEL_KEYS)}")
        if not str(p.get("heading") or "").strip():
            raise SystemExit(f"{path}: panel {i} has no heading")
        caps = p.get("caps")
        if not isinstance(caps, list) or not caps or any(
                not str(c or "").strip() for c in caps):
            raise SystemExit(f"{path}: panel {i} needs caps as a non-empty list of "
                             "non-empty strings — a chart with no caption is a "
                             "picture nobody can read")
        if "footnote" in p and p["footnote"] is not None \
                and not str(p["footnote"]).strip():
            raise SystemExit(f"{path}: panel {i} has an empty footnote; use null to "
                             "leave it out")

        mount = p.get("mount")
        if not isinstance(mount, dict):
            raise SystemExit(f"{path}: panel {i} has no mount — the chart has nowhere "
                             f"to render\n{SHAPE}")
        unknown = sorted(set(mount) - MOUNT_KEYS)
        if unknown:
            raise SystemExit(f"{path}: panel {i} mount has unknown key(s) {unknown}; "
                             f"`scroll_x` misspelt unwraps a wide chart and nothing "
                             f"fails — expected {sorted(MOUNT_KEYS)}")
        if mount.get("id") not in MOUNT_IDS:
            raise SystemExit(
                f"{path}: panel {i} mounts {mount.get('id')!r}; the report's script "
                f"fills {sorted(MOUNT_IDS)} and an id outside that set renders a blank "
                "panel silently. Extend MOUNT_IDS with the script, not before it.")
        if mount["id"] in seen:
            raise SystemExit(f"{path}: panels {seen[mount['id']]} and {i} both mount "
                             f"{mount['id']!r}; the second chart would overwrite the "
                             "first")
        seen[mount["id"]] = i
        if not isinstance(mount.get("scroll_x"), bool):
            raise SystemExit(f"{path}: panel {i} mount needs scroll_x true or false, "
                             f"got {mount.get('scroll_x')!r}")
        if mount.get("class") is not None and not str(mount["class"]).strip():
            raise SystemExit(f"{path}: panel {i} mount has an empty class; use null")

    # The same guard the claim generator applies: reviews have repeatedly caught
    # 净/实/约 arriving from an editor with the wrong locale.
    text = " ".join([prose["eyebrow"], prose["title"], prose["lede"]]
                    + [str(p["heading"]) for p in panels]
                    + [str(c) for p in panels for c in p["caps"]]
                    + [str(p.get("footnote") or "") for p in panels])
    bad = sorted(set(text) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"{path}: simplified glyph(s) {bad} — this report is "
                         "traditional characters only")
    return prose


def _legend(players):
    """One swatch per player, in facts order — never champion-first."""
    if len(players) > len(DOT_CLASSES):
        raise SystemExit(f"{len(players)} players but the stylesheet defines swatches "
                         f"{list(DOT_CLASSES)} only")
    return [f'      <span class="sw"><span class="dot {cls}"></span>'
            f'{html.escape(name)}</span>'
            for cls, name in zip(DOT_CLASSES, players)]


def _mount(mount):
    attrs = (f' class="{html.escape(mount["class"])}"' if mount.get("class") else "")
    div = f'<div{attrs} id="{html.escape(mount["id"])}"></div>'
    return f'<div class="scroll-x">{div}</div>' if mount["scroll_x"] else div


def build(facts, prose):
    out = ['<section id="stats">', '  <div class="wrap-wide">',
           f'    <div class="eyebrow">{html.escape(prose["eyebrow"])}</div>',
           f'    <h2 class="section-title">{html.escape(prose["title"])}</h2>',
           f'    <p class="section-lede">{prose["lede"]}</p>',
           '',
           '    <div class="legend-row">']
    out += _legend(facts["players"])
    out.append('    </div>')

    for p in prose["panels"]:
        out += ['', '    <div class="chart-panel">',
                f'      <h3>{html.escape(p["heading"])}</h3>']
        out += [f'      <p class="cap">{c}</p>' for c in p["caps"]]
        out.append(f'      {_mount(p["mount"])}')
        if p.get("footnote"):
            out.append(f'      <p class="footnote">{p["footnote"]}</p>')
        out.append('    </div>')

    out += ['  </div>', '</section>']
    return "\n".join(out)
