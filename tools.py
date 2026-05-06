# tools.py

from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import pypdf
import io
import re

# -------------------------------------------------
# Tool 1: PDF Parsing Tool
# -------------------------------------------------

class PDFParsingInput(BaseModel):
    file_bytes: bytes = Field(
        description="The raw bytes of the PDF file to be parsed"
    )

@tool(args_schema=PDFParsingInput)
def parse_pdf_resume(file_bytes: bytes) -> str:
    \"\"\"
    Parses a PDF resume and extracts its text content.
    Use this to convert an uploaded PDF resume into text before analysis.
    \"\"\"
    pdf_file = io.BytesIO(file_bytes)
    reader = pypdf.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()


# -------------------------------------------------
# Tool 2: Skill Extraction & Match Scoring
# -------------------------------------------------

class MatchScoreInput(BaseModel):
    resume_text: str = Field(
        description="The full extracted text of the candidate's resume"
    )
    job_description: str = Field(
        description="The job description or requirements to evaluate against"
    )

@tool(args_schema=MatchScoreInput)
def calculate_match_score(resume_text: str, job_description: str) -> dict:
    \"\"\"
    Analyzes a candidate's resume against a job description.
    Returns a match score (0-100), matched skills, and missing skills.
    Use this as the core evaluation tool for a single candidate.
    \"\"\"
    # Extract meaningful keywords (filter out short/common words)
    stop_words = {"the", "a", "an", "and", "or", "in", "of", "to", "for", "with",
                  "is", "are", "was", "be", "have", "has", "at", "on", "as", "by",
                  "that", "this", "it", "its", "from", "we", "our", "you", "their"}

    def extract_keywords(text: str) -> set:
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\+\#\.]{1,30}\b', text)
        return {w.lower() for w in words if w.lower() not in stop_words and len(w) > 2}

    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_description)

    if not job_keywords:
        return {"score": 0, "matched": [], "missing": [], "verdict": "No job keywords found."}

    matched = sorted(resume_keywords & job_keywords)
    missing = sorted(job_keywords - resume_keywords)

    score = round((len(matched) / len(job_keywords)) * 100, 1)

    if score >= 70:
        verdict = "Strong Match – Recommend for interview."
    elif score >= 40:
        verdict = "Partial Match – Consider if critical skills are present."
    else:
        verdict = "Weak Match – Candidate likely does not meet requirements."

    print(f"DEBUG: calculate_match_score called → score={score}, matched={len(matched)}, missing={len(missing)}")

    return {
        "score": score,
        "matched_skills": matched[:20],   # top 20 to avoid context overflow
        "missing_skills": missing[:20],
        "verdict": verdict
    }

# -------------------------------------------------
# Tool 3: Knowledge Base RAG Tool
# -------------------------------------------------

from rag_pipeline import search_knowledge_base

class GuidelinesInput(BaseModel):
    query: str = Field(
        description="The specific policy, guideline, or requirement to search for."
    )

@tool(args_schema=GuidelinesInput)
def search_hiring_guidelines(query: str) -> str:
    \"\"\"
    Searches the GlobalTech corporate HR guidelines and policies.
    Use this to retrieve exact rules for candidate evaluation, such as degree requirements,
    experience levels, diversity policies, or required skills.
    \"\"\"
    print(f"DEBUG: RAG search triggered for query: {query}")
    return search_knowledge_base(query)
