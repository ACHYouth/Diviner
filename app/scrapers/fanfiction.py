import requests
from bs4 import BeautifulSoup

from app.models import Novel
from app.scrapers.base import NovelSource, compact_text, number_from_text, slugify


class FanFictionSource(NovelSource):
    name = "FanFiction.net"
    base_url = "https://www.fanfiction.net"

    def fetch(self, limit: int = 25) -> list[Novel]:
        response = requests.get(
            f"{self.base_url}/book/Harry-Potter/",
            params={"srt": "4", "r": "10"},
            headers={"User-Agent": "Diviner metadata research bot"},
            timeout=20,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        novels = []

        for item in soup.select(".z-list")[:limit]:
            link = item.select_one("a.stitle")
            if not link:
                continue

            title = compact_text(link.get_text(" ", strip=True))
            url = self.base_url + link.get("href", "")
            author = item.select_one("a[href*='/u/']")
            text = compact_text(item.get_text(" ", strip=True))
            synopsis_node = item.select_one(".z-indent")

            novels.append(
                Novel(
                    id=f"ffn-{slugify(title)}-{slugify(author.get_text(' ', strip=True) if author else 'unknown')}",
                    title=title,
                    author=compact_text(author.get_text(" ", strip=True)) if author else "Unknown",
                    source=self.name,
                    url=url,
                    genres=["Fanfiction"],
                    tags=[],
                    rating=0.0,
                    favorites=number_from_text(text.split("Favs:")[-1]) if "Favs:" in text else 0,
                    follows=number_from_text(text.split("Follows:")[-1]) if "Follows:" in text else 0,
                    reviews=number_from_text(text.split("Reviews:")[-1]) if "Reviews:" in text else 0,
                    chapters=number_from_text(text.split("Chapters:")[-1]) if "Chapters:" in text else 0,
                    status="completed" if "Complete" in text else "unknown",
                    synopsis=compact_text(synopsis_node.get_text(" ", strip=True)) if synopsis_node else "",
                )
            )

        return novels
