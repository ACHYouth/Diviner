import json
from pathlib import Path
from typing import Optional

from app.models import Novel


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA = ROOT / "data" / "sample_novels.json"
CATALOG_DATA = ROOT / "data" / "catalog.json"


class Catalog:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or CATALOG_DATA

    def load(self) -> list[Novel]:
        source = self.path if self.path.exists() else SAMPLE_DATA
        if not source.exists():
            return []

        rows = json.loads(source.read_text(encoding="utf-8"))
        return [Novel(**row) for row in rows]

    def save(self, novels: list[Novel]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rows = [novel.model_dump() for novel in novels]
        self.path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def upsert_many(self, incoming: list[Novel]) -> list[Novel]:
        novels = {novel.id: novel for novel in self.load()}
        for novel in incoming:
            novels[novel.id] = novel

        merged = sorted(novels.values(), key=lambda item: item.title.lower())
        self.save(merged)
        return merged
