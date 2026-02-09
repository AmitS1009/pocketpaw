# File-based memory store implementation.
# Created: 2026-02-02 - Memory System
# Updated: 2026-02-09 - Fixed UUID collision, daily file loading, search, persistent delete
#
# Stores memories as markdown files for human readability:
# - ~/.pocketclaw/memory/MEMORY.md     (long-term)
# - ~/.pocketclaw/memory/2026-02-02.md (daily)
# - ~/.pocketclaw/memory/sessions/     (session JSON files)

import asyncio
import json
import re
import uuid
from datetime import date, datetime
from pathlib import Path

from pocketclaw.memory.protocol import MemoryEntry, MemoryType

# Stop words excluded from word-overlap search scoring
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "about",
        "like",
        "through",
        "after",
        "over",
        "between",
        "out",
        "against",
        "during",
        "without",
        "before",
        "under",
        "around",
        "among",
        "and",
        "but",
        "or",
        "nor",
        "not",
        "so",
        "yet",
        "both",
        "either",
        "neither",
        "each",
        "every",
        "all",
        "any",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "only",
        "own",
        "same",
        "than",
        "too",
        "very",
        "just",
        "because",
        "if",
        "when",
        "where",
        "how",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "he",
        "him",
        "his",
        "she",
        "her",
        "it",
        "its",
        "they",
        "them",
        "their",
    }
)


