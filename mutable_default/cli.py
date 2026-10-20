"""Command-line interface for mutable-default."""

import argparse
import json
import sys
from pathlib import Path

try:
    from .scanner import scan
except ImportError:  # pragma: no cover - script usage
    from scanner import scan


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="mutable-default",
        description="Detect mutable default argument values in Python code.",
    )
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--exclude", action="append", default=[],
                        help="directory or path to exclude (repeatable)")
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.exists():
        print(f"Path not found: {root}", file=sys.stderr)
        return 2

    hits = scan(str(root), exclude=args.exclude)

    if args.format == "json":
        payload = [
            {"path": h.path, "line": h.line, "function": h.function,
             "param": h.param, "kind": h.kind}
            for h in hits
        ]
        print(json.dumps(payload, indent=2))
        return 1 if hits else 0

    if not hits:
        print("No mutable default arguments found.")
        return 0

    for hit in hits:
        print(f"{hit.path}:{hit.line}: {hit.function}() param '{hit.param}' "
              f"has mutable default ({hit.kind})")
    print(f"\nFound {len(hits)} mutable default argument(s).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
