"""The opener route sites and mid-game technique sites, in the order their cards appear on the index.

ONE list of each, read by `bin/build-docs` (which renders their pages and cards) and by
`replay_labels` (which labels the replay pages' key moments from their artefacts), so a site added to
the index cannot be missing from the replay labels, or the reverse."""
from pipeline import gamushiro_page, honey_cup_page, mountainous2_page, sdpcspin_page, stickspin_page
from pipeline import stray_cannon_page
from pipeline import btcannon_page, doubledagger_page, imperialcross_page, stmbcave_page, stsd_page
from pipeline import cutcopy_page, shachikutrain_page, parapet_page, kaidan_page

#: every opener route site, in the order its card appears under 定式路線
ROUTE_SITES = [stray_cannon_page.SITE, honey_cup_page.SITE, mountainous2_page.SITE, stickspin_page.SITE,
               gamushiro_page.SITE, sdpcspin_page.SITE]
#: every mid-game technique site, in the order its card appears under 中盤手法
TECHNIQUE_SITES = [stsd_page.SITE, stmbcave_page.SITE, imperialcross_page.SITE, doubledagger_page.SITE,
                   btcannon_page.SITE, cutcopy_page.SITE, shachikutrain_page.SITE, parapet_page.SITE,
                   kaidan_page.SITE]
