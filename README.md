# Skiller

A Claude Code plugin that instruments sessions and analyzes behavioral gaps to suggest improvements.

Skiller silently records lifecycle events during your Claude Code sessions, then lets you analyze that data to find recurring pain points — missing tools, repeated failures, wrong assumptions — and turn them into actionable feature suggestions. It can also scan your permission grant patterns and recommend auto-allow rules to reduce approval prompts.

## Installation

Add the plugin to your Claude Code settings:

```json
{
  "plugins": [
    "/path/to/skiller"
  ]
}
```

Session data is stored in `~/.claude/skiller/sessions/`.

## How It Works

### Instrumentation (automatic)

Hooks capture every Claude Code lifecycle event — session start/end, tool use, user prompts, compaction, notifications — and write structured JSONL records to per-session directories. This happens transparently in the background with no user interaction required.

**Captured events:** `SessionStart`, `SessionEnd`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `UserPromptSubmit`, `PreCompact`, `Notification`

### Gap Analysis

Run `/analyze-gaps` to scan your session history for behavioral gaps. The analyzer:

1. Discovers sessions not yet analyzed (up to 30 days back)
2. Spawns parallel agents to classify gaps in each session using a seed taxonomy:
   - **`missing_tool`** — Claude needed a capability that wasn't available
   - **`repeated_failure`** — same action attempted 3+ times before succeeding or failing
   - **`wrong_info`** — incorrect assumptions, outdated info, or wrong paths
3. Aggregates findings across sessions, ranking by frequency and impact
4. Generates feature suggestions backed by concrete evidence
5. Writes a full report to `~/.claude/skiller/reports/`

Novel gap categories are proposed automatically when patterns don't fit the seed taxonomy.

### Permission Consent Analysis

Run `/analyze-consented-permissions` to review which tool permissions you keep approving manually. The analyzer:

1. Scans sessions for `PermissionGrant` events
2. Groups similar commands into Claude Code permission patterns (e.g., individual git commands → `Bash(git:*)`)
3. Classifies each pattern as **safe**, **caution**, or **unsafe**
4. Presents recommendations and lets you save selected patterns to your global or project settings

## Plugin Structure

```
skiller/
├── .claude-plugin/
│   └── plugin.json            # Plugin manifest
├── hooks/
│   ├── hooks.json             # Hook registrations (all lifecycle events)
│   └── instrument.py          # Event capture script
├── scripts/
│   ├── lib.py                 # Shared utilities
│   ├── session_manager.py     # Session discovery and analysis markers
│   └── scan_permissions.py    # Permission grant scanner
├── commands/
│   ├── analyze-gaps.md        # /analyze-gaps slash command
│   └── analyze-consented-permissions.md  # /analyze-consented-permissions slash command
├── skills/
│   ├── gap-analyzer/
│   │   ├── SKILL.md           # Gap analysis workflow
│   │   └── references/
│   │       ├── gap-taxonomy.md    # Seed gap categories
│   │       └── report-template.md # Report format
│   └── permission-consent-analyzer/
│       ├── SKILL.md           # Permission analysis workflow
│       └── references/
│           └── safety-rules.md    # Safety classification heuristics
└── agents/
    └── session-analyzer.md    # Per-session analysis agent
```

## Commands

| Command | Description |
|---------|-------------|
| `/analyze-gaps` | Analyze sessions for behavioral gaps and generate improvement suggestions |
| `/analyze-consented-permissions` | Analyze permission patterns and suggest auto-allow rules |

## Requirements

- Claude Code with plugin support
- Python 3

## Author

Sebastiano Merlino
