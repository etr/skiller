# Solution Taxonomy

This document defines the solution types for addressing gaps identified during Claude Code session analysis. Each gap should map to one of these solution types, ordered by implementation effort.

## Solution Types

### 1. `settings_config`

**Definition:** The gap can be fixed by changing Claude Code settings, permission patterns, or configuration values. These are immediate fixes requiring no code.

**When to use:**
- Tool permission prompts that the user always approves
- Missing environment variables or model configuration
- MCP server connections that need enabling
- Allowed/denied tool patterns

**Output template:**
```json
{
  "solution_type": "settings_config",
  "title": "Short descriptive title",
  "summary": "One-sentence description of the fix",
  "effort": "low",
  "implementation": {
    "file": "~/.claude/settings.json or ~/.claude/settings.local.json",
    "change": "Exact JSON to add/modify",
    "snippet": "{ \"permissions\": { \"allow\": [\"Bash(npm test)\"] } }"
  },
  "evidence": ["session_id: context"]
}
```

**Examples:**
- Auto-allow `npm test` to avoid repeated permission prompts → add to `permissions.allow`
- Set environment variable for API key → add to `env` block
- Allow Bash commands matching a pattern → add regex to `permissions.allow`

---

### 2. `claude_md_guidance`

**Definition:** The gap can be fixed by adding behavioral rules to a CLAUDE.md file so Claude knows how to handle a situation. These are immediate fixes requiring no code — just text.

**When to use:**
- Claude repeatedly makes the same wrong assumption about the project
- Claude uses the wrong approach for a task the project handles a specific way
- Claude doesn't know about project conventions, tools, or workflows
- Claude lacks context that would prevent repeated failures

**Output template:**
```json
{
  "solution_type": "claude_md_guidance",
  "title": "Short descriptive title",
  "summary": "One-sentence description of the fix",
  "effort": "low",
  "implementation": {
    "file": "CLAUDE.md or .claude/CLAUDE.md",
    "section": "Suggested section heading",
    "rule_text": "Exact text to add to CLAUDE.md"
  },
  "evidence": ["session_id: context"]
}
```

**Examples:**
- Claude keeps using `yarn` but project uses `pnpm` → add "This project uses pnpm, not yarn or npm" to CLAUDE.md
- Claude doesn't know about a custom test runner → add "Run tests with `make test-unit`, not `pytest` directly"
- Claude assumes wrong database schema → add schema notes to CLAUDE.md

---

### 3. `plugin_component`

**Definition:** The gap requires building a new plugin component — a hook, skill, command, agent, or script. Moderate effort but provides automated, reusable solutions.

**When to use:**
- A recurring task needs automation (hook)
- A multi-step workflow should be packaged (skill)
- A common operation needs a shortcut (command)
- A complex analysis needs delegation (agent)
- Supporting logic is needed (script)

**Output template:**
```json
{
  "solution_type": "plugin_component",
  "title": "Short descriptive title",
  "summary": "One-sentence description of the component",
  "effort": "medium",
  "implementation": {
    "component_type": "hook | skill | command | agent | script",
    "description": "What the component does",
    "structure": "Directory layout and key files",
    "template_reference": "Existing component to use as starting point",
    "key_logic": "Core behavior the component must implement"
  },
  "evidence": ["session_id: context"]
}
```

**Template references for each component type:**
- **Hook:** Use `hooks/instrument.py` + `hooks/hooks.json` as template. Hooks intercept events (PreToolUse, PostToolUse, Stop, etc.) and can block, modify, or log tool calls.
- **Agent:** Use `agents/session-analyzer.md` as template. Agents are autonomous subprocesses with specific tools and turn limits.
- **Skill:** Use `skills/gap-analyzer/SKILL.md` as template. Skills are multi-step workflows triggered by user intent.
- **Command:** Commands are markdown files in `commands/` with YAML frontmatter defining slash-command behavior.
- **Script:** Use `scripts/session_manager.py` or `scripts/lib.py` as template. Python scripts for supporting logic.

**Examples:**
- Auto-format code before commit → PreToolUse hook on Bash(git commit) that runs formatter
- Analyze PR readiness → new skill combining test runner, linter, and diff analysis
- Quick project stats → command that runs and formats common queries

---

### 4. `platform_limitation`

**Definition:** The gap cannot be fixed within the plugin or Claude Code configuration. It requires changes to Claude Code itself, the Claude model, or external systems.

**When to use:**
- The limitation is in Claude Code's architecture (e.g., no streaming tool output)
- The limitation is in the model itself (e.g., knowledge cutoff, context window)
- The limitation requires changes to tool APIs that plugins can't modify
- External service limitations

**Output template:**
```json
{
  "solution_type": "platform_limitation",
  "title": "Short descriptive title",
  "summary": "One-sentence description of the limitation",
  "effort": "high",
  "implementation": {
    "limitation": "What specifically cannot be done",
    "reason": "Why it's a platform limitation",
    "workaround": "Best available workaround, if any",
    "workaround_effort": "low | medium | high | none"
  },
  "evidence": ["session_id: context"]
}
```

**Examples:**
- Claude can't see real-time terminal output → platform limitation, workaround: check output after command completes
- Context window exceeded on large files → platform limitation, workaround: read specific line ranges
- No access to browser for visual testing → platform limitation, workaround: use screenshot tool or headless browser via Bash

---

## Prioritization Rules

When presenting solutions, order by:

1. **Within each priority tier:** effort ascending (quick wins first)
   - `settings_config` (minutes to apply)
   - `claude_md_guidance` (minutes to apply)
   - `plugin_component` (hours to build)
   - `platform_limitation` (no immediate fix)

2. **Across tiers:** impact × frequency descending (most impactful first)

3. **Quick Wins section:** Extract all `settings_config` and `claude_md_guidance` solutions into a dedicated section with copy-pasteable snippets that the user can apply immediately.
