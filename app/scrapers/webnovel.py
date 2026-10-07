from app.models import Novel
from app.scrapers.base import NovelSource


class WebnovelSource(NovelSource):
    name = "Webnovel"

    def fetch(self, limit: int = 100) -> list[Novel]:
        return []
