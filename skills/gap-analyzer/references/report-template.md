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

## Feature Suggestions

{{#each feature_suggestions}}
### {{rank}}. {{title}}

**Addresses gaps:** {{gap_types}}
**Estimated impact:** {{impact}}

{{description}}

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
