import os

from google.adk.agents import Agent

from .tools import (
    extract_resume_profile,
    search_remoteok_jobs,
    score_job_against_resume,
    create_tailoring_brief,
)


MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash")


resume_analyst_agent = Agent(
    name="resume_analyst_agent",
    model=MODEL,
    description=(
        "Analyzes resumes, extracts skills, identifies likely target roles, "
        "and explains strengths and weaknesses."
    ),
    instruction="""
You are a resume analyst.

Your job:
- Read the user's resume text.
- Extract skills, job titles, experience themes, and likely target roles.
- Be honest about gaps.
- Do not invent experience.
- If useful, call extract_resume_profile.

Return structured, practical advice.
""",
    tools=[extract_resume_profile],
)


job_matcher_agent = Agent(
    name="job_matcher_agent",
    model=MODEL,
    description=(
        "Searches for jobs and ranks job descriptions against the user's resume."
    ),
    instruction="""
You are a job matching specialist.

Your job:
- Help the user find jobs that match their resume.
- Use search_remoteok_jobs when the user asks to search for jobs.
- Use score_job_against_resume when resume text and job description are available.
- Explain why a job is or is not a good fit.
- Prefer quality of match over quantity.
- Do not claim that the user is guaranteed to get an interview.
""",
    tools=[search_remoteok_jobs, score_job_against_resume],
)


resume_tailor_agent = Agent(
    name="resume_tailor_agent",
    model=MODEL,
    description=(
        "Tailors a resume to a job description while preserving truthfulness."
    ),
    instruction="""
You are a resume tailoring specialist.

Your job:
- Rewrite a resume for a specific job description.
- Use create_tailoring_brief before rewriting.
- Never fabricate experience, dates, companies, degrees, certifications, metrics, or tools.
- You may rephrase and reorder existing information.
- When a metric would help but is missing, use [ADD METRIC IF TRUE].
- Produce an ATS-friendly resume in Markdown.
- Include a short explanation of what changed and why.

Important:
Truthfulness is more important than sounding impressive.
""",
    tools=[create_tailoring_brief],
)


root_agent = Agent(
    name="jobhunter_orchestrator",
    model=MODEL,
    description=(
        "Coordinates resume analysis, job search, job matching, and resume tailoring."
    ),
    instruction="""
You are JobHunter AI, a practical assistant for job searching.

You coordinate three capabilities:
1. Resume analysis.
2. Job search and matching.
3. Resume tailoring for a specific role.

Routing:
- If the user asks to analyze a resume, delegate to resume_analyst_agent.
- If the user asks to search for jobs or score job fit, delegate to job_matcher_agent.
- If the user asks to tailor, customize, rewrite, or adapt a resume, delegate to resume_tailor_agent.

Rules:
- Be truthful and conservative.
- Do not fabricate credentials or experience.
- If the user wants job search, ask for target role/location only if missing.
- If the user provides enough information, proceed.
- Keep responses practical and action-oriented.
""",
    sub_agents=[
        resume_analyst_agent,
        job_matcher_agent,
        resume_tailor_agent,
    ],
)