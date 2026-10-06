from app.models import Novel
from app.scrapers.base import NovelSource


class WebnovelSource(NovelSource):
    name = "Webnovel"

    def fetch(self, limit: int = 25) -> list[Novel]:
        return []

