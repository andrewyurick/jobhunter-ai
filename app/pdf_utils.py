from io import BytesIO
from pathlib import Path
import re
import textwrap
from uuid import uuid4

from pypdf import PdfReader

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.enums import TA_LEFT


GENERATED_DIR = Path("generated")
GENERATED_DIR.mkdir(exist_ok=True)


def extract_pdf_text(file_bytes: bytes) -> str:
    """
    Extracts text from a text-based resume PDF.

    This will not work well for scanned image PDFs.
    """
    reader = PdfReader(BytesIO(file_bytes))
    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return "\n\n".join(pages).strip()


def clean_markdown_for_pdf(text: str) -> str:
    """
    Keeps basic Markdown readable when converted to PDF paragraphs.
    """
    text = text.replace("\r\n", "\n")
    text = text.replace("\t", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def markdown_line_to_html(line: str) -> str:
    """
    Converts a small subset of Markdown to ReportLab-friendly HTML.
    """
    line = line.strip()

    # Escape unsafe HTML-ish characters first.
    line = (
        line.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    # Bold: **text**
    line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)

    return line


def build_tailored_resume_pdf(
    tailored_resume_markdown: str,
    original_filename: str | None = None,
) -> Path:
    """
    Creates a formatted PDF from the tailored resume Markdown returned by the agent.
    """
    safe_stem = "tailored_resume"

    if original_filename:
        candidate = Path(original_filename).stem
        candidate = re.sub(r"[^a-zA-Z0-9_-]+", "_", candidate).strip("_")
        if candidate:
            safe_stem = f"{candidate}_tailored"

    output_path = GENERATED_DIR / f"{safe_stem}_{uuid4().hex[:8]}.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ResumeTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_LEFT,
        spaceAfter=10,
    )

    heading_style = ParagraphStyle(
        "ResumeHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "ResumeBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=12,
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "ResumeBullet",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-8,
        spaceAfter=3,
    )

    note_style = ParagraphStyle(
        "ResumeNote",
        parent=styles["BodyText"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=11,
        spaceBefore=8,
        textColor="#555555",
    )

    content = clean_markdown_for_pdf(tailored_resume_markdown)

    story = []

    lines = content.split("\n")
    first_heading_used = False

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            story.append(Spacer(1, 5))
            continue

        # Page break marker, optional.
        if line.strip() == "---PAGE BREAK---":
            story.append(PageBreak())
            continue

        # Markdown heading handling.
        if line.startswith("# "):
            text = markdown_line_to_html(line[2:])
            story.append(Paragraph(text, title_style))
            first_heading_used = True
            continue

        if line.startswith("## "):
            text = markdown_line_to_html(line[3:])
            story.append(Paragraph(text, heading_style))
            continue

        if line.startswith("### "):
            text = markdown_line_to_html(line[4:])
            story.append(Paragraph(text, heading_style))
            continue

        # Bullet handling.
        if line.startswith("- ") or line.startswith("* "):
            text = markdown_line_to_html(line[2:])
            story.append(Paragraph(f"- {text}", bullet_style))
            continue

        # If the first non-empty line is likely the candidate name,
        # make it title-style.
        if not first_heading_used and len(line.split()) <= 6:
            text = markdown_line_to_html(line)
            story.append(Paragraph(text, title_style))
            first_heading_used = True
            continue

        text = markdown_line_to_html(line)

        # Soft-wrap very long unbroken lines.
        if len(text) > 130:
            wrapped = "<br/>".join(textwrap.wrap(text, width=120))
            story.append(Paragraph(wrapped, body_style))
        else:
            story.append(Paragraph(text, body_style))

    story.append(
        Paragraph(
            "Generated by JobHunter AI. Review carefully before submitting.",
            note_style,
        )
    )

    doc.build(story)
    return output_path