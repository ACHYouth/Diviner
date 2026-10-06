import re
from collections import Counter

from app.models import Novel, RecommendationResult


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "for",
    "from",
    "has",
    "have",
    "i",
    "in",
    "is",
    "it",
    "like",
    "novel",
    "of",
    "on",
    "or",
    "story",
    "that",
    "the",
    "to",
    "want",
    "with",
}


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [word for word in words if word not in STOPWORDS and len(word) > 1]


def text_for_novel(novel: Novel) -> str:
    parts = [
        novel.title,
        novel.author,
        novel.source,
        novel.status,
        novel.synopsis,
        " ".join(novel.genres),
        " ".join(novel.tags),
    ]
    return " ".join(parts)


def score_novel(query: str, novel: Novel) -> RecommendationResult:
    query_terms = tokenize(query)
    novel_terms = tokenize(text_for_novel(novel))
    query_counts = Counter(query_terms)
    novel_counts = Counter(novel_terms)

    matched = sorted(set(query_terms) & set(novel_terms))
    overlap = sum(min(query_counts[word], novel_counts[word]) for word in matched)
    base = overlap / max(len(query_terms), 1)

    genre_hits = sorted(set(tokenize(" ".join(novel.genres))) & set(query_terms))
    tag_hits = sorted(set(tokenize(" ".join(novel.tags))) & set(query_terms))

    genre_bonus = min(len(genre_hits) * 0.08, 0.24)
    tag_bonus = min(len(tag_hits) * 0.05, 0.25)
    completion_bonus = 0.08 if "completed" in query_terms and novel.status.lower() == "completed" else 0.0

    similarity = min(base + genre_bonus + tag_bonus + completion_bonus, 1.0)
    rating_score = min(max(novel.rating / 5.0, 0), 1)

    reasons = []
    if genre_hits:
        reasons.append("genre match: " + ", ".join(genre_hits))
    if tag_hits:
        reasons.append("tag match: " + ", ".join(tag_hits))
    if completion_bonus:
        reasons.append("completed story requested")
    if not reasons and matched:
        reasons.append("synopsis/title overlap")
    if not reasons:
        reasons.append("closest catalog match")

    return RecommendationResult(
        novel=novel,
        similarity_score=round(similarity, 3),
        rating_score=round(rating_score, 3),
        matched_terms=matched[:12],
        reasons=reasons,
    )


def recommend(query: str, novels: list[Novel], sort_by: str = "similarity", limit: int = 10) -> list[RecommendationResult]:
    results = [score_novel(query, novel) for novel in novels]

    if sort_by == "rating":
        results.sort(key=lambda item: (item.novel.rating, item.similarity_score), reverse=True)
    else:
        results.sort(key=lambda item: (item.similarity_score, item.novel.rating), reverse=True)

    return results[: max(1, min(limit, 50))]

