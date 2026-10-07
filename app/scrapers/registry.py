from app.scrapers.ao3 import AO3Source
from app.scrapers.fanfiction import FanFictionSource
from app.scrapers.royalroad import RoyalRoadSource
from app.scrapers.scribblehub import ScribbleHubSource
from app.scrapers.webnovel import WebnovelSource
from app.scrapers.wuxiaworld import WuxiaworldSource


SOURCES = {
    "ao3": AO3Source,
    "fanfiction": FanFictionSource,
    "royalroad": RoyalRoadSource,
    "scribblehub": ScribbleHubSource,
    "webnovel": WebnovelSource,
    "wuxiaworld": WuxiaworldSource,
}
