"""Agent Router - routes to Open Interpreter or Claude Code."""

import logging
from typing import AsyncIterator, Optional

from pocketclaw.config import Settings
from pocketclaw.agents.open_interpreter import OpenInterpreterAgent
from pocketclaw.agents.claude_code import ClaudeCodeAgent

logger = logging.getLogger(__name__)


class AgentRouter:
    """Routes agent requests to the selected backend."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._agent: Optional[OpenInterpreterAgent | ClaudeCodeAgent] = None
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        """Initialize the selected agent backend."""
        backend = self.settings.agent_backend
        
        if backend == "open_interpreter":
            self._agent = OpenInterpreterAgent(self.settings)
            logger.info("🧠 Initialized Open Interpreter agent")
        elif backend == "claude_code":
            self._agent = ClaudeCodeAgent(self.settings)
            logger.info("🧠 Initialized Claude Code agent")
        else:
            logger.warning(f"Unknown agent backend: {backend}, defaulting to Open Interpreter")
            self._agent = OpenInterpreterAgent(self.settings)
    
    async def run(self, message: str) -> AsyncIterator[dict]:
        """Run the agent with the given message."""
        if not self._agent:
            yield {"type": "message", "content": "❌ No agent initialized"}
            return
        
        async for chunk in self._agent.run(message):
            yield chunk
    
    async def stop(self) -> None:
        """Stop the agent."""
        if self._agent:
            await self._agent.stop()
