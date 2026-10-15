"""Transcribe harddrop's SDPC Spin route page into `sdpcspin-routes.json`.

    python3 -m pipeline.openers.extract_sdpcspin_routes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_sdpcspin_routes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_sdpcspin_routes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_sdpcspin_routes --html-dir <dir> --write  # ...and rewrite

The sixth opener ROUTE page, and the first whose source is not shiwehi.com: harddrop's own SDPC Spin
page (by Ecchou), read from its WIKITEXT. Its first bag is SDPC's (「stacked the same way as SDPC」):
the T laid flat into a T-spin Single, drawn in two J/L colourings on one occupancy (`bag1.lj`,
`bag1.jl`), and `bag1.after`. One bag-2 TSD board (`2.tsd`, `2.after`). Three bag-3 builds that fire
a TST (`3.first`, `3.second`, `3.third`), and each build's own continuation:

  * 3.first  — 「STMB Cave into STSD」 (`3.first.cave` → `.cave.stsd` → `.cave.stsd.next`) or a
               Trinity on the fifth bag (`3.first.trinity` → `.trinity.tsd` / `.trinity.tss`);
  * 3.second — the second C-Spin build (`3.second.cspin`, and `.cspin.z_early` with the Z on the J),
               the 「Alternate fourth bag」 with the I held (`3.second.alt#1/#2`), and on the C-Spin's
               residue a DT Cannon (`.cspin.dt#1/#2`), the 「First build」 (`.cspin.first#1/#2`) and
               swng's 「Second builds」 (`.cspin.o_first#1/#2`, `.cspin.l_first#1..#4`);
  * 3.third  — an Imperial Cross (`3.third.imperial`) and its four 14-line Perfect Clears
               (`3.third.imperial.pc#1..#4`), or the two setups that transition into the second C-Spin
               build (`3.third.transition#1/#2`).

Every rule the openers share is `route_transcription.py`'s, once; this file holds the transcription,
its `SPEC` and the rules only this page needs (`_sdpcspin_checks`).

WHERE THE TRANSCRIPTION COMES FROM. `NODES` below is a literal, hand-checked transcription of the
page's wikitext (`action=edit`), fetched with only-cli's `oc raw` (NOT curl). The saved snapshot holds
the page on ONE line (whitespace runs collapsed by the fetch); its hash is of those bytes. Each
`{{pfstart}} … {{pfend}}` is a board, `{{pfrow|…}}` ten cells, and every board was read by
`route_transcription.wikitext_cell` (blank `-`, G `c`, P and T `U`, `L<x>` the muted upper case `<x>`,
`'` `v`). Two independent hand transcriptions and a third direct parse agreed on every cell of all 35
boards before this file was written; `--html-dir` re-parses the page and compares board for board.

THE CROSS-SOURCES. Bag 1 has three, all of them checked here:
  * rule 2 (`harddrop_wikitext`): the FIRST TABLE of harddrop's SingleYou (SDPC) page's wikitext, the
    boards it introduces with 「In all continuations, the first bag is stacked like so:」. It draws the
    same three boards, cell for cell — which is the page's own sentence 「stacked the same way as
    SDPC」 checked, not assumed.
  * stick spin's transcription (`stickspin-routes.json`, a shiwehi.com page): `bag1.jl` is its
    `bag1.pc` mirrored, cell for cell, the T in the same U cells; `bag1.lj` is the same occupancy with
    the J and L cells divided the other way (the J/L split stick spin's test names); `bag1.after` is its
    `bag1.pc.after` mirrored, by occupancy.
  * Ivan's catalogue (`opener-fields.json`): the compound entry that names SDPC-Spin. Its four fields
    are SDPC's bag 1 with the T laid flat (this page's, as drawn and mirrored) and with the T stood up
    (stick spin's `bag1.fire`, which this page does not draw). Both halves are checked, so every field
    of the entry is accounted for and none is matched by a guess.
Bag 2 onward has NO second source and the file says so (`cross_source.bag2_onward`).

WHAT IS AN INFERENCE, flagged in the JSON rather than in prose only:
  * P and T are both read as the T in its spin slot (`U`): every board drawing either has the rows
    that T completes full (checked by the `spin:` rule), and the four PC boards are the only ones that
    write the T as T.
  * G is read as cells placed before the diagram (`c`): every board's c cells are exactly the board it
    continues after that board's T-spin (shared rule 3), so no G is garbage.
  * `base` is never read off a heading; it is the one earlier board whose post-spin cells equal this
    board's c cells (probed over every pair). That is how `3.first.trinity` comes to rest on
    `3.first.cave` (the fifth bag after the STMB Cave's TSD), and `3.second.alt` on `3.second`.
  * the spin NAMES (TSS, TSD, TST) are the rows each drawn T completes, never the page's word: the page
    names the TSD, the C-Spin, the STMB Cave, the STSD, the Trinity and the Imperial Cross, not each
    spin.
  * the paired boards (`first`, `o_first`, `l_first`) are one build with its T in two slots (equal,
    colour for colour, once the U cells are removed: checked). The page does not say which slot fires
    first, and nothing here does.

THE TERMS. harddrop publishes no licence for wiki content: the page footer carries only Privacy policy,
About and Powered by MediaWiki, and the About page has no body (both read 2026-10-15 with oc). The
credit is the source link in every page header, as for every harddrop page this repo reads.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers.route_transcription import EMPTY, after_spin, bottom, mirror, node, occ, setcell, t_slot

HERE = Path(__file__).resolve().parent
OUT = HERE / 'sdpcspin-routes.json'
STICKSPIN = HERE / 'stickspin-routes.json'
CATALOGUE = HERE / 'opener-fields.json'

#: live pieces lower case; c earlier cells; U the T in its spin; muted residue upper case; v vacated
ALPHABET = frozenset('-ijlostzcUvJLOSZ')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://harddrop.com/wiki/SDPC_Spin',
    'edit_url': 'https://harddrop.com/w/index.php?title=SDPC_Spin&action=edit',
    'title': 'SDPC Spin',
    'author': 'Ecchou (page text: 「an opener invented by Ecchou」)',
    'site': 'harddrop.com (Hard Drop Tetris Wiki, MediaWiki)',
    'updated': '2025-05-10',
    'updated_note': 'the rendered page\'s footer 「This page was last edited on 10 May 2025, at 14:16.」, read 2026-10-15 with oc',
    'oldid': 42723,
    'oldid_note': 'the rendered page\'s 「Retrieved from」 link names oldid=42723 (read 2026-10-15 with oc); the wikitext itself carries no revision id',
    'categories': ['T-Spin openers', 'T-Spin Single openers', 'Single Double openers'],
    'fetched': '2026-10-15',
    'fetch_method': 'only-cli `oc raw` of the action=edit page (NOT curl): the textarea\'s wikitext. The saved snapshot '
                    'holds the page on ONE line, whitespace runs collapsed by the fetch; the hash is of those bytes. '
                    'Boards are {{pfstart}} … {{pfend}} templates, 35 of them in 14 {| |} tables, read by '
                    'route_transcription.wikitext_tables / wikitext_cell',
    'snapshot_file': 'SDPC_Spin.wikitext',
    'snapshot_sha256': '6470895c2b8074f1e5b6051d06444eaac9ef38d95919e7ed1f581144012a0f80',
    'snapshot_bytes': 10999,
    'snapshot_note': 'sha256 of the wikitext this transcription was checked against. Not re-verifiable in CI: the page '
                     'is not committed and cannot be fetched there. Re-check with --html-dir after any refetch (with '
                     'SingleYou.wikitext, cross_source, beside it). A refetch that keeps the newlines will move the '
                     'hash without moving a board; the board diff is what to read.',
    'references_listed': ['https://harddrop.com/wiki/SDPC', 'https://harddrop.com/wiki/Stickspin',
                          'https://harddrop.com/wiki/STMB_Cave', 'https://harddrop.com/wiki/STSD',
                          'https://harddrop.com/wiki/Trinity', 'https://harddrop.com/wiki/Imperial_Cross',
                          'https://harddrop.com/wiki/Donation', 'https://harddrop.com/wiki/6-3',
                          'https://harddrop.com/wiki/5-4', 'https://harddrop.com/wiki/Tuck'],
    'references_note': 'the page\'s own [[links]], as URLs; none of them is read here except SDPC (as SingleYou, cross_source)',
}

#: harddrop's SingleYou page (the SDPC page), its FIRST table: the three bag-1 boards it introduces with
#: 「In all continuations, the first bag is stacked like so:」, in this file's alphabet. Rule 2's
#: `harddrop_wikitext` route compares `bag1.lj`, `bag1.jl` and `bag1.after` with them; `--html-dir`
#: re-parses the table (`route_transcription.check_wikitext_cross_source`).
CROSS_SOURCE = {
    'kind': 'harddrop_wikitext',
    'page': 'SingleYou',
    'url': 'https://harddrop.com/w/index.php?title=SingleYou&action=edit',
    'rendered_url': 'https://harddrop.com/wiki/SingleYou',
    'oldid': 43398,
    'oldid_note': 'the current revision per the page\'s history at the fetch; the wikitext itself carries no revision id',
    'fetched': '2026-10-15',
    'fetch_method': 'only-cli `oc raw` of the action=edit page, as for the source: one line, whitespace collapsed',
    'snapshot_file': 'SingleYou.wikitext',
    'snapshot_sha256': '9e659fb741834fe51b480530c5f4b974a2b291a7e18541dc340f04f742819121',
    'snapshot_bytes': 73303,
    'parser': 'pipeline.openers.route_transcription.wikitext_boards (wikitext_tables, cells read by wikitext_cell), '
              'each board trimmed by bottom(rows, 0): the reader the source page is read with',
    'table': 0,
    'table_context_verbatim': 'In all continuations, the first bag is stacked like so:',
    'fields': [
        ['--------s-', 'i-------ss', 'ilj---UUUs', 'iljjjzzUoo', 'ill---zzoo'],
        ['--------s-', 'i-------ss', 'ijj---UUUs', 'ijlllzzUoo', 'ijl---zzoo'],
        ['--------c-', 'c-------cc', 'ccc---cccc', 'ccc---cccc'],
    ],
    'fields_note': 'the table\'s three boards, in order: the T-spin Single with the L under the J at column 1, with '
                   'the J there, and the board after the TSS in grey. The page\'s sentence 「stacked the same way as '
                   'SDPC」 is this equality',
    'bag2_onward': 'single source: nothing outside this page draws its bag-2 board or anything after it. SingleYou\'s '
                   'own second bag (its Perfect Clear route) is a different board, and is not compared',
    'why_not_wiki_openers': 'wiki-openers.json transcribes seven openers and has no SDPC or SDPC Spin field; adding one '
                            'would re-emit every session\'s opener-facts.json (the 六個具名定式 table reads it)',
}

TERMS = {
    'url': 'https://harddrop.com/wiki/Hard_Drop_Tetris_Wiki:About',
    'dated': 'not stated: harddrop publishes no licence or terms page for wiki content',
    'read': '2026-10-15, with oc: the SDPC Spin page footer (Privacy policy, About Hard Drop Tetris Wiki, Powered by '
            'MediaWiki — no licence line) and the About page it links (no body)',
    'allows': 'not stated (no licence is published)',
    'excludes': 'not stated (no licence is published)',
    'requests': 'not stated; credited by link, as this repo credits every harddrop page it reads',
    'how_met': 'source link to the harddrop page in every page header; no ads on GitHub Pages',
}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ, align at the BOTTOM row',
    '-': 'empty (a blank cell or {{pfrowblank}})',
    'i o s z j l': 'a live cell of that piece (the page\'s single upper-case letter)',
    'c': 'a cell placed before this diagram, drawn grey G (checked: exactly what the board this one continues leaves after its spin)',
    'U': 'the T, drawn in the slot whose rows it completes: the page writes it P (purple), and T on the four PC boards (OUR READING, one letter for both)',
    'J L O S Z': 'a muted cell of that piece, the page\'s two-letter L<x> (DT Cannon continuation): residue of the C-Spin, drawn dimmed',
    'v': 'the page\'s apostrophe: the cells the Z leaves when it goes on the J instead (checked: exactly 3.second.cspin\'s z cells)',
    '%X': 'the X piece',
    'label_jp': 'the source\'s own words (here English): a heading path or a bold label, never a caption of ours',
}


#: Every sentence the transcription leans on, verbatim from the wikitext (markup kept, so --html-dir
#: finds each byte for byte); every `*_verbatim` field below must be one of these (`_sdpcspin_checks`).
QUOTES = [
    {'id': 'overview.intro', 'figure': None,
     'verbatim': "'''SDPC Spin''' is an opener invented by Ecchou. It sends the same amount of attack as [[Stickspin]], but has a simpler third bag."},
    {'id': 'bag1.sdpc', 'figure': None, 'verbatim': 'The first bag is stacked the same way as [[SDPC]].'},
    {'id': 'bag3.ways', 'figure': 'two',
     'verbatim': 'There are two main ways to stack the third bag. The first is always possible, but the second results in a flatter stack.'},
    {'id': 'bag3.third', 'figure': None, 'verbatim': 'If S comes before O, the third build can also be stacked.'},
    {'id': 'bag3.center', 'figure': None,
     'verbatim': 'If the first build or third build is used, the center area must be filled in to complete the T-Spin Double. This can be done freestyle or using the [[STMB Cave]] continuation below.'},
    {'id': 'first.heading', 'figure': None, 'verbatim': '===First C-Spin build==='},
    {'id': 'cave.heading', 'figure': None, 'verbatim': "'''[[STMB Cave]] into [[STSD]]'''"},
    {'id': 'cave.author', 'figure': None, 'verbatim': 'Created by stickmancomic.'},
    {'id': 'cave.requires', 'figure': None, 'verbatim': 'This requires the first build to be taken for the third bag.'},
    {'id': 'cave.j', 'figure': 'two', 'verbatim': 'J needs to come before at least two of T, L, and Z.'},
    {'id': 'trinity', 'figure': None,
     'verbatim': 'Alternatively, one can build a [[Trinity]] on the fifth bag, leaving cleaner residue.'},
    {'id': 'trinity.after', 'figure': None, 'verbatim': 'From here it is possible to upstack or [[Donation|donate]] a TSD.'},
    {'id': 'second.heading', 'figure': None, 'verbatim': '===Second C-Spin build==='},
    {'id': 'second.covers', 'figure': '73.33%', 'verbatim': 'Covers 73.33% of all bags.'},
    {'id': 'second.z_early', 'figure': None, 'verbatim': 'If Z comes too early, one can sometimes put Z on top of the J piece.'},
    {'id': 'alt.heading', 'figure': None, 'verbatim': "'''Alternate fourth bag'''"},
    {'id': 'alt.pc12', 'figure': '68.10% / 12-line',
     'verbatim': 'If I is saved, there is a 68.10% chance of being able to do a 12-line perfect clear.',
     'note': 'no 12-line PC is drawn; nothing here re-derives 68.10%'},
    {'id': 'alt.transition', 'figure': None, 'verbatim': 'Otherwise, one can transition into [[6-3]] or [[5-4]].'},
    {'id': 'dt.heading', 'figure': None, 'verbatim': "'''DT Cannon continuation'''"},
    {'id': 'dt', 'figure': None, 'verbatim': 'One can build a DT Cannon with the residue after completing the C-Spin.'},
    {'id': 'cspin_first.heading', 'figure': None, 'verbatim': "'''First build'''"},
    {'id': 'cspin_first.covers', 'figure': '91.67%', 'verbatim': 'Covers 91.67% of all fifth bags, leading into 6-3.'},
    {'id': 'cspin_second.heading', 'figure': None, 'verbatim': "'''Second builds'''"},
    {'id': 'cspin_second.author', 'figure': None, 'verbatim': 'Made by swng.'},
    {'id': 'o_first', 'figure': None, 'verbatim': "'''O before L'''"},
    {'id': 'l_first', 'figure': None, 'verbatim': "'''L before O'''"},
    {'id': 'third.heading', 'figure': None, 'verbatim': '===Third C-Spin build==='},
    {'id': 'third.imperial', 'figure': None, 'verbatim': 'An [[Imperial Cross]] can sometimes be built.'},
    {'id': 'third.pc', 'figure': '99.68% / 14-line / 4',
     'verbatim': 'From here, there is a 99.68% chance of a 14-line Perfect Clear with 4 minimals.',
     'note': '14 is re-derived along the base chain (`lines:`); 99.68% is not'},
    {'id': 'third.transition', 'figure': None,
     'verbatim': 'The setups below can transition to the second C-Spin build. For the second diagram hold O and [[tuck]] it after taking the TSD.'},
]


BAG1 = {
    'locks': 7,
    'spin': 'TSS',
    't_orientation': 'flat',
    'sdpc_verbatim': 'The first bag is stacked the same way as [[SDPC]].',
    'colourings': ['bag1.lj', 'bag1.jl'],
    'colourings_note': 'one occupancy, two colourings, NOT mirrors (checked): the page draws the I at the left wall in '
                       'both and divides the J and L cells of columns 1-4 two ways. bag1.jl is stick spin\'s bag1.pc '
                       'mirrored; bag1.lj is the J/L split stick spin\'s test names',
    'stickspin': {'jl': 'bag1.pc', 'after': 'bag1.pc.after', 'how': 'mirrored'},
    'catalogue_name_contains': 'SDPC-Spin',
    'catalogue_note': 'Ivan\'s compound entry (SDPC / Motchi PC / Stickspin / SDPC-Spin / …): its four fields are the '
                      'flat-T board (bag1.lj / bag1.jl, T placed, as drawn and mirrored, by occupancy) and the stood-T '
                      'board (stick spin\'s bag1.fire, which this page does not draw). Checked both ways by `catalogue:`',
    'mirror_note': 'the page draws no mirrored bag 1 and names no side; the mirror is the classifier\'s business',
    'requires': {},
    'requires_note': 'the page states no bag-1 piece order or early piece; empty, not absent, so the shared demo '
                     'check reads "no early piece" from the transcription itself',
}


BASIC_FORM: list = []


KNOWN_DISCREPANCIES = [
    {
        'id': '3.second.cspin.dt#1:colour',
        'what': 'the DT Cannon board draws the C-Spin\'s residue muted (LJ LZ LS LL LO) except the bag-3 I at the left '
                'wall, which it draws as a live I: so the board carries two live I pieces, the old one and the new one '
                'at column 9 (checked: the cells the residue leaves unmuted are exactly that I)',
    },
    {
        'id': '3.second.cspin.dt#2:colour',
        'what': 'as #1: the residue\'s bag-3 I drawn live beside the new I at column 6',
    },
]


#: Every node, in page order (the PC patterns are inserted after their anchor by `build`).
NODES: list[dict] = [
    # ── ==First bag== ──
    {
        'id': 'bag1.lj.left',
        'bag': 1, 'parent': None, 'locks': 6,
        'derived': True, 'derived_from': 'bag1.lj',
        'label': 'bag 1, less its T (derived: the TSS board with its U cells removed)',
        'rows': _b('---------- --------s- i-------ss ilj------s iljjjzz-oo ill---zzoo'),
    },
    {
        'id': 'bag1.lj',
        'bag': 1, 'parent': 'bag1.lj.left', 'locks': 7, 'spin': 'TSS',
        'label_jp': 'First bag',
        'label': 'bag 1, the T laid flat into a T-spin Single; the L under the J at column 1 (the J/L split)',
        'group': 'bag1.sdpc', 'variant': 1,
        'rows': _b('---------- --------s- i-------ss ilj---UUUs iljjjzzUoo ill---zzoo'),
        'spin_of': 'bag1.lj.left',
    },
    {
        'id': 'bag1.jl.left',
        'bag': 1, 'parent': None, 'locks': 6,
        'derived': True, 'derived_from': 'bag1.jl',
        'label': 'bag 1, less its T (derived: the TSS board with its U cells removed)',
        'rows': _b('---------- --------s- i-------ss ijj------s ijlllzz-oo ijl---zzoo'),
    },
    {
        'id': 'bag1.jl',
        'bag': 1, 'parent': 'bag1.jl.left', 'locks': 7, 'spin': 'TSS',
        'label_jp': 'First bag',
        'label': 'bag 1, the T laid flat into a T-spin Single; the J at column 1 (stick spin\'s bag1.pc, mirrored)',
        'group': 'bag1.sdpc', 'variant': 2,
        'rows': _b('---------- --------s- i-------ss ijj---UUUs ijlllzzUoo ijl---zzoo'),
        'spin_of': 'bag1.jl.left',
    },
    {
        'id': 'bag1.after',
        'bag': 1, 'parent': 'bag1.sdpc',
        'label_jp': 'First bag',
        'label': 'bag 1 after the TSS, in grey (both colourings collapse to it; checked)',
        'node_kind': 'illustration',
        'after_of': 'bag1.lj',
        'also_after_of': 'bag1.jl',
        'rows': _b('---------- ---------- --------c- c-------cc ccc---cccc ccc---cccc'),
    },
    # ── ==Second bag== ──
    {
        'id': '2.tsd',
        'bag': 2, 'parent': None, 'base': 'bag1.after', 'spin': 'TSD',
        'label_jp': 'Second bag',
        'label': 'bag 2, the T laid flat into a TSD under the bag-1 residue',
        'rows': _b('---------- ---------i -j-----ooi -j----sooi jj-l--ssci clllUUUscc ccczzUcccc ccc-zzcccc'),
    },
    {
        'id': '2.after',
        'bag': 2, 'parent': '2.tsd',
        'label_jp': 'Second bag',
        'label': 'bag 2 after the TSD, in grey',
        'node_kind': 'illustration',
        'after_of': '2.tsd',
        'rows': _b('---------- ---------- ---------- ---------c -c-----ccc -c----cccc cc-c--cccc ccc-cccccc'),
    },
    # ── ==Third bag== ──
    {
        'id': '3.first',
        'bag': 3, 'parent': '2.tsd', 'base': '2.after', 'spin': 'TST',
        'label_jp': 'Third bag',
        'label': 'bag 3, the first build (「always possible」): the T stood up into the C-Spin\'s TST',
        'group': '3.build', 'variant': 1,
        'rows': _b('---------- --------s- --z-----ss izz----oos iz-----ooc icUlljjccc icUUljcccc ccUcljcccc ccc-cccccc'),
    },
    {
        'id': '3.second',
        'bag': 3, 'parent': '2.tsd', 'base': '2.after', 'spin': 'TST',
        'label_jp': 'Third bag',
        'label': 'bag 3, the second build (「a flatter stack」): the O and S lower than in the first',
        'group': '3.build', 'variant': 2,
        'rows': _b('---------- ---------- --z------- izz--oo-ss iz---oossc icUlljjccc icUUljcccc ccUcljcccc ccc-cccccc'),
    },
    {
        'id': '3.third',
        'bag': 3, 'parent': '2.tsd', 'base': '2.after', 'spin': 'TST',
        'label_jp': 'Third bag',
        'label': 'bag 3, the third build (S before O): the O on the S at the right',
        'group': '3.build', 'variant': 3,
        'condition_verbatim': 'If S comes before O, the third build can also be stacked.',
        'condition': {'all': [{'before': ['S', 'O']}]},
        'condition_evidence': [{'before': ['S', 'O'], 'by': 'support'}],
        'condition_note': 'the page\'s order; the board forces it (an O cell rests on an S cell)',
        'rows': _b('---------- --------oo --z-----oo izz-----ss iz-----ssc icUlljjccc icUUljcccc ccUcljcccc ccc-cccccc'),
    },
    # ── ===First C-Spin build=== '''STMB Cave into STSD''' ──
    {
        'id': '3.first.cave',
        'bag': 4, 'parent': '3.first', 'base': '3.first', 'spin': 'TSD',
        'label_jp': 'First C-Spin build / STMB Cave into STSD',
        'label': 'first build, bag 4: the STMB Cave, its T into the TSD at the centre',
        'requires_verbatim': 'This requires the first build to be taken for the third bag.',
        'condition_verbatim': 'J needs to come before at least two of T, L, and Z.',
        'condition': {'at_least': {'before': 'J', 'count': 2, 'of': ['T', 'L', 'Z']}},
        'condition_evidence': [
            {'before': ['J', 'T'], 'by': 'support'},
            {'before': ['J', 'L'], 'by': None, 'note': 'stated (at least two of three): the board does not force it, no L cell rests on the J'},
            {'before': ['J', 'Z'], 'by': None, 'note': 'stated (at least two of three): the board does not force it, no Z cell rests on the J'},
        ],
        'condition_note': 'OUR READING of 「at least two of T, L, and Z」 as J before any two of the three; the board forces only J before T',
        'rows': _b('---------- -------s-i -------ssi ------llsi oozzUUUlci ooczzUjlcc ccc---jccc cc---jjccc ccc-cccccc'),
    },
    {
        'id': '3.first.cave.stsd',
        'bag': 5, 'parent': '3.first.cave', 'base': '3.first.cave', 'spin': 'TSD',
        'label_jp': 'First C-Spin build / STMB Cave into STSD',
        'label': 'first build, bag 5: the STSD, its T into the TSD at the bottom',
        'unmatchable': '9 non-empty rows > ROWS = 8',
        'rows': _b('------s--- ------ss-z i----llszz i-----lczc ioojj-lccc iooj--cccc cccj--cccc ccUUUccccc cccUcccccc'),
    },
    {
        'id': '3.first.cave.stsd.next',
        'bag': 6, 'parent': '3.first.cave.stsd', 'base': '3.first.cave.stsd', 'spin': 'TSD',
        'label_jp': 'First C-Spin build / STMB Cave into STSD',
        'label': 'first build, after the STSD: an O and the T into the next TSD (the T stood up)',
        'bag_note': 'OUR READING: the two pieces after a 7-piece bag 5 are bag 6',
        'rows': _b('---------- ---------- ------c--- ------cc-c coo--ccccc coo---cccc cccccUcccc ccccUUcccc cccc-Ucccc'),
    },
    {
        'id': '3.first.trinity',
        'bag': 5, 'parent': '3.first.cave', 'base': '3.first.cave', 'spin': 'TSD',
        'label_jp': 'First C-Spin build',
        'label_jp_note': 'the heading only: the bold 「STMB Cave into STSD」 labels the table before; this one follows 「Alternatively, one can build a Trinity on the fifth bag」',
        'label': 'first build, bag 5: a Trinity instead of the STSD, its T into the TSD at the bottom',
        'text_verbatim': 'Alternatively, one can build a [[Trinity]] on the fifth bag, leaving cleaner residue.',
        'rows': _b('---------- ---------z i-ss--jjzz iss---jczc ioo-lljccc ioo--lcccc ccc--lcccc ccUUUccccc cccUcccccc'),
    },
    {
        'id': '3.first.trinity.tsd',
        'bag': 6, 'parent': '3.first.trinity', 'base': '3.first.trinity', 'spin': 'TSD',
        'label_jp': 'First C-Spin build',
        'label': 'Trinity, the T alone into the cave its TSD leaves (the T stood up)',
        'bag_note': 'OUR READING: placed after bag 5',
        'order_note': 'this board and 3.first.trinity.tss both rest on 3.first.trinity after its TSD and neither holds the other\'s T (checked): the page does not say which T fires first',
        'rows': _b('---------- ---------- ---------- ---------c c-cc--cccc ccc---cccc cccUcccccc cccUUccccc cccU-ccccc'),
    },
    {
        'id': '3.first.trinity.tss',
        'bag': 6, 'parent': '3.first.trinity', 'base': '3.first.trinity', 'spin': 'TSS',
        'label_jp': 'First C-Spin build',
        'label': 'Trinity, a Z and an S and the T laid flat over the left wall: one row',
        'bag_note': 'OUR READING: placed after bag 5',
        'order_note': 'see 3.first.trinity.tsd',
        'rows': _b('---------- ---------- --zz------ UUUzzss--c cUccsscccc ccc---cccc ccc-cccccc ccc--ccccc ccc--ccccc'),
    },
    {
        'id': '3.first.trinity.donate',
        'bag': 6, 'parent': '3.first.trinity',
        'node_kind': 'text_only',
        'label': 'after the Trinity: upstack, or donate a TSD (no board)',
        'page_text': 'From here it is possible to upstack or [[Donation|donate]] a TSD.',
    },
    # ── ===Second C-Spin build=== ──
    {
        'id': '3.second.cspin',
        'bag': 4, 'parent': '3.second', 'base': '3.second', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build',
        'label': 'second build, bag 4: the C-Spin\'s TSD at the bottom',
        'text_verbatim': 'Covers 73.33% of all bags.',
        'rows': _b('---------- ---------- ---------- i--------- ijj----lll ij---zsloo ijc-zzssoo ccc-zccscc ccUUUccccc cccUcccccc'),
    },
    {
        'id': '3.second.cspin.z_early',
        'bag': 4, 'parent': '3.second', 'base': '3.second', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build',
        'label': 'second build, bag 4, when the Z comes too early: the Z on the J, its usual cells marked',
        'text_verbatim': 'If Z comes too early, one can sometimes put Z on top of the J piece.',
        'vacated_of': '3.second.cspin',
        'unmatchable': 'draws one Z twice (on the J, and its usual cells marked with apostrophes): not one board state; '
                       'and 9 non-empty rows > ROWS = 8',
        'rows': _b('---------- --z------- -zz------- iz-------- ijj----lll ij---vsloo ijc-vvssoo ccc-vccscc ccUUUccccc cccUcccccc'),
    },
    # '''Alternate fourth bag'''
    {
        'id': '3.second.alt#1',
        'bag': 4, 'parent': '3.second', 'base': '3.second', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / Alternate fourth bag',
        'label': 'second build, alternate bag 4 with the I held: J and Z at the left wall',
        'group': '3.second.alt', 'variant': 1,
        'hold': 'I', 'hold_verbatim': 'If I is saved, there is a 68.10% chance of being able to do a 12-line perfect clear.',
        'rows': _b('---------- jjz----lll jzz---sloo jzc---ssoo ccc--ccscc ccUUUccccc cccUcccccc'),
    },
    {
        'id': '3.second.alt#2',
        'bag': 4, 'parent': '3.second', 'base': '3.second', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / Alternate fourth bag',
        'label': 'second build, alternate bag 4 with the I held: L and O at the left wall',
        'group': '3.second.alt', 'variant': 2,
        'hold': 'I', 'hold_verbatim': 'If I is saved, there is a 68.10% chance of being able to do a 12-line perfect clear.',
        'rows': _b('---------- loo----jjj loo---szzj llc---sszz ccc--ccscc ccUUUccccc cccUcccccc'),
    },
    {
        'id': '3.second.alt.pc12',
        'bag': 5, 'parent': '3.second.alt',
        'node_kind': 'text_only',
        'label': 'with the I held, a 12-line Perfect Clear (no board drawn)',
        'page_text': 'If I is saved, there is a 68.10% chance of being able to do a 12-line perfect clear.',
    },
    {
        'id': '3.second.alt.transition',
        'bag': 5, 'parent': '3.second.alt',
        'node_kind': 'text_only',
        'label': 'otherwise, into 6-3 or 5-4 (no board drawn)',
        'page_text': 'Otherwise, one can transition into [[6-3]] or [[5-4]].',
    },
    # '''DT Cannon continuation'''
    {
        'id': '3.second.cspin.dt#1',
        'bag': 5, 'parent': '3.second.cspin', 'residue_of': '3.second.cspin', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / DT Cannon continuation',
        'label': 'second build, DT Cannon on the C-Spin\'s residue: the new I at the right wall',
        'group': '3.second.cspin.dt', 'variant': 1,
        'text_verbatim': 'One can build a DT Cannon with the residue after completing the C-Spin.',
        'residue_note': 'no `base`: the residue is drawn muted (upper case), not grey, so the shared c-cells rule cannot '
                        'read it. `residue:` checks c plus the muted cells plus the one I drawn live are exactly '
                        '3.second.cspin after its TSD, letter for letter',
        'live_residue': 'i',
        'rows': _b('---------- ---------i s-jj--oo-i ssj---ooli isj-zzllli iJJ--zzLLL iJUUUZSLOO iJcUZZSSOO ccc-ZccScc'),
    },
    {
        'id': '3.second.cspin.dt#2',
        'bag': 5, 'parent': '3.second.cspin', 'residue_of': '3.second.cspin', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / DT Cannon continuation',
        'label': 'second build, DT Cannon on the C-Spin\'s residue: the new I at column 6',
        'group': '3.second.cspin.dt', 'variant': 2,
        'text_verbatim': 'One can build a DT Cannon with the residue after completing the C-Spin.',
        'live_residue': 'i',
        'rows': _b('---------- ------i--- s-jj--i-ll ssj---iool isj-zziool iJJ--zzLLL iJUUUZSLOO iJcUZZSSOO ccc-ZccScc'),
    },
    # '''First build'''
    {
        'id': '3.second.cspin.first#1',
        'bag': 5, 'parent': '3.second.cspin', 'base': '3.second.cspin', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / First build',
        'label': 'second build, bag 5, first build: the T in the residue\'s slot at the bottom',
        'group': '3.second.cspin.first', 'variant': 1, 't_slot': 'residue',
        'text_verbatim': 'Covers 91.67% of all fifth bags, leading into 6-3.',
        'unmatchable': '9 non-empty rows > ROWS = 8',
        'rows': _b('---------- i--------- i--------- i-z---oos- izz--jooss cz---jllls ccc-jjlccc ccUUUccccc cccUcccccc ccc-cccccc'),
    },
    {
        'id': '3.second.cspin.first#2',
        'bag': 5, 'parent': '3.second.cspin', 'base': '3.second.cspin', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / First build',
        'label': 'second build, bag 5, first build: the T in the slot the build makes',
        'group': '3.second.cspin.first', 'variant': 2, 't_slot': 'build',
        'text_verbatim': 'Covers 91.67% of all fifth bags, leading into 6-3.',
        'unmatchable': '9 non-empty rows > ROWS = 8',
        'rows': _b('---------- i--------- i--------- i-z---oos- izz--jooss czUUUjllls cccUjjlccc cc---ccccc ccc-cccccc ccc-cccccc'),
    },
    # '''Second builds''' '''O before L'''
    {
        'id': '3.second.cspin.o_first#1',
        'bag': 5, 'parent': '3.second.cspin', 'base': '3.second.cspin', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / Second builds / O before L',
        'label': 'second build, bag 5, swng\'s build with the O before the L: the T in the residue\'s slot',
        'group': '3.second.cspin.o_first', 'variant': 1, 't_slot': 'residue',
        'condition_verbatim': "'''O before L'''",
        'condition': {'all': [{'before': ['O', 'L']}]},
        'condition_evidence': [{'before': ['O', 'L'], 'by': 'support'}],
        'condition_note': 'the page\'s order; the board forces it (an L cell rests on an O cell)',
        'rows': _b('---------- -----z---- s---zzi-ll ss--zjiool cs---jiool ccc-jjiccc ccUUUccccc cccUcccccc ccc-cccccc'),
    },
    {
        'id': '3.second.cspin.o_first#2',
        'bag': 5, 'parent': '3.second.cspin', 'base': '3.second.cspin', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / Second builds / O before L',
        'label': 'second build, bag 5, O before L: the T in the slot the build makes',
        'group': '3.second.cspin.o_first', 'variant': 2, 't_slot': 'build',
        'condition_verbatim': "'''O before L'''",
        'condition': {'all': [{'before': ['O', 'L']}]},
        'condition_evidence': [{'before': ['O', 'L'], 'by': 'support'}],
        'rows': _b('---------- -----z---- s---zzi-ll ss--zjiool csUUUjiool cccUjjiccc cc---ccccc ccc-cccccc ccc-cccccc'),
    },
    # '''L before O'''
    {
        'id': '3.second.cspin.l_first#1',
        'bag': 5, 'parent': '3.second.cspin', 'base': '3.second.cspin', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / Second builds / L before O',
        'label': 'second build, bag 5, L before O, the I at the right wall: the T in the residue\'s slot',
        'group': '3.second.cspin.l_first', 'variant': 1, 't_slot': 'residue', 'build': 1,
        'condition_verbatim': "'''L before O'''",
        'condition': {'all': [{'before': ['L', 'O']}]},
        'condition_evidence': [{'before': ['L', 'O'], 'by': 'support'}],
        'condition_note': 'the page\'s order; the board forces it (an O cell rests on an L cell)',
        'rows': _b('---------- -----z---i s---zz-ooi ss--zj-ooi cs---jllli ccc-jjlccc ccUUUccccc cccUcccccc ccc-cccccc'),
    },
    {
        'id': '3.second.cspin.l_first#2',
        'bag': 5, 'parent': '3.second.cspin', 'base': '3.second.cspin', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / Second builds / L before O',
        'label': 'second build, bag 5, L before O, the I at the right wall: the T in the slot the build makes',
        'group': '3.second.cspin.l_first', 'variant': 2, 't_slot': 'build', 'build': 1,
        'condition_verbatim': "'''L before O'''",
        'condition': {'all': [{'before': ['L', 'O']}]},
        'condition_evidence': [{'before': ['L', 'O'], 'by': 'support'}],
        'rows': _b('---------- -----z---i s---zz-ooi ss--zj-ooi csUUUjllli cccUjjlccc cc---ccccc ccc-cccccc ccc-cccccc'),
    },
    {
        'id': '3.second.cspin.l_first#3',
        'bag': 5, 'parent': '3.second.cspin', 'base': '3.second.cspin', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / Second builds / L before O',
        'label': 'second build, bag 5, L before O, the I at column 6: the T in the residue\'s slot',
        'group': '3.second.cspin.l_first', 'variant': 3, 't_slot': 'residue', 'build': 2,
        'condition_verbatim': "'''L before O'''",
        'condition': {'all': [{'before': ['L', 'O']}]},
        'condition_evidence': [{'before': ['L', 'O'], 'by': 'support'}],
        'rows': _b('---------- -----z---- s---zzioo- ss--zjiool cs---jilll ccc-jjiccc ccUUUccccc cccUcccccc ccc-cccccc'),
    },
    {
        'id': '3.second.cspin.l_first#4',
        'bag': 5, 'parent': '3.second.cspin', 'base': '3.second.cspin', 'spin': 'TSD',
        'label_jp': 'Second C-Spin build / Second builds / L before O',
        'label': 'second build, bag 5, L before O, the I at column 6: the T in the slot the build makes',
        'group': '3.second.cspin.l_first', 'variant': 4, 't_slot': 'build', 'build': 2,
        'condition_verbatim': "'''L before O'''",
        'condition': {'all': [{'before': ['L', 'O']}]},
        'condition_evidence': [{'before': ['L', 'O'], 'by': 'support'}],
        'rows': _b('---------- -----z---- s---zzioo- ss--zjiool csUUUjilll cccUjjiccc cc---ccccc ccc-cccccc ccc-cccccc'),
    },
    # ── ===Third C-Spin build=== ──
    {
        'id': '3.third.imperial',
        'bag': 4, 'parent': '3.third', 'base': '3.third', 'spin': 'TSD',
        'label_jp': 'Third C-Spin build',
        'label': 'third build, bag 4: an Imperial Cross, its first T into rows 5 and 7 (not adjacent)',
        'text_verbatim': 'An [[Imperial Cross]] can sometimes be built.',
        'rows': _b('---------- i------jjj i------ssj illl--sscc ilc---oocc cccUzzoocc ccUU-zzccc cccUcccccc'),
    },
    {
        'id': '3.third.transition#1',
        'bag': 4, 'parent': '3.third', 'base': '3.third', 'spin': 'TSD',
        'label_jp': 'Third C-Spin build',
        'label': 'third build, bag 4: a TSD that leaves the second C-Spin build\'s residue',
        'group': '3.third.transition', 'variant': 1,
        'transition_to': '3.second.cspin',
        'text_verbatim': 'The setups below can transition to the second C-Spin build. For the second diagram hold O and [[tuck]] it after taking the TSD.',
        'rows': _b('i--------- ijj----lll ij---zslcc ijc-zzsscc ccc-zooscc ccUUUooccc cccUcccccc'),
    },
    {
        'id': '3.third.transition#2',
        'bag': 4, 'parent': '3.third', 'base': '3.third', 'spin': 'TSD',
        'label_jp': 'Third C-Spin build',
        'label': 'third build, bag 4: the same, the O held and tucked after the TSD',
        'group': '3.third.transition', 'variant': 2,
        'transition_to': '3.second.cspin',
        'hold': 'O',
        'hold_verbatim': 'The setups below can transition to the second C-Spin build. For the second diagram hold O and [[tuck]] it after taking the TSD.',
        'hold_note': 'the page\'s instruction; the board draws the O where it ends after the tuck, so nothing here checks the hold',
        'rows': _b('i--------- ijj----lll ij---zzlcc ijc-oozzcc ccc-oosscc ccUUUssccc cccUcccccc'),
    },
]


#: The page's PC list. `shown` / `rest_stated` are the page's own split.
_IMPERIAL_PC_ROWS = [
    '---------- lljjooiiii cljsoozccc cljsszzccc ccccszcccc cccUUUcccc ccccUccccc',
    '---------- lljjzziiii cljoozzccc cljoossccc ccccsscccc cccUUUcccc ccccUccccc',
    '---------- lljjssiiii cljssooccc cljzzooccc cccczzcccc cccUUUcccc ccccUccccc',
    '---------- zzjjjsiiii czzljssccc cllloosccc ccccoocccc cccUUUcccc ccccUccccc',
]

#: several boards under one heading: each member names its group. `drawn` is the page's own count.
GROUPS = [
    {'id': 'bag1.sdpc', 'heading': 'First bag', 'drawn': 2,
     'text_verbatim': 'The first bag is stacked the same way as [[SDPC]].',
     'note': 'one occupancy, two J/L colourings (bag1.after, the third board of the table, is their after board)'},
    {'id': '3.build', 'heading': 'Third bag', 'drawn': 3,
     'text_verbatim': 'There are two main ways to stack the third bag. The first is always possible, but the second results in a flatter stack.'},
    {'id': '3.second.alt', 'heading': 'Second C-Spin build / Alternate fourth bag', 'drawn': 2},
    {'id': '3.second.cspin.dt', 'heading': 'Second C-Spin build / DT Cannon continuation', 'drawn': 2},
    {'id': '3.second.cspin.first', 'heading': 'Second C-Spin build / First build', 'drawn': 2,
     'reading': 'one build, its T drawn in two slots (equal colour for colour once the U cells are removed, checked); which fires first is not stated'},
    {'id': '3.second.cspin.o_first', 'heading': 'Second C-Spin build / Second builds / O before L', 'drawn': 2,
     'reading': 'as 3.second.cspin.first'},
    {'id': '3.second.cspin.l_first', 'heading': 'Second C-Spin build / Second builds / L before O', 'drawn': 4,
     'reading': 'two builds (the I at the right wall, the I at column 6), each its T in two slots'},
    {'id': '3.third.transition', 'heading': 'Third C-Spin build', 'drawn': 2,
     'text_verbatim': 'The setups below can transition to the second C-Spin build. For the second diagram hold O and [[tuck]] it after taking the TSD.'},
]

LISTS = [
    {'id': '3.third.imperial.pc', 'parent': '3.third.imperial', 'base': '3.third.imperial', 'bag': 5,
     'heading': 'Third C-Spin build', 'rows': _IMPERIAL_PC_ROWS,
     'stated_pattern_count': 4, 'shown': 4, 'rest_stated': 0, 'complete': True,
     'count_note': 'the page\'s 「4 minimals」: a minimal solution set the page gives its 99.68% over, read as complete for that reason',
     'rate_verbatim': 'From here, there is a 99.68% chance of a 14-line Perfect Clear with 4 minimals.',
     'pc_lines': 8, 'total_lines': 14, 'total_lines_quote': 'third.pc',
     'pc_lines_note': 'the 6-row body plus the Imperial Cross\'s first TSD before it; the page\'s 14-line counts every '
                      'spin from bag 1 (TSS 1 + TSD 2 + TST 3 + TSD 2 + 6), re-derived along the base chain by `lines:`'},
]

#: where each list's patterns are inserted in page order: after this node
_LIST_AFTER = {'3.third.imperial.pc': '3.third.imperial'}

#: The page's content that has no board: each a node with the page's own sentence
NON_BOARD = {'3.first.trinity.donate': 'text_only', '3.second.alt.pc12': 'text_only',
             '3.second.alt.transition': 'text_only'}


def _pattern_nodes(lst: dict) -> list[dict]:
    out = []
    for i, text in enumerate(lst['rows'], 1):
        rows = _b(text)
        pieces = ''.join(sorted({ch for r in rows for ch in r if ch in 'ijlostz'} | ({'t'} if 'U' in text else set())))
        out.append({'id': f'{lst["id"]}#{i}', 'bag': lst['bag'], 'parent': lst['parent'],
                    'base': lst['base'], 'list': lst['id'], 'index': i,
                    'listed_under': 'shown' if i <= lst['shown'] else 'rest',
                    'label_jp': f'{lst["heading"]} {i}', 'pieces': pieces, 'rows': rows})
    return out


#: The order boards appear on the page (the wikitext). `--html-dir` compares a snapshot against exactly this.
PAGE_ORDER = (
    ['bag1.lj', 'bag1.jl', 'bag1.after', '2.tsd', '2.after', '3.first', '3.second', '3.third',
     '3.first.cave', '3.first.cave.stsd', '3.first.cave.stsd.next',
     '3.first.trinity', '3.first.trinity.tsd', '3.first.trinity.tss',
     '3.second.cspin', '3.second.cspin.z_early', '3.second.alt#1', '3.second.alt#2',
     '3.second.cspin.dt#1', '3.second.cspin.dt#2', '3.second.cspin.first#1', '3.second.cspin.first#2',
     '3.second.cspin.o_first#1', '3.second.cspin.o_first#2']
    + [f'3.second.cspin.l_first#{i}' for i in range(1, 5)]
    + ['3.third.imperial'] + [f'3.third.imperial.pc#{i}' for i in range(1, 5)]
    + ['3.third.transition#1', '3.third.transition#2']
)


def _u_flat_bottom(rows: list[str]) -> bool:
    """The four U cells are the flat UUU-over-U shape in the body's bottom two rows: where the
    Imperial Cross leaves its second TSD slot."""
    body = bottom(rows, 0)
    return sum(r.count('U') for r in body) == 4 and t_slot(body[-2:]) == 'flat'


#: the list-node flags, computed from the cells and re-checked by the gate
SLOT_FLAGS = {'u_flat_bottom': _u_flat_bottom}

SLOT_FLAG_MEANING = {
    'u_flat_bottom': 'the pattern\'s T (U) is the flat UUU-over-U shape in its bottom two body rows: the Imperial '
                     'Cross\'s second TSD slot, filled as the Perfect Clear\'s last spin',
}


def build() -> dict:
    nodes = copy.deepcopy(NODES)
    for lst in LISTS:
        at = next(i for i, n in enumerate(nodes) if n['id'] == _LIST_AFTER[lst['id']]) + 1
        nodes[at:at] = _pattern_nodes(lst)
    for n in nodes:
        if 'list' in n:
            for k, fn in SLOT_FLAGS.items():
                n[k] = fn(n['rows'])
    lists = []
    for lst in LISTS:
        drawn = sum(1 for n in nodes if n.get('list') == lst['id'])
        lists.append({**{k: v for k, v in lst.items() if k != 'rows'}, 'drawn': drawn})
    return {
        'schema': 'sdpcspin-routes/1',
        'source': SOURCE,
        'cross_source': CROSS_SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'quotes': QUOTES,
        'bag1': BAG1,
        'basic_form': BASIC_FORM,
        'groups': GROUPS,
        'lists': lists,
        'slot_flags': SLOT_FLAG_MEANING,
        'known_discrepancies': KNOWN_DISCREPANCIES,
        'page_order': PAGE_ORDER,
        'nodes': nodes,
    }


# ── SDPC Spin's own rules, and its half of the shared gate ─────────────────────────────────────
_SPIN_LINES = {'TSS': 1, 'TSD': 2, 'TST': 3}
#: a piece named in a condition, as the letters that draw it (the T is U on this page)
_LETTERS = {'T': 'U'}


def _verbatims(obj, path=''):
    """Every `*_verbatim` string (or list of strings) in a dict tree, with where it sits."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith('_verbatim') and isinstance(v, str):
                yield f'{path}.{k}', v
            elif k.endswith('_verbatim') and isinstance(v, list):
                for i, s in enumerate(v):
                    yield f'{path}.{k}[{i}]', s
            else:
                yield from _verbatims(v, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _verbatims(v, f'{path}[{i}]')


def _cells(rows: list[str], letters: str) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(rows) for c, x in enumerate(row) if x in letters}


