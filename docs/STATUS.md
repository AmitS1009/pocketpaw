# PocketClaw: Project Status & Roadmap

> Last updated: 2026-02-01

## 🎯 Current Status: **MVP Complete + Web Dashboard**

The core functionality is implemented and tested.

---

## ✅ Completed (v0.1.0)

### Core Infrastructure

- [x] UV package manager setup
- [x] Cross-platform project structure
- [x] Pydantic-based configuration
- [x] MIT License
- [x] Unit tests (19 passing)

### Telegram Bot

- [x] Long-polling gateway
- [x] Persistent keyboard UI
- [x] User authorization (single-user lock)
- [x] Settings menu with inline keyboard

### Web Dashboard (New!)

- [x] Full web UI for testing without Telegram
- [x] WebSocket real-time updates
- [x] API key input fields (Anthropic, OpenAI)
- [x] Live settings persistence

### Web Pairing

- [x] FastAPI server on localhost:8888
- [x] QR code generation
- [x] Beautiful setup UI
- [x] Auto-shutdown after pairing

### Tools

- [x] 🟢 Status (CPU, RAM, Disk, Battery, Uptime)
- [x] 📁 Fetch (file browser with inline keyboard)
- [x] 📸 Screenshot (with graceful fallback)
- [x] 🛑 Panic (hard kill switch)

### LLM Router

- [x] Auto-detection (Ollama → OpenAI → Claude)
- [x] Ollama client (local LLMs)
- [x] OpenAI client
- [x] Anthropic client
- [x] Conversation history

### Agent Backends

- [x] Agent router (switchable via settings)
- [x] Open Interpreter wrapper
- [x] Claude Code wrapper (with computer use tools)

---

## 🔄 In Progress

| Task               | Status              | Notes                               |
| ------------------ | ------------------- | ----------------------------------- |
| End-to-end testing | 🟡 Pending          | Need Telegram bot token to test     |
| QR deep link flow  | 🟡 Needs refinement | Current flow requires manual /start |

---

## 📋 TODO (v0.2.0)

### High Priority

- [ ] **Fix QR deep link** — Auto-extract bot username for proper deep link
- [ ] **Test Open Interpreter integration** — Verify streaming works
- [ ] **Test Claude Code integration** — Test computer use tools
- [ ] **Error handling** — Add proper error messages for common failures
- [ ] **Logging** — Add structured logging with levels

### Medium Priority

- [ ] **Cost controls** — Warn user before expensive LLM operations
- [ ] **Rate limiting** — Prevent Telegram API spam
- [ ] **Multi-user support** — Allow household/team access
- [ ] **Conversation persistence** — Save chat history to disk

### Nice to Have

- [ ] **PyInstaller binaries** — Single executable for distribution
- [ ] **Auto-update** — Check for new versions
- [ ] **Plugin system** — User-defined tools
- [ ] **Webhook mode** — Alternative to long-polling

---

## 📋 TODO (v0.3.0 - Future)

- [ ] **Tailscale integration** — Secure remote access
- [ ] **Web dashboard** — Alternative to Telegram
- [ ] **Mobile app** — Native iOS/Android
- [ ] **Voice messages** — Process voice via Whisper
- [ ] **Scheduled tasks** — Cron-like automation

---

## 📊 File Structure

```
pocketclaw/
├── pyproject.toml         ✅ UV config
├── .python-version        ✅ Python 3.12
├── README.md              ✅ Documentation
├── LICENSE                ✅ MIT
├── docs/
│   ├── STATUS.md          ✅ This file
│   ├── idea.md            📄 Original idea
│   ├── openclaw.md        📄 Competition analysis
│   └── tech-spec.md       📄 Original tech spec
└── src/pocketclaw/
    ├── __init__.py        ✅
    ├── __main__.py        ✅ Entry point
    ├── config.py          ✅ Settings
    ├── bot_gateway.py     ✅ Telegram handlers
    ├── web_server.py      ✅ QR pairing
    ├── tools/
    │   ├── __init__.py    ✅
    │   ├── status.py      ✅
    │   ├── fetch.py       ✅
    │   └── screenshot.py  ✅
    ├── llm/
    │   ├── __init__.py    ✅
    │   └── router.py      ✅
    └── agents/
        ├── __init__.py    ✅
        ├── router.py      ✅
        ├── open_interpreter.py  ✅
        └── claude_code.py       ✅
```

---

## 🚀 How to Test

```bash
# 1. Create a Telegram bot
# Visit @BotFather, send /newbot, get token

# 2. Run PocketClaw
cd /Users/prakash/Documents/Qbtrix/pocketClaw
uv run pocketclaw

# 3. Setup
# - Browser opens to localhost:8888
# - Paste bot token
# - Add API keys (optional)
# - Scan QR / send /start to bot

# 4. Test
# - Tap 🟢 Status → see system stats
# - Tap 📁 Fetch → browse files
# - Tap 📸 Screenshot → get screen image
# - Tap 🧠 Agent Mode → enable agent
# - Type "List files in Downloads" → agent executes
```

---

## 📈 Metrics

| Metric          | Value     |
| --------------- | --------- |
| Total files     | 17        |
| Lines of code   | ~1,500    |
| Dependencies    | 15 direct |
| Python version  | 3.11+     |
| Package manager | UV        |

---

## 🔗 Links

- Repository: [github.com/pocketclaw/pocketclaw](https://github.com/pocketclaw/pocketclaw)
- Issues: TBD
- Discord: TBD
