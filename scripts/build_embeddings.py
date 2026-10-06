import json

from app.catalog import Catalog
from app.semantic import EMBEDDINGS_DATA, MODEL_NAME, build_vectors


def main():
    novels = Catalog().load()
    vectors = build_vectors(novels)
    if not vectors:
        raise SystemExit("Could not build embeddings. Install sentence-transformers first.")

    EMBEDDINGS_DATA.write_text(
        json.dumps(
            {
                "model": MODEL_NAME,
                "count": len(vectors),
                "vectors": vectors,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"built embeddings for {len(vectors)} novels at {EMBEDDINGS_DATA}")


if __name__ == "__main__":
    main()
