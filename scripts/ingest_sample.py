import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog import Catalog, SAMPLE_DATA
from app.models import Novel


def main():
    rows = json.loads(SAMPLE_DATA.read_text(encoding="utf-8"))
    novels = [Novel(**row) for row in rows]
    Catalog().upsert_many(novels)
    print(f"loaded {len(novels)} sample novels")


if __name__ == "__main__":
    main()
