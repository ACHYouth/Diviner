import difflib
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
    "book",
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
    "me",
    "novel",
    "novels",
    "of",
    "on",
    "or",
    "read",
    "series",
    "something",
    "story",
    "that",
    "the",
    "to",
    "want",
    "webnovel",
    "with",
}

SYNONYMS = {
    "academy": {"academy", "school", "student", "class", "university", "magic school"},
    "alchemist": {"alchemist", "alchemy", "potion", "crafter", "crafting"},
    "apocalypse": {"apocalypse", "post apocalypse", "system apocalypse", "end of world"},
    "assassin": {"assassin", "killer", "stealth", "spy"},
    "battle": {"battle", "fight", "combat", "war", "action"},
    "clever": {"clever", "smart", "intelligent", "scheming", "strategic", "tactical", "cunning"},
    "completed": {"completed", "complete", "finished", "ended", "done"},
    "comedy": {"comedy", "funny", "humor", "humour", "satire"},
    "cozy": {"cozy", "slice of life", "peaceful", "healing", "slow life"},
    "cultivation": {"cultivation", "cultivator", "xianxia", "wuxia", "qi", "dao"},
    "dark": {"dark", "grimdark", "bleak", "horror", "tragic"},
    "dungeon": {"dungeon", "delve", "labyrinth", "tower", "raid"},
    "fantasy": {"fantasy", "magic", "magical", "mage", "wizard", "sorcery"},
    "female protagonist": {"female protagonist", "female lead", "fl", "heroine"},
    "game": {"game", "vr", "vrmmo", "rpg", "mmorpg", "litrpg"},
    "isekai": {"isekai", "portal fantasy", "transmigration", "transmigrated", "otherworld"},
    "kingdom": {"kingdom", "empire", "nobility", "politics", "court"},
    "loop": {"loop", "time loop", "redo", "regression", "second chance"},
    "mystery": {"mystery", "conspiracy", "secret", "investigation", "detective"},
    "progression": {"progression", "weak to strong", "leveling", "level up", "training", "growth"},
    "reincarnation": {"reincarnation", "reborn", "reincarnated", "second life"},
    "ritual": {"ritual", "rituals", "occult", "ceremony", "sacrifice", "pathway"},
    "romance": {"romance", "romantic", "relationship", "love"},
    "science fiction": {"science fiction", "sci fi", "scifi", "space", "cyberpunk", "technology"},
    "secret organization": {"secret organization", "secret society", "hidden organization", "cult", "church"},
    "slow burn": {"slow burn", "slow paced", "gradual", "patient"},
    "sports": {"sports", "athlete", "competition", "team"},
    "strategy": {"strategy", "strategic", "tactics", "planning", "scheming"},
    "superhero": {"superhero", "superpower", "superpowers", "heroes", "villains"},
    "survival": {"survival", "survive", "desperate", "dangerous", "harsh"},
    "villain": {"villain", "antihero", "evil", "ruthless", "morally gray"},
}

FIELD_WEIGHTS = {
    "title": 3.0,
    "genres": 3.2,
    "tags": 3.0,
    "synopsis": 1.2,
    "status": 1.0,
    "author": 0.6,
    "source": 0.3,
}


