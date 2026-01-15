# rag_wrapper.py
from rag_store import ResumeRAGStore
from groq_service import generate_project_questions

rag_store = ResumeRAGStore()


def generate_project_questions_rag(
    resume_text: str,
    difficulty: str = "medium",
    count: int = 4
):
    """
    RAG-enhanced wrapper for generate_project_questions
    (Original function remains unchanged)
    """

    # Build vector index
    rag_store.build_index(resume_text)

    # Retrieve most relevant resume/JD sections
    retrieved_context = rag_store.retrieve(
        query="technical projects architecture challenges design decisions impact",
        top_k=6
    )

    augmented_context = f"""
RETRIEVED CONTEXT (MOST RELEVANT SECTIONS):
{retrieved_context}

FULL SOURCE DOCUMENT:
{resume_text}
"""

    return generate_project_questions(
        resume_text=augmented_context,
        difficulty=difficulty,
        count=count
    )
