# 💼 Fresher Job Finder

A personal-use, locally-hosted job aggregation and ATS resume scoring tool built for fresher / entry-level candidates in India. Combines real-time job scraping (Naukri, Google Jobs, Instagram), an NLP-powered ATS resume analyzer, and a Streamlit UI — all running on your machine with no cloud auth required.

---

## ✨ Features

- **ATS Resume Scorer** — paste or upload a PDF/DOCX resume and get a score out of 100 with section-wise breakdown and specific improvement suggestions
- **JD-Specific Scoring** — optionally paste a Job Description to compare your resume against that exact role
- **Real Job Feed** — aggregates live fresher jobs from Naukri.com, Google Jobs (via SerpAPI), and Instagram hiring posts
- **Filters** — filter jobs by role, location, work mode (Remote/Onsite), and source
- **Score History** — every resume analysis is saved locally so you can track improvement over time
- **Zero auth** — no login, no cloud account needed; everything runs on localhost

---

## 🏗️ Architecture

```
fresher-job-finder/
├── app.py                      # Streamlit frontend (UI)
├── main.py                     # FastAPI backend (REST API)
├── resume_analyzer.py          # ATS scoring engine (spaCy + TF-IDF)
├── scrapers/
│   ├── naukri_scraper.py       # Playwright scraper for Naukri.com
│   ├── serpapi_jobs.py         # Google Jobs via SerpAPI / Jobicy fallback
│   └── instagram_scraper.py   # Public Instagram hiring posts
├── db/
│   └── database.py             # SQLite helpers (jobs + score history)
├── data/
│   └── jobs.db                 # Auto-created SQLite database
├── uploads/                    # Temporary resume file uploads
├── .env                        # API keys (never commit this)
└── requirements.txt
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI + Uvicorn |
| NLP / ATS | spaCy, scikit-learn (TF-IDF), PyPDF2, python-docx |
| Scraping | Playwright (Chromium headless) |
| Job APIs | SerpAPI (Google Jobs), Jobicy (free fallback) |
| Database | SQLite (via Python `sqlite3`) |
| Environment | python-dotenv |

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js (not required — only if you modify DOCX tooling)
- A free [SerpAPI](https://serpapi.com) account (100 free searches/month)

### 1. Clone the repository

```bash
git clone https://github.com/Siddhesh-Bhatkar/fresher-job-finder.git
cd fresher-job-finder
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the spaCy language model

```bash
python -m spacy download en_core_web_sm
```

### 5. Install Playwright browser

```bash
playwright install chromium
```

### 6. Configure environment variables

Create a `.env` file in the project root:

```env
SERPAPI_KEY=your_serpapi_key_here
IG_SESSION_COOKIE=your_instagram_sessionid_cookie_here
```

