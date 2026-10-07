import requests
from bs4 import BeautifulSoup

from app.models import Novel
from app.scrapers.base import NovelSource, compact_text, number_from_text, slugify


class AO3Source(NovelSource):
    name = "AO3"
    base_url = "https://archiveofourown.org"

    def fetch(self, limit: int = 100) -> list[Novel]:
        response = requests.get(
            f"{self.base_url}/works/search",
            params={
                "work_search[query]": "",
                "work_search[sort_column]": "kudos_count",
                "work_search[sort_direction]": "desc",
            },
            headers={"User-Agent": "Diviner metadata research bot"},
            timeout=20,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        novels = []

        for item in soup.select("li.work")[:limit]:
            heading = item.select_one("h4.heading a")
            if not heading:
                continue

            title = compact_text(heading.get_text(" ", strip=True))
            author = item.select_one("a[rel='author']")
            url = self.base_url + heading.get("href", "")
            fandoms = [compact_text(link.get_text(" ", strip=True)) for link in item.select("h5.fandoms a")]
            tags = [compact_text(tag.get_text(" ", strip=True)) for tag in item.select("li.freeforms a, li.relationships a, li.characters a")]
            summary = item.select_one("blockquote.userstuff")
            stats = item.select_one("dl.stats")
            stats_text = stats.get_text(" ", strip=True) if stats else ""

            novels.append(
                Novel(
                    id=f"ao3-{slugify(title)}-{slugify(author.get_text(' ', strip=True) if author else 'unknown')}",
                    title=title,
                    author=compact_text(author.get_text(" ", strip=True)) if author else "Unknown",
                    source=self.name,
                    url=url,
                    genres=fandoms[:5],
                    tags=tags[:20],
                    rating=0.0,
                    kudos=number_from_text(stats_text.split("Kudos")[-1]) if "Kudos" in stats_text else 0,
                    bookmarks=number_from_text(stats_text.split("Bookmarks")[-1]) if "Bookmarks" in stats_text else 0,
                    comments=number_from_text(stats_text.split("Comments")[-1]) if "Comments" in stats_text else 0,
                    chapters=number_from_text(stats_text.split("Chapters")[-1]) if "Chapters" in stats_text else 0,
                    status="unknown",
                    synopsis=compact_text(summary.get_text(" ", strip=True)) if summary else "",
                )
            )

        return novels
