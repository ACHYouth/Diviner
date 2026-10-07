from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.catalog import Catalog
from app.models import Novel, RecommendationRequest, RecommendationResult
from app.recommender import recommend


app = FastAPI(title="Diviner")
catalog = Catalog()

frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
def index():
    return FileResponse(frontend_dir / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "catalog_size": len(catalog.load()), "sources": catalog.source_counts()}


@app.get("/api/sources")
def sources():
    return catalog.source_counts()


@app.get("/api/ingestion-runs")
def ingestion_runs(limit: int = Query(default=10, ge=1, le=100)):
    return catalog.ingestion_runs(limit)


@app.get("/api/novels", response_model=list[Novel])
def novels(sort: str = Query(default="rating")):
    rows = catalog.load()
    if sort == "title":
        rows.sort(key=lambda item: item.title.lower())
    elif sort == "source":
        rows.sort(key=lambda item: (item.source.lower(), item.title.lower()))
    elif sort == "popularity":
        rows.sort(key=lambda item: item.popularity_score, reverse=True)
    else:
        rows.sort(key=lambda item: item.rating, reverse=True)
    return rows


@app.post("/api/recommend", response_model=list[RecommendationResult])
def recommendations(request: RecommendationRequest):
    return recommend(request.query, catalog.load(), request.sort_by, request.limit)
