import asyncio
import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from resume_analyzer import compute_ats_score, extract_text_from_pdf, extract_text_from_docx
from scrapers.naukri_scraper import scrape_naukri_freshers
from scrapers.serpapi_jobs import search_jobs_serpapi
from scrapers.instagram_scraper import scrape_instagram_jobs
from db.database import init_db, save_jobs, get_jobs, save_score_history, get_score_history

app = FastAPI(title="Fresher Job Finder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

init_db()


class ResumeTextRequest(BaseModel):
    resume_text: str
    jd_text: Optional[str] = None
    role: str = "general_fresher"


@app.post("/analyze/text")
async def analyze_resume_text(req: ResumeTextRequest):
    """Analyze pasted resume text."""
    result = compute_ats_score(req.resume_text, req.jd_text, req.role)
    save_score_history({
        "score": result["total_score"],
        "grade": result["grade"],
        "role": req.role,
        "suggestions": result["suggestions"]
    })
    return result


@app.post("/analyze/file")
async def analyze_resume_file(
    file: UploadFile = File(...),
    jd_text: str = Form(default=""),
    role: str = Form(default="general_fresher")
):
    """Analyze uploaded PDF or DOCX."""
    content = await file.read()
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(content)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(content)
    else:
        return {"error": "Only PDF and DOCX files are supported."}

    result = compute_ats_score(text, jd_text or None, role)
    save_score_history({
        "score": result["total_score"],
        "grade": result["grade"],
        "role": role,
        "suggestions": result["suggestions"]
    })
    return result


@app.get("/jobs")
async def get_cached_jobs(location: str = "", role: str = "", limit: int = 50):
    """Return jobs from local DB cache."""
    return get_jobs(location, role, limit)


@app.post("/jobs/refresh")
async def refresh_jobs(location: str = "", role: str = "developer"):
    """Scrape all sources and cache results."""
    all_jobs = []

    # Naukri
    try:
        naukri = await scrape_naukri_freshers(location=location, role=role)
        all_jobs.extend(naukri)
    except Exception as e:
        print(f"Naukri scrape failed: {e}")

    # SerpAPI / Google Jobs
    try:
        serp = search_jobs_serpapi(query=role, location=location or "India")
        all_jobs.extend(serp)
    except Exception as e:
        print(f"SerpAPI failed: {e}")

    # Instagram (optional — slower)
    try:
        ig = await scrape_instagram_jobs()
        all_jobs.extend(ig)
    except Exception as e:
        print(f"Instagram scrape failed: {e}")

    save_jobs(all_jobs)
    return {"fetched": len(all_jobs), "jobs": all_jobs}


@app.get("/score-history")
async def score_history():
    return get_score_history()
