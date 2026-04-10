import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
SERPAPI_URL = "https://serpapi.com/search"


def search_jobs_serpapi(query: str, location: str = "India",
                        num_results: int = 15) -> list[dict]:
    """
    Search for fresher jobs via SerpAPI Google Jobs endpoint.
    Docs: https://serpapi.com/google-jobs-api
    """
    if not SERPAPI_KEY:
        raise ValueError("SERPAPI_KEY missing in .env file")

    params = {
        "engine":   "google_jobs",
        "q":        f"{query} fresher entry level",
        "location": location,
        "hl":       "en",
        "gl":       "in",
        "api_key":  SERPAPI_KEY,
        "num":      num_results,
        "chips":    "date_posted:week",   # Only last 7 days
    }

    resp = requests.get(SERPAPI_URL, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    jobs = []
    for item in data.get("jobs_results", []):
        jobs.append({
            "title":       item.get("title", "N/A"),
            "company":     item.get("company_name", "N/A"),
            "location":    item.get("location", "N/A"),
            "description": item.get("description", "")[:300],
            "salary":      item.get("salary", "Not disclosed"),
            "posted":      item.get("detected_extensions", {}).get("posted_at", ""),
            "work_mode":   item.get("detected_extensions", {}).get("work_from_home", False),
            "link":        (item.get("related_links") or [{}])[0].get("link", ""),
            "source":      "Google Jobs / LinkedIn"
        })

    return jobs


def search_linkedin_fresher(role: str, location: str = "India") -> list[dict]:
    """Specifically target LinkedIn fresher postings via SerpAPI."""
    return search_jobs_serpapi(
        query=f"site:linkedin.com/jobs {role} 0-1 years experience fresher",
        location=location
    )