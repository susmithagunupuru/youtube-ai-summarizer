import os
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
from yt_dlp import YoutubeDL


load_dotenv()


ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
ASSEMBLYAI_API_URL = "https://api.assemblyai.com/v2"


class TranscriptError(Exception):
    """Custom error for transcript-related problems."""


def _get_assemblyai_headers() -> dict:
    if not ASSEMBLYAI_API_KEY:
        raise TranscriptError("ASSEMBLYAI_API_KEY is not set in the environment.")
    return {"authorization": ASSEMBLYAI_API_KEY, "content-type": "application/json"}


def _extract_video_id(url: str) -> str:
    """Extract a YouTube video ID from common URL formats."""
    # youtube_transcript_api accepts both full URLs and IDs, but we normalize for clarity
    if "v=" in url:
        # Typical watch URL
        return url.split("v=")[1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    # Fallback: assume the whole string might be an ID
    return url


def get_subtitles_with_api(youtube_url: str) -> Optional[str]:
    """
    Try to fetch subtitles using youtube-transcript-api.
    Returns the transcript text if available, otherwise None.
    """
    video_id = _extract_video_id(youtube_url)

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        return None
    except Exception as exc:  # pylint: disable=broad-except
        raise TranscriptError(f"Failed to fetch subtitles: {exc}") from exc

    lines = [entry["text"].strip() for entry in transcript if entry.get("text")]
    return "\n".join(lines)


def download_audio_with_ytdlp(youtube_url: str, output_dir: Path) -> Path:
    """
    Download the audio track of a YouTube video using yt-dlp.
    Returns the path to the downloaded audio file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    # Use a simple naming scheme; yt-dlp will pick the right extension.
    out_template = str(output_dir / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        filename = ydl.prepare_filename(info)

    return Path(filename)


def upload_audio_to_assemblyai(audio_path: Path) -> str:
    """Upload a local audio file to AssemblyAI and return the upload URL."""
    if not audio_path.exists():
        raise TranscriptError(f"Audio file not found: {audio_path}")

    headers = {"authorization": ASSEMBLYAI_API_KEY}
    with audio_path.open("rb") as f:
        response = requests.post(f"{ASSEMBLYAI_API_URL}/upload", headers=headers, data=f, timeout=60)

    if response.status_code != 200:
        raise TranscriptError(f"Error uploading audio: {response.text}")

    return response.json()["upload_url"]


def request_assemblyai_transcript(audio_url: str) -> str:
    """Create a new AssemblyAI transcription job and return its ID."""
    payload = {"audio_url": audio_url}
    response = requests.post(
        f"{ASSEMBLYAI_API_URL}/transcript",
        json=payload,
        headers=_get_assemblyai_headers(),
        timeout=30,
    )
    if response.status_code != 200:
        raise TranscriptError(f"Error creating transcript: {response.text}")
    return response.json()["id"]


def poll_assemblyai_transcript(transcript_id: str, poll_interval: int = 5) -> str:
    """Poll AssemblyAI until the transcript is ready, then return its text."""
    endpoint = f"{ASSEMBLYAI_API_URL}/transcript/{transcript_id}"

    while True:
        response = requests.get(endpoint, headers=_get_assemblyai_headers(), timeout=30)
        if response.status_code != 200:
            raise TranscriptError(f"Error getting transcript: {response.text}")

        data = response.json()
        status = data.get("status")

        if status == "completed":
            return data.get("text", "")
        if status == "error":
            raise TranscriptError(f"Transcription failed: {data.get('error')}")

        time.sleep(poll_interval)


def get_transcript_for_youtube(youtube_url: str, work_dir: Path) -> str:
    """
    End-to-end helper:
    1) Try subtitles via youtube-transcript-api.
    2) If not available, download audio with yt-dlp and transcribe with AssemblyAI.
    """
    # 1) Try subtitles
    subtitles = get_subtitles_with_api(youtube_url)
    if subtitles:
        return subtitles

    # 2) Fall back to audio + AssemblyAI
    audio_dir = work_dir / "audio"
    audio_path = download_audio_with_ytdlp(youtube_url, audio_dir)

    upload_url = upload_audio_to_assemblyai(audio_path)
    transcript_id = request_assemblyai_transcript(upload_url)
    transcript_text = poll_assemblyai_transcript(transcript_id)

    return transcript_text

