# 🦀 PocketClaw

> **The AI agent that runs on your laptop, not a datacenter.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![UV](https://img.shields.io/badge/uv-package%20manager-blueviolet)](https://docs.astral.sh/uv/)

PocketClaw is a self-hosted, cross-platform personal AI agent you control via **Telegram**. Unlike cloud-hosted AI assistants, PocketClaw runs on _your_ machine, respects _your_ privacy, and works even on that dusty laptop in your closet.

## ✨ Features

- 🔋 **Sleep Mode** — Near-zero CPU when idle, wakes on your message
- 🔒 **Local-First** — Runs on your machine, your data stays yours
- 🧠 **Dual Agent Backend** — Choose between Open Interpreter or Claude Code
- 🤖 **Multi-LLM Support** — Ollama (local), OpenAI, or Anthropic
- 📱 **Telegram-First** — Control from anywhere, no port forwarding needed
- 🖥️ **Cross-Platform** — macOS, Windows, Linux

## 🚀 Quick Start

### Prerequisites

Install [UV](https://docs.astral.sh/uv/) (the fast Python package manager):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install & Run

```bash
# Clone the repo
git clone https://github.com/pocketclaw/pocketclaw.git
cd pocketclaw

# Run (UV handles everything automatically!)
uv run pocketclaw
```

That's it! UV will:

1. Create a virtual environment
2. Install all dependencies
3. Run PocketClaw
4. Open your browser for setup

### One-liner (after release)

```bash
uvx pocketclaw
```

## 🤖 Agent Backends

### Open Interpreter (Default)

Works with any LLM (Ollama, OpenAI, Claude). Full shell and Python execution.

```
User: "Find all PDFs in Downloads and organize them by date"
Agent: [Runs shell commands, moves files]
Agent: "Done! Moved 23 PDFs into dated folders."
```

### Claude Code

Uses Anthropic's computer use capability. Can see your screen and control GUI.

```
User: "Open Chrome and search for weather"
Agent: [Takes screenshot, clicks, types]
Agent: "Done! Showing weather results."
```

## ⚙️ Configuration

PocketClaw stores config in `~/.pocketclaw/config.json`:

```json
{
  "telegram_bot_token": "your-bot-token",
  "allowed_user_id": 123456789,
  "agent_backend": "open_interpreter",
  "llm_provider": "auto",
  "ollama_model": "llama3.2",
  "openai_api_key": "sk-...",
  "anthropic_api_key": "sk-ant-..."
}
```

Or use environment variables:

```bash
export POCKETCLAW_OPENAI_API_KEY="sk-..."
export POCKETCLAW_AGENT_BACKEND="claude_code"
```

## 🛠️ Telegram Controls

| Button        | Function                           |
| ------------- | ---------------------------------- |
| 🟢 Status     | CPU, RAM, disk, battery, uptime    |
| 📁 Fetch      | Browse and download files          |
| 📸 Screenshot | Capture current screen             |
| 🧠 Agent Mode | Toggle autonomous agent            |
| 🛑 Panic      | Emergency stop all agent processes |
| ⚙️ Settings   | Switch agent/LLM backends          |

## 🔐 Security

- **Single User Lock** — Only one Telegram user can control the bot
- **File Jail** — File operations restricted to home directory
- **Panic Button** — Hard kill switch for runaway agents
- **Local LLM Option** — Keep everything on-device with Ollama

## 🧑‍💻 Development

```bash
# Clone
git clone https://github.com/pocketclaw/pocketclaw.git
cd pocketclaw

# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

## 🤝 Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT © PocketClaw Team
