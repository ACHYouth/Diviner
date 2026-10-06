import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog import Catalog
from app.semantic import EMBEDDINGS_DATA, build_embedding_payload


def main():
    novels = Catalog().load()
    payload = build_embedding_payload(novels)

    EMBEDDINGS_DATA.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(f"built embeddings for {payload['count']} novels at {EMBEDDINGS_DATA}")


if __name__ == "__main__":
    main()