def _rests_on(rows: list[str], below: str, above: str) -> bool:
    """Some cell of piece `above` sits directly on a cell of piece `below` (gravity, not a planner)."""
    lo = _cells(rows, _LETTERS.get(below, below.lower()))
    return any((r + 1, c) in lo for r, c in _cells(rows, _LETTERS.get(above, above.lower())))


def _no_u(rows: list[str], h: int) -> list[str]:
    return [r.replace('U', EMPTY) for r in bottom(rows, h)]


def _post(boards: dict, by_id: dict, nid: str) -> list[str] | None:
    """What a board leaves after its spin (an after-illustration is already that board)."""
    if nid not in boards:
        return None
    if by_id.get(nid, {}).get('after_of'):
        return boards[nid]
    return after_spin(boards[nid])[0] if 'U' in ''.join(boards[nid]) else boards[nid]


def _sdpcspin_checks(data: dict, ctx: dict) -> tuple[list[str], set[str]]:
    """The rules only this page needs, and the source discrepancies they measure."""
    bad: list[str] = []
    found: set[str] = set()
    boards, by_id, groups = ctx['boards'], ctx['by_id'], ctx['groups']
    nodes = data.get('nodes', [])
    quotes = {q['id']: q for q in data.get('quotes', [])}

    # every sentence the transcription leans on is a quote, so --html-dir finds it on the page
    qtext = [q['verbatim'] for q in quotes.values()]
    for where, v in _verbatims({k: data.get(k) for k in ('bag1', 'groups', 'nodes', 'lists', 'cross_source')}):
        if where.startswith('.cross_source'):
            continue                                                   # SingleYou's own sentence: --html-dir finds it there
        if not any(v in q for q in qtext):
            bad.append(f'verbatim: {where} is not one of the quoted sentences')

    # a spin named on a board is the rows its U completes; a board with a U names its spin
    for n in nodes:
        rows = n.get('rows')
        if not rows or n.get('node_kind') or 'list' in n:
            continue
        has_u = 'U' in ''.join(rows)
        lines = after_spin(rows)[1] if has_u else 0
        if has_u != bool(n.get('spin')) or (has_u and _SPIN_LINES.get(n['spin']) != lines):
            bad.append(f'spin: {n["id"]} names {n.get("spin")!r} but its U slot completes {lines} rows')

    # an unmatchable reason that states a row count states the true one, and nothing is unmatchable
    # without a cause the gate can see (too tall, or a placeholder cell)
    for n in nodes:
        if 'unmatchable' not in n or 'rows' not in n:
            continue
        tall = len(bottom(n['rows'], 0))
        if 'non-empty rows' in n['unmatchable'] and f'{tall} non-empty rows' not in n['unmatchable']:
            bad.append(f'unmatchable: {n["id"]} says {n["unmatchable"]!r} but draws {tall} non-empty rows')
        if tall <= RT.ROWS and not any(ph in ''.join(n['rows']) for ph in 'v'):
            bad.append(f'unmatchable: {n["id"]} is {tall} rows with no placeholder: nothing makes it unmatchable')

    # the after-illustration of bag 1 is the after board of BOTH colourings
    ab = by_id.get('bag1.after', {})
    for k in ('after_of', 'also_after_of'):
        src = boards.get(ab.get(k))
        if src is None or 'rows' not in ab or occ(bottom(after_spin(src)[0], 6)) != occ(bottom(ab['rows'], 6)):
            bad.append(f'bag1: bag1.after is not what {ab.get(k)} leaves after its TSS')
    lj, jl = boards.get('bag1.lj'), boards.get('bag1.jl')
    if not lj or not jl or occ(lj) != occ(jl) or lj == jl or bottom(lj, 6) == mirror(bottom(jl, 6)):
        bad.append('bag1: bag1.lj and bag1.jl are not one occupancy in two colourings (and not mirrors)')
    elif {(r, c) for r, (a, b) in enumerate(zip(lj, jl)) for c, (x, y) in enumerate(zip(a, b)) if x != y} != \
            _cells(lj, 'jl') - {(r, c) for r, (a, b) in enumerate(zip(lj, jl)) for c, (x, y) in enumerate(zip(a, b)) if x == y}:
        bad.append('bag1: bag1.lj and bag1.jl differ outside their J and L cells')

    # each derived 6-lock board is its TSS board less its four U cells (the page draws only the 7-lock
    # boards), and each TSS board names it as the board its spin is fired from
    for d in ('bag1.lj.left', 'bag1.jl.left'):
        dn = by_id.get(d, {})
        src = dn.get('derived_from')
        sn = by_id.get(src, {})
        if not dn.get('derived') or src not in boards or 'rows' not in dn or dn.get('locks') != 6 \
                or sum(r.count('U') for r in boards[src]) != 4 or bottom(dn['rows'], RT.ROWS) != _no_u(boards[src], RT.ROWS):
            bad.append(f'bag1-derived: {d} is not {src} less its four U cells')
        if sn.get('spin_of') != d or sn.get('parent') != d:
            bad.append(f'bag1-derived: {src} does not name {d} as its spin_of and parent')

    # stick spin's transcription (a shiwehi.com page): bag1.jl is its bag1.pc mirrored, cell for cell;
    # bag1.lj its occupancy with the J and L divided the other way; bag1.after its bag1.pc.after mirrored
    ss = {n['id']: n['rows'] for n in json.loads(STICKSPIN.read_text())['nodes'] if 'rows' in n}
    pc, pca = ss.get('bag1.pc'), ss.get('bag1.pc.after')
    if pc is None or jl is None or bottom(jl, 6) != mirror(bottom(pc, 6)):
        bad.append('stickspin: bag1.jl is not stick spin\'s bag1.pc mirrored, cell for cell')
    if pc is None or lj is None or occ(bottom(lj, 6)) != occ(mirror(bottom(pc, 6))):
        bad.append('stickspin: bag1.lj is not stick spin\'s bag1.pc mirrored, by occupancy')
    if pca is None or 'bag1.after' not in boards or occ(bottom(boards['bag1.after'], 6)) != occ(mirror(bottom(pca, 6))):
        bad.append('stickspin: bag1.after is not stick spin\'s bag1.pc.after mirrored, by occupancy')

    # Ivan's compound catalogue entry naming SDPC-Spin: our flat-T bag 1 matches some of its fields, stick
    # spin's stood-T bag1.fire the rest, and between them every field is accounted for
    cat = json.loads(CATALOGUE.read_text())
    key = data.get('bag1', {}).get('catalogue_name_contains', '')
    names = sorted({p['name'] for p in cat['pages'] if key and key in p['name']})
    fields = [tuple(p['rows']) for p in cat['pages'] if names and p['name'] == names[0]]

    def as_fields(rows):
        placed = bottom([r.replace('U', 't') for r in rows], 0)
        return {tuple(r.replace('#', 'X') for r in occ(placed)), tuple(r.replace('#', 'X') for r in occ(mirror(placed)))}
    ours = set().union(*(as_fields(boards[k]) for k in ('bag1.lj', 'bag1.jl') if k in boards)) if boards else set()
    theirs = as_fields(ss['bag1.fire']) if 'bag1.fire' in ss else set()
    if len(names) != 1 or not fields:
        bad.append(f'catalogue: {len(names)} opener-fields.json entries name {key!r}, not one')
    elif not (ours & set(fields)) or ours - set(fields):
        bad.append('catalogue: bag1.lj / bag1.jl (T placed) are not fields of the SDPC-Spin entry, as drawn or mirrored')
    elif set(fields) - ours - theirs:
        bad.append(f'catalogue: {len(set(fields) - ours - theirs)} field(s) of the entry match neither this bag 1 '
                   'nor stick spin\'s bag1.fire')

    # node conditions: every order has its evidence, and the evidence holds on the board
    for n in nodes:
        cond, ev = n.get('condition'), n.get('condition_evidence')
        if not cond:
            continue
        if 'at_least' in cond:
            al = cond['at_least']
            pairs = [[al.get('before'), p] for p in al.get('of', [])]
            pieces = [al.get('before')] + list(al.get('of', []))
            if any(p not in RT.PIECES for p in pieces) or not 0 < al.get('count', 0) <= len(al.get('of', [])):
                bad.append(f'condition: {n["id"]} at_least names something that is not a piece, or a bad count')
                continue
        else:
            pairs = [c.get('before') for c in cond.get('all', [])]
            if any(p not in RT.PIECES for pr in pairs for p in (pr or ['?'])):
                bad.append(f'condition: {n["id"]} names something that is not a piece')
                continue
        if [e.get('before') for e in ev or []] != pairs:
            bad.append(f'order: {n["id"]} condition_evidence does not cover its condition, pair for pair')
            continue
        for e in ev:
            a, b = e['before']
            ok = _rests_on(n['rows'], a, b) if e['by'] == 'support' else (e['by'] is None and bool(e.get('note')))
            if not ok:
                bad.append(f'order: {n["id"]} %{a}>%{b} ({e["by"]}) does not hold on its board')
            if e['by'] is None and _rests_on(n['rows'], a, b):
                bad.append(f'order: {n["id"]} %{a}>%{b} is marked not forced, but the board forces it')

    # a group whose members carry a t_slot is ONE build: equal colour for colour without the U cells,
    # the U in a different place on each
    for g in groups.values():
        members = [n for n in nodes if n.get('group') == g['id'] and 't_slot' in n]
        by_build: dict = {}
        for n in members:
            by_build.setdefault(n.get('build', 1), []).append(n)
        for b, ms in by_build.items():
            h = max(len(m['rows']) for m in ms)
            if len({tuple(_no_u(m['rows'], h)) for m in ms}) != 1 or \
                    len({frozenset(_cells(bottom(m['rows'], h), 'U')) for m in ms}) != len(ms) or len(ms) != 2:
                bad.append(f'pair: {g["id"]} build {b} is not one build with its T in two slots')

    # a held piece is absent from the board: the alternate fourth bag places every piece but the I
    for n in nodes:
        if n.get('hold') == 'I':
            if 'rows' not in n or _cells(n['rows'], 'i') or len({ch for r in n['rows'] for ch in r if ch in 'josltz'} | {'t'}) != 6:
                bad.append(f'hold: {n["id"]} holds the I but does not place exactly the other six pieces')
    if 'If I is saved' not in quotes.get('alt.pc12', {}).get('verbatim', ''):
        bad.append('hold: the I-hold reading has no quote')

    # the DT Cannon boards: c, the muted cells and one live I are exactly the C-Spin's residue
    for n in nodes:
        src = n.get('residue_of')
        if not src:
            continue
        post = _post(boards, by_id, src)
        if post is None or 'rows' not in n or 'base' in n:
            bad.append(f'residue: {n["id"]} names no board ({src}) or also carries a base')
            continue
        h = max(len(post), len(n['rows']))
        pb, nb = bottom(post, h), bottom(n['rows'], h)
        filled = RT.cells(pb, lambda ch: ch != EMPTY)
        muted = _cells(nb, 'c' + ''.join(sorted(set('JLOSZ'))))
        live = filled - muted
        letter = n.get('live_residue', '')
        if not muted <= filled or any(nb[r][c] != pb[r][c].upper() for r, c in _cells(nb, 'JLOSZ')) or \
                any(pb[r][c] != 'c' for r, c in _cells(nb, 'c')) or \
                {nb[r][c] for r, c in live} != {letter} or {pb[r][c] for r, c in live} != {letter} or len(live) != 4:
            bad.append(f'residue: {n["id"]} c + muted + one live {letter} are not exactly {src} after its spin')

    # the apostrophes: exactly the cells the Z vacates, the Z drawn on the J instead
    for n in nodes:
        src = n.get('vacated_of')
        if not src:
            continue
        h = max(len(n['rows']), len(boards.get(src, [])))
        nb, sb = bottom(n['rows'], h), bottom(boards.get(src, []), h)
        jz = _cells(nb, 'z')
        if src not in boards or _cells(nb, 'v') != _cells(sb, 'z') or \
                [r.replace('z', EMPTY).replace('v', EMPTY) for r in nb] != [r.replace('z', EMPTY) for r in sb] or \
                len(jz) != 4 or not _rests_on(nb, 'J', 'Z'):
            bad.append(f'vacated: {n["id"]}\'s v cells are not {src}\'s z cells, or its Z is not on the J')

    # the transition setups: after their TSD, the board is the second C-Spin build's after its TSD
    for n in nodes:
        dst = n.get('transition_to')
        if not dst:
            continue
        a, b = after_spin(n['rows'])[0], _post(boards, by_id, dst)
        h = max(len(a), len(b or []))
        if b is None or occ(bottom(a, h)) != occ(bottom(b, h)):
            bad.append(f'transition: {n["id"]} after its spin is not {dst} after its spin, by occupancy')
    if 'transition to the second C-Spin build' not in quotes.get('third.transition', {}).get('verbatim', ''):
        bad.append('transition: the transition reading has no quote')

    # a list's stated total line count is re-derived along its base chain: the body, plus every spin
    # from the PC's base back to bag 1
    for lst in data.get('lists', []):
        pats = [n for n in nodes if n.get('list') == lst['id']]
        if lst.get('total_lines') is None or not pats:
            continue
        total, cur, seen = len(bottom(pats[0]['rows'], 0)), lst.get('base'), set()
        while cur in by_id and cur not in seen:
            seen.add(cur)
            b = by_id[cur]
            if b.get('after_of') in boards:
                total += after_spin(boards[b['after_of']])[1]
                cur = by_id[b['after_of']].get('base')
            else:
                total += after_spin(boards[cur])[1] if 'U' in ''.join(boards.get(cur, [])) else 0
                cur = b.get('base')
        if total != lst['total_lines']:
            bad.append(f'lines: {lst["id"]} clears {total} lines over its line, the page says {lst["total_lines"]}')
        qv = quotes.get(lst.get('total_lines_quote'), {}).get('verbatim', '')
        if f'{lst["total_lines"]}-line' not in qv:
            bad.append(f'lines: quote {lst.get("total_lines_quote")!r} does not state {lst["total_lines"]} lines '
                       f'for {lst["id"]}')

    # the source is harddrop, and bag 2 onward has no second source: said, not implied
    xs = data.get('cross_source') or {}
    if not str(xs.get('bag2_onward', '')).startswith('single source'):
        bad.append('single-source: cross_source does not say that bag 2 onward is single source')
    return bad, found


