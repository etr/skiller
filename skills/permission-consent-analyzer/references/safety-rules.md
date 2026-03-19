# Permission Safety Classification Rules

Use these seed heuristics when classifying permission patterns. These are guidelines — use judgment for edge cases.

## Safe

Patterns that only read data or perform side-effect-free operations:

- `Read` — reading files (scoped or unscoped)
- `Glob` — file pattern matching
- `Grep` — content search
- `WebSearch` — web search queries
- `Bash(git status:*)`, `Bash(git log:*)`, `Bash(git diff:*)`, `Bash(git branch:*)` — read-only git
- `Bash(ls:*)`, `Bash(cat:*)`, `Bash(head:*)`, `Bash(tail:*)`, `Bash(wc:*)` — read-only shell
- `Bash(echo:*)`, `Bash(printf:*)` — output only
- `Bash(which:*)`, `Bash(command:*)`, `Bash(type:*)` — command lookup
- MCP tools that only read data (e.g., `mcp__*__read_*`, `mcp__*__search_*`, `mcp__*__list_*`)

## Caution

Patterns that modify local state or could have broader effects depending on arguments:

- `Bash(git:*)` — broad git access includes push, reset, rebase
- `Bash(npm:*)`, `Bash(npx:*)`, `Bash(pip:*)`, `Bash(yarn:*)`, `Bash(pnpm:*)` — package managers execute arbitrary code
- `Bash(python3:*)`, `Bash(python:*)`, `Bash(node:*)` — script execution
- `Bash(make:*)`, `Bash(cargo:*)`, `Bash(go:*)` — build tools
- `Write` (scoped to project) — file writes within a known directory
- `Edit` (scoped to project) — file edits within a known directory
- `WebFetch(domain:...)` — network access to specific domains
- `Bash(docker:*)` — container operations
- `Bash(gh:*)` — GitHub CLI (can create PRs, issues, comments)

## Unsafe

Patterns that are destructive, grant broad system access, or reach external systems without restriction:

- `Bash` (unscoped) — arbitrary shell command execution
- `Write` (unscoped) — write to any file on the system
- `Bash(rm:*)` — file deletion
- `Bash(chmod:*)`, `Bash(chown:*)` — permission changes
- `Bash(sudo:*)` — elevated privileges
- `Bash(curl:*)`, `Bash(wget:*)` — unscoped network access
- `WebFetch` (unscoped) — fetch any URL
- `Bash(ssh:*)`, `Bash(scp:*)` — remote system access
- `Bash(kill:*)`, `Bash(pkill:*)` — process management
- `Bash(mv:*)` when unscoped — file moves across the system
