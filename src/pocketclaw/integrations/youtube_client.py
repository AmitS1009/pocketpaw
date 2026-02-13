# YouTube Client — Client for fetching and searching YouTube video transcripts.
# Created: 2026-02-13
# Part of Advanced RAG & Semantic Search Integrations




import re
from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


class YouTubeClient:
    """Client for fetching and analyzing YouTube transcripts."""

    @staticmethod
    def extract_video_id(url: str) -> str | None:
        """Extracts the 11-character video ID from a YouTube URL."""
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        return match.group(1) if match else None

    @staticmethod
    def format_time(seconds: float) -> str:
        """Converts seconds into MM:SS format."""
        mins, secs = divmod(int(seconds), 60)
        return f"{mins}:{secs:02d}"

    async def get_transcript(self, video_id: str) -> list[dict[str, Any]]:
        """Fetches the raw transcript data with timestamps."""
        # Note: This is a synchronous call in the library, in a real async heavy app
        # we'd run this in an executor, but for this tool it's fast enough.
        return YouTubeTranscriptApi.get_transcript(video_id)

    async def search_transcript(self, video_id: str, query: str) -> str:
        """Searches the transcript for a specific keyword/query and returns timestamps."""
        try:
            transcript = await self.get_transcript(video_id)
            query = query.lower()
            results = []

            # Simple keyword search mimicking RAG retrieval
            for item in transcript:
                if query in item["text"].lower():
                    timestamp = self.format_time(item["start"])
                    # Clean up the text
                    text = item["text"].replace("\n", " ")
                    results.append(f"[{timestamp}] {text}")

            if not results:
                return f"No mentions of '{query}' found in the video."

            # Limit results so we don't blow up the LLM context window
            max_results = 15
            output = f"Found {len(results)} matches for '{query}'.\n\nTop matches:\n"
            output += "\n".join(results[:max_results])
            if len(results) > max_results:
                output += f"\n\n... and {len(results) - max_results} more."

            return output

        except Exception as e:
            raise RuntimeError(f"Could not search transcript: {str(e)}")

    async def get_full_text(self, video_id: str) -> str:
        """Gets the full transcript formatted as text."""
        try:
            transcript = await self.get_transcript(video_id)
            formatter = TextFormatter()
            text = formatter.format_transcript(transcript)

            # Context window protection (approx 20k chars)
            if len(text) > 20000:
                return (
                    text[:20000]
                    + "\n\n... [Transcript truncated due to length. Use 'search' action to find specific topics.]"
                )
            return text
        except Exception as e:
            raise RuntimeError(f"Could not fetch transcript: {str(e)}")
