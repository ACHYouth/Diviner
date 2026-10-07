from app.models import Novel
from app.scrapers.base import NovelSource


class WuxiaworldSource(NovelSource):
    name = "Wuxiaworld"

    def fetch(self, limit: int = 100) -> list[Novel]:
        return []
