---
name: permission-consent-analyzer
description: |
  This skill should be used when the user asks to "analyze permissions",
  "suggest permissions", "reduce prompts", "auto-allow patterns",
  "permission analysis", "what am I always approving". Scans instrumented
  session data for permission grant patterns, groups them with safety
  classifications, and helps the user save approved patterns to Claude
  Code settings.
user-invocable: false
---

# Permission Pattern Analysis & Configuration

You are running the Skiller permission analysis workflow. Your goal is to scan session data for repeated permission grants, identify patterns that could be auto-allowed, classify their safety, and help the user save them to settings.

## Workflow

### Step 1: Scan Permission Grants

First, get the cutoff timestamp so only new sessions since the last analysis are scanned:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py cutoff --type permission-consent-analyzer
```

Then run the session scanner with the cutoff to extract permission grant patterns:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scan_permissions.py --min-sessions 1 --since <CUTOFF_TIMESTAMP>
```

Replace `<CUTOFF_TIMESTAMP>` with the output from the cutoff command above.

Use `--min-sessions 1` initially to see all data. If there are many patterns, the grouping step will filter noise.

If the scanner returns no patterns, inform the user:
- No `PermissionGrant` events were found in new session data since the last analysis
- This means either no new sessions have been instrumented, or all tool calls were already pre-allowed
- Suggest the user run a few normal sessions and come back

Parse the JSON output for the next steps.

### Step 2: LLM-Driven Smart Grouping

Analyze the raw permission patterns from Step 1 and group similar commands into Claude Code permission format patterns. For example:

- Individual `git status`, `git diff`, `git log`, `git branch` commands → `Bash(git:*)`
- Individual file reads in the same project → `Read(//project/path/**)`
- Multiple npm commands → `Bash(npm:*)`

For each group, produce:
- **Pattern**: The Claude Code permission string (e.g., `Bash(git:*)`)
- **Covers**: List of individual commands/paths this pattern would match
- **Frequency**: How many sessions this appeared in

Keep ungroupable patterns as-is. Prefer broader patterns when commands clearly belong to the same tool family, but don't over-generalize (e.g., don't group `git` and `npm` into `Bash`).

### Step 3: Safety Classification

Read the safety rules reference at `${CLAUDE_PLUGIN_ROOT}/skills/permission-consent-analyzer/references/safety-rules.md`.

Classify each grouped pattern as:
- **safe** — read-only or side-effect-free; safe to auto-allow
- **caution** — modifies local state or has broader effects; review recommended
- **unsafe** — destructive, broad system access, or unscoped network; not recommended for auto-allow

Provide a brief reasoning for each classification.

### Step 4: Present to User

Present the patterns grouped by safety classification. Use this format:

#### Safe (recommended to auto-allow)
| Pattern | Covers | Sessions | Reasoning |
|---------|--------|----------|-----------|
| `Bash(git status:*)` | git status, git status -s | 5 | Read-only git |

#### Caution (review before allowing)
| Pattern | Covers | Sessions | Reasoning |
|---------|--------|----------|-----------|

#### Unsafe (not recommended)
| Pattern | Covers | Sessions | Reasoning |
|---------|--------|----------|-----------|

Then ask: **"Which patterns would you like to save? You can say 'all safe', list specific patterns, or pick by number."**

### Step 5: Choose Save Target

After the user selects patterns, ask:

**"Where should I save these permissions?"**
1. **Global** (`~/.claude/settings.json`) — applies to all projects
2. **Project** (`.claude/settings.json` in the current working directory) — applies only to this project

### Step 6: Save Permissions

1. Read the target settings file (create if it doesn't exist)
2. Merge the selected patterns into `permissions.allow`, deduplicating with existing entries
3. Write the file back, preserving all existing content (attribution, hooks, other settings)
4. Show the user what was added

Use the Edit tool to modify the settings file. If the file doesn't exist, use the Write tool to create it with the standard structure:

```json
{
  "permissions": {
    "allow": [
      ...selected patterns...
    ]
  }
}
```

### Step 7: Update Analysis Marker

After successfully saving permissions (or if the user declines all patterns), mark the analysis as complete:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py mark --type permission-consent-analyzer
```

Do NOT update the marker if no eligible sessions were found or if scanning failed.

## Edge Cases

- **No sessions**: Inform user and suggest running some sessions first
- **All already allowed**: Report that all detected tool usage is already covered by existing permissions
- **Few sessions** (< 3): Still show patterns but note that more sessions would give higher confidence
- **Very many patterns** (50+): Focus on the top 20 by frequency, mention others are available
- **Settings file has no permissions key**: Add the `permissions.allow` array without disturbing other keys
- **User declines all**: Acknowledge and suggest they can re-run later when they have more session data
