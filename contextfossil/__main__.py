from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import diff, dump, load, snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture and diff the ambient context visible to a coding agent.")
    sub = parser.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot", help="capture workspace context metadata")
    snap.add_argument("workspace", nargs="?", default=".")
    snap.add_argument("-o", "--output", required=True, type=Path)

    compare = sub.add_parser("diff", help="compare two ContextFossil snapshots")
    compare.add_argument("before", type=Path)
    compare.add_argument("after", type=Path)
    compare.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            dump(snapshot(Path(args.workspace)), args.output)
            print(f"wrote {args.output}")
            return 0
        result = diff(load(args.before), load(args.after))
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        elif not result["changed"]:
            print("No material context drift detected.")
        else:
            print(f"{result['count']} material context change(s) detected:")
            for change in result["changes"]:
                print(f"- {change['kind']}")
        return 1 if result["changed"] else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"contextfossil: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
