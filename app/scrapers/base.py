from abc import ABC, abstractmethod
import re

from app.models import Novel


class NovelSource(ABC):
    name: str

    @abstractmethod
    def fetch(self, limit: int = 25) -> list[Novel]:
        raise NotImplementedError


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def number_from_text(value: str) -> int:
    cleaned = value.replace(",", "").strip()
    match = re.search(r"(\d+)", cleaned)
    return int(match.group(1)) if match else 0


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