def simple_stem(word: str) -> str:
    irregular = {
        "classes": "class",
        "class": "class",
        "completed": "complete",
        "stories": "story",
    }
    if word in irregular:
        return irregular[word]
    if len(word) > 5 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 5 and word.endswith("ing"):
        return word[:-3]
    if len(word) > 4 and word.endswith("ed"):
        return word[:-2]
    if len(word) > 4 and word.endswith("es"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def raw_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def tokenize(text: str) -> list[str]:
    words = raw_tokens(text)
    return [simple_stem(word) for word in words if word not in STOPWORDS and len(word) > 1]


def phrases(text: str) -> set[str]:
    tokens = tokenize(text)
    found = set(tokens)
    for size in (2, 3):
        for index in range(max(len(tokens) - size + 1, 0)):
            found.add(" ".join(tokens[index : index + size]))
    return found


def expanded_terms(text: str) -> set[str]:
    base = phrases(text)
    expanded = set(base)

    for key, values in SYNONYMS.items():
        normalized_values = set()
        for value in values:
            normalized_values.update(concept_forms(value))
        normalized_key = next(iter(concept_forms(key)), simple_stem(key))
        if base & normalized_values or normalized_key in base:
            expanded.add(normalized_key)
            expanded.update(normalized_values)

    return expanded


def concept_forms(value: str) -> set[str]:
    tokens = tokenize(value)
    if not tokens:
        return set()
    joined = " ".join(tokens)
    if len(tokens) == 1:
        return {joined}
    return {joined}


def fields_for_novel(novel: Novel) -> dict[str, str]:
    return {
        "title": novel.title,
        "author": novel.author,
        "source": novel.source,
        "status": novel.status,
        "genres": " ".join(novel.genres),
        "tags": " ".join(novel.tags),
        "synopsis": novel.synopsis,
    }


def fuzzy_match(term: str, candidates: set[str]) -> bool:
    if len(term) < 5:
        return False
    for candidate in candidates:
        if len(candidate) < 5:
            continue
        if difflib.SequenceMatcher(None, term, candidate).ratio() >= 0.86:
            return True
    return False


def weighted_match_score(query_terms: set[str], novel: Novel) -> tuple[float, list[str], list[str]]:
    total_weight = sum(FIELD_WEIGHTS.values())
    score = 0.0
    matched_terms = set()
    reasons = []

    for field, text in fields_for_novel(novel).items():
        field_terms = expanded_terms(text)
        exact_hits = query_terms & field_terms
        fuzzy_hits = {term for term in query_terms if term not in exact_hits and fuzzy_match(term, field_terms)}
        hits = exact_hits | fuzzy_hits

        if not hits:
            continue

        coverage = len(hits) / max(len(query_terms), 1)
        score += coverage * FIELD_WEIGHTS[field]
        matched_terms.update(hits)

        if field in {"genres", "tags", "title"}:
            pretty_field = "title" if field == "title" else field[:-1]
            reasons.append(f"{pretty_field} match: " + ", ".join(sorted(hits)[:4]))

    normalized = score / total_weight
    return normalized, sorted(matched_terms), reasons


def intent_bonus(query_terms: set[str], novel: Novel) -> tuple[float, list[str]]:
    bonus = 0.0
    reasons = []
    status_terms = expanded_terms(novel.status)

    if query_terms & expanded_terms("completed finished ended") and status_terms & expanded_terms("completed"):
        bonus += 0.08
        reasons.append("completed story requested")

    if query_terms & expanded_terms("ongoing updating current") and status_terms & expanded_terms("ongoing"):
        bonus += 0.05
        reasons.append("ongoing story requested")

    if query_terms & expanded_terms("long epic many chapters") and novel.chapters >= 500:
        bonus += 0.06
        reasons.append("long read requested")

    if query_terms & expanded_terms("short quick") and 0 < novel.chapters <= 150:
        bonus += 0.04
        reasons.append("shorter read requested")

    return bonus, reasons


def score_novel(query: str, novel: Novel) -> RecommendationResult:
    query_terms = expanded_terms(query)
    exact_score, matched, reasons = weighted_match_score(query_terms, novel)
    bonus, bonus_reasons = intent_bonus(query_terms, novel)
    rating_score = min(max(novel.rating / 5.0, 0), 1)

    query_counts = Counter(tokenize(query))
    title_counts = Counter(tokenize(novel.title))
    title_overlap = sum(min(query_counts[word], title_counts[word]) for word in query_counts)
    title_bonus = min(title_overlap * 0.05, 0.15)

    similarity = min((exact_score * 0.82) + (rating_score * 0.08) + bonus + title_bonus, 1.0)

    if bonus_reasons:
        reasons.extend(bonus_reasons)
    if not reasons and matched:
        reasons.append("close wording match")
    if not reasons:
        reasons.append("closest catalog match")

    return RecommendationResult(
        novel=novel,
        similarity_score=round(similarity, 3),
        rating_score=round(rating_score, 3),
        matched_terms=matched[:12],
        reasons=reasons[:4],
    )


def recommend(query: str, novels: list[Novel], sort_by: str = "similarity", limit: int = 10) -> list[RecommendationResult]:
    results = [score_novel(query, novel) for novel in novels]

    if sort_by == "rating":
        results.sort(key=lambda item: (item.novel.rating, item.similarity_score), reverse=True)
    else:
        results.sort(key=lambda item: (item.similarity_score, item.novel.rating), reverse=True)

    return results[: max(1, min(limit, 50))]
