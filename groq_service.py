from typing import List, Dict
import json
import os
import re
from groq import Groq
from pydantic import BaseModel
import tempfile

# ─────────────────────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────────────────────
class InterviewQuestion(BaseModel):
    id: str
    question: str
    type: str
    estimated_time_min: int
    difficulty: str


class EvaluationResult(BaseModel):
    scores: Dict[str, int]
    overall_score: float
    strengths: str
    weaknesses: str
    improvements: List[str]
    ideal_answer_example: str


# ─────────────────────────────────────────────────────────────
# GROQ CLIENT
# ─────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY environment variable not set")

client = Groq(api_key=GROQ_API_KEY)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def safe_json_loads(text: str) -> dict | list:
    """More robust JSON parsing - handles common LLM mistakes"""
    text = text.strip()
    text = re.sub(r'^```json?\s*|\s*```$', '', text, flags=re.IGNORECASE | re.MULTILINE)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        raise ValueError(f"Failed to parse JSON from:\n{text[:400]}")


# ─────────────────────────────────────────────────────────────
# PROJECT QUESTIONS GENERATION
# ─────────────────────────────────────────────────────────────
def generate_project_questions(
    resume_text: str,
    difficulty: str = "medium",
    count: int = 4,
    model: str = "llama-3.3-70b-versatile"
) -> List[InterviewQuestion]:
    if not resume_text or len(resume_text.strip()) < 100:
        return []

    user_prompt = f"""
Generate **exactly {count}** {difficulty}-level interview questions.
STRICTLY based on the **projects and real experiences** mentioned in the resume.

Resume:
{resume_text[:5500]}

VERY IMPORTANT RULES:
- ONLY create questions about things **clearly mentioned** in the resume
- Focus on: technical decisions, challenges, architecture, trade-offs, scaling, impact
- Do NOT invent projects or technologies that are not in the resume
- Return **ONLY** a valid JSON array — nothing else, no explanations, no markdown

Format:
[
  {{
    "id": "q1",
    "question": "very specific question...",
    "type": "project_deep_dive",
    "estimated_time_min": 8,
    "difficulty": "{difficulty}"
  }},
  ...
]
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You return ONLY valid JSON array. No text before or after the JSON."},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.15,
            max_tokens=1400,
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content.strip()
        parsed = safe_json_loads(raw_content)

        if isinstance(parsed, list):
            questions_data = parsed
        elif isinstance(parsed, dict):
            questions_data = (
                parsed.get("questions", [])
                or list(parsed.values())[0]
                if isinstance(list(parsed.values())[0], list)
                else []
            )
        else:
            questions_data = []

        questions = []
        for q in questions_data[:count]:
            try:
                q.setdefault("type", "project_deep_dive")
                q.setdefault("estimated_time_min", 8)
                q.setdefault("difficulty", difficulty)
                questions.append(InterviewQuestion(**q))
            except Exception:
                continue

        return questions or [
            InterviewQuestion(
                id="fallback",
                question="Tell me about your most significant project mentioned in your resume.",
                type="project_deep_dive",
                estimated_time_min=6,
                difficulty=difficulty
            )
        ]

    except Exception as e:
        print(f"Question generation error: {str(e)}")
        return [
            InterviewQuestion(
                id="error_fallback",
                question="Describe your strongest technical project experience.",
                type="project_deep_dive",
                estimated_time_min=5,
                difficulty=difficulty
            )
        ]


# ─────────────────────────────────────────────────────────────
# ANSWER EVALUATION
# ─────────────────────────────────────────────────────────────
def evaluate_answer(
    question: str,
    answer: str,
    model: str = "llama-3.3-70b-versatile"
) -> EvaluationResult:
    prompt = f"""
You are a strict technical interviewer.

Question:
{question}

Candidate answer:
{answer[:2000]}  # ← truncate very long answers to avoid token limits

Evaluate strictly based on:
- Technical accuracy
- Clarity & structure
- Relevance to question
- Depth of explanation

Return **ONLY** valid JSON object. Nothing else. Do NOT add explanations, markdown, or code blocks.

Example valid output:
{{
  "scores": {{
    "technical_accuracy": 7,
    "clarity": 6,
    "relevance": 8,
    "depth": 5
  }},
  "overall_score": 6.5,
  "strengths": "Clear points...",
  "weaknesses": "Missing important detail...",
  "improvements": ["Add specific example", "Explain trade-off"],
  "ideal_answer_example": "Better structured answer..."
}}
"""

    try:
        print("\n[DEBUG] Sending evaluation prompt...")
        print(f"[DEBUG] Question length: {len(question)} | Answer length: {len(answer)}")

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        raw = response.choices[0].message.content.strip()
        print("[DEBUG] Raw model response:")
        print(raw[:500] + "..." if len(raw) > 500 else raw)  # truncate for console

        data = safe_json_loads(raw)

        if isinstance(data, dict):
            print("[DEBUG] Parsed data successfully")
            return EvaluationResult(**data)
        else:
            raise ValueError(f"Model returned non-dict: {type(data)}")

    except Exception as e:
        print(f"[ERROR] Evaluation failed: {str(e)}")
        print(f"[ERROR] Raw content was: {raw if 'raw' in locals() else 'No response'}")
        return EvaluationResult(
            scores={"technical_accuracy": 0, "clarity": 0, "relevance": 0, "depth": 0},
            overall_score=0.0,
            strengths="Evaluation failed — check console/logs for details",
            weaknesses=str(e),
            improvements=[],
            ideal_answer_example="N/A (error occurred)"
        )


# ─────────────────────────────────────────────────────────────
# VOICE TRANSCRIPTION (NEW)
# ─────────────────────────────────────────────────────────────
def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes using Groq Whisper API
    Returns transcribed text or empty string on failure
    """
    if not audio_bytes:
        return ""

    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_path = tmp_file.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="text",
                language="en",              # ← change if needed
                temperature=0.0
            )
        return transcription.strip()

    except Exception as e:
        print(f"Transcription error: {str(e)}")
        return ""

    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass