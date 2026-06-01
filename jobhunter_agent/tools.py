import re
import html
import requests
from typing import Any


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_resume_profile(resume_text: str) -> dict[str, Any]:
    """
    Extracts a simple structured profile from resume text.

    Args:
        resume_text: Plain-text resume content.

    Returns:
        A structured profile containing likely skills, titles, years signals,
        and resume summary text.
    """
    text = resume_text.strip()
    lower = text.lower()

    known_skills = [
        "python", "fastapi", "django", "flask", "sql", "postgresql", "mysql",
        "sqlite", "mongodb", "redis", "celery", "docker", "kubernetes",
        "aws", "gcp", "azure", "terraform", "linux", "git", "github",
        "rest", "graphql", "microservices", "pytest", "unittest",
        "pandas", "numpy", "machine learning", "llm", "langchain",
        "google adk", "gemini", "api", "backend", "asyncio",
        "javascript", "typescript", "react", "node"
    ]

    found_skills = sorted(
        {skill for skill in known_skills if skill in lower}
    )

    title_patterns = [
        "software engineer",
        "backend engineer",
        "python developer",
        "full stack developer",
        "data engineer",
        "machine learning engineer",
        "ai engineer",
        "cloud engineer",
        "devops engineer",
    ]

    likely_titles = sorted(
        {title for title in title_patterns if title in lower}
    )

    year_matches = re.findall(r"(\d+)\+?\s+years?", lower)
    years_mentions = [int(y) for y in year_matches if y.isdigit()]

    return {
        "status": "success",
        "skills": found_skills,
        "likely_titles": likely_titles,
        "years_mentions": years_mentions,
        "resume_preview": text[:1500],
        "resume_length_chars": len(text),
    }


def search_remoteok_jobs(
    query: str,
    location: str = "remote",
    max_results: int = 10,
) -> dict[str, Any]:
    """
    Searches RemoteOK public job listings.

    Args:
        query: Job search query such as 'python fastapi backend'.
        location: Location preference. RemoteOK is mostly remote, but this is used for filtering text.
        max_results: Maximum number of jobs to return.

    Returns:
        A list of matching job postings with title, company, url, tags, and description.
    """
    url = "https://remoteok.com/api"
    headers = {
        "User-Agent": "jobhunter-ai-learning-project/0.1"
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    data = response.json()

    # First item is often metadata.
    jobs = [item for item in data if isinstance(item, dict) and item.get("position")]

    query_terms = [term.lower() for term in query.split() if term.strip()]
    location_lower = location.lower().strip()

    matches = []

    for job in jobs:
        title = clean_text(job.get("position"))
        company = clean_text(job.get("company"))
        description = clean_text(job.get("description"))
        tags = job.get("tags") or []
        tags_text = " ".join(tags).lower()

        haystack = f"{title} {company} {description} {tags_text}".lower()

        query_score = sum(1 for term in query_terms if term in haystack)

        location_score = 0
        if location_lower in ["", "remote", "anywhere"]:
            location_score = 1
        elif location_lower in haystack:
            location_score = 1

        if query_score > 0 and location_score > 0:
            matches.append(
                {
                    "id": str(job.get("id") or job.get("slug") or len(matches)),
                    "title": title,
                    "company": company,
                    "url": job.get("url") or f"https://remoteok.com/remote-jobs/{job.get('id')}",
                    "tags": tags[:10],
                    "description": description[:2500],
                    "source": "RemoteOK",
                    "rough_keyword_score": query_score,
                }
            )

    matches = sorted(
        matches,
        key=lambda item: item["rough_keyword_score"],
        reverse=True,
    )

    return {
        "status": "success",
        "query": query,
        "location": location,
        "count": len(matches[:max_results]),
        "jobs": matches[:max_results],
    }


def score_job_against_resume(
    resume_text: str,
    job_description: str,
) -> dict[str, Any]:
    """
    Scores how well a job description matches a resume.

    Args:
        resume_text: Plain-text resume.
        job_description: Job description text.

    Returns:
        A heuristic match score with matching keywords and missing keywords.
    """
    resume_lower = resume_text.lower()
    job_lower = job_description.lower()

    important_terms = [
        "python", "fastapi", "django", "flask", "sql", "postgresql", "mysql",
        "redis", "docker", "kubernetes", "aws", "gcp", "azure", "rest",
        "graphql", "microservices", "pytest", "ci/cd", "linux", "backend",
        "api", "async", "distributed systems", "machine learning", "llm",
        "security", "authentication", "authorization", "terraform",
    ]

    job_terms = [term for term in important_terms if term in job_lower]
    matched = [term for term in job_terms if term in resume_lower]
    missing = [term for term in job_terms if term not in resume_lower]

    if not job_terms:
        score = 50
    else:
        score = round((len(matched) / len(job_terms)) * 100)

    return {
        "status": "success",
        "match_score_out_of_100": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "job_keywords_detected": job_terms,
    }


def create_tailoring_brief(
    resume_text: str,
    job_description: str,
) -> dict[str, Any]:
    """
    Creates a resume-tailoring brief without fabricating experience.

    Args:
        resume_text: Plain-text resume.
        job_description: Job description text.

    Returns:
        A tailoring brief with keywords to emphasize, likely gaps, and rewrite rules.
    """
    score = score_job_against_resume(resume_text, job_description)
    profile = extract_resume_profile(resume_text)

    return {
        "status": "success",
        "profile": profile,
        "match_analysis": score,
        "tailoring_rules": [
            "Do not invent employers, titles, degrees, dates, metrics, or tools.",
            "Only rephrase existing experience to better match the job.",
            "Prefer measurable bullets, but mark unknown metrics as placeholders.",
            "Use the job description's language when it accurately reflects the resume.",
            "Keep the resume ATS-friendly: simple headings, no tables, no graphics.",
        ],
    }