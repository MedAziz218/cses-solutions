#!/usr/bin/env python3
"""Open a problem's main.cpp in a configurable editor."""

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

from cses_config import read_dotenv

ROOT = Path(__file__).resolve().parents[1]


def editor_command(override=None):
    local = read_dotenv(ROOT)
    command = (override or os.environ.get("CSES_EDITOR") or local.get("CSES_EDITOR")
               or os.environ.get("VISUAL") or os.environ.get("EDITOR") or "code")
    args = shlex.split(command)
    if not args:
        raise ValueError("Editor command is empty.")
    return args


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("problem_id")
    parser.add_argument("--editor", help="editor command, e.g. 'vim' or 'code --wait'")
    args = parser.parse_args()
    if not re.fullmatch(r"[1-9][0-9]*", args.problem_id):
        parser.error("problem_id must be a positive integer")
    source = ROOT / "problems" / args.problem_id / "main.cpp"
    if not source.is_file():
        print(f"Problem not found: {source}. Add it first with just add {args.problem_id}.", file=sys.stderr)
        return 1
    try:
        command = editor_command(args.editor)
        # No shell evaluation; editor arguments and file paths stay separate.
        return subprocess.run(command + [str(source)], cwd=ROOT).returncode
    except FileNotFoundError:
        print("Editor executable not found. Set CSES_EDITOR in .env or pass --editor.", file=sys.stderr)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        return 130
    return 1


if __name__ == "__main__":
    sys.exit(main())
