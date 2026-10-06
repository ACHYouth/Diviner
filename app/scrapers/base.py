from abc import ABC, abstractmethod

from app.models import Novel


class NovelSource(ABC):
    name: str

    @abstractmethod
    def fetch(self, limit: int = 25) -> list[Novel]:
        raise NotImplementedError