SPEC = RT.TranscriptionSpec(
    out=OUT, build=build, alphabet=ALPHABET, non_board=NON_BOARD,
    harddrop=None,
    harddrop_wikitext={'nodes': ['bag1.lj', 'bag1.jl', 'bag1.after']},
    board_kinds=frozenset({'illustration'}),
    pc_lines=8, prior_letters='',
    upper_groups={x: 'separate' for x in 'JLOSZ'},
    placeholders='v',
    slot_flags=SLOT_FLAGS, occupancy_class_parents=1, extra_checks=_sdpcspin_checks)


def verify(data: dict) -> list[str]:
    return RT.verify(data, SPEC)


def drift(data: dict) -> list[str]:
    return RT.drift(data, SPEC)


# ── selftest ───────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    """A gate nothing can fail is decorative. Plant one defect per rule, each in a named SDPC Spin id."""

    def drop_pattern(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != '3.third.imperial.pc#4']

    def shift_bag1(d):
        n = node(d, 'bag1.jl')
        n['rows'] = ['-' + r[:-1] for r in n['rows']]

    def field_off(d):
        f = d['cross_source']['fields'][0]
        f[0] = '-------s--'                                            # SingleYou's S moved one column

    def no_provenance(d):
        d['cross_source']['oldid'] = None

    def jl_swap(d):
        n = node(d, 'bag1.jl')                                         # one J cell drawn L: not stick spin's
        setcell(n['rows'], 3, 1, 'l')
        setcell(n['rows'], 5, 1, 'j')

    def ghost_group(d):
        node(d, '3.second.alt#2')['group'] = '3.second.nowhere'

    def bad_cell(d):
        setcell(node(d, '3.first.cave.stsd')['rows'], 0, 0, 'p')

    def flag_flip(d):
        n = node(d, '3.third.imperial.pc#2')
        n['u_flat_bottom'] = not n['u_flat_bottom']

    def drop_discrepancy(d):
        d['known_discrepancies'] = [x for x in d['known_discrepancies'] if x['id'] != '3.second.cspin.dt#2:colour']

    def recolour(d):
        setcell(node(d, '3.first')['rows'], 3, 0, 'o')                 # an i cell drawn as o

    def tall(d):
        node(d, '3.first.cave')['rows'].insert(0, 'i---------')

    def no_reason(d):
        node(d, '3.second.cspin.first#2')['unmatchable'] = ''

    def wrong_reason(d):
        node(d, '3.second.cspin.first#1')['unmatchable'] = '10 non-empty rows > ROWS = 8'

    def c_cells(d):
        setcell(node(d, '3.second.cspin')['rows'], 3, 9, 'c')          # a c where 3.second leaves none

    def wrong_base(d):
        node(d, '3.first.trinity')['base'] = '3.first.cave.stsd'

    def wrong_after(d):
        node(d, '2.after')['after_of'] = '3.first'

    def wrong_bag2(d):
        setcell(node(d, '2.tsd')['rows'], 9 - 2, 0, 'j')                # a bag-1 cell drawn live

    def pc_short(d):
        n = node(d, '3.third.imperial.pc#3')
        n['rows'] = n['rows'][:1] + n['rows'][2:]                       # a 13-line PC drawn

    def wrong_spin(d):
        node(d, '3.first.trinity.tss')['spin'] = 'TSD'

    def total_lines(d):
        d['lists'][0]['total_lines'] = 12

    def unquoted(d):
        node(d, '3.third')['condition_verbatim'] = 'If S comes after O, the third build can also be stacked.'

    def cond_piece(d):
        node(d, '3.first.cave')['condition']['at_least']['of'] = ['T', 'L', 'X']

    def order(d):
        n = node(d, '3.second.cspin.o_first#1')
        n['condition']['all'][0]['before'] = ['L', 'O']
        n['condition_evidence'][0]['before'] = ['L', 'O']

    def order_unforced(d):
        node(d, '3.first.cave')['condition_evidence'][0] = {'before': ['J', 'T'], 'by': None, 'note': 'x'}

    def order_uncovered(d):
        node(d, '3.third')['condition_evidence'].pop()

    def pair_moved(d):
        setcell(node(d, '3.second.cspin.l_first#4')['rows'], 1, 5, '-')
        setcell(node(d, '3.second.cspin.l_first#4')['rows'], 1, 4, 'z')

    def hold_i(d):
        setcell(node(d, '3.second.alt#1')['rows'], 1, 4, 'i')

    def residue(d):
        setcell(node(d, '3.second.cspin.dt#1')['rows'], 6, 9, 'o')     # one muted O drawn live

    def vacated(d):
        n = node(d, '3.second.cspin.z_early')
        setcell(n['rows'], 7, 4, '-')

    def transition(d):
        setcell(node(d, '3.third.transition#2')['rows'], 1, 9, '-')

    def single_source(d):
        d['cross_source']['bag2_onward'] = 'cross-checked against SingleYou'

    def stickspin_after(d):
        setcell(node(d, 'bag1.after')['rows'], 2, 8, '-')
        setcell(node(d, 'bag1.after')['rows'], 2, 7, 'c')

    def derived_off(d):
        setcell(node(d, 'bag1.lj.left')['rows'], 4, 1, '-')            # one cell of the derived board dropped

    def derived_link(d):
        node(d, 'bag1.lj')['spin_of'] = 'bag1.jl.left'                 # the other colouring's stage board

    def catalogue(d):
        d['bag1']['catalogue_name_contains'] = 'SDPC Spin'               # the entry spells it SDPC-Spin

    def mirror_jl(d):
        node(d, 'bag1.lj')['rows'] = mirror(node(d, 'bag1.jl')['rows'])

    mutants = [
        (drop_pattern, 'a dropped PC pattern', 'list-count:'),
        (shift_bag1, 'bag1.jl shifted one column', 'harddrop-wikitext:'),
        (field_off, 'one SingleYou field moved off', 'harddrop-wikitext:'),
        (no_provenance, 'the SingleYou wikitext without its oldid', 'harddrop-wikitext:'),
        (jl_swap, 'bag1.jl recoloured off stick spin', 'stickspin:'),
        (stickspin_after, 'bag1.after moved off stick spin\'s after board', 'stickspin:'),
        (derived_off, 'a derived bag-1 board that is not its TSS board less its U cells', 'bag1-derived:'),
        (derived_link, 'a TSS board fired from the other colouring\'s stage board', 'bag1-derived:'),
        (catalogue, 'the catalogue entry name misspelt', 'catalogue:'),
        (mirror_jl, 'the two colourings made mirrors', 'bag1:'),
        (ghost_group, 'a group no node declares', 'grammar:'),
        (bad_cell, 'a cell outside the alphabet', 'grammar:'),
        (flag_flip, 'a u_flat_bottom flag flipped', 'grammar:'),
        (drop_discrepancy, 'a dropped known discrepancy', 'discrepancy:'),
        (recolour, 'one cell of a bag-3 build recoloured', 'discrepancy:'),
        (tall, 'a 9-row board not marked unmatchable', 'grammar:'),
        (no_reason, 'an unmatchable node with no reason', 'grammar:'),
        (wrong_reason, 'an unmatchable reason with the wrong row count', 'unmatchable:'),
        (c_cells, 'a c cell where the TST leaves none', 'c-cells:'),
        (wrong_base, 'the Trinity on the STSD instead of the Cave', 'c-cells:'),
        (wrong_after, 'bag-2 after read off the wrong spin', 'after-of:'),
        (wrong_bag2, 'a bag-1 cell drawn live in bag 2', 'bag2-base:'),
        (pc_short, 'a PC that is not 8 lines over its base', 'pc:'),
        (wrong_spin, 'a TSS board named a TSD', 'spin:'),
        (total_lines, 'the 14-line total misstated', 'lines:'),
        (unquoted, 'a verbatim field that is not on the page', 'verbatim:'),
        (cond_piece, 'a condition naming a non-piece', 'condition:'),
        (order, 'an order the board does not force', 'order:'),
        (order_unforced, 'a forced order marked unforced', 'order:'),
        (order_uncovered, 'a condition order with no evidence', 'order:'),
        (pair_moved, 'one of a pair no longer the same build', 'pair:'),
        (hold_i, 'the held I placed on the board', 'hold:'),
        (residue, 'a muted residue cell drawn live', 'residue:'),
        (vacated, 'an apostrophe cell dropped', 'vacated:'),
        (transition, 'a transition setup that no longer lands on the C-Spin residue', 'transition:'),
        (single_source, 'bag 2 onward claimed cross-checked', 'single-source:'),
    ]
    spec_mutants = [
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'harddrop_wikitext': {'nodes': ['bag1.lj', 'bag1.jl']}}),
         'the after board dropped (one SingleYou field left unmatched)', 'harddrop-wikitext:'),
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'harddrop_wikitext': {'nodes': ['bag1.lj', 'bag1.jl', '2.tsd']}}),
         'a bag-2 board named against the first-bag table', 'harddrop-wikitext:'),
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'harddrop_wikitext': None}),
         'no cross-source at all', 'harddrop:'),
    ]
    return RT.run_selftest(SPEC, mutants, {'board': ('{{pfrow| | | | | | | | |S| }}', '{{pfrow| | | | | | | |S| | }}'),
                                           'text': ('68.10%', '68.11%'),
                                           'hand_edit': '3.third.imperial', 'quote': 'cave.j'},
                           spec_mutants)


def main() -> int:
    return RT.main(SPEC, selftest, __doc__)


if __name__ == '__main__':
    raise SystemExit(main())
