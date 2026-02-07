# Tool Policy System

Fine-grained control over which tools the AI agent can use.

## Overview

The tool policy system lets you restrict which tools the agent has access to. This is critical for security — you can run the agent in "chat only" mode (no system access), "coding" mode (files + shell only), or "full" mode (everything).

## Configuration

Three settings in `~/.pocketclaw/config.json` (or via `POCKETCLAW_` env vars):

```json
{
  "tool_profile": "coding",
  "tools_allow": ["browser"],
  "tools_deny": ["desktop"]
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `tool_profile` | string | `"full"` | Base profile: `minimal`, `coding`, or `full` |
| `tools_allow` | list | `[]` | Extra tools/groups to allow on top of the profile |
| `tools_deny` | list | `[]` | Tools/groups to block (overrides profile and allow) |

## Profiles

| Profile | Allowed Tools | Use Case |
|---------|--------------|----------|
| `minimal` | Memory only (`remember`, `recall`) | Chat assistant, no system access |
| `coding` | File system + shell + memory | Developer assistant |
| `full` | All tools (no restrictions) | Power users |

## Tool Groups

Tools are organized into groups for easier management:

| Group | Tools |
|-------|-------|
| `group:fs` | `read_file`, `write_file`, `list_dir` |
| `group:shell` | `shell` |
| `group:browser` | `browser` |
| `group:memory` | `remember`, `recall` |
| `group:desktop` | `desktop`, `screenshot` |
| `group:status` | `status` |

You can use group names in `tools_allow` and `tools_deny`:

```json
{
  "tool_profile": "minimal",
  "tools_allow": ["group:browser"],
  "tools_deny": []
}
```

This gives the agent memory tools (from `minimal` profile) plus browser access.

## Precedence

**deny > allow > profile**

1. If a tool is in `tools_deny`, it is always blocked
2. If a tool is in `tools_allow`, it is allowed (unless denied)
3. Otherwise, the `tool_profile` determines access

## Claude Agent SDK Mapping

The Claude Agent SDK uses different tool names than PocketPaw's internal names. The policy system handles this mapping transparently:

| SDK Tool | Policy Tool |
|----------|------------|
| `Bash` | `shell` |
| `Read` | `read_file` |
| `Write` | `write_file` |
| `Edit` | `write_file` |
| `Glob` | `list_dir` |
| `Grep` | `read_file` |
| `WebSearch` | `browser` |
| `WebFetch` | `browser` |

## Implementation

- **Policy engine**: `src/pocketclaw/tools/policy.py`
- **Wired into**: `ToolRegistry`, `claude_sdk.py`, `pocketpaw_native.py`
- **Tests**: `tests/test_tool_policy.py` (26 tests)
