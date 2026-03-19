#!/usr/bin/env python3
"""
Skiller instrumentation hook.

Single handler for all 9 Claude Code lifecycle events.
Reads event JSON from stdin, appends structured records to
~/.claude/skiller/sessions/<session_id>/events.jsonl.

Errors are logged as InstrumentationError events and never disrupt the session.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts/ to path for shared utilities
_plugin_root = os.environ.get(
    "CLAUDE_PLUGIN_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
sys.path.insert(0, os.path.join(_plugin_root, "scripts"))

from lib import (
    append_event,
    delete_old_sessions,
    get_session_cwd,
    get_session_dir,
    is_pre_allowed,
    load_settings_permissions,
    suggest_permission_pattern,
    truncate,
)


def build_record(event: dict) -> dict:
    """Build a structured event record from hook input."""
    hook_event = event.get("hook_event_name", "Unknown")
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": hook_event,
        "session_id": event.get("session_id", "unknown"),
    }

    if hook_event in ("PreToolUse", "PostToolUse"):
        record["tool_name"] = event.get("tool_name")
        tool_input = event.get("tool_input")
        if tool_input is not None:
            record["tool_input"] = json.loads(truncate(tool_input, 4000))  \
                if isinstance(tool_input, str) else tool_input
        if hook_event == "PreToolUse":
            # PRD-PERM-REQ-002: Check if this tool call is pre-allowed
            try:
                cwd = get_session_cwd(event.get("session_id", "unknown"))
                perms = load_settings_permissions(cwd)
                record["pre_allowed"] = is_pre_allowed(
                    event.get("tool_name", ""), tool_input, perms
                )
            except Exception:
                record["pre_allowed"] = False
        if hook_event == "PostToolUse":
            record["tool_result"] = truncate(event.get("tool_result", ""), 2000)

    elif hook_event == "UserPromptSubmit":
        record["user_prompt"] = truncate(event.get("user_prompt", ""), 4000)

    elif hook_event in ("Stop", "SubagentStop"):
        record["reason"] = event.get("reason")

    elif hook_event == "SessionStart":
        record["transcript_path"] = event.get("transcript_path")
        record["cwd"] = event.get("cwd")

    elif hook_event == "SessionEnd":
        record["transcript_path"] = event.get("transcript_path")

    elif hook_event == "PreCompact":
        record["cwd"] = event.get("cwd")

    return record


def emit_synthetic_subagent_start(event: dict) -> None:
    """Emit a synthetic SubagentStart event when Agent tool is called."""
    tool_input = event.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "SubagentStart",
        "session_id": event.get("session_id", "unknown"),
        "subagent_type": tool_input.get("subagent_type", "general-purpose"),
        "prompt": truncate(tool_input.get("prompt", ""), 500),
        "description": tool_input.get("description", ""),
        "synthetic": True,
    }
    append_event(record["session_id"], record)


def write_session_cwd(event: dict, session_dir: Path) -> None:
    """On SessionStart, persist cwd to session directory (PRD-PERM-REQ-001)."""
    cwd = event.get("cwd")
    if cwd:
        cwd_file = session_dir / "cwd.txt"
        if not cwd_file.exists():
            cwd_file.write_text(cwd)


def emit_permission_grant(event: dict) -> None:
    """Emit synthetic PermissionGrant for non-pre-allowed tools (PRD-PERM-REQ-003)."""
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input")
    session_id = event.get("session_id", "unknown")

    # Re-check if pre-allowed (PostToolUse doesn't carry the flag)
    try:
        cwd = get_session_cwd(session_id)
        perms = load_settings_permissions(cwd)
        if is_pre_allowed(tool_name, tool_input, perms):
            return
    except Exception:
        pass

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "PermissionGrant",
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input if isinstance(tool_input, dict) else {},
        "permission_pattern": suggest_permission_pattern(tool_name, tool_input),
        "synthetic": True,
    }
    append_event(session_id, record)


def symlink_transcript(event: dict, session_dir: Path) -> None:
    """On SessionEnd, create a symlink to the transcript file."""
    transcript = event.get("transcript_path")
    if not transcript:
        return
    transcript_path = Path(transcript)
    if not transcript_path.exists():
        return
    link_path = session_dir / "transcript.jsonl"
    if link_path.exists():
        return
    try:
        link_path.symlink_to(transcript_path)
    except OSError:
        # Fallback: store the path as a text reference
        (session_dir / "transcript_ref.txt").write_text(transcript)


def main():
    raw = ""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"continue": True}))
            return

        event = json.loads(raw)
        session_id = event.get("session_id", "unknown")
        hook_event = event.get("hook_event_name", "Unknown")

        # Ensure session directory exists
        session_dir = get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        # Build and append the main event record
        record = build_record(event)
        append_event(session_id, record)

        # Write cwd on session start (PRD-PERM-REQ-001)
        if hook_event == "SessionStart":
            write_session_cwd(event, session_dir)
            try:
                delete_old_sessions()
            except Exception:
                pass

        # Synthetic SubagentStart for Agent tool calls (PRD-INS-REQ-004)
        if hook_event == "PreToolUse" and event.get("tool_name") == "Agent":
            emit_synthetic_subagent_start(event)

        # Emit PermissionGrant for non-pre-allowed tools (PRD-PERM-REQ-003)
        if hook_event == "PostToolUse":
            emit_permission_grant(event)

        # Symlink transcript on session end (PRD-INS-REQ-005)
        if hook_event == "SessionEnd":
            symlink_transcript(event, session_dir)

    except Exception as e:
        # PRD-INS-REQ-006: Log errors, never disrupt the session
        try:
            sid = "unknown"
            try:
                sid = json.loads(raw).get("session_id", "unknown") if raw else "unknown"
            except Exception:
                pass
            error_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "InstrumentationError",
                "session_id": sid,
                "error": str(e),
            }
            append_event(sid, error_record)
        except Exception:
            pass  # Last resort: silently fail

    # Always output continue and exit 0
    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