def _make_deterministic_id(path: Path, header: str, body: str) -> str:
    """Generate a deterministic UUID5 from path, header, AND body content."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{path}:{header}:{body}"))


def _tokenize(text: str) -> set[str]:
    """Lowercase, split on non-alpha, strip stop words."""
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    return words - _STOP_WORDS


class FileMemoryStore:
    """
    File-based memory store.

    Human-readable markdown for long-term and daily memories.
    JSON for session memories (machine-readable).
    """

    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or (Path.home() / ".pocketclaw" / "memory")
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Sub-directories
        self.sessions_path = self.base_path / "sessions"
        self.sessions_path.mkdir(exist_ok=True)

        # File paths
        self.long_term_file = self.base_path / "MEMORY.md"

        # In-memory index for fast lookup
        self._index: dict[str, MemoryEntry] = {}
        self._session_write_locks: dict[str, asyncio.Lock] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load existing memories into index."""
        # Load long-term memories
        if self.long_term_file.exists():
            self._parse_markdown_file(self.long_term_file, MemoryType.LONG_TERM)

        # Load ALL daily files (not just today's)
        for daily_file in sorted(
            self.base_path.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md")
        ):
            self._parse_markdown_file(daily_file, MemoryType.DAILY)

    def _parse_markdown_file(self, path: Path, memory_type: MemoryType) -> None:
        """Parse a markdown file into memory entries."""
        content = path.read_text(encoding="utf-8")

        # Split by headers (## or ###)
        sections = re.split(r"\n(?=##+ )", content)

        for section in sections:
            if not section.strip():
                continue

            # Extract header and content
            lines = section.strip().split("\n")
            header = lines[0].lstrip("#").strip()
            body = "\n".join(lines[1:]).strip()

            if body:
                entry_id = _make_deterministic_id(path, header, body)
                self._index[entry_id] = MemoryEntry(
                    id=entry_id,
                    type=memory_type,
                    content=body,
                    tags=self._extract_tags(body),
                    metadata={"header": header, "source": str(path)},
                )

    def _extract_tags(self, content: str) -> list[str]:
        """Extract #tags from content."""
        return re.findall(r"#(\w+)", content)

    def _get_daily_file(self, d: date) -> Path:
        """Get the path for a daily notes file."""
        return self.base_path / f"{d.isoformat()}.md"

    def _get_session_file(self, session_key: str) -> Path:
        """Get the path for a session file."""
        safe_key = session_key.replace(":", "_").replace("/", "_")
        return self.sessions_path / f"{safe_key}.json"

    # =========================================================================
    # MemoryStoreProtocol Implementation
    # =========================================================================

    async def save(self, entry: MemoryEntry) -> str:
        """Save a memory entry."""
        if entry.type == MemoryType.SESSION:
            # Session entries use random UUIDs (no collision issue)
            if not entry.id:
                entry.id = str(uuid.uuid4())
            entry.updated_at = datetime.now()
            self._index[entry.id] = entry
            await self._save_session_entry(entry)
            return entry.id

        # For LONG_TERM and DAILY: compute deterministic ID from content
        header = entry.metadata.get("header", "Memory")
        if entry.type == MemoryType.LONG_TERM:
            target_path = self.long_term_file
        else:
            target_path = self._get_daily_file(date.today())

        det_id = _make_deterministic_id(target_path, header, entry.content)

        # Dedup: if this exact content already exists, skip
        if det_id in self._index:
            return det_id

        entry.id = det_id
        entry.metadata["source"] = str(target_path)
        entry.updated_at = datetime.now()
        self._index[entry.id] = entry

        # Persist to markdown
        await self._append_to_markdown(target_path, entry)

        return entry.id

    async def _append_to_markdown(self, path: Path, entry: MemoryEntry) -> None:
        """Append a memory entry to a markdown file."""
        header = entry.metadata.get("header", datetime.now().strftime("%H:%M"))
        tags_str = " ".join(f"#{t}" for t in entry.tags) if entry.tags else ""

        section = f"\n\n## {header}\n\n{entry.content}"
        if tags_str:
            section += f"\n\n{tags_str}"

        with open(path, "a", encoding="utf-8") as f:
            f.write(section)

    async def _save_session_entry(self, entry: MemoryEntry) -> None:
        """Save a session memory entry."""
        if not entry.session_key:
            return

        # Per-session lock to prevent concurrent read-modify-write corruption
        if entry.session_key not in self._session_write_locks:
            self._session_write_locks[entry.session_key] = asyncio.Lock()

        async with self._session_write_locks[entry.session_key]:
            session_file = self._get_session_file(entry.session_key)

            # Load existing session
            session_data = []
            if session_file.exists():
                try:
                    session_data = json.loads(session_file.read_text())
                except json.JSONDecodeError:
                    pass

            # Append new entry
            session_data.append(
                {
                    "id": entry.id,
                    "role": entry.role,
                    "content": entry.content,
                    "timestamp": entry.created_at.isoformat(),
                    "metadata": entry.metadata,
                }
            )

            # Save back
            session_file.write_text(json.dumps(session_data, indent=2))

    async def get(self, entry_id: str) -> MemoryEntry | None:
        """Get a memory entry by ID."""
        return self._index.get(entry_id)

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry and rewrite source file."""
        if entry_id not in self._index:
            return False

        entry = self._index.pop(entry_id)

        # Rewrite the source markdown file without this entry
        source = entry.metadata.get("source")
        if source:
            self._rewrite_markdown(Path(source))

        return True

    def _rewrite_markdown(self, path: Path) -> None:
        """Reconstruct a markdown file from remaining index entries for that file."""
        source_str = str(path)
        entries = [e for e in self._index.values() if e.metadata.get("source") == source_str]

        if not entries:
            # No entries left — remove file
            if path.exists():
                path.unlink()
            return

        parts = []
        for e in entries:
            header = e.metadata.get("header", "Memory")
            tags_str = " ".join(f"#{t}" for t in e.tags) if e.tags else ""
            section = f"## {header}\n\n{e.content}"
            if tags_str:
                section += f"\n\n{tags_str}"
            parts.append(section)

        path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")

    async def search(
        self,
        query: str | None = None,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Search memories using word-overlap scoring."""
        candidates: list[tuple[float, MemoryEntry]] = []
        query_words = _tokenize(query) if query else set()

        for entry in self._index.values():
            # Type filter
            if memory_type and entry.type != memory_type:
                continue

            # Tag filter
            if tags and not any(t in entry.tags for t in tags):
                continue

            # Query filter: word-overlap scoring
            if query_words:
                content_words = _tokenize(entry.content)
                # Also include header in searchable text
                header = entry.metadata.get("header", "")
                if header:
                    content_words |= _tokenize(header)

                overlap = query_words & content_words
                if not overlap:
                    continue
                score = len(overlap) / len(query_words)
            else:
                score = 0.0

            candidates.append((score, entry))

        # Sort by score descending
        candidates.sort(key=lambda x: x[0], reverse=True)

        return [entry for _, entry in candidates[:limit]]

    async def get_by_type(self, memory_type: MemoryType, limit: int = 100) -> list[MemoryEntry]:
        """Get all memories of a specific type."""
        return [e for e in self._index.values() if e.type == memory_type][:limit]

    async def get_session(self, session_key: str) -> list[MemoryEntry]:
        """Get session history."""
        session_file = self._get_session_file(session_key)

        if not session_file.exists():
            return []

        try:
            data = json.loads(session_file.read_text())
            return [
                MemoryEntry(
                    id=item["id"],
                    type=MemoryType.SESSION,
                    content=item["content"],
                    role=item.get("role"),
                    session_key=session_key,
                    created_at=datetime.fromisoformat(item["timestamp"]),
                    metadata=item.get("metadata", {}),
                )
                for item in data
            ]
        except (json.JSONDecodeError, KeyError):
            return []

    async def clear_session(self, session_key: str) -> int:
        """Clear session history."""
        session_file = self._get_session_file(session_key)

        if session_file.exists():
            try:
                data = json.loads(session_file.read_text())
                count = len(data)
                session_file.unlink()
                return count
            except json.JSONDecodeError:
                session_file.unlink()
                return 0
        return 0
