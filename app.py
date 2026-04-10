import streamlit as st
import requests
import json
from pathlib import Path
from datetime import datetime

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Fresher Job Finder",
    page_icon="💼",
    layout="wide"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
.job-card {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
    background: #fafafa;
}
.score-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: bold;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("💼 Fresher Job Finder")
    st.markdown("---")
    page = st.radio("Navigate", ["🔍 ATS Checker", "📋 Job Feed", "📊 Score History"])


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: ATS Checker
# ─────────────────────────────────────────────────────────────────────────────
if page == "🔍 ATS Checker":
    st.header("ATS Resume Score Checker")
    st.caption("Paste your resume text OR upload a PDF/DOCX file.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Your Resume")
        input_method = st.radio("Input method", ["Paste text", "Upload file"], horizontal=True)

        resume_text = ""
        uploaded_file = None

        if input_method == "Paste text":
            resume_text = st.text_area(
                "Paste resume content here",
                height=350,
                placeholder="Copy and paste your entire resume text..."
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload PDF or DOCX",
                type=["pdf", "docx"]
            )

    with col2:
        st.subheader("Job Description (optional)")
        jd_text = st.text_area(
            "Paste the JD to compare against",
            height=200,
            placeholder="Paste the job description here for a tailored score..."
        )
        role = st.selectbox(
            "Fallback role (if no JD)",
            ["general_fresher", "data_analyst", "software_engineer", "marketing"]
        )

    if st.button("🎯 Analyze Resume", type="primary", use_container_width=True):
        with st.spinner("Analyzing your resume..."):
            try:
                if uploaded_file:
                    resp = requests.post(
                        f"{API_BASE}/analyze/file",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                        data={"jd_text": jd_text, "role": role},
                        timeout=30
                    )
                elif resume_text.strip():
                    resp = requests.post(
                        f"{API_BASE}/analyze/text",
                        json={"resume_text": resume_text, "jd_text": jd_text or None, "role": role},
                        timeout=30
                    )
                else:
                    st.warning("Please paste your resume text or upload a file.")
                    st.stop()

                result = resp.json()
                score = result["total_score"]
                grade = result["grade"]

                # ── Score display ──────────────────────────────────────────
                st.markdown("---")
                color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 50 else "#ef4444"

                score_col, grade_col = st.columns([1, 2])
                with score_col:
                    st.markdown(f"""
                        <div style="text-align:center;padding:20px;background:{color}22;
                             border-radius:12px;border:2px solid {color}">
                            <div style="font-size:56px;font-weight:bold;color:{color}">{score}</div>
                            <div style="font-size:14px;color:gray">out of 100</div>
                            <div style="font-size:20px;font-weight:600;color:{color};margin-top:4px">{grade}</div>
                        </div>
                    """, unsafe_allow_html=True)

                with grade_col:
                    st.subheader("Section Scores")
                    for key, val in result.get("rubric", {}).items():
                        label = key.replace("_", " ").title()
                        section_score = val.get("score", 0)
                        max_score = val.get("max", 10)
                        pct = section_score / max_score
                        st.markdown(f"**{label}** — {section_score}/{max_score}")
                        st.progress(pct)

                # ── Suggestions ────────────────────────────────────────────
                st.subheader("💡 Improvement Suggestions")
                suggestions = result.get("suggestions", [])
                if suggestions:
                    for s in suggestions:
                        st.info(s)
                else:
                    st.success("Great job! No major issues found.")

                # ── Keyword gap ────────────────────────────────────────────
                kw = result.get("keywords", {})
                if kw.get("missing"):
                    with st.expander(f"🔑 Missing Keywords ({len(kw['missing'])})"):
                        st.write(", ".join(kw["missing"][:20]))
                if kw.get("present"):
                    with st.expander(f"✅ Keywords Found ({len(kw['present'])})"):
                        st.write(", ".join(kw["present"]))

            except requests.ConnectionError:
                st.error("Cannot connect to the API. Make sure `uvicorn main:app` is running on port 8000.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: Job Feed
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📋 Job Feed":
    st.header("Fresher Job Feed")

    # Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        search_role = st.text_input("Role / Keywords", placeholder="Python developer")
    with f2:
        search_loc = st.text_input("Location", placeholder="Bangalore")
    with f3:
        work_mode = st.selectbox("Work Mode", ["All", "Remote", "Onsite", "Hybrid"])
    with f4:
        source_filter = st.selectbox("Source", ["All", "Naukri", "Google Jobs / LinkedIn", "Instagram"])

    col_refresh, col_load = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Refresh Jobs", type="primary"):
            with st.spinner("Scraping all sources... (this takes ~30 seconds)"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/jobs/refresh",
                        params={"location": search_loc, "role": search_role or "developer"},
                        timeout=90
                    )
                    data = resp.json()
                    st.success(f"Fetched {data.get('fetched', 0)} new jobs!")
                except Exception as e:
                    st.error(f"Refresh failed: {e}")

    # Load from cache
    try:
        params = {"location": search_loc, "role": search_role, "limit": 100}
        resp = requests.get(f"{API_BASE}/jobs", params=params, timeout=10)
        jobs = resp.json()
    except Exception:
        jobs = []
        st.warning("Could not load jobs. Make sure the API server is running.")

    # Apply local filters
    if work_mode != "All":
        jobs = [j for j in jobs if work_mode.lower() in str(j.get("work_mode", "")).lower()]
    if source_filter != "All":
        jobs = [j for j in jobs if source_filter in j.get("source", "")]

    st.caption(f"Showing {len(jobs)} jobs")

    if not jobs:
        st.info('No jobs found. Click "Refresh Jobs" to scrape fresh data.')
    else:
        for job in jobs:
            source_badge = {
                "Naukri": "🟠",
                "Google Jobs / LinkedIn": "🔵",
                "Instagram": "🟣"
            }.get(job.get("source", ""), "⚪")

            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <strong style="font-size:16px">{job.get('title','N/A')}</strong>
                    &nbsp;&nbsp;{source_badge} <small>{job.get('source','')}</small><br>
                    🏢 {job.get('company','N/A')} &nbsp;|&nbsp;
                    📍 {job.get('location','N/A')} &nbsp;|&nbsp;
                    💰 {job.get('salary','Not disclosed')}
                </div>
                """, unsafe_allow_html=True)

                btn_col, save_col = st.columns([1, 4])
                with btn_col:
                    if job.get("link"):
                        st.link_button("Apply →", job["link"], use_container_width=True)
                with save_col:
                    if st.button(f"🔖 Save", key=f"save_{job['id']}"):
                        # Save to session state (use IndexedDB via JS in production)
                        if "saved_jobs" not in st.session_state:
                            st.session_state.saved_jobs = []
                        st.session_state.saved_jobs.append(job)
                        st.toast("Job saved!")

                st.divider()

    # Saved jobs
    if st.session_state.get("saved_jobs"):
        with st.expander(f"🔖 Saved Jobs ({len(st.session_state.saved_jobs)})"):
            for sj in st.session_state.saved_jobs:
                st.write(f"• **{sj['title']}** @ {sj['company']} — {sj['location']}")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: Score History
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📊 Score History":
    st.header("Resume Score History")

    try:
        resp = requests.get(f"{API_BASE}/score-history", timeout=10)
        history = resp.json()
    except Exception:
        history = []
        st.warning("API not reachable.")

    if not history:
        st.info("No score history yet. Analyze your resume to get started.")
    else:
        for h in history:
            score = h["score"]
            color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 50 else "#ef4444"
            with st.expander(
                f"{h['timestamp'][:16]}  •  Score: {score}/100  •  {h['grade']}  •  Role: {h['role']}"
            ):
                for s in h.get("suggestions", []):
                    st.write(s)
