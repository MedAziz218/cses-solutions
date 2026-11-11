# Commit conventions

Use this format for new commits:

```text
<type>(<scope>): <short imperative summary>
```

Keep the subject at most 72 characters, start the summary with a lowercase verb,
and omit the trailing period. Use a body when the reason or trade-offs need
explanation. These rules apply to new commits; do not rewrite existing history
unless asked.

## Problem changes

Use the CSES problem ID as the scope. Prefer one problem per commit.

- `solve(1068): implement weird algorithm` — add a completed solution.
- `fix(1068): use 64-bit integers to prevent overflow` — correct a solution.
- `refactor(1068): simplify sequence generation` — change structure, not behavior.
- `chore(1068): add starter and problem statement` — scaffold an unsolved problem.
- `docs(1068): explain the solution approach` — problem-specific documentation.

A `solve` commit should pass all available official local tests for that problem.
Do not claim CSES acceptance unless a submission was actually accepted.

## Tooling and repository changes

Use `tooling` for build scripts, CMake helpers, Make/Just recipes, downloaders,
initialization, credential loading, and their tests:

- `feat(tooling): restore missing tests after cloning`
- `fix(tooling): preserve local tests during initialization`
- `refactor(tooling): move test runner into cmake directory`
- `test(tooling): cover credential precedence`

Use `repo` for repository-wide documentation, policy, and housekeeping:

- `docs(repo): document local setup`
- `chore(repo): ignore downloaded test cases`
- `chore(repo): define commit message conventions`

Choose the type by the purpose of the change, not just its file extension. For
example, a CMake bug fix is `fix(tooling)`, not `chore(repo)`.

## Commit boundaries and checks

- Keep solution changes separate from tooling changes. Stage related files
  explicitly when both are present in the working tree.
- Problem folders are discovered automatically. A problem commit only needs its
  own folder; do not edit `problems/CMakeLists.txt` to register individual IDs.
- Run the relevant checks before committing: `just test <id>` for a solution,
  and `just check` (or `make check`) for tooling. Tests live in `tests/`.
- Never commit `.env`, credentials, downloaded test cases, or build artifacts.
- Do not create commits or push unless the user requests it.
