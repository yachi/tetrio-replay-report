"""證明附錄 — the claims island and the appendix table.

Two generated things, both from the hand ledgers plus the proof map:

  claims-data   the JSON island the badges read (id -> canto, gloss, lemma,
                status). Kept, because every badge in the report resolves through
                it at runtime.
  appendix      the section itself: the trust-chain note, the status line, and one
                table row per claim — **rendered here as static HTML** rather than
                assembled in the browser. The old row builder concatenated five
                values into an innerHTML string, which is how a value becomes
                markup; every field is escaped here instead. Static rows also mean
                the appendix exists with JavaScript disabled and prints properly.

The island carries no timestamp. It used to record `generated_at`, which nothing
displayed and which made the artefact differ on every run — the opposite of what
this repo checks about its own outputs.

Counts in the prose are derived: the number of replay files and the claim total
were typed into the trust-chain text by hand and had to be edited whenever a
session changed shape.
"""
import html
import json
import os

from pipeline import claim_cards

# The island keeps the markers it has always had, so anything that locates it by
# name — including check_prose_figures, which skips it — keeps working.
ISLAND_START = "<!-- CLAIMS_DATA_START -->"
ISLAND_END = "<!-- CLAIMS_DATA_END -->"

PROOF_MAP = "claims-proof-map.json"
# Ledger filename -> the short tag the appendix labels its rows with.
TAGS = {"claims-narrative.json": "narrative",
        "claims-coaching.json": "coaching",
        "claims-generated.json": "generated"}


def _ledgers(report_dir):
    """The ledgers this session's committed proofs cover, in canonical order.

    The rule is "whose lemma is committed in this session's dafny/", which
    `claims-proof-map.json` already records — so no session needs to be named here.
    For 07-22 and 07-24 that is the two hand ledgers (their generated lemmas are
    built and verified in CI, never committed); for 07-28, whose hand claims carry
    specs and compile into the same Claims.dfy, it is both ledgers.

    Getting this wrong is not cosmetic. The island built from these rows is what a
    badge resolves against, and an unresolved badge renders as "⏳ G014" linking to
    an anchor that does not exist — indistinguishable from a claim still being
    proved. 38 cited claims looked pending that way.
    """
    names = sorted(n for n in os.listdir(report_dir)
                   if n.startswith("claims") and n.endswith(".json")
                   and "proof-map" not in n)
    order = ["claims-generated.json", "claims-narrative.json", "claims-coaching.json"]
    names.sort(key=lambda n: (order.index(n) if n in order else len(order), n))
    return [(n, TAGS.get(n, "hand")) for n in names]


def _rows(report_dir):
    """Every claim the committed proofs cover, in ledger order, status resolved."""
    out = []
    covered = set()
    path = os.path.join(report_dir, PROOF_MAP)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        rows = data if isinstance(data, list) else [dict(v, id=k) for k, v in data.items()]
        covered = {r["id"] for r in rows}
    for ledger, tag in _ledgers(report_dir):
        if not os.path.exists(os.path.join(report_dir, ledger)):
            continue
        for c in claim_cards.load(report_dir, ledger, proof_map=PROOF_MAP):
            if c["id"] not in covered:
                continue
            verified = c["verified"]
            raw = c["status"]
            # An unknown status still shows 驗證中 — never a tick the verifier did
            # not produce — but says which status it was, so a failure is visible.
            label = ("已驗證" if verified
                     else "驗證中" if raw is None else f"驗證中（{raw}）")
            out.append({"id": c["id"], "source": tag, "canto": c["canto"],
                        "english_gloss": c["english_gloss"], "category": c["category"],
                        "lemma": c["lemma"] or "—",
                        "status": "verified" if verified else "pending",
                        "status_label": label})
    return out


