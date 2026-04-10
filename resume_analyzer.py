import re
import json
import spacy
from io import BytesIO
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import docx

nlp = spacy.load("en_core_web_sm")

# ── Industry keyword corpus (fallback when no JD is pasted) ──────────────────
ROLE_KEYWORDS = {
    "data_analyst": [
        "python", "sql", "excel", "power bi", "tableau", "pandas", "numpy",
        "data visualization", "machine learning", "statistics", "r", "etl",
        "data cleaning", "hypothesis testing", "regression"
    ],
    "software_engineer": [
        "python", "java", "javascript", "git", "api", "rest", "microservices",
        "docker", "kubernetes", "ci/cd", "algorithms", "data structures",
        "agile", "scrum", "cloud", "aws", "system design"
    ],
    "marketing": [
        "seo", "google analytics", "content marketing", "social media",
        "email marketing", "crm", "brand management", "campaign", "roi",
        "market research", "copywriting", "lead generation"
    ],
    "general_fresher": [
        "communication", "teamwork", "leadership", "problem solving",
        "microsoft office", "internship", "project", "achievement",
        "volunteer", "certification", "academic"
    ]
}

REQUIRED_SECTIONS = [
    "education", "experience", "skills", "projects",
    "summary", "objective", "certifications", "achievements"
]

WEAK_VERBS = ["did", "worked", "helped", "was", "were", "made", "got", "had"]
STRONG_VERBS = [
    "developed", "implemented", "designed", "optimized", "led",
    "built", "automated", "reduced", "increased", "managed", "created",
    "architected", "delivered", "launched", "mentored", "analyzed"
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs)


def extract_text_from_raw(text: str) -> str:
    return text.strip()


def detect_sections(text: str) -> dict:
    """Detect which standard resume sections are present."""
    text_lower = text.lower()
    found = {}
    for section in REQUIRED_SECTIONS:
        found[section] = section in text_lower
    return found


def extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords using spaCy."""
    doc = nlp(text.lower())
    keywords = []
    for token in doc:
        if (not token.is_stop and not token.is_punct
                and token.pos_ in {"NOUN", "PROPN", "VERB", "ADJ"}
                and len(token.text) > 2):
            keywords.append(token.lemma_)
    # Also extract multi-word noun phrases
    for chunk in doc.noun_chunks:
        keywords.append(chunk.text.lower())
    return list(set(keywords))


def tfidf_similarity(resume_text: str, jd_text: str) -> float:
    """Compute cosine similarity between resume and JD using TF-IDF."""
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    try:
        matrix = vectorizer.fit_transform([resume_text, jd_text])
        score = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return round(float(score), 4)
    except Exception:
        return 0.0


def find_missing_keywords(resume_text: str, jd_text: str = None,
                          role: str = "general_fresher") -> dict:
    """
    Returns:
      present  – keywords found in resume
      missing  – important keywords absent from resume
      critical – top 5 missing with frequency data
    """
    resume_lower = resume_text.lower()

    if jd_text:
        jd_doc = nlp(jd_text.lower())
        all_kws = [t.lemma_ for t in jd_doc
                   if not t.is_stop and not t.is_punct and len(t.text) > 2]
        # Deduplicate and weight by frequency
        from collections import Counter
        freq = Counter(all_kws)
        target_keywords = [kw for kw, _ in freq.most_common(40)]
    else:
        target_keywords = ROLE_KEYWORDS.get(role, ROLE_KEYWORDS["general_fresher"])

    present = [kw for kw in target_keywords if kw in resume_lower]
    missing = [kw for kw in target_keywords if kw not in resume_lower]
    critical = missing[:5]

    return {"present": present, "missing": missing, "critical": critical}


def check_quantified_achievements(text: str) -> dict:
    """Check if resume has measurable impact statements."""
    number_pattern = re.compile(
        r'\b(\d+[\%x]|\d+\s*(percent|users|clients|projects|hours|days|'
        r'weeks|months|years|members|employees|crore|lakh|million|billion))\b',
        re.IGNORECASE
    )
    matches = number_pattern.findall(text)
    has_numbers = len(matches) >= 2
    return {"has_quantified": has_numbers, "count": len(matches), "examples": matches[:5]}


def check_action_verbs(text: str) -> dict:
    text_lower = text.lower()
    strong_found = [v for v in STRONG_VERBS if v in text_lower]
    weak_found = [v for v in WEAK_VERBS if v in text_lower]
    return {"strong": strong_found, "weak": weak_found}


def check_length(text: str) -> dict:
    words = len(text.split())
    lines = len(text.strip().splitlines())
    ideal = 400 <= words <= 900
    return {
        "word_count": words,
        "line_count": lines,
        "is_ideal_length": ideal,
        "advice": (
            "Resume is too short. Add more detail to projects and skills."
            if words < 400 else
            "Resume is too long for a fresher. Trim to under 900 words."
            if words > 900 else
            "Resume length is ideal."
        )
    }


def compute_ats_score(
    resume_text: str,
    jd_text: str = None,
    role: str = "general_fresher"
) -> dict:
    """
    Master scoring function. Returns a score out of 100 with rubric breakdown
    and actionable improvement suggestions.
    """
    sections = detect_sections(resume_text)
    keywords_data = find_missing_keywords(resume_text, jd_text, role)
    quant = check_quantified_achievements(resume_text)
    verbs = check_action_verbs(resume_text)
    length = check_length(resume_text)

    # ── Scoring rubric (100 points total) ────────────────────────────────────
    score = 0
    rubric = {}
    suggestions = []

    # 1. Keyword match (30 pts)
    if jd_text:
        sim = tfidf_similarity(resume_text, jd_text)
        kw_score = round(sim * 30)
    else:
        total_kw = len(keywords_data["present"]) + len(keywords_data["missing"])
        kw_ratio = len(keywords_data["present"]) / max(total_kw, 1)
        kw_score = round(kw_ratio * 30)
    score += kw_score
    rubric["keyword_match"] = {"score": kw_score, "max": 30}

    if keywords_data["critical"]:
        top = ", ".join(f'"{k}"' for k in keywords_data["critical"][:3])
        suggestions.append(
            f"🔑 Add missing keywords: {top} — these appear in 70–90% of "
            f"{'JD requirements' if jd_text else 'fresher job postings'}."
        )

    # 2. Required sections (20 pts)
    present_sections = sum(1 for v in sections.values() if v)
    section_score = round((present_sections / len(REQUIRED_SECTIONS)) * 20)
    score += section_score
    rubric["sections"] = {"score": section_score, "max": 20, "found": sections}

    missing_secs = [s for s, found in sections.items() if not found]
    if missing_secs:
        suggestions.append(
            f"📋 Missing sections: {', '.join(missing_secs).title()}. "
            f"ATS scanners rely on section headers — add them explicitly."
        )

    # 3. Quantified achievements (15 pts)
    quant_score = 15 if quant["has_quantified"] else (7 if quant["count"] == 1 else 0)
    score += quant_score
    rubric["quantified_achievements"] = {"score": quant_score, "max": 15}

    if not quant["has_quantified"]:
        suggestions.append(
            "📊 No measurable achievements found. Add metrics like "
            "'Reduced API response time by 40%' or 'Built dashboard used by 500+ students'."
        )

    # 4. Action verbs (15 pts)
    verb_score = min(len(verbs["strong"]) * 2, 15)
    score += verb_score
    rubric["action_verbs"] = {
        "score": verb_score, "max": 15,
        "strong_verbs_found": verbs["strong"],
        "weak_verbs_to_replace": verbs["weak"]
    }

    if verbs["weak"]:
        wv = ", ".join(f'"{v}"' for v in verbs["weak"][:3])
        suggestions.append(
            f"✍️  Replace weak verbs ({wv}) with strong action verbs like "
            f"'Developed', 'Implemented', 'Optimized'."
        )

    # 5. Resume length (10 pts)
    len_score = 10 if length["is_ideal_length"] else 4
    score += len_score
    rubric["length"] = {"score": len_score, "max": 10, **length}
    if not length["is_ideal_length"]:
        suggestions.append(f"📏 {length['advice']}")

    # 6. Summary/objective quality (10 pts)
    has_summary = sections.get("summary") or sections.get("objective")
    summary_score = 0
    if has_summary:
        # Simple heuristic: penalise vague phrases
        vague = ["passionate", "hardworking", "team player", "fast learner",
                 "good communication", "enthusiastic"]
        resume_lower = resume_text.lower()
        vague_count = sum(1 for v in vague if v in resume_lower)
        summary_score = max(10 - vague_count * 2, 2)
        if vague_count > 1:
            phrases = ", ".join(f'"{v}"' for v in vague if v in resume_lower)[:3]
            suggestions.append(
                f"✨ Your summary uses clichés ({phrases}). Rewrite it to "
                f"reflect specific skills, e.g. 'CS fresher with 2 Python projects "
                f"in ML and a 3-star CodeChef rating seeking data roles.'"
            )
    else:
        suggestions.append(
            "📝 Add a 3–4 line Summary/Objective at the top. This is the first "
            "thing recruiters read and ATS systems scan for role relevance."
        )
    score += summary_score
    rubric["summary_quality"] = {"score": summary_score, "max": 10}

    # ── Final result ──────────────────────────────────────────────────────────
    return {
        "total_score": min(score, 100),
        "grade": (
            "Excellent" if score >= 80 else
            "Good" if score >= 65 else
            "Average" if score >= 50 else
            "Needs Work"
        ),
        "rubric": rubric,
        "suggestions": suggestions,
        "keywords": keywords_data,
        "sections_found": sections,
    }