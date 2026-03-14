import os
from typing import Any, Dict, List

from dotenv import load_dotenv
import google.generativeai as genai


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class SummarizationError(Exception):
    """Custom error for summarization-related problems."""


def summarize_transcript_with_openai(transcript_text: str) -> Dict[str, Any]:
    """
    Summarize the transcript text using Google Gemini.

    Returns a dict with:
      - key_points: List[str]
      - short_summary: str
      - topics: List[str]
    """
    if not GEMINI_API_KEY:
        raise SummarizationError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set in the environment.")

    prompt = (
        "You are a helpful assistant that summarizes YouTube videos.\n"
        "You will receive a video transcript. Read it carefully and respond ONLY in JSON "
        "with the following keys:\n"
        "  - key_points: an array of 3-7 bullet point strings capturing the main ideas\n"
        "  - short_summary: a concise paragraph (3-6 sentences) summarizing the video\n"
        "  - topics: an array of short topic strings (1-3 words each)\n\n"
        "Transcript:\n"
        "-----\n"
        f"{transcript_text}\n"
        "-----\n\n"
        "Remember: respond with valid JSON only, no extra commentary."
    )

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        content = response.text or ""
    except Exception as exc:  # pylint: disable=broad-except
        raise SummarizationError(f"Gemini API error: {exc}") from exc

    # Try to parse JSON; fall back to a simple structure if parsing fails.
    import json

    try:
        data = json.loads(content)
        key_points = data.get("key_points") or []
        short_summary = data.get("short_summary") or ""
        topics = data.get("topics") or []
    except Exception:
        key_points = [content.strip()]
        short_summary = content.strip()
        topics: List[str] = []

    return {
        "key_points": key_points,
        "short_summary": short_summary,
        "topics": topics,
    }

