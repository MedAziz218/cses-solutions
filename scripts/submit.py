#!/usr/bin/env python3
"""Test and submit one C++17 solution to CSES, with default-no confirmation."""

import argparse
import hashlib
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

import add_problem
from cses_config import get_credentials

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = add_problem.BASE_URL


class SubmissionFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.current = None
        self.in_language = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.current = {"attrs": attrs, "hidden": {}, "files": [], "languages": []}
        elif self.current is not None:
            if tag == "input":
                name = attrs.get("name", "")
                if attrs.get("type") == "hidden":
                    self.current["hidden"][name] = attrs.get("value", "")
                elif attrs.get("type") == "file":
                    self.current["files"].append(name)
            elif tag == "select":
                self.in_language = attrs.get("name") == "lang"
            elif tag == "option" and self.in_language:
                self.current["languages"].append(attrs.get("value", ""))

    def handle_endtag(self, tag):
        if tag == "select":
            self.in_language = False
        elif tag == "form" and self.current is not None:
            self.forms.append(self.current)
            self.current = None
            self.in_language = False


def submission_form(page, problem_id):
    parser = SubmissionFormParser()
    parser.feed(page)
    for form in parser.forms:
        fields = form["hidden"]
        if fields.get("task") != problem_id or "file" not in form["files"]:
            continue
        attrs = form["attrs"]
        url = urllib.parse.urljoin(BASE_URL, attrs.get("action", ""))
        if (url != BASE_URL + "/course/send.php"
                or attrs.get("method", "").lower() != "post"
                or attrs.get("enctype") != "multipart/form-data"
                or fields.get("type") != "course"
                or fields.get("target") != "problemset"
                or not fields.get("csrf_token")
                or "C++" not in form["languages"]
                or '"C++17"' not in page):
            raise ValueError("CSES submission form changed or does not support C++17; refusing to upload.")
        fields.update({"lang": "C++", "option": "C++17"})
        return url, fields
    raise ValueError("No matching submission form found; login or problem access may have failed.")


def multipart(fields, source):
    boundary = "cses-" + uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        if not re.fullmatch(r"[a-zA-Z0-9_]+", name):
            raise ValueError("Unexpected form field name; refusing to upload.")
        parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
                      f'\r\n\r\n{value}\r\n').encode())
    parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
                  'filename="main.cpp"\r\nContent-Type: text/plain\r\n\r\n').encode())
    parts.extend([source, f"\r\n--{boundary}--\r\n".encode()])
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def upload(opener, url, fields, source):
    body, content_type = multipart(fields, source)
    request = urllib.request.Request(url, data=body, headers={"Content-Type": content_type})
    # Exactly one upload attempt. A timeout may occur after the server accepted it.
    with opener.open(request, timeout=60) as response:
        result_url = response.geturl()
    result = urllib.parse.urlsplit(result_url)
    if (result.scheme != "https" or result.netloc != "cses.fi"
            or not re.fullmatch(r"/problemset/result/[0-9]+/?", result.path)):
        raise ValueError("Upload response did not identify a submission; check your CSES results before retrying.")
    return result_url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("problem_id")
    parser.add_argument("username", nargs="?", help="defaults to environment/.env or prompt")
    args = parser.parse_args()
    if not re.fullmatch(r"[1-9][0-9]*", args.problem_id):
        parser.error("problem_id must be a positive integer")
    source_path = ROOT / "problems" / args.problem_id / "main.cpp"
    if not source_path.is_file():
        parser.error(f"No solution at {source_path}")

    uploading = False
    try:
        source = source_path.read_bytes()
        # Do not let a caller's CASE selection skip any local tests.
        env = os.environ.copy()
        env.pop("CSES_TEST_CASES", None)
        subprocess.run(["make", "--no-print-directory", "test", f"ID={args.problem_id}", "CASE="],
                       cwd=ROOT, env=env, check=True)
        if source_path.read_bytes() != source:
            raise ValueError("Solution changed during testing; rerun submit to test the current file.")
        print(f"\nProblem: {args.problem_id}\nSource: {source_path}\nCompiler: C++17")
        print(f"SHA-256: {hashlib.sha256(source).hexdigest()}")
        if input("Submit to CSES? [y/N] ").strip().lower() not in {"y", "yes"}:
            print("Cancelled; nothing submitted.")
            return 0
        username, password = get_credentials(args.username, root=ROOT)
        opener = add_problem.authenticated_session(username, password)
        with opener.open(f"{BASE_URL}/problemset/submit/{args.problem_id}/", timeout=60) as response:
            page = response.read().decode("utf-8")
        url, fields = submission_form(page, args.problem_id)
        uploading = True
        result_url = upload(opener, url, fields, source)
        print(f"Submission created. Check the verdict: {result_url}")
        print("An uploaded submission is not necessarily an accepted solution.")
        return 0
    except subprocess.CalledProcessError:
        print("Local tests failed; nothing submitted.", file=sys.stderr)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        if uploading:
            print("Upload not confirmed. Do not blindly retry: check your submission history first.", file=sys.stderr)
            print(f"{BASE_URL}/problemset/view/{args.problem_id}/", file=sys.stderr)
        print(f"Error: {exc}", file=sys.stderr)
    except (KeyboardInterrupt, EOFError):
        if uploading:
            print(f"\nInterrupted during upload. Check {BASE_URL}/problemset/view/{args.problem_id}/ before retrying.",
                  file=sys.stderr)
        else:
            print("\nCancelled; nothing submitted.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
