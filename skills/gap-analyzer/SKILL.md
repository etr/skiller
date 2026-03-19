---
name: gap-analyzer
description: |
  This skill should be used when the user asks to "analyze sessions",
  "find gaps", "review Claude behavior", "what went wrong in my sessions",
  "suggest improvements". Scans instrumented session data, classifies
  behavioral gaps, and generates feature suggestions.
user-invocable: false
---

# Session Gap Analysis

You are running the Skiller gap analysis workflow. Your goal is to analyze captured Claude Code session data, identify behavioral gaps, and generate actionable feature suggestions.

## Workflow

### Step 1: Discover Sessions

List all session directories under `~/.claude/skiller/sessions/`. Each session directory contains an `events.jsonl` file with structured event records.

If no sessions are found, inform the user that no instrumented sessions exist yet and explain that sessions are captured automatically by the skiller hooks during normal Claude Code usage.

### Step 2: Analyze Sessions

For each session directory found, use the **Agent tool** with `subagent_type: "skiller:session-analyzer"` to analyze the session in parallel. Pass the following prompt to each agent:

```
Analyze the session at: ~/.claude/skiller/sessions/<session_id>/

Read the events.jsonl file and any available transcript.
Read the gap taxonomy reference at: ${CLAUDE_PLUGIN_ROOT}/skills/gap-analyzer/references/gap-taxonomy.md

Classify all gaps found using the seed taxonomy and propose novel categories if needed.
Return your findings as the specified JSON structure.
```

Launch multiple session-analyzer agents in parallel (up to 5 at a time) to speed up analysis.

### Step 3: Aggregate Results

Once all session analyzers return, aggregate their findings:

1. **Collect all gaps** across sessions into a unified list
2. **Count frequency** of each gap type across sessions
3. **Rank gaps** by frequency × impact (high=3, medium=2, low=1)
4. **Merge novel categories** — if multiple sessions propose the same novel category, consolidate with combined examples
5. **Identify cross-session patterns** — gaps that appear in 3+ sessions are systemic

### Step 4: Generate Feature Suggestions

Based on the aggregated gaps, generate feature suggestions:

- Each suggestion should address one or more related gaps
- Include a clear title, description, and which gap types it addresses
- Cite specific session examples as evidence
- Prioritize by potential impact (how many sessions × how severe)
- Be concrete and actionable — "Add a dedicated JSON schema validation tool" not "Improve tooling"

### Step 5: Write Report

Generate a markdown report and write it to `~/.claude/skiller/reports/<timestamp>-analysis.md` where `<timestamp>` is the current date-time in `YYYY-MM-DD-HHmmss` format.

The report should follow the structure in `${CLAUDE_PLUGIN_ROOT}/skills/gap-analyzer/references/report-template.md` and include:

- Executive summary
- Top gaps ranked by frequency and impact
- Feature suggestions with supporting evidence
- Per-session breakdown
- Any discovered novel gap categories

### Step 6: Present Findings

After writing the report, present the key findings interactively in the conversation:

1. **Top 3-5 gaps** with brief descriptions and frequency
2. **Most notable session** — the session with the most or highest-impact gaps
3. **Top 3 feature suggestions** with brief rationale
4. **Novel categories** discovered (if any)
5. **Report location** — tell the user where the full report was saved

Keep the conversation output concise and actionable. The full details are in the report.

## Edge Cases

- **Single session**: Still run the full analysis but note that cross-session patterns require more data
- **Empty sessions**: Skip sessions with 0 events or only a SessionStart event
- **Very large sessions** (1000+ events): Summarize event patterns rather than analyzing each event individually
- **No gaps found**: Report this positively — "No significant gaps detected" is a valid outcome
- **Analysis errors**: If a session-analyzer agent fails, log the error and continue with remaining sessions
