# Gap Taxonomy

This document defines the seed taxonomy for classifying gaps identified during Claude Code session analysis. Analysts should use these categories as a starting point and may propose new categories when patterns don't fit.

## Seed Categories

### `missing_tool`

**Definition:** Claude needed a capability that wasn't available as a tool, leading to a workaround via Bash, manual steps, or abandoning the approach.

**Signals:**
- Bash commands used to accomplish what a dedicated tool could do better
- Claude explicitly stating "I don't have a tool for this"
- Multi-step workarounds for conceptually simple operations
- User providing information that a tool should have been able to retrieve

**Record fields:**
- `task_context`: What Claude was trying to accomplish
- `tool_needed`: Description of the missing capability
- `workaround`: How Claude (or the user) worked around it
- `impact`: How much time/effort was lost (low/medium/high)

**Examples:**
- No tool for searching git history by content, fell back to `git log --grep` via Bash
- No tool for validating JSON schemas, had to write inline validation
- No tool for diffing two files side-by-side, used sequential reads instead

---

### `repeated_failure`

**Definition:** Claude attempted the same or similar action multiple times before succeeding or giving up, indicating a reliability or knowledge gap.

**Signals:**
- Same tool called 3+ times with minor variations
- Error → retry → error → retry patterns
- Claude changing approach after multiple failures
- "Let me try a different approach" after failed attempts

**Record fields:**
- `failing_action`: What Claude was trying to do
- `retry_count`: Number of attempts
- `error_pattern`: Common error message or failure mode
- `resolved`: Whether the issue was eventually resolved
- `resolution`: How it was resolved (if applicable)
- `impact`: How much time/effort was lost (low/medium/high)

**Examples:**
- Regex pattern failing 4 times before finding the right escape sequence
- Build command failing repeatedly due to missing dependency
- File edit failing because old_string wasn't unique, retried with more context 3 times

---

### `wrong_info`

**Definition:** Claude stated something incorrect, used outdated information, or made an assumption that turned out to be wrong, requiring correction.

**Signals:**
- User correcting Claude's statement
- Claude's code/command failing because of incorrect assumption
- API calls using deprecated endpoints or wrong parameters
- File paths or function names that don't exist

**Record fields:**
- `incorrect_assertion`: What Claude stated or assumed
- `correction_source`: How the error was discovered (user correction, runtime error, etc.)
- `actual_truth`: The correct information
- `impact`: Consequence of the wrong information (low/medium/high)

**Examples:**
- Claude using a deprecated API parameter that no longer exists
- Assuming a function signature that doesn't match the actual code
- Stating a file exists at a path where it doesn't

---

## Proposing New Categories

When analyzing sessions, you may encounter gap patterns that don't fit the seed categories above. In such cases:

1. **Name the category** using `snake_case` (e.g., `context_loss`, `permission_gap`, `slow_feedback_loop`)
2. **Write a definition** following the format above
3. **List 2-3 signals** that indicate this gap type
4. **Provide at least 1 example** from the session data
5. **Explain why existing categories don't fit**

Novel categories are valuable — they represent previously unknown failure modes that could drive new features.
