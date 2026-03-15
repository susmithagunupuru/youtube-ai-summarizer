from pathlib import Path
from typing import Optional

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


def get_transcript_for_youtube(youtube_url: str, work_dir: Path) -> str:
    """
    End-to-end helper:
    1) Try subtitles via youtube-transcript-api.
    2) If not available, raise a clear error (no external transcription).
    """
    subtitles = get_subtitles_with_api(youtube_url)
    if subtitles:
        return subtitles

    raise TranscriptError(
        "No subtitles are available for this video, and audio transcription is disabled."
    )

