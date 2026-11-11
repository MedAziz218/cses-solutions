#!/usr/bin/env python3
"""Restore local CSES tests and configure CMake after cloning."""

import argparse
import shutil
import subprocess
import sys
import urllib.error
import zipfile

import add_problem
from cses_config import get_credentials


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username", nargs="?", help="CSES username; prompted only if tests are missing")
    args = parser.parse_args()
    missing_tools = [tool for tool in ("cmake", "c++", "make") if not shutil.which(tool)]
    if missing_tools:
        print("Install these prerequisites first: " + ", ".join(missing_tools), file=sys.stderr)
        return 1

    root = add_problem.ROOT
    folders = sorted(path.parent for path in (root / "problems").glob("*/main.cpp")
                     if path.parent.name.isdigit())
    missing = [folder for folder in folders if not add_problem.has_tests(folder)]
    try:
        if missing:
            username, password = get_credentials(args.username, root=root)
            for folder in missing:
                print(f"Downloading tests for {folder.name}...", flush=True)
                data = add_problem.download_tests(folder.name, username, password)
                count = add_problem.restore_tests(folder, data)
                print(f"Restored {count} tests for {folder.name}.")
        else:
            print("No missing test sets; no login needed.", flush=True)
        print(f"Skipped {len(folders) - len(missing)} existing test sets.", flush=True)
        subprocess.run(["cmake", "-S", str(root), "-B", str(root / "build")], check=True)
        print("Ready. Use make / just to build, or just test ID to test a problem.")
        return 0
    except urllib.error.HTTPError as exc:
        print(f"Error: CSES returned HTTP {exc.code}; check your account and problem access.", file=sys.stderr)
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
