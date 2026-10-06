import json
import math
import re
from pathlib import Path

from app.models import Novel


ROOT = Path(__file__).resolve().parents[1]
EMBEDDINGS_DATA = ROOT / "data" / "embeddings.json"
MODEL_NAME = "diviner-local-tfidf-v1"

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

EXTRA_RELATED_TERMS = {
    "horror": {"spooky", "spooked", "scary", "creepy", "ghost", "haunted", "occult", "supernatural", "demon"},
    "cozy": {"chill", "peaceful", "comfort", "warm", "healing", "relaxing"},
    "comedy": {"funny", "humor", "jokes", "silly", "absurd"},
    "strategy": {"smart", "clever", "planning", "scheming", "tactical"},
    "dark": {"grim", "bleak", "ruthless", "violent", "tragic"},
    "action": {"hype", "battle", "fight", "fast", "intense"},
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


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def expand_query_mood(query: str) -> str:
    query_tokens = set(tokens(query))
    expansions = [text for key, text in MOOD_EXPANSIONS.items() if key in query_tokens]
    if not expansions:
        return query
    return query + " " + " ".join(expansions)


def expanded_tokens(text: str) -> list[str]:
    base = tokens(expand_query_mood(text))
    expanded = list(base)
    base_set = set(base)

    for root, related in EXTRA_RELATED_TERMS.items():
        if root in base_set or base_set & related:
            expanded.append(root)
            expanded.extend(sorted(related))

    return expanded


def document_frequency(documents: list[list[str]]) -> dict[str, int]:
    counts = {}
    for doc in documents:
        for token in set(doc):
            counts[token] = counts.get(token, 0) + 1
    return counts


def build_vocabulary(novels: list[Novel]) -> tuple[list[str], dict[str, float]]:
    documents = [expanded_tokens(novel_embedding_text(novel)) for novel in novels]
    counts = document_frequency(documents)
    total_docs = max(len(documents), 1)
    vocab = sorted(counts)
    idf = {token: math.log((1 + total_docs) / (1 + counts[token])) + 1 for token in vocab}
    return vocab, idf


def vectorize(text: str, vocab: list[str], idf: dict[str, float]) -> list[float]:
    terms = expanded_tokens(text)
    if not terms:
        return [0.0 for _ in vocab]

    term_counts = {}
    for term in terms:
        term_counts[term] = term_counts.get(term, 0) + 1

    total = len(terms)
    vector = []
    for token in vocab:
        tf = term_counts.get(token, 0) / total
        vector.append(tf * idf.get(token, 0.0))

    return normalize_vector(vector)


def normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def build_embedding_payload(novels: list[Novel]) -> dict:
    vocab, idf = build_vocabulary(novels)
    vectors = {novel.id: vectorize(novel_embedding_text(novel), vocab, idf) for novel in novels}
    return {
        "model": MODEL_NAME,
        "count": len(vectors),
        "vocabulary": vocab,
        "idf": idf,
        "vectors": vectors,
    }


def load_cached_payload(novels: list[Novel]) -> dict:
    if not EMBEDDINGS_DATA.exists():
        return {}

    data = json.loads(EMBEDDINGS_DATA.read_text(encoding="utf-8"))
    if data.get("model") != MODEL_NAME:
        return {}

    vectors = data.get("vectors", {})
    novel_ids = {novel.id for novel in novels}
    if not novel_ids.issubset(vectors.keys()):
        return {}

    return data


def semantic_scores(query: str, novels: list[Novel]) -> dict[str, float]:
    payload = load_cached_payload(novels) or build_embedding_payload(novels)
    vocab = payload.get("vocabulary", [])
    idf = payload.get("idf", {})
    vectors = payload.get("vectors", {})

    query_vector = vectorize(query, vocab, idf)
    return {
        novel.id: max(0.0, min(cosine(query_vector, vectors.get(novel.id, [])), 1.0))
        for novel in novels
    }
