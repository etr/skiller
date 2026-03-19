#!/usr/bin/env python3
"""Scan session events for PermissionGrant patterns and output JSON summary.

Usage: python3 scan_permissions.py [--min-sessions N]

Reads all events.jsonl files under ~/.claude/skiller/sessions/,
filters PermissionGrant events, groups by (tool_name, permission_pattern),
counts frequency across sessions (not just total events), and outputs
a JSON summary to stdout.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SESSIONS_ROOT = Path.home() / ".claude" / "skiller" / "sessions"


def scan_sessions(min_sessions: int = 3, since: datetime | None = None) -> dict:
    """Scan all sessions for PermissionGrant events."""
    if not SESSIONS_ROOT.exists():
        return {"patterns": [], "total_sessions": 0, "sessions_with_grants": 0}

    # pattern_key -> { sessions: set, total_count: int, examples: list }
    patterns: dict[str, dict] = defaultdict(lambda: {
        "sessions": set(),
        "total_count": 0,
        "examples": [],
    })
    total_sessions = 0
    sessions_with_grants = set()

    for session_dir in SESSIONS_ROOT.iterdir():
        if not session_dir.is_dir():
            continue
        events_file = session_dir / "events.jsonl"
        if not events_file.exists():
            continue

        # --since filter: skip sessions older than the cutoff
        if since is not None:
            try:
                first_line = events_file.read_text().split("\n", 1)[0]
                ts = datetime.fromisoformat(json.loads(first_line)["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < since:
                    continue
            except Exception:
                pass  # include session if timestamp is unparseable

        total_sessions += 1
        session_id = session_dir.name

        try:
            for line in events_file.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if event.get("event_type") != "PermissionGrant":
                    continue

                sessions_with_grants.add(session_id)
                tool_name = event.get("tool_name", "")
                pattern = event.get("permission_pattern", tool_name)
                key = f"{tool_name}|{pattern}"

                entry = patterns[key]
                entry["sessions"].add(session_id)
                entry["total_count"] += 1

                # Keep up to 5 example tool_inputs per pattern
                if len(entry["examples"]) < 5:
                    tool_input = event.get("tool_input", {})
                    example = _summarize_input(tool_name, tool_input)
                    if example and example not in entry["examples"]:
                        entry["examples"].append(example)
        except (OSError, IOError):
            continue

    # Build output, filtering by min_sessions
    result_patterns = []
    for key, data in sorted(patterns.items(), key=lambda x: len(x[1]["sessions"]), reverse=True):
        session_count = len(data["sessions"])
        if session_count < min_sessions:
            continue
        tool_name, pattern = key.split("|", 1)
        result_patterns.append({
            "tool_name": tool_name,
            "permission_pattern": pattern,
            "session_count": session_count,
            "total_count": data["total_count"],
            "examples": data["examples"],
        })

    return {
        "patterns": result_patterns,
        "total_sessions": total_sessions,
        "sessions_with_grants": len(sessions_with_grants),
    }


def _summarize_input(tool_name: str, tool_input: dict) -> str:
    """Create a short human-readable summary of a tool_input."""
    if not isinstance(tool_input, dict):
        return ""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return cmd[:120] if cmd else ""
    if tool_name in ("Read", "Write", "Edit"):
        return tool_input.get("file_path", tool_input.get("path", ""))[:120]
    if tool_name == "WebFetch":
        return tool_input.get("url", "")[:120]
    if tool_name in ("Glob", "Grep"):
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", "")
        return f"{pattern} in {path}"[:120] if path else pattern[:120]
    # Generic: first key's value
    for v in tool_input.values():
        if isinstance(v, str):
            return v[:120]
    return ""


def main():
    parser = argparse.ArgumentParser(description="Scan sessions for permission patterns")
    parser.add_argument("--min-sessions", type=int, default=3,
                        help="Minimum sessions a pattern must appear in (default: 3)")
    parser.add_argument("--since", type=str, default=None,
                        help="ISO 8601 timestamp; skip sessions older than this")
    args = parser.parse_args()

    since = None
    if args.since:
        since = datetime.fromisoformat(args.since)
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

    result = scan_sessions(min_sessions=args.min_sessions, since=since)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
