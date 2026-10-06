from app.catalog import Catalog, SAMPLE_DATA
from app.recommender import recommend


def test_recommends_completed_academy_progression_fantasy():
    novels = Catalog(SAMPLE_DATA).load()
    rows = recommend(
        "completed academy progression fantasy smart protagonist",
        novels,
        "similarity",
        3,
    )

    assert rows[0].novel.title == "Mother of Learning"
    assert rows[0].similarity_score > 0


def test_rating_sort_prioritizes_rating():
    novels = Catalog(SAMPLE_DATA).load()
    rows = recommend("fantasy magic", novels, "rating", 2)

    assert rows[0].novel.rating >= rows[1].novel.rating

