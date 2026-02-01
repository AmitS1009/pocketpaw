"""LLM Router - routes requests to available LLM backends."""

import logging
from typing import Optional, List

import httpx

from pocketclaw.config import Settings

logger = logging.getLogger(__name__)


class LLMRouter:
    """Routes LLM requests to available backends."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.conversation_history: List[dict] = []
        self._available_backend: Optional[str] = None
    
    async def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.settings.ollama_host}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    async def _detect_backend(self) -> Optional[str]:
        """Detect available LLM backend based on settings."""
        provider = self.settings.llm_provider
        
        if provider == "ollama":
            if await self._check_ollama():
                return "ollama"
            return None
        
        if provider == "openai":
            if self.settings.openai_api_key:
                return "openai"
            return None
        
        if provider == "anthropic":
            if self.settings.anthropic_api_key:
                return "anthropic"
            return None
        
        # Auto mode - try in order: Ollama → OpenAI → Anthropic
        if provider == "auto":
            if await self._check_ollama():
                return "ollama"
            if self.settings.openai_api_key:
                return "openai"
            if self.settings.anthropic_api_key:
                return "anthropic"
        
        return None
    
    async def chat(self, message: str) -> str:
        """Send a chat message and get a response."""
        if not self._available_backend:
            self._available_backend = await self._detect_backend()
        
        if not self._available_backend:
            return (
                "❌ No LLM backend available.\n\n"
                "Options:\n"
                "• Install [Ollama](https://ollama.ai) and run `ollama run llama3.2`\n"
                "• Add OpenAI API key in ⚙️ Settings\n"
                "• Add Anthropic API key in ⚙️ Settings"
            )
        
        self.conversation_history.append({"role": "user", "content": message})
        
        try:
            if self._available_backend == "ollama":
                response = await self._chat_ollama(message)
            elif self._available_backend == "openai":
                response = await self._chat_openai(message)
            elif self._available_backend == "anthropic":
                response = await self._chat_anthropic(message)
            else:
                response = "Unknown backend"
            
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"❌ LLM Error: {str(e)}"
    
    async def _chat_ollama(self, message: str) -> str:
        """Chat via Ollama."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.settings.ollama_host}/api/chat",
                json={
                    "model": self.settings.ollama_model,
                    "messages": self.conversation_history,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "No response")
    
    async def _chat_openai(self, message: str) -> str:
        """Chat via OpenAI."""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        
        response = await client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": "You are PocketClaw, a helpful AI assistant running locally on the user's machine."},
                *self.conversation_history
            ]
        )
        
        return response.choices[0].message.content
    
    async def _chat_anthropic(self, message: str) -> str:
        """Chat via Anthropic."""
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        
        response = await client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=4096,
            system="You are PocketClaw, a helpful AI assistant running locally on the user's machine.",
            messages=self.conversation_history
        )
        
        return response.content[0].text
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
