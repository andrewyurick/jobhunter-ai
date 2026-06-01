import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

from app.adk_runtime import call_agent  # noqa: E402
from app.pdf_utils import extract_pdf_text, build_tailored_resume_pdf  # noqa: E402


DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "local_user")

app = FastAPI(
    title="JobHunter AI",
    description="Gemini + Google ADK + FastAPI job search and resume tailoring agent.",
    version="0.2.0",
)

app.mount("/generated", StaticFiles(directory="generated"), name="generated")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = DEFAULT_USER_ID
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    user_id: str
    response: str


class TailorPdfResponse(BaseModel):
    session_id: str
    user_id: str
    response: str
    extracted_resume_preview: str
    pdf_url: str


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


@app.post("/resume/tailor-pdf", response_model=TailorPdfResponse)
async def tailor_resume_pdf(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    target_role: str = Form(default=""),
    user_id: str = Form(default=DEFAULT_USER_ID),
    session_id: Optional[str] = Form(default=None),
) -> TailorPdfResponse:
    """
    Upload a resume PDF and job description.
    The agent returns a tailored resume and the app generates a downloadable PDF.
    """
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="Missing uploaded file.")

    if not resume_file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    file_bytes = await resume_file.read()

    try:
        resume_text = extract_pdf_text(file_bytes)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read PDF: {exc}",
        ) from exc

    if len(resume_text) < 50:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not extract enough text from this PDF. "
                "If this is a scanned resume, use a text-based PDF or add OCR later."
            ),
        )

    message = f"""
You are tailoring a resume to a job description.

Return ONLY the tailored resume in clean Markdown.

Formatting rules:
- Start with the candidate name as a top-level heading if available.
- Use sections like Summary, Skills, Experience, Projects, Education.
- Use concise bullets.
- Keep it ATS-friendly.
- Do not use tables.
- Do not invent employers, dates, degrees, titles, certifications, tools, or metrics.
- You may reword, reorganize, and emphasize true existing experience.
- If a metric would help but is not present, write [ADD METRIC IF TRUE].
- Do not include a long explanation after the resume.
- Do not include cover letter content.

Target role:
{target_role or "Not specified"}

Job description:
{job_description}

Original resume text extracted from PDF:
{resume_text}
"""

    result = await call_agent(
        message=message,
        user_id=user_id,
        session_id=session_id,
    )

    if result["response"].startswith("Agent error:") or "Gemini is currently overloaded" in result["response"]:
        raise HTTPException(
            status_code=502,
            detail=result["response"],
        )

    pdf_path = build_tailored_resume_pdf(
        tailored_resume_markdown=result["response"],
        original_filename=resume_file.filename,
    )

    return TailorPdfResponse(
        session_id=result["session_id"],
        user_id=result["user_id"],
        response=result["response"],
        extracted_resume_preview=resume_text[:1000],
        pdf_url=f"/generated/{pdf_path.name}",
    )