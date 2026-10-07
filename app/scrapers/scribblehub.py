import requests
from bs4 import BeautifulSoup

from app.models import Novel
from app.scrapers.base import NovelSource, compact_text, slugify


class ScribbleHubSource(NovelSource):
    name = "ScribbleHub"
    base_url = "https://www.scribblehub.com"

    def fetch(self, limit: int = 100) -> list[Novel]:
        response = requests.get(
            f"{self.base_url}/series-ranking/",
            headers={"User-Agent": "Diviner metadata research bot"},
            timeout=20,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        novels = []

        for item in soup.select(".search_main_box")[:limit]:
            link = item.select_one(".search_title a")
            if not link:
                continue

            title = compact_text(link.get_text(" ", strip=True))
            author = item.select_one(".search_author a")
            synopsis = item.select_one(".search_body")
            tags = [compact_text(tag.get_text(" ", strip=True)) for tag in item.select(".search_genre a")]

            novels.append(
                Novel(
                    id=f"scribblehub-{slugify(title)}",
                    title=title,
                    author=compact_text(author.get_text(" ", strip=True)) if author else "Unknown",
                    source=self.name,
                    url=link.get("href", ""),
                    genres=[],
                    tags=tags,
                    rating=0.0,
                    status="unknown",
                    synopsis=compact_text(synopsis.get_text(" ", strip=True)) if synopsis else "",
                )
            )

        return novels
