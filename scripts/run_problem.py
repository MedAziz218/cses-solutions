#!/usr/bin/env python3
"""Build once and run with stdin, or selected test inputs such as 2,3,5-9."""

import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def select_inputs(folder, selection):
    """Resolve all selected inputs before building; preserve order, remove duplicates."""
    paths = []
    seen = set()
    for item in selection.split(","):
        item = item.strip()
        if not re.fullmatch(r"[0-9]+(?:-[0-9]+)?", item):
            raise ValueError("Invalid case selection; use names, lists, or inclusive ranges: 2,3,5-9")
        if "-" in item:
            first, last = item.split("-")
            start, end = int(first), int(last)
            if start > end:
                raise ValueError(f"Descending range is not allowed: {item}")
            width = max(len(first), len(last)) if first.startswith("0") or last.startswith("0") else 0
            names = (str(number).zfill(width) for number in range(start, end + 1))
        else:
            names = (item,)
        for name in names:
            path = folder / "in" / f"{name}.txt"
            if not path.is_file():
                raise ValueError(f"Test input not found: {path}")
            if path not in seen:
                paths.append(path)
                seen.add(path)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("problem_id")
    parser.add_argument("cases", nargs="?", default="", help="e.g. 2,3 or 2-9 or 1,3-5")
    args = parser.parse_args()
    if not re.fullmatch(r"[1-9][0-9]*", args.problem_id):
        parser.error("problem_id must be a positive integer")
    try:
        inputs = select_inputs(ROOT / "problems" / args.problem_id, args.cases) if args.cases else []
        subprocess.run(["make", "--no-print-directory", "build", f"ID={args.problem_id}"],
                       cwd=ROOT, check=True)
        command = [str(ROOT / "build" / "problems" / args.problem_id / f"problem_{args.problem_id}")]
        if not inputs:
            return subprocess.run(command, cwd=ROOT).returncode
        for path in inputs:
            if len(inputs) > 1:
                print(f"\n=== test input {path.stem} ===", flush=True)
            with path.open("rb") as source:
                result = subprocess.run(command, cwd=ROOT, stdin=source)
            if result.returncode:
                print(f"Program failed on input {path.stem} (exit {result.returncode}).", file=sys.stderr)
                return result.returncode if result.returncode > 0 else 1
        return 0
    except subprocess.CalledProcessError:
        print("Build failed; nothing run.", file=sys.stderr)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        return 130
    return 1


if __name__ == "__main__":
    sys.exit(main())
