# PocketClaw Issues Log

## Issue #1: Agent UI Silent During Execution

**Status:** ✅ Fixed  
**Date:** 2026-02-01

### Problem

When using the web dashboard with Agent Mode ON:

- Open Interpreter output appeared in terminal (verbose)
- Web UI showed nothing until execution completed
- Long agent responses made UI appear "frozen"

### Root Cause

The `open_interpreter.py` agent wrapper collected ALL response chunks in a sync function, then yielded them only AFTER the entire execution completed.

### Fix

Implemented real-time streaming using `asyncio.Queue`:

- Chunks are pushed to queue from sync thread as they arrive
- Async generator yields chunks immediately to WebSocket
- Added timeout handling for long operations

### Files Changed

- `src/pocketclaw/agents/open_interpreter.py`

---

## Issue #2: Agent Misidentifies Active VS Code Project

**Status:** 🟡 Open  
**Date:** 2026-02-01

### Problem

When asked "what's running in my VS Code", Open Interpreter:

- Found `pocketclaw --web` processes
- Incorrectly assumed that was the active VS Code project
- Didn't check the actual VS Code window/workspace

### Root Cause

Open Interpreter used process list (`ps aux`) to infer what's running, but VS Code's active workspace isn't exposed via process info.

### Potential Fix

Could add a tool that reads VS Code's recently opened workspaces from:

```
~/Library/Application Support/Code/storage.json
```

Or use AppleScript to query the front VS Code window's title.

### Status

This is an Open Interpreter limitation, not a PocketClaw bug. The agent made a reasonable inference but got it wrong.

---

## Issue #3: Missing `python-multipart` dependency

**Status:** ✅ Fixed  
**Date:** 2026-02-01

### Problem

Running `uv run pocketclaw` failed with:

```
Form data requires "python-multipart" to be installed.
```

### Fix

Added dependency:

```bash
uv add python-multipart
```
