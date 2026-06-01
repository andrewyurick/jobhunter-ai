import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

load_dotenv()

from app.adk_runtime import call_agent  # noqa: E402


DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "local_user")

app = FastAPI(
    title="JobHunter AI",
    description="Gemini + Google ADK + FastAPI job search and resume tailoring agent.",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = DEFAULT_USER_ID
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    user_id: str
    response: str


class AnalyzeResumeRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    user_id: str = DEFAULT_USER_ID
    session_id: Optional[str] = None


class SearchJobsRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    target_role: str = Field(..., examples=["Python FastAPI Backend Engineer"])
    location: str = Field(default="remote")
    user_id: str = DEFAULT_USER_ID
    session_id: Optional[str] = None


class TailorResumeRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=50)
    user_id: str = DEFAULT_USER_ID
    session_id: Optional[str] = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    result = await call_agent(
        message=request.message,
        user_id=request.user_id,
        session_id=request.session_id,
    )
    return ChatResponse(**result)


@app.post("/resume/analyze", response_model=ChatResponse)
async def analyze_resume(request: AnalyzeResumeRequest) -> ChatResponse:
    message = f"""
Analyze this resume for backend/software engineering job search.

Resume:
{request.resume_text}
"""
    result = await call_agent(
        message=message,
        user_id=request.user_id,
        session_id=request.session_id,
    )
    return ChatResponse(**result)


@app.post("/jobs/search", response_model=ChatResponse)
async def search_jobs(request: SearchJobsRequest) -> ChatResponse:
    message = f"""
Find jobs that match this resume.

Target role:
{request.target_role}

Location preference:
{request.location}

Resume:
{request.resume_text}

Return:
- Top job matches
- Why each job fits
- Possible gaps
- Which one I should tailor my resume for first
"""
    result = await call_agent(
        message=message,
        user_id=request.user_id,
        session_id=request.session_id,
    )
    return ChatResponse(**result)


@app.post("/resume/tailor", response_model=ChatResponse)
async def tailor_resume(request: TailorResumeRequest) -> ChatResponse:
    message = f"""
Tailor my resume for this job.

Rules:
- Do not invent experience.
- Keep it ATS-friendly.
- Use Markdown.
- Add [ADD METRIC IF TRUE] where a real metric would strengthen a bullet.
- After the resume, explain what changed.

Resume:
{request.resume_text}

Job description:
{request.job_description}
"""
    result = await call_agent(
        message=message,
        user_id=request.user_id,
        session_id=request.session_id,
    )
    return ChatResponse(**result)