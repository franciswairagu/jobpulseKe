"""Centralized prompt templates for the RAG system.

Provides templates for each question type, system prompts, and
context formatting utilities.
"""
from typing import Any


SYSTEM_PROMPT = (
    "You are JobPulse Assistant, an AI helper for the African tech job market. "
    "Answer questions about tech jobs, skills, careers, and market trends across Africa "
    "using ONLY the provided context. "
    "Rules:\n"
    "1. Base your answer ONLY on the provided context. Do not invent facts.\n"
    "2. If the context does not contain enough information, say so honestly.\n"
    "3. When listing skills or roles, cite the specific job postings where you found them.\n"
    "4. Be concise but thorough. Aim for 2-4 paragraphs.\n"
    "5. Use markdown formatting: bold for emphasis, bullet points for lists.\n"
    "6. Always end with a practical recommendation or next step."
)

FINETUNED_SYSTEM_PROMPT = (
    "You are JobPulse Assistant, a specialized AI for the African tech job market. "
    "You have been fine-tuned on job posting data from across Africa. "
    "Answer questions using the provided context from the JobPulse dataset. "
    "Be specific, cite job postings when relevant, and provide actionable advice."
)

QUESTION_TYPE_HINTS = {
    "skill_inquiry": "Focus on skill demand, frequency across jobs, and learning recommendations.",
    "job_search": "List the most relevant job postings with company, location, and key skills.",
    "career_advice": "Provide career progression advice based on the retrieved roles and seniority levels.",
    "market_intelligence": "Summarize market trends, top skills, and hiring patterns from the data.",
    "salary_compensation": "Note any salary or compensation data found in the context.",
    "company_industry": "Focus on which companies are hiring and what roles they offer.",
    "location_geography": "Focus on geographic distribution of jobs and location-specific insights.",
    "general": "Provide a comprehensive answer covering all relevant aspects.",
}


def build_rag_prompt(
    question: str,
    question_type: str = "general",
    context: str = "",
) -> str:
    """Build the user prompt for the LLM."""
    hint = QUESTION_TYPE_HINTS.get(question_type, QUESTION_TYPE_HINTS["general"])

    parts = []
    if context:
        parts.append(f"Context:\n{context}\n")
    parts.append(f"Question type: {question_type}")
    parts.append(f"Guidance: {hint}\n")
    parts.append(f"User question: {question}\n")
    parts.append("Using the context above, provide a grounded, helpful answer.")

    return "\n".join(parts)


def format_retrieved_context(results: list[dict[str, Any]]) -> str:
    """Format retrieved results into a context block for the LLM."""
    blocks = []
    for i, result in enumerate(results):
        text = result.get("text", result.get("rag_document", ""))
        score = result.get("score", 0.0)
        metadata = result.get("metadata", {})

        title = metadata.get("job_title", "Unknown")
        company = metadata.get("company", "Unknown")
        location = metadata.get("location", "")
        skills = metadata.get("skills", [])

        header = f"[Result {i + 1} | score={score:.3f}] {title} at {company}"
        if location:
            header += f" - {location}"

        body = text
        if skills and isinstance(skills, list):
            body += f"\nSkills: {', '.join(skills[:10])}"

        blocks.append(f"{header}\n{body}")

    return "\n\n---\n\n".join(blocks)


def build_market_intelligence_prompt(
    question: str,
    context: str = "",
    market_data: dict | None = None,
) -> str:
    """Build a specialized prompt for market intelligence questions."""
    parts = []
    if context:
        parts.append(f"Context:\n{context}\n")

    if market_data:
        parts.append("Market Data:")
        if market_data.get("skills"):
            parts.append(f"Top skills: {', '.join(market_data['skills'][:10])}")
        if market_data.get("total_jobs"):
            parts.append(f"Total jobs analyzed: {market_data['total_jobs']}")
        parts.append("")

    parts.append(f"Question: {question}")
    parts.append("Provide a market intelligence answer based on the data above.")

    return "\n".join(parts)
