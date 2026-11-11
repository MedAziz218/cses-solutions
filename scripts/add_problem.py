#!/usr/bin/env python3
"""Create a CSES starter and download official tests (Python standard library only)."""

import argparse
from html.parser import HTMLParser
import http.cookiejar
import io
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from cses_config import get_credentials

BASE_URL = "https://cses.fi"
ROOT = Path(__file__).resolve().parents[1]
STARTER = """#include <iostream>
#include <string>
#include <vector>

using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // Single integer (long long for potentially large values):
    // long long n;
    // cin >> n;

    // Array of n integers (spaces and newlines both work):
    // int n;
    // cin >> n;
    // vector<long long> a(n);
    // for (auto& x : a) cin >> x;

    // One word (no spaces):
    // string s;
    // cin >> s;

    // Whole line (including spaces; use before any cin >> reads):
    // string line;
    // getline(cin, line);
    // If switching from cin >> to getline, discard the leftover newline first.

    // Output: cout << answer << '\\n';


    return 0;
}
"""


class StatementParser(HTMLParser):
    """Convert CSES statement containers to Markdown, excluding site navigation."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = []
        self.in_title = False
        self.parts = []
        self.stack = []
        self.pre = False
        self.found_statement = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "title":
            self.in_title = True
        if not self.stack:
            if tag == "div" and "md" in classes:
                self.found_statement = True
            elif not (tag == "ul" and "task-constraints" in classes):
                return
        if tag in {"br", "hr", "img", "input", "link", "meta", "wbr"}:
            if tag == "img":
                source = urllib.parse.urljoin(BASE_URL, attrs.get("src", ""))
                self.parts.append(f'![{attrs.get("alt", "")}]({source})')
            else:
                self.parts.append("\n")
            return
        opening, closing = "", ""
        if tag in {"p", "div", "ul", "ol"}:
            opening, closing = "\n\n", "\n\n"
        elif tag in {"h1", "h2", "h3", "h4"}:
            opening, closing = "\n\n" + "#" * (int(tag[1]) + 1) + " ", "\n\n"
        elif tag == "li":
            opening, closing = "\n- ", "\n"
        elif tag == "pre":
            opening, closing = "\n\n```text\n", "\n```\n\n"
            self.pre = True
        elif tag in {"b", "strong"}:
            opening = closing = "**"
        elif tag in {"i", "em"}:
            opening = closing = "*"
        elif tag == "code" and not self.pre:
            opening = closing = "`"
        elif tag == "span" and "math" in classes:
            opening = closing = "$$" if "math-display" in classes else "$"
            if "math-display" in classes:
                opening, closing = "\n\n$$\n", "\n$$\n\n"
        elif tag == "a":
            opening = "["
            closing = "](" + urllib.parse.urljoin(BASE_URL, attrs.get("href", "")) + ")"
        self.parts.append(opening)
        self.stack.append((tag, closing))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if self.stack and self.stack[-1][0] == tag:
            self.parts.append(self.stack.pop()[1])
            if tag == "pre":
                self.pre = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if self.stack:
            self.parts.append(data if self.pre else re.sub(r"\s+", " ", data))

    def markdown(self, problem_id):
        if not self.found_statement:
            raise ValueError("CSES did not provide a problem statement.")
        title = "".join(self.title).removeprefix("CSES - ").strip()
        # Clean structural whitespace without changing sample indentation/content.
        sections = "".join(self.parts).split("```text\n")
        body = re.sub(r"\n[ \t]+", "\n", sections[0])
        body = re.sub(r"\n{3,}", "\n\n", body)
        for section in sections[1:]:
            code, separator, rest = section.partition("\n```")
            rest = re.sub(r"\n[ \t]+", "\n", rest)
            rest = re.sub(r"\n{3,}", "\n\n", rest)
            body += "```text\n" + code.rstrip("\n") + separator + rest
        return f"# {title or problem_id}\n\nSource: {BASE_URL}/problemset/task/{problem_id}/\n\n{body.strip()}\n"


def download_statement(problem_id):
    with urllib.request.urlopen(f"{BASE_URL}/problemset/task/{problem_id}/", timeout=60) as response:
        parser = StatementParser()
        parser.feed(response.read().decode("utf-8"))
    return parser.markdown(problem_id)


def csrf_token(page):
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', page)
    if not match:
        raise ValueError("CSES did not provide a CSRF token; the page may have changed.")
    return match.group(1)


def authenticated_session(username, password):
    # Cookies stay in memory and are never saved to disk.
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )

    def request(path, fields=None):
        data = urllib.parse.urlencode(fields).encode() if fields is not None else None
        with opener.open(BASE_URL + path, data=data, timeout=60) as response:
            return response.read()

    login = request("/login").decode()
    result = request("/login", {
        "csrf_token": csrf_token(login), "nick": username, "pass": password,
    }).decode()
    if 'href="/logout"' not in result:
        raise ValueError("Login failed. Check your username and password.")

    return opener


def download_tests(problem_id, username, password):
    opener = authenticated_session(username, password)
    url = f"{BASE_URL}/problemset/tests/{problem_id}/"
    with opener.open(url, timeout=60) as response:
        page = response.read().decode()
    data = urllib.parse.urlencode({"csrf_token": csrf_token(page), "download": "true"}).encode()
    with opener.open(url, data=data, timeout=60) as response:
        return response.read()


def extract_tests(folder, archive_data):
    """Validate the archive and write only numbered input/output pairs."""
    with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
        tests = {}
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            match = re.fullmatch(r"([0-9]+)\.(in|out)", entry.filename)
            if not match:
                raise ValueError(f"Unexpected file in test archive: {entry.filename!r}")
            key = match.groups()
            if key in tests:
                raise ValueError(f"Duplicate test file: {entry.filename}")
            tests[key] = entry
        inputs = {number for number, kind in tests if kind == "in"}
        outputs = {number for number, kind in tests if kind == "out"}
        if not inputs or inputs != outputs:
            raise ValueError("Archive has no tests or has unmatched inputs/outputs.")

        (folder / "in").mkdir()
        (folder / "out").mkdir()
        for (number, kind), entry in tests.items():
            target = folder / ("in" if kind == "in" else "out")
            target /= number + (".txt" if kind == "in" else ".out")
            target.write_bytes(archive.read(entry))

    return len(inputs)


def restore_tests(folder, archive_data):
    """Restore missing tests without overwriting differing local test files."""
    with tempfile.TemporaryDirectory(prefix=".cses-add-", dir=folder.parent) as temp:
        staged = Path(temp)
        count = extract_tests(staged, archive_data)
        files = [path for kind in ("in", "out") for path in (staged / kind).iterdir()]
        # Check all conflicts before changing anything in the destination.
        for source in files:
            target = folder / source.relative_to(staged)
            if target.exists() and target.read_bytes() != source.read_bytes():
                raise ValueError(f"Local test differs; refusing to overwrite: {target}")
        for source in files:
            target = folder / source.relative_to(staged)
            target.parent.mkdir(exist_ok=True)
            if not target.exists():
                shutil.copyfile(source, target)
        return count


def has_tests(folder):
    inputs = {path.stem for path in (folder / "in").glob("*.txt")}
    outputs = {path.stem for path in (folder / "out").glob("*.out")}
    return bool(inputs) and inputs == outputs


def prepare_problem(folder, problem_id, archive_data):
    count = extract_tests(folder, archive_data)
    (folder / "main.cpp").write_text(STARTER)
    (folder / "CMakeLists.txt").write_text("""add_executable(problem_@ID@ main.cpp)

