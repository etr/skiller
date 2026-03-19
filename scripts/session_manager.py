#!/usr/bin/env python3
"""Manage session lifecycle: list eligible sessions, cleanup old ones, markers.

Subcommands:
  list    --type TYPE [--max-age DAYS]   Print eligible session directory paths
  cleanup [--max-age DAYS]               Delete old sessions, print deleted IDs
  mark    --type TYPE                    Update analysis marker, print timestamp
  cutoff  --type TYPE [--max-age DAYS]   Print ISO 8601 cutoff timestamp
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

# Add scripts/ to path for shared utilities (same pattern as hooks/instrument.py)
_plugin_root = os.environ.get(
    "CLAUDE_PLUGIN_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
sys.path.insert(0, os.path.join(_plugin_root, "scripts"))

from lib import (
    delete_old_sessions,
    get_analysis_marker,
    get_eligible_sessions,
    set_analysis_marker,
)


def cmd_list(args):
    sessions = get_eligible_sessions(args.type, max_age_days=args.max_age)
    for s in sessions:
        print(s)


def cmd_cleanup(args):
    deleted = delete_old_sessions(max_age_days=args.max_age)
    for sid in deleted:
        print(sid)


def cmd_mark(args):
    set_analysis_marker(args.type)
    marker = get_analysis_marker(args.type)
    if marker is not None:
        print(marker.isoformat())


def cmd_cutoff(args):
    now = datetime.now(timezone.utc)
    age_cutoff = now - timedelta(days=args.max_age)

    marker = get_analysis_marker(args.type)
    if marker is not None:
        if marker.tzinfo is None:
            marker = marker.replace(tzinfo=timezone.utc)
        cutoff = max(marker, age_cutoff)
    else:
        cutoff = age_cutoff

    print(cutoff.isoformat())


def main():
    parser = argparse.ArgumentParser(description="Skiller session manager")
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List eligible session directories")
    p_list.add_argument("--type", required=True, help="Analysis type (e.g. gap-analyzer)")
    p_list.add_argument("--max-age", type=int, default=30, help="Max session age in days (default: 30)")
    p_list.set_defaults(func=cmd_list)

    # cleanup
    p_cleanup = sub.add_parser("cleanup", help="Delete old sessions")
    p_cleanup.add_argument("--max-age", type=int, default=30, help="Max session age in days (default: 30)")
    p_cleanup.set_defaults(func=cmd_cleanup)

    # mark
    p_mark = sub.add_parser("mark", help="Update analysis marker")
    p_mark.add_argument("--type", required=True, help="Analysis type")
    p_mark.set_defaults(func=cmd_mark)

    # cutoff
    p_cutoff = sub.add_parser("cutoff", help="Print cutoff timestamp")
    p_cutoff.add_argument("--type", required=True, help="Analysis type")
    p_cutoff.add_argument("--max-age", type=int, default=30, help="Max session age in days (default: 30)")
    p_cutoff.set_defaults(func=cmd_cutoff)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