**Getting your SerpAPI key:** Sign up free at [serpapi.com](https://serpapi.com) → Dashboard → API Key.

**Getting your Instagram session cookie (optional):**
1. Log in to instagram.com in Chrome
2. Open DevTools (`F12`) → Application → Cookies → `instagram.com`
3. Copy the value of `sessionid` and paste it into `.env`

> ⚠️ The Instagram scraper is optional. The app works fully without it using Naukri + SerpAPI.

### 7. Create required directories

```bash
mkdir -p data uploads
```

---

## 🚀 Running the App

You need **two terminals** running simultaneously.

**Terminal 1 — Start the FastAPI backend:**

```bash
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Start the Streamlit frontend:**

```bash
streamlit run app.py
```

Then open your browser at **http://localhost:8501**

---

## 📡 API Endpoints

The FastAPI backend runs on `http://localhost:8000`. Interactive docs available at `http://localhost:8000/docs`.

### ATS Resume Analysis

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze/text` | Analyze pasted resume text |
| `POST` | `/analyze/file` | Analyze uploaded PDF or DOCX |

**POST `/analyze/text` — Request body:**
```json
{
  "resume_text": "Your full resume content here...",
  "jd_text": "Optional job description to compare against...",
  "role": "general_fresher"
}
```

**Supported roles:** `general_fresher`, `data_analyst`, `software_engineer`, `marketing`

**Response:**
```json
{
  "total_score": 74,
  "grade": "Good",
  "rubric": {
    "keyword_match":           { "score": 22, "max": 30 },
    "sections":                { "score": 16, "max": 20 },
    "quantified_achievements": { "score": 15, "max": 15 },
    "action_verbs":            { "score": 10, "max": 15 },
    "length":                  { "score": 10, "max": 10 },
    "summary_quality":         { "score":  1, "max": 10 }
  },
  "suggestions": [
    "🔑 Add missing keywords: \"docker\", \"microservices\", \"agile\"",
    "✍️  Replace weak verbs (\"did\", \"helped\") with strong action verbs"
  ],
  "keywords": {
    "present": ["python", "rest api", "mysql"],
    "missing": ["docker", "microservices", "agile"],
    "critical": ["docker", "microservices", "agile", "junit", "ci/cd"]
  }
}
```

---

### Job Feed

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/jobs` | Fetch cached jobs from local DB |
| `POST` | `/jobs/refresh` | Scrape all sources and refresh the cache |

**GET `/jobs` — Query parameters:**

| Param | Type | Description |
|---|---|---|
| `location` | string | Filter by location (e.g. `Mumbai`) |
| `role` | string | Filter by job title keyword (e.g. `python`) |
| `limit` | int | Max results to return (default: `50`) |

**POST `/jobs/refresh` — Query parameters:**

| Param | Type | Description |
|---|---|---|
| `location` | string | Location to scrape for (e.g. `Bangalore`) |
| `role` | string | Role keyword to search (e.g. `developer`) |

---

### Score History

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/score-history` | Returns last 10 resume scan results |

---

## 🖥️ UI Pages

### 🔍 ATS Checker
- Paste resume text or upload a PDF / DOCX
- Optionally paste a specific Job Description for tailored scoring
- View score out of 100 with rubric breakdown and colour-coded grade
- See specific improvement suggestions and missing keyword list

### 📋 Job Feed
- Click **Fetch Live Jobs** to scrape all sources in real time
- Filter by role, location, work mode, and source
- Click **Apply →** to open the job listing directly
- Save jobs to session for quick reference

### 📊 Score History
- View all past resume analyses with timestamp, score, grade, and suggestions
- Tracks improvement over multiple iterations

---

## 🔧 ATS Scoring Rubric

| Category | Max Points | What it checks |
|---|---|---|
| Keyword match | 30 | TF-IDF cosine similarity vs JD or role corpus |
| Required sections | 20 | Presence of Education, Skills, Projects, Summary, etc. |
| Quantified achievements | 15 | Numbers, percentages, measurable impact |
| Action verbs | 15 | Strong verbs (Developed, Optimised) vs weak (did, helped) |
| Resume length | 10 | Ideal: 400–900 words for a fresher |
| Summary quality | 10 | Specific vs generic/cliché phrases |

---

## 📦 requirements.txt

```
fastapi==0.111.0
uvicorn==0.30.1
streamlit==1.36.0
python-dotenv==1.0.1
requests==2.32.3
playwright==1.44.0
spacy==3.7.5
scikit-learn==1.5.0
PyPDF2==3.0.1
python-docx==1.1.2
sentence-transformers==3.0.1
httpx==0.27.0
python-multipart==0.0.9
aiofiles==24.1.0
pydantic==2.8.0
google-search-results==2.4.2
```

---

## ⚠️ Disclaimers

- **Naukri.com scraping:** This tool scrapes public job listings for personal use. Naukri's Terms of Service prohibit automated scraping. Use responsibly and only for personal job searching.
- **Instagram scraping:** Accessing Instagram via Playwright violates Instagram's ToS (Section 3.2). The Instagram scraper is provided for educational reference only. The app functions fully without it.
- **SerpAPI:** The free tier provides 100 searches/month — sufficient for daily personal use.
- **No warranty:** This tool is for personal use only. Do not deploy it publicly or use it commercially.

---

## 🗺️ Roadmap / Possible Improvements

- [ ] Add LinkedIn Easy Apply automation
- [ ] Email digest of new jobs matching saved filters
- [ ] Resume version comparison (side-by-side score diff)
- [ ] Add Internshala scraper for internship listings
- [ ] Docker Compose setup for one-command start

---

## 👤 Author

**Siddhesh Madhav Bhatkar**
[github.com/Siddhesh-Bhatkar](https://github.com/Siddhesh-Bhatkar) · [linkedin.com/in/siddhesh-bhatkar](https://linkedin.com/in/siddhesh-bhatkar)

---

*Built for personal job searching during the 2025–2026 fresher hiring season in India.*
