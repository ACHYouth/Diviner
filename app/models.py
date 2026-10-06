from pydantic import BaseModel, Field


class Novel(BaseModel):
    id: str
    title: str
    author: str
    source: str
    url: str
    genres: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    rating: float = 0.0
    chapters: int = 0
    status: str = "unknown"
    synopsis: str = ""


class RecommendationRequest(BaseModel):
    query: str
    sort_by: str = "similarity"
    limit: int = 10


class RecommendationResult(BaseModel):
    novel: Novel
    similarity_score: float
    rating_score: float
    matched_terms: list[str]
    reasons: list[str]

