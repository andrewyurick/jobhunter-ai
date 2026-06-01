# JobHunter AI

A Google ADK + Gemini + FastAPI app that helps find jobs and tailor resumes.

## Features

- Analyze resume text
- Search RemoteOK jobs
- Score resume/job fit
- Tailor resume to a job description
- Serve everything through FastAPI
- Use Gemini through Google ADK

## Setup

Use Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload