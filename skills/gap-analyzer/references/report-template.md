# Session Gap Analysis Report

**Generated:** {{timestamp}}
**Sessions analyzed:** {{session_count}}
**Total events processed:** {{event_count}}

---

## Executive Summary

{{summary}}

---

## Top Gaps by Frequency

| Rank | Gap Type | Count | Sessions Affected | Avg Impact |
|------|----------|-------|-------------------|------------|
{{top_gaps_table}}

---

## Quick Wins

Immediately actionable solutions — copy-paste these to apply.

{{#each quick_wins}}
### {{rank}}. {{title}}

**Type:** `{{solution_type}}` | **Effort:** {{effort}}

{{summary}}

{{#if implementation.snippet}}
**Apply this:**
```json
{{implementation.snippet}}
```
{{/if}}

{{#if implementation.rule_text}}
**Add to `{{implementation.file}}`** (section: {{implementation.section}}):
```
{{implementation.rule_text}}
```
{{/if}}

{{#if pros}}
**Pros:**
{{#each pros}}
- {{this}}
{{/each}}
{{/if}}

{{#if cons}}
**Cons:**
{{#each cons}}
- {{this}}
{{/each}}
{{/if}}

**Gaps addressed:**
{{#each gaps_addressed}}
- {{this}}
{{/each}}

{{/each}}

{{#unless quick_wins}}
No quick wins identified — all solutions require component development or are platform limitations.
{{/unless}}

---

## Solution Proposals

{{#each solution_proposals}}
### {{rank}}. {{title}}

**Type:** `{{solution_type}}` | **Effort:** {{effort}}
**Addresses gaps:** {{gap_types}}

{{description}}

**Pros:**
{{#each pros}}
- {{this}}
{{/each}}

**Cons:**
{{#each cons}}
- {{this}}
{{/each}}

**Implementation path:**
{{implementation_path}}

**Supporting evidence:**
{{#each examples}}
- Session `{{session_id}}`: {{context}}
{{/each}}

{{/each}}

---

## Per-Session Breakdown

{{#each sessions}}
### Session: `{{session_id}}`

**Duration:** {{duration}} | **Events:** {{event_count}} | **Gaps found:** {{gap_count}}

{{#each gaps}}
- **[{{type}}]** {{description}}
  - Context: {{context}}
  - Impact: {{impact}}
{{/each}}

{{/each}}

---

## Discovered Gap Categories

{{#if novel_categories}}
{{#each novel_categories}}
### `{{name}}`

**Definition:** {{definition}}

**Signals:** {{signals}}

**Examples from data:**
{{#each examples}}
- {{this}}
{{/each}}

{{/each}}
{{else}}
No novel gap categories were discovered in this analysis. All gaps fit within the seed taxonomy.
{{/if}}

---

## Methodology

- Events sourced from `~/.claude/skiller/sessions/`
- Gap classification uses seed taxonomy: `missing_tool`, `repeated_failure`, `wrong_info`
- LLM-driven analysis with novel category discovery enabled
- Impact rated as: low (minor inconvenience), medium (significant delay), high (task blocked/failed)
