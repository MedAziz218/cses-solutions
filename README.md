# CSES Problem Set

My C++ solutions to the [CSES Problem Set](https://cses.fi/problemset/), added
incrementally. Solutions and statements are committed; official test cases stay local.

## Layout

```text
problems/
├── CMakeLists.txt          # Registered problems
├── 1068/
│   ├── main.cpp            # Solution to submit
│   ├── statement.md        # Problem statement, limits, and examples
│   ├── CMakeLists.txt
│   ├── in/                 # Local test inputs (*.txt), ignored by Git
│   └── out/                # Local expected outputs (*.out), ignored by Git
└── ...
scripts/
├── add_problem.py          # Creates a starter or restores tests only
├── init.py                 # Fresh-clone setup
├── cses_config.py          # Local credential loading
├── open_problem.py         # Configurable editor shortcut
├── run_problem.py          # Stdin or selected test inputs
└── submit.py               # Confirmed C++17 submission
tests/
├── __init__.py             # Test discovery setup
├── test_open.py            # Editor shortcut checks
├── test_run.py             # Stdin and test-file run checks
├── test_submit.py          # Submission checks (mocked uploads)
└── test_tooling.py         # Other offline regression checks
cmake/
└── test_runner.cmake       # Shared test runner
CMakeLists.txt
Makefile
justfile
```

Build artifacts and downloaded tests are ignored by Git. Solutions, statements,
and per-problem CMake files are tracked under `problems/`.

## Shortcuts

Run these from the project root. Requires CMake, a C++ compiler, Make, and
optionally `just`. Both interfaces use the same build setup.

| Action | Make | Just |
| --- | --- | --- |
| Initialize after cloning | `make init` | `just init` |
| Restore one test set | `make download-tests ID=1068` | `just download-tests 1068` |
| Build all | `make` | `just` |
| Build one | `make build ID=1070` | `just build 1070` |
| Build and test one | `make test ID=1070` | `just test 1070` |
| Run one test case | `make test ID=1068 CASE=3` | `just test 1068 3` |
| Run selected cases | `make test ID=1068 CASE=1,3,7` | `just test 1068 1,3,7` |
| Test all | `make test-all` | `just test-all` |
| Check tooling | `make check` | `just check` |
| Build and run (stdin) | `make run ID=1070` | `just run 1070` |
| Run with test input | `make run ID=1069 CASE=2` | `just run 1069 2` |
| Run multiple inputs | `make run ID=1069 CASE=2,3,5-9` | `just run 1069 2,3,5-9` |
| Open solution | `make open ID=1069` | `just open 1069` |
| Submit after local tests | `make submit ID=1068` | `just submit 1068` |
| Add problem | `make add ID=1071` | `just add 1071` |
| List problems | `make list` | `just list` |
| Remove compiled outputs | `make clean` | `just clean` |
| Remove entire build directory | `make distclean` | `just distclean` |
| Help | `make help` | `just help` |

Case names match input filenames: `3` selects `in/3.txt`, while `01` selects
`in/01.txt`. A `.txt` suffix is optional. Unknown cases fail with an error;
omitting the selection runs all cases. Selection applies only to that invocation.

`just run 1069` reads from stdin as usual. `just run 1069 2` instead reads
`problems/1069/in/2.txt` and prints the program's output without comparing it.
Lists (`2,3`), inclusive ranges (`2-9`), and combinations (`2,3,5-9`) are supported.
The command builds once, runs inputs in the selected order, removes duplicates,
and labels output when multiple inputs are selected. A program failure stops the
remaining runs. All input paths are checked before building or running.

Use `just test 1069 2` to compare against the expected output. For zero-padded
filenames, pass the exact name: `just run 1069 02` selects `in/02.txt`;
`02-09` selects zero-padded names. Descending ranges and missing/invalid cases
are rejected. Range selection currently applies to `run`; `test` accepts names
or comma-separated lists.

Explicit redirection still works: `just run 1070 < problems/1070/in/1.txt`.
Builds are incremental: configuration runs automatically for a fresh build, and
CMake tracks subsequent source, header, and CMake changes. An unchanged `run`
checks the target but does not reconfigure, compile, or link. Use `just configure`
when you explicitly want to force configuration.
Building does not run tests. Test commands fail until your solution produces the
expected output. Clean commands leave your sources and downloaded tests intact.

## Open a solution

```bash
just open 1069                  # Open problems/1069/main.cpp
just open 1069 vim              # One-off override
just open 1069 'code --wait'    # Editor arguments are supported
# Make equivalents:
make open ID=1069
make open ID=1069 OPEN_WITH=vim
```

Set a persistent local default in `.env`:

```dotenv
CSES_EDITOR=vim
```

Selection order: explicit override, process `CSES_EDITOR`, `.env`'s
`CSES_EDITOR`, `VISUAL`, `EDITOR`, then `code`. Quoted executable paths and
arguments are supported, but shell expressions/pipelines are not evaluated.
The editor runs in the foreground, so terminal editors such as Vim work normally.
Missing problems are reported, not automatically created; no build/login is needed.

## Setup after cloning

Prerequisites: a C++17 compiler available as `c++`, CMake 3.16+, Make, and
Python 3.9+. `just` is optional. Install these with your system's package manager;
there are no Python packages to install. An optional local `.env` avoids repeated
credential prompts:

```bash
cp .env.example .env
chmod 600 .env
# Edit .env and fill in CSES_USERNAME and CSES_PASSWORD.
```

`.env` contains plaintext secrets: it is Git-ignored and must never be shared.
Only the blank `.env.example` belongs in Git. Values are literal (no variable or
shell expansion); single/double quotes are optional. Credential precedence is
command-line arguments, process environment, `.env`, then interactive prompts.
You can omit the password from `.env` to keep using the hidden password prompt.

```bash
make init
# Or: just init
make
```

You can also run `make init` / `just init` without a username; it prompts only
when tests are missing. Initialization checks for build tools, restores missing
test sets for existing problems, and configures `build/`. It does not compile or
run solutions. Credentials come from environment/`.env` or a hidden password
prompt. The scripts never write credentials or login cookies to disk.

Repeated initialization skips test sets whose input/output files are already
paired. It never changes solution, statement, or CMake source files, and refuses
to overwrite differing local tests. Interrupted downloads can be retried. A
repository with no problems needs no login.

For offline build setup without downloading tests, use `make configure` or
`just configure`. A test command fails with setup instructions if its tests are
missing rather than silently passing.

The repository can start with no problems. Add one using `just add ID USERNAME`
or the script below, then implement its `main.cpp`.

To restore tests for just one existing problem:

```bash
just download-tests 1068 YOUR_USERNAME
# Or: make download-tests ID=1068 USERNAME=YOUR_USERNAME
# Or: python3 scripts/add_problem.py 1068 YOUR_USERNAME --tests-only
```

## Run tests for a problem

```bash
just test 1068          # All cases (after adding the problem)
just test 1068 1,3      # Selected cases
# Or: make test ID=1068 CASE=1,3
```

## Submit a solution

```bash
just submit 1068
# Or: make submit ID=1068
```

Currently supports `main.cpp` with C++17. The command runs **all** local tests,
ignoring any case selection. Failed or missing tests stop submission. It then
shows the source path and hash and asks:

```text
Submit to CSES? [y/N]
```

Only `y` or `yes` confirms. Enter, any other answer, EOF, or interruption before
upload cancels. There is no confirmation-bypass flag. Login and upload happen
only after confirmation, using environment/`.env` credentials or prompts.

The tool makes one upload attempt, then prints the submission's verdict link;
it does not claim acceptance or repeatedly poll CSES. On an upload timeout or
unclear response, inspect your submission history before trying again—the server
may already have received it. Rate limits and authentication/security failures
stop the command; it does not bypass protections.

This uses CSES's website form, not a documented public submission API. Automation
permission has not been confirmed; use at your own discretion and follow any
site rules or restrictions. Manual submission remains an option.

## Check the tooling

Run the offline checks for statement formatting, starter compilation, problem
creation, overwrite protection, and test-case selection:

```bash
just check
# Or: make check
# Direct: python3 -m unittest discover -s tests -t . -p 'test_*.py' -v
```

These checks use temporary fixtures and do not log in or download anything.

## Adding test cases

Place input files in `problems/<id>/in/` and expected output in `problems/<id>/out/`:

```
problems/1068/
├── in/
│   ├── 01.txt    # input for test 1
│   └── 02.txt    # input for test 2
└── out/
    ├── 01.out    # expected output for test 1
    └── 02.out    # expected output for test 2
```

## Add a problem

Requires Python 3, with no extra packages. From the project root:

```bash
python3 scripts/add_problem.py 1070
# Uses environment/.env credentials, or prompts for missing values.
```

Alternatively, supply all three arguments (the password may appear in shell history
and process listings):

```bash
python3 scripts/add_problem.py 1070 YOUR_USERNAME 'YOUR_PASSWORD'
```

The script logs in, downloads official tests, saves the problem description as
`problems/1070/statement.md`, creates `problems/1070/main.cpp` with no solution,
and registers the folder in `problems/CMakeLists.txt`. Existing problem
folders are never overwritten. The scripts never write credentials or login
cookies to disk; an optional `.env` is created and maintained by you.
The script works from any directory; run the following commands from this project's root:

```bash
cmake -S . -B build
cmake --build build --target problem_1070  # Build only
cmake --build build --target test_1070     # Build and run tests
```

Tests run only when you request a `test_NNNN` target. The empty starter will fail
output checks until you implement your solution.

## Commit messages

Use `<type>(<scope>): <summary>`. Keep problem changes separate from tooling:

```text
solve(1068): implement weird algorithm
fix(1068): use 64-bit integers to prevent overflow
chore(1070): add starter and problem statement
feat(tooling): restore missing tests after cloning
fix(tooling): preserve local test files
docs(repo): document local setup
```

Problem scopes are their CSES IDs; infrastructure uses `tooling`, and
repository-wide documentation/policy uses `repo`. See [AGENTS.md](AGENTS.md) for
the full conventions and pre-commit checks. These are documented rules, not an
automated Git hook.
