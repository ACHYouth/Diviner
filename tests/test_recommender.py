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

    assert "Mother of Learning" in [row.novel.title for row in rows]
    assert rows[0].similarity_score > 0


def test_rating_sort_prioritizes_rating():
    novels = Catalog(SAMPLE_DATA).load()
    rows = recommend("fantasy magic", novels, "rating", 2)

    assert rows[0].novel.rating >= rows[1].novel.rating


def test_plural_query_matches_singular_catalog_terms():
    novels = Catalog(SAMPLE_DATA).load()
    rows = recommend("rituals", novels, "similarity", 5)
    titles = [row.novel.title for row in rows]

    assert "Lord of the Mysteries" in titles
    assert rows[0].similarity_score > 0.2


def test_larger_catalog_is_available_for_testing():
    novels = Catalog(SAMPLE_DATA).load()

    assert len(novels) >= 30


def test_trope_query_can_find_cultivation_villain_story():
    novels = Catalog(SAMPLE_DATA).load()
    rows = recommend("cultivation villain scheming", novels, "similarity", 3)

    assert rows[0].novel.title == "Reverend Insanity"


def test_mood_query_can_find_horror_without_exact_genre_word():
    novels = Catalog(SAMPLE_DATA).load()
    rows = recommend("i wanna get spooked", novels, "similarity", 5)
    titles = [row.novel.title for row in rows]

    assert "My House of Horrors" in titles or "Pact" in titles
