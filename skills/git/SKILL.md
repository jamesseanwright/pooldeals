---
name: git
description: Stage, commit, sync, and push changes using Git for this project's trunk-based workflow, including Conventional Commits message rules and the TDD/review workflow. Use whenever a task's implementation is ready to be saved to source control.
metadata:
  version: "1.0"
---

This project uses a simple, trunk-based Git workflow: no feature branches, no pull requests. There are no long-lived feature branches — all work is committed straight to `main` in small, frequent, atomic commits. This skill covers everything needed to do that: the commands, commit message conventions, and the TDD/review workflow.

## 1. Check what changed — `git status`

If you are not certain exactly which files you created, modified, or deleted, run Git Status first:

```
git status --porcelain
```

Use its output to get the exact paths for the next step. Do not guess or rely on your memory of earlier steps.

## 2. Stage your changes — `git add`

Stage only the files relevant to the current, atomic change:

```
git add <file> [<file> ...]
```

Avoid `git add .` or `git add -A` unless you have reviewed `git status` first and are certain every changed file belongs in this commit.

`files` is required and must never be an empty list — an empty list is rejected. If Git Add fails because `files` was empty, its error message includes the current `git status --porcelain` output; use those exact paths to retry.

## 3. Verify your changes before committing — see the `static-analysis` skill

Before committing, you **must** run Ruff Check and Mypy Check against the exact files you changed, and fix everything they report. This is covered in full in the `static-analysis` skill — follow it now if you haven't already.

## 4. Commit — `git commit`

Prefer combining the stage-and-commit step with the `-a` flag when every tracked file you touched belongs in the commit, and always pass the message inline with `-m` rather than opening an editor:

```
git commit -am "<type>(<scope>): <description>"
```

- Use `-a` to automatically stage modifications to already-tracked files (it will not pick up new, untracked files — use `git add` for those first).
- Use `-m` to supply the Conventional Commits message directly on the command line.
- Keep each commit atomic: bundle only related changes into a single commit — prefer several small commits over one large one.

### Commit message format

Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification: `<type>(<optional scope>): <description>`, written in a clear, imperative tone (e.g., `feat: add retry logic to API client`, `fix(api): handle null response from pricing service`).

Use one of the types from [`@commitlint/config-conventional`](https://github.com/conventional-changelog/commitlint/tree/master/%40commitlint/config-conventional):

- `feat` — a new feature
- `fix` — a bug fix
- `docs` — documentation-only changes
- `style` — changes that don't affect code meaning (formatting, whitespace, etc.)
- `refactor` — a code change that neither fixes a bug nor adds a feature
- `perf` — a code change that improves performance
- `test` — adding or correcting tests
- `build` — changes to the build system or external dependencies
- `ci` — changes to CI configuration or scripts
- `chore` — other changes that don't modify source or test files
- `revert` — reverts a previous commit

Note breaking changes with a `!` after the type/scope (e.g., `feat!: drop support for legacy pricing API`) or a `BREAKING CHANGE:` footer.

**Keep Trunk Healthy:** because there is no branch isolation, every commit to `main` must leave the codebase in a working state — never commit code that fails tests or linting.

**Note:** this repository is configured to run pre-commit checks, which can be found in the [.pre-commit-config.yaml](../../.pre-commit-config.yaml) file in the repository root. If you skipped step 3 or committed before Ruff Check and Mypy Check both reported a clean result, these checks will run again here and may still fail — resolve the errors as described in the output before you can proceed with the next step of the task. If you attempt to proceed without resolving these errors, then **all** subsequent attempted commits will fail your latest changes will not be synchronised with the Git repository.

## 5. Sync before you push — `git pull --rebase`

Always rebase onto the latest trunk before pushing, so history stays linear and your commits land on top of the current `main`:

```
git pull --rebase origin main
```

The Git pull tool does not support continuing a rebase. If conflicts arise, stop and report the failure rather than attempting to resolve and continue the rebase yourself.

## 6. Push — `git push`

Push your rebased commits directly to the trunk:

```
git push origin main
```

**Never** force-push (`--force` / `--force-with-lease`) to `main`. If the push is rejected because the trunk has moved, repeat step 5 (`git pull --rebase`) and push again.

## Test-Driven Development Workflow

For each task:

1. Write a test case upfront that captures the desired behavior — see the `testing` skill.
2. Implement the code required to satisfy that test.
3. Run the full local test suite and linter to confirm nothing is broken — see the `static-analysis` skill.
4. Commit the change with a clear, atomic commit message (see above).

## Review Workflow

There is no GitHub pull request process. Instead, review happens agent-to-agent, directly on the working code:

1. **Initial Output:** The builder agent completes a task (implementation plus tests) and commits it.
2. **Critique:** The reviewer agent inspects the builder's changes and produces feedback — noting any issues with coding standards, test coverage, security, performance, or adherence to the task definition.
3. **Apply Feedback:** The builder agent applies the reviewer's feedback directly to the working tree, or responds with a rationale if it disagrees with a specific point.
4. **Re-validation:** After applying feedback, the builder re-runs the test suite and linter before committing the follow-up changes.
5. **Completion:** Once the reviewer has no further feedback, the task is considered complete. No merge step is required since work already lives on `main`.

## Allowed argument combinations

The Git tool enforces a strict, narrow set of command/argument permutations. Any other combination is rejected before it runs:

| Command       | `files`                | `message`      | `all_tracked`  |
| ------------- | ---------------------- | -------------- | -------------- |
| `status`      | ❌ not allowed         | ❌ not allowed | ❌ not allowed |
| `add`         | ✅ required, non-empty | ❌ not allowed | ❌ not allowed |
| `commit`      | ❌ not allowed         | ✅ required    | optional       |
| `pull_rebase` | ❌ not allowed         | ❌ not allowed | ❌ not allowed |
| `push`        | ❌ not allowed         | ❌ not allowed | ❌ not allowed |

In particular:

- `files` may only be passed with `add`, and must contain at least one path — never `[]`.
- `message` and `all_tracked` may only be passed with `commit`.
- `status`, `pull_rebase`, and `push` take no arguments at all — never pass a message, files, or `all_tracked` alongside them (e.g. `push` with a commit message is invalid).

There is no fallback or best-effort handling: a disallowed permutation raises an error instead of running.

## Typical sequence

```
git status --porcelain       # if unsure what changed
git add <new-files>          # only if there are new/untracked files
# ... run Ruff Check and Mypy Check per the static-analysis skill, fix everything ...
git commit -am "feat: add retry logic to API client"
git pull --rebase origin main
git push origin main
```