def island(report_dir):
    claims = _rows(report_dir)
    payload = {"proof_map_available": os.path.exists(
                   os.path.join(report_dir, "claims-proof-map.json")),
               "total_claims": len(claims),
               "verified_count": sum(1 for c in claims if c["status"] == "verified"),
               "claims": claims}
    return ('<script type="application/json" id="claims-data">\n'
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n</script>")


def _status_prose(total, verified, proof_map_available):
    """(status line, method paragraph) — the honest one of three wordings.

    Only the applicable branch is emitted, rather than shipping all three and
    picking in the browser.
    """
    if not proof_map_available:
        return (f"claims-proof-map.json 未搵到 · {total} 條 claim 全部「驗證中」⏳",
                "呢一版報告出爐嗰陣，claims-proof-map.json 仲未落地，所以下面啲狀態暫時"
                "全部顯示「驗證中」⏳；Dafny 引理一驗證完，淨係要行一次 "
                "<code>python3 -m pipeline.build_report &lt;report dir&gt;</code>，"
                "呢份報告就會自動翻新做 ✓，唔使再改呢份 HTML。")
    line = f"proof-map 已載入 · 已驗證 {verified} / {total}"
    if verified == total and total:
        return (line,
                f"呢一版報告出爐嗰陣，claims-proof-map.json 已經落地，下面 {total} 條 claim "
                "全部搵到對應嘅 Dafny 引理，逐條窮舉驗證完，加埋 mutation test 確認條 guard "
                "唔係擺個樣——所以下面啲狀態全部顯示「已驗證」✓。呢個信任鏈以後如果重新驗證，"
                "淨係要再行一次 <code>python3 -m pipeline.build_report &lt;report dir&gt;</code> "
                "就會自動同步，唔使再改呢份 HTML。")
    return (line,
            f"呢一版報告出爐嗰陣，claims-proof-map.json 已經落地，但 {total} 條 claim 入面"
            f"暫時得 {verified} 條驗證完，其餘仲喺度証緊，所以下面部分狀態仲顯示「驗證中」⏳；"
            "Dafny 引理跑晒之後，淨係要再行一次 "
            "<code>python3 -m pipeline.build_report &lt;report dir&gt;</code>，"
            "呢份報告就會自動翻新，唔使再改呢份 HTML。")


def section(facts, report_dir):
    claims = _rows(report_dir)
    total = len(claims)
    verified = sum(1 for c in claims if c["status"] == "verified")
    nfiles = len(facts["matches"])
    line, method = _status_prose(
        total, verified,
        os.path.exists(os.path.join(report_dir, "claims-proof-map.json")))

    out = ['<section id="appendix">', '  <div class="wrap-wide">',
           '    <div class="eyebrow">證明附錄 · 信任鏈</div>',
           '    <h2 class="section-title">證明附錄</h2>',
           '',
           '    <div class="method-note">',
           '      <p>呢份報告入面，每一句數得出嚟嘅嘢背後都有一條信任鏈：</p>',
           '      <div class="chain">',
           '        <div class="chain-step"><div class="n">1</div><div>數據由兩個獨立嘅 '
           'parser（extract.py 同 extract2.ts）各自由 '
           f'{nfiles} 個 replay 檔案（.ttrm）入面抽 facts，'
           '兩份輸出逐個欄位比對完全一致先算過關。</div></div>',
           '        <div class="chain-step"><div class="n">2</div><div>每一條 claim'
           f'（下面表入面嘅 {total} 條）都會有一條 Dafny 引理做形式驗證，'
           '證實個講法喺數學上一定成立——唔係跑幾個 sample 就話啱，而係窮舉證明。</div></div>',
           '        <div class="chain-step"><div class="n">3</div><div>仲會做 mutation '
           'test：刻意將條引理嘅 guard/前提拆走，睇下會唔會有 test 應聲斷——'
           '如果冧唔到，即係話條 guard 得個樣冇實際用，要補返。</div></div>',
           '      </div>',
           f'      <p id="method-status-text">{method}</p>',
           f'      <div id="status-line" class="mono" data-all-verified='
           f'"{str(verified == total and total > 0).lower()}">{html.escape(line)}</div>',
           '    </div>',
           '',
           '    <div class="scroll-x">',
           '      <table class="appendix-table">',
           '        <thead>',
           '          <tr>',
           '            <th>編號</th>',
           '            <th>廣東話講法</th>',
           '            <th>English gloss</th>',
           '            <th>Dafny 引理</th>',
           '            <th>狀態</th>',
           '          </tr>',
           '        </thead>',
           '        <tbody id="appendix-tbody">']
    for c in claims:
        icon = "✓" if c["status"] == "verified" else "⏳"
        out += [
            f'          <tr id="claim-{html.escape(c["id"])}">',
            f'            <td class="id-cell">{html.escape(c["id"])}</td>',
            f'            <td class="canto-cell">{html.escape(c["canto"])}</td>',
            f'            <td class="gloss-cell">{html.escape(c["english_gloss"])}</td>',
            f'            <td class="lemma-cell">{html.escape(c["lemma"])}</td>',
            f'            <td><span class="status-pill" data-status="{c["status"]}">'
            f'{icon} {html.escape(c["status_label"])}</span></td>',
            '          </tr>',
        ]
    out += ['        </tbody>', '      </table>', '    </div>',
            '  </div>', '</section>']
    return "\n".join(out)
