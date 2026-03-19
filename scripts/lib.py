"""Shared utilities for the skiller plugin."""

import json
import os
import re
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlparse

SKILLER_ROOT = Path.home() / ".claude" / "skiller"
SESSIONS_ROOT = SKILLER_ROOT / "sessions"
REPORTS_ROOT = SKILLER_ROOT / "reports"


def get_sessions_root() -> Path:
    """Return the sessions root directory, creating it if needed."""
    SESSIONS_ROOT.mkdir(parents=True, exist_ok=True)
    return SESSIONS_ROOT


def get_reports_root() -> Path:
    """Return the reports root directory, creating it if needed."""
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    return REPORTS_ROOT


def get_session_dir(session_id: str) -> Path:
    """Return the directory for a specific session."""
    return get_sessions_root() / session_id


def append_event(session_id: str, record: dict) -> None:
    """Append a structured JSON record to a session's events.jsonl."""
    session_dir = get_session_dir(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    events_file = session_dir / "events.jsonl"
    with open(events_file, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def truncate(value, max_len: int = 2000) -> str:
    """Truncate a string value to max_len characters."""
    if not isinstance(value, str):
        value = json.dumps(value, default=str)
    if len(value) > max_len:
        return value[:max_len] + "...[truncated]"
    return value


# ---------------------------------------------------------------------------
# Permission utilities (PRD-PERM)
# ---------------------------------------------------------------------------

def get_session_cwd(session_id: str) -> str | None:
    """Read cwd.txt from a session directory, return None if not found."""
    cwd_file = get_session_dir(session_id) / "cwd.txt"
    try:
        return cwd_file.read_text().strip() or None
    except (OSError, IOError):
        return None


def load_settings_permissions(cwd: str | None = None) -> list[str]:
    """Load and merge permissions.allow from all applicable settings files."""
    paths = [
        Path.home() / ".claude" / "settings.json",
        Path.home() / ".claude" / "settings.local.json",
    ]
    if cwd:
        paths.append(Path(cwd) / ".claude" / "settings.json")
        paths.append(Path(cwd) / ".claude" / "settings.local.json")

    all_perms: list[str] = []
    for p in paths:
        try:
            data = json.loads(p.read_text())
            perms = data.get("permissions", {}).get("allow", [])
            if isinstance(perms, list):
                all_perms.extend(perms)
        except (OSError, IOError, json.JSONDecodeError, TypeError):
            continue
    return all_perms


def parse_permission(perm: str) -> tuple[str, str | None]:
    """Parse a permission string into (tool_name, scope_or_None).

    Examples:
        "Read"                           -> ("Read", None)
        "Bash(git:*)"                    -> ("Bash", "git:*")
        "Read(//home/etr/progs/**)"      -> ("Read", "//home/etr/progs/**")
        "WebFetch(domain:example.com)"   -> ("WebFetch", "domain:example.com")
        "mcp__wonk__wonk_summary"        -> ("mcp__wonk__wonk_summary", None)
    """
    m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\((.+)\)$', perm)
    if m:
        return m.group(1), m.group(2)
    return perm, None


def _extract_command(tool_input: dict | str | None) -> str:
    """Extract the command string from Bash tool_input."""
    if isinstance(tool_input, dict):
        return tool_input.get("command", "")
    if isinstance(tool_input, str):
        try:
            parsed = json.loads(tool_input)
            if isinstance(parsed, dict):
                return parsed.get("command", "")
        except (json.JSONDecodeError, TypeError):
            pass
        return tool_input
    return ""


def _extract_path(tool_input: dict | str | None) -> str:
    """Extract the file_path from Read/Write/Edit tool_input."""
    if isinstance(tool_input, dict):
        return tool_input.get("file_path", tool_input.get("path", ""))
    if isinstance(tool_input, str):
        try:
            parsed = json.loads(tool_input)
            if isinstance(parsed, dict):
                return parsed.get("file_path", parsed.get("path", ""))
        except (json.JSONDecodeError, TypeError):
            pass
    return ""


def _extract_url(tool_input: dict | str | None) -> str:
    """Extract URL from WebFetch tool_input."""
    if isinstance(tool_input, dict):
        return tool_input.get("url", "")
    if isinstance(tool_input, str):
        try:
            parsed = json.loads(tool_input)
            if isinstance(parsed, dict):
                return parsed.get("url", "")
        except (json.JSONDecodeError, TypeError):
            pass
    return ""


def matches_permission(tool_name: str, tool_input, perm_tool: str, perm_scope: str | None) -> bool:
    """Check if a (tool_name, tool_input) pair matches a parsed permission."""
    if tool_name != perm_tool:
        # MCP/skill tools: tool_name is the full string, perm has no scope
        if perm_scope is None and tool_name == perm_tool:
            return True
        return False

    # Bare tool name — matches everything for that tool
    if perm_scope is None:
        return True

    if tool_name == "Bash":
        cmd = _extract_command(tool_input)
        if perm_scope.endswith(":*"):
            prefix = perm_scope[:-2]  # e.g. "git"
            # Command starts with prefix (first word or prefix followed by space)
            return cmd == prefix or cmd.startswith(prefix + " ")
        else:
            # Literal match
            return cmd == perm_scope

    if tool_name in ("Read", "Write", "Edit", "Glob"):
        path = _extract_path(tool_input)
        if perm_scope.startswith("//"):
            # Path glob — // prefix maps to / (absolute path root)
            pattern = "/" + perm_scope[2:]
            return fnmatch(path, pattern)
        return False

    if tool_name == "WebFetch":
        url = _extract_url(tool_input)
        if perm_scope.startswith("domain:"):
            domain = perm_scope[7:]
            try:
                parsed = urlparse(url)
                return parsed.hostname == domain or (parsed.hostname or "").endswith("." + domain)
            except Exception:
                return False
        return False

    return False


def is_pre_allowed(tool_name: str, tool_input, permissions: list[str]) -> bool:
    """Return True if the tool call matches any permission in the allow list."""
    for perm in permissions:
        perm_tool, perm_scope = parse_permission(perm)
        if matches_permission(tool_name, tool_input, perm_tool, perm_scope):
            return True
    return False


def suggest_permission_pattern(tool_name: str, tool_input) -> str:
    """Generate a heuristic permission pattern string for a tool call."""
    if tool_name == "Bash":
        cmd = _extract_command(tool_input)
        first_word = cmd.split()[0] if cmd.split() else ""
        if first_word:
            return f"Bash({first_word}:*)"
        return "Bash"

    if tool_name in ("Read", "Write", "Edit"):
        path = _extract_path(tool_input)
        if path:
            # Use the first few directory components as a glob
            parts = Path(path).parts
            # For absolute paths like ('/', 'home', 'etr', 'progs', 'foo.py'),
            # take up to 4 parts (/, home, etr, progs) to get a meaningful base
            depth = 4 if len(parts) >= 4 else len(parts) - 1
            if depth >= 2:
                base = str(Path(*parts[:depth]))
                # Strip leading / since // prefix is the Claude Code format marker
                base = base.lstrip("/")
                return f"{tool_name}(//{base}/**)"
        return tool_name

    if tool_name == "WebFetch":
        url = _extract_url(tool_input)
        try:
            parsed = urlparse(url)
            if parsed.hostname:
                return f"WebFetch(domain:{parsed.hostname})"
        except Exception:
            pass
        return "WebFetch"

    if tool_name == "Glob":
        path = ""
        if isinstance(tool_input, dict):
            path = tool_input.get("path", "")
        if path:
            parts = Path(path).parts
            depth = 4 if len(parts) >= 4 else len(parts)
            if depth >= 2:
                base = str(Path(*parts[:depth])).lstrip("/")
                return f"Glob(//{base}/**)"
        return "Glob"

    if tool_name == "Grep":
        path = ""
        if isinstance(tool_input, dict):
            path = tool_input.get("path", "")
        if path:
            parts = Path(path).parts
            depth = 4 if len(parts) >= 4 else len(parts)
            if depth >= 2:
                base = str(Path(*parts[:depth])).lstrip("/")
                return f"Grep(//{base}/**)"
        return "Grep"

    # MCP tools, Agent, etc. — bare name
    return tool_name
