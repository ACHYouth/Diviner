import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog import Catalog
from app.scrapers.registry import SOURCES


def ingest(source_name: str, limit: int) -> None:
    if source_name == "all":
        names = sorted(SOURCES)
    else:
        names = [source_name]

    catalog = Catalog()
    for name in names:
        source_class = SOURCES.get(name)
        if source_class is None:
            raise SystemExit(f"Unknown source: {name}")

        source = source_class()
        try:
            novels = source.fetch(limit)
            catalog.upsert_many(novels)
            catalog.log_ingestion_run(source.name, "success", len(novels))
            print(f"{source.name}: saved {len(novels)} novels")
        except Exception as exc:
            catalog.log_ingestion_run(source.name, "failed", 0, str(exc))
            print(f"{source.name}: failed: {exc}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", choices=sorted(list(SOURCES) + ["all"]))
    parser.add_argument("--limit", type=int, default=100, help="novels to request from each source, default: 100")
    args = parser.parse_args()
    ingest(args.source, args.limit)


if __name__ == "__main__":
    main()
