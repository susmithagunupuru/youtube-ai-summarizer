import os
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv

from .transcript import get_transcript_for_youtube, TranscriptError
from .summarizer import summarize_transcript_with_openai, SummarizationError


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv()


class SummarizeRequest(BaseModel):
    youtube_url: HttpUrl


class SummaryResult(BaseModel):
    key_points: List[str]
    short_summary: str
    topics: List[str]


app = FastAPI(title="YouTube AI Summarizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/summarize", response_model=SummaryResult)
def summarize_video(payload: SummarizeRequest) -> SummaryResult:
    """
    Full pipeline:
    1. Accept a YouTube URL.
    2. Try subtitles via youtube-transcript-api.
    3. If not available, download audio with yt-dlp and send to AssemblyAI.
    4. Clean transcript text.
    5. Summarize with OpenAI into key points, summary, topics.
    """
    youtube_url = str(payload.youtube_url)

    try:
        transcript_text = get_transcript_for_youtube(youtube_url, DATA_DIR)
    except TranscriptError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Failed to get transcript: {exc}") from exc

    # Basic cleaning: collapse excessive whitespace.
    cleaned = " ".join(transcript_text.split())

    try:
        summary_data: Dict[str, Any] = summarize_transcript_with_openai(cleaned)
    except SummarizationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Failed to summarize: {exc}") from exc

    return SummaryResult(
        key_points=summary_data.get("key_points", []),
        short_summary=summary_data.get("short_summary", ""),
        topics=summary_data.get("topics", []),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

