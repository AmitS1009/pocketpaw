"""Configuration management for PocketClaw."""

import json
from pathlib import Path
from typing import Optional
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_config_dir() -> Path:
    """Get the config directory, creating if needed."""
    config_dir = Path.home() / ".pocketclaw"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Get the config file path."""
    return get_config_dir() / "config.json"


class Settings(BaseSettings):
    """PocketClaw settings with env and file support."""
    
    model_config = SettingsConfigDict(
        env_prefix="POCKETCLAW_",
        env_file=".env",
        extra="ignore"
    )
    
    # Telegram
    telegram_bot_token: Optional[str] = Field(default=None, description="Telegram Bot Token from @BotFather")
    allowed_user_id: Optional[int] = Field(default=None, description="Telegram User ID allowed to control the bot")
    
    # Agent Backend
    agent_backend: str = Field(default="open_interpreter", description="Agent backend: 'open_interpreter' or 'claude_code'")
    
    # LLM Configuration
    llm_provider: str = Field(default="auto", description="LLM provider: 'auto', 'ollama', 'openai', 'anthropic'")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama API host")
    ollama_model: str = Field(default="llama3.2", description="Ollama model to use")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model to use")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514", description="Anthropic model to use")
    
    # Security
    file_jail_path: Path = Field(default_factory=Path.home, description="Root path for file operations")
    
    # Web Server
    web_host: str = Field(default="127.0.0.1", description="Web server host")
    web_port: int = Field(default=8888, description="Web server port")
    
    def save(self) -> None:
        """Save settings to config file."""
        config_path = get_config_path()
        data = {
            "telegram_bot_token": self.telegram_bot_token,
            "allowed_user_id": self.allowed_user_id,
            "agent_backend": self.agent_backend,
            "llm_provider": self.llm_provider,
            "ollama_host": self.ollama_host,
            "ollama_model": self.ollama_model,
            "openai_api_key": self.openai_api_key,
            "openai_model": self.openai_model,
            "anthropic_api_key": self.anthropic_api_key,
            "anthropic_model": self.anthropic_model,
        }
        config_path.write_text(json.dumps(data, indent=2))
    
    @classmethod
    def load(cls) -> "Settings":
        """Load settings from config file, falling back to env/defaults."""
        config_path = get_config_path()
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                return cls(**data)
            except (json.JSONDecodeError, Exception):
                pass
        return cls()


@lru_cache
def get_settings(force_reload: bool = False) -> Settings:
    """Get cached settings instance."""
    if force_reload:
        get_settings.cache_clear()
    return Settings.load()