add_custom_target(test_@ID@
    COMMAND "${CMAKE_COMMAND}"
        "-DPROG=$<TARGET_FILE:problem_@ID@>"
        "-DTEST_DIR=${CMAKE_CURRENT_SOURCE_DIR}"
        "-DBINARY_DIR=${CMAKE_CURRENT_BINARY_DIR}"
        -P "${CMAKE_SOURCE_DIR}/cmake/test_runner.cmake"
    WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
    DEPENDS problem_@ID@
    COMMENT "Running tests for problem @ID@..."
    VERBATIM
)
""".replace("@ID@", problem_id))
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("problem_id", help="CSES problem ID, e.g. 1070")
    parser.add_argument("username", nargs="?", help="defaults to environment/.env or prompt")
    parser.add_argument("password", nargs="?", help="defaults to environment/.env or hidden prompt")
    parser.add_argument("--tests-only", action="store_true",
                        help="restore tests for an existing problem without changing its sources")
    args = parser.parse_args()
    if not re.fullmatch(r"[1-9][0-9]*", args.problem_id):
        parser.error("problem_id must be a positive integer")

    destination = ROOT / "problems" / args.problem_id
    if args.tests_only:
        if not (destination / "main.cpp").is_file():
            parser.error(f"No existing problem at {destination}")
    elif destination.exists():
        parser.error(f"{destination} already exists; refusing to overwrite your work")

    try:
        username, password = get_credentials(args.username, args.password, root=ROOT)
        if args.tests_only:
            count = restore_tests(destination, download_tests(args.problem_id, username, password))
            print(f"Restored {count} tests in {destination}; sources unchanged.")
            return 0
        print(f"Downloading statement and tests for {args.problem_id}...")
        statement = download_statement(args.problem_id)
        archive_data = download_tests(args.problem_id, username, password)
        cmake_path = ROOT / "problems" / "CMakeLists.txt"
        cmake = cmake_path.read_text()
        registration = f"add_subdirectory({args.problem_id})"
        if not re.search(r"(?m)^\s*add_subdirectory\(\s*" + re.escape(args.problem_id) + r"\s*\)", cmake):
            cmake = cmake.rstrip() + "\n" + registration + "\n"

        # Stage everything before creating the problem directory or changing CMake.
        with tempfile.TemporaryDirectory(prefix=".cses-add-", dir=ROOT) as temp:
            staged = Path(temp) / args.problem_id
            staged.mkdir()
            count = prepare_problem(staged, args.problem_id, archive_data)
            (staged / "statement.md").write_text(statement, encoding="utf-8")
            if destination.exists():
                raise ValueError("Problem directory appeared during download; refusing to overwrite.")
            staged.rename(destination)
            try:
                cmake_path.write_text(cmake)
            except OSError:
                shutil.rmtree(destination)
                raise
        print(f"Created {destination} with statement.md, {count} official tests, and an empty main.cpp.")
        print("Configure: cmake -S . -B build")
        print(f"Build:     cmake --build build --target problem_{args.problem_id}")
        print(f"Test:      cmake --build build --target test_{args.problem_id}")
        return 0
    except urllib.error.HTTPError as exc:
        print(f"Error: CSES returned HTTP {exc.code}; check the problem ID and access.", file=sys.stderr)
    except (OSError, ValueError, zipfile.BadZipFile, urllib.error.URLError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
