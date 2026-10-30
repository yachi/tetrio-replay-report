"""The opener route sites and mid-game technique sites, in the order their cards appear on the index.

ONE list of each, read by `bin/build-docs` (which renders their pages and cards) and by
`replay_labels` (which labels the replay pages' key moments from their artefacts), so a site added to
the index cannot be missing from the replay labels, or the reverse. The one exception is named:
`PAGE_ONLY_ROUTE_SITES`, a route page with a card and no label or report column, for a reason given
beside it; `INDEX_ROUTE_SITES` is the order of the cards and is checked to hold both lists."""
from pipeline import gamushiro_page, hdgamushiro_page, honey_cup_page, mountainous2_page, sdpcspin_page, stickspin_page
from pipeline import stray_cannon_page
from pipeline import btcannon_page, doubledagger_page, imperialcross_page, stmbcave_page, stsd_page
from pipeline import cutcopy_page, shachikutrain_page, parapet_page, kaidan_page, dtcannon_page
from pipeline import basicdonating_page, kingcrimson_page

#: every opener route site, in the order its card appears under 定式路線
ROUTE_SITES = [stray_cannon_page.SITE, honey_cup_page.SITE, mountainous2_page.SITE, stickspin_page.SITE,
               gamushiro_page.SITE, sdpcspin_page.SITE]
#: route sites that get a page and an index card but no report column and no replay label: harddrop's
#: ガムシロ積み draws the same opener as shiwehi.com's (its bag 1 and its first bag-2 form are the same
#: boards, which hdgamushiro.test.ts checks), so a report column would repeat gamushiro's
PAGE_ONLY_ROUTE_SITES = [hdgamushiro_page.SITE]
#: every route site in the order its card appears on the index: each of the two lists above, once
INDEX_ROUTE_SITES = [stray_cannon_page.SITE, honey_cup_page.SITE, mountainous2_page.SITE, stickspin_page.SITE,
                     gamushiro_page.SITE, hdgamushiro_page.SITE, sdpcspin_page.SITE]
if sorted(map(id, INDEX_ROUTE_SITES)) != sorted(map(id, ROUTE_SITES + PAGE_ONLY_ROUTE_SITES)):
    raise SystemExit("pipeline.sites: INDEX_ROUTE_SITES must hold ROUTE_SITES and PAGE_ONLY_ROUTE_SITES, each once")
#: every mid-game technique site, in the order its card appears under 中盤手法
TECHNIQUE_SITES = [stsd_page.SITE, stmbcave_page.SITE, imperialcross_page.SITE, doubledagger_page.SITE,
                   btcannon_page.SITE, cutcopy_page.SITE, shachikutrain_page.SITE, parapet_page.SITE,
                   kaidan_page.SITE, dtcannon_page.SITE, basicdonating_page.SITE,
                   kingcrimson_page.SITE]
