import re

import requests
from bs4 import BeautifulSoup

from app.models import Novel
from app.scrapers.base import NovelSource, compact_text, number_from_text, slugify


class RoyalRoadSource(NovelSource):
    name = "RoyalRoad"
    base_url = "https://www.royalroad.com"

    def fetch(self, limit: int = 100) -> list[Novel]:
        novels = []
        seen = set()
        page = 1

        while len(novels) < limit:
            response = requests.get(
                f"{self.base_url}/fictions/best-rated",
                params={"page": page},
                headers={"User-Agent": "Diviner metadata research bot"},
                timeout=30,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select(".fiction-list-item")
            if not items:
                break

            before = len(novels)
            for item in items:
                if len(novels) >= limit:
                    break

                link = item.select_one("h2 a")
                if not link:
                    continue

                title = link.get_text(" ", strip=True)
                url = self.base_url + link.get("href", "")
                if url in seen:
                    continue
                seen.add(url)

                fiction_id = slugify(title)
                author = item.select_one(".author")
                synopsis = item.select_one(".fiction-description")
                tags = [tag.get_text(" ", strip=True) for tag in item.select(".tags a")]
                rating_text = item.get_text(" ", strip=True)
                rating_match = re.search(r"(\d\.\d{1,2})", rating_text)
                chapters = 0
                for span in item.select("span"):
                    text = span.get_text(" ", strip=True)
                    if "Chapter" in text:
                        chapters = number_from_text(text)

                novels.append(
                    Novel(
                        id=f"royalroad-{fiction_id}",
                        title=title,
                        author=author.get_text(" ", strip=True) if author else "Unknown",
                        source=self.name,
                        url=url,
                        genres=[],
                        tags=tags,
                        rating=float(rating_match.group(1)) if rating_match else 0.0,
                        chapters=chapters,
                        status="unknown",
                        synopsis=compact_text(synopsis.get_text(" ", strip=True)) if synopsis else "",
                    )
                )

            if len(novels) == before:
                break
            page += 1

        return novels
