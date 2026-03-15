from pathlib import Path
from typing import Optional


import subprocess
import whisper
import yt_dlp
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)



class TranscriptError(Exception):
    """Custom error for transcript-related problems."""


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
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=["en"])
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        return None
    except Exception as exc:  # pylint: disable=broad-except
        raise TranscriptError(f"Failed to fetch subtitles: {exc}") from exc

    # `transcript` is a FetchedTranscript containing FetchedTranscriptSnippet
    # objects with `.text` attributes.
    lines = [snippet.text.strip() for snippet in transcript if getattr(snippet, "text", "").strip()]
    return "\n".join(lines)



def download_audio(youtube_url: str, work_dir: Path) -> Path:
    """Download audio with yt-dlp to temp file."""
    video_id = _extract_video_id(youtube_url)
    audio_path = work_dir / f"{video_id}.%(ext)s"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(audio_path),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    
    # Find actual downloaded file
    for p in work_dir.glob(f"{video_id}.*"):
        if p.suffix in {'.wav', '.mp3', '.m4a'}:
            return p
    raise TranscriptError("Failed to download audio")


def get_transcript_for_youtube(youtube_url: str, work_dir: Path) -> str:
    """
    End-to-end helper:
    1) Try subtitles via youtube-transcript-api.
    2) Fallback: download audio → Whisper transcribe.
    """
    subtitles = get_subtitles_with_api(youtube_url)
    if subtitles:
        return subtitles

    try:
        audio_file = download_audio(youtube_url, work_dir)
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_file))
        return result["text"]
    except Exception as exc:
        raise TranscriptError(f"Audio transcription failed: {exc}")


