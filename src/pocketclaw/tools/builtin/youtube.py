import logging
from typing import Any

from pocketclaw.tools.protocol import BaseTool

logger = logging.getLogger(__name__)


class YouTubeAnalysisTool(BaseTool):
    """Analyze YouTube videos, extract transcripts, and search for specific topics."""

    @property
    def name(self) -> str:
        return "youtube_analyzer"

    @property
    def description(self) -> str:
        return (
            "Analyze YouTube videos. Actions: 'transcript' (get full text) or 'search' (find keywords). "
            "Use 'transcript' to summarize a video. "
            "Use 'search' to find exact timestamps where a topic is discussed."
        )

    @property
    def trust_level(self) -> str:
        return "standard"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full YouTube video URL",
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'transcript' or 'search' (default: transcript)",
                },
                "query": {
                    "type": "string",
                    "description": "Keyword or topic to search for (required if action is 'search')",
                },
            },
            "required": ["url"],
        }

    async def execute(self, url: str, action: str = "transcript", query: str | None = None) -> str:
        valid_actions = {"transcript", "search"}
        if action not in valid_actions:
            return self._error(f"Unknown action '{action}'. Valid: {', '.join(valid_actions)}")

        try:
            # Importing the client we just built
            from pocketclaw.integrations.youtube_client import YouTubeClient

            client = YouTubeClient()
            video_id = client.extract_video_id(url)

            if not video_id:
                return self._error("Invalid YouTube URL provided. Could not extract Video ID.")

            if action == "search":
                if not query:
                    return self._error(
                        "You must provide a 'query' parameter when using the 'search' action."
                    )
                return await client.search_transcript(video_id, query)

            # Default: get full transcript
            result = await client.get_full_text(video_id)
            return f"Transcript successfully extracted for video {video_id}:\n\n{result}"

        except RuntimeError as e:
            return self._error(str(e))
        except Exception as e:
            return self._error(
                f"YouTube analysis failed: {e}. Video might not have closed captions."
            )
