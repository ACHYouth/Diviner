from app.catalog import Catalog, SAMPLE_DATA


def main():
    catalog = Catalog(SAMPLE_DATA)
    novels = catalog.load()
    Catalog().upsert_many(novels)
    print(f"loaded {len(novels)} sample novels")


if __name__ == "__main__":
    main()

