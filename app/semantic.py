import json
import math
import re
from functools import lru_cache
from pathlib import Path

from app.models import Novel


ROOT = Path(__file__).resolve().parents[1]
EMBEDDINGS_DATA = ROOT / "data" / "embeddings.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

MOOD_EXPANSIONS = {
    "spooked": "horror scary creepy ghosts haunted supernatural unsettling thriller occult demons nightmares",
    "scared": "horror scary creepy ghosts haunted supernatural unsettling thriller occult demons nightmares",
    "creepy": "horror scary creepy ghosts haunted supernatural unsettling thriller occult demons nightmares",
    "afraid": "horror scary creepy ghosts haunted supernatural unsettling thriller occult demons nightmares",
    "cozy": "cozy peaceful healing slice of life warm wholesome farming innkeeper slow life",
    "funny": "comedy humor satire witty absurd lighthearted parody",
    "hype": "action battle fast paced tournament war intense epic",
    "sad": "tragic emotional trauma grief bittersweet drama",
    "smart": "clever intelligent strategic tactical scheming planning mystery",
    "dark": "dark grim bleak horror ruthless morally gray tragic",
    "chill": "cozy peaceful healing slice of life relaxing slow life",
}


def novel_embedding_text(novel: Novel) -> str:
    pieces = [
        novel.title,
        novel.author,
        novel.source,
        novel.status,
        " ".join(novel.genres),
        " ".join(novel.tags),
        novel.synopsis,
    ]
    return ". ".join(piece for piece in pieces if piece)


def expand_query_mood(query: str) -> str:
    words = {word.strip(".,!?;:()[]{}\"'").lower() for word in query.split()}
    expansions = [text for key, text in MOOD_EXPANSIONS.items() if key in words]
    if not expansions:
        return query
    return query + " " + " ".join(expansions)


@lru_cache(maxsize=1)
def load_model():
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None
    return SentenceTransformer(MODEL_NAME)


def cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def normalize_score(value: float) -> float:
    return max(0.0, min((value + 1.0) / 2.0, 1.0))


def load_cached_embeddings(novels: list[Novel]) -> dict[str, list[float]]:
    if not EMBEDDINGS_DATA.exists():
        return {}

    data = json.loads(EMBEDDINGS_DATA.read_text(encoding="utf-8"))
    if data.get("model") != MODEL_NAME:
        return {}

    vectors = data.get("vectors", {})
    novel_ids = {novel.id for novel in novels}
    if not novel_ids.issubset(vectors.keys()):
        return {}

    return {novel_id: vector for novel_id, vector in vectors.items() if novel_id in novel_ids}


def build_vectors(novels: list[Novel]) -> dict[str, list[float]]:
    model = load_model()
    if model is None:
        return {}

    texts = [novel_embedding_text(novel) for novel in novels]
    encoded = model.encode(texts, normalize_embeddings=True)
    return {novel.id: vector.tolist() for novel, vector in zip(novels, encoded)}


def semantic_scores(query: str, novels: list[Novel]) -> dict[str, float]:
    model = load_model()
    if model is None:
        return fallback_semantic_scores(query, novels)

    vectors = load_cached_embeddings(novels) or build_vectors(novels)
    if not vectors:
        return fallback_semantic_scores(query, novels)

    query_vector = model.encode(expand_query_mood(query), normalize_embeddings=True).tolist()
    return {novel.id: normalize_score(cosine(query_vector, vectors[novel.id])) for novel in novels if novel.id in vectors}


def fallback_semantic_scores(query: str, novels: list[Novel]) -> dict[str, float]:
    expanded_words = set(re.findall(r"[a-z0-9]+", expand_query_mood(query).lower()))
    scores = {}

    for novel in novels:
        text_words = set(re.findall(r"[a-z0-9]+", novel_embedding_text(novel).lower()))
        hits = expanded_words & text_words
        scores[novel.id] = min(len(hits) / max(len(expanded_words), 1), 1.0)

    return scores
