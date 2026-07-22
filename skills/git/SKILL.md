---
name: git
description: Stage, commit, sync, and push changes using Git for this project's trunk-based workflow. Use whenever a task's implementation is ready to be saved to source control.
metadata:
  version: "1.0"
---

This project uses a simple, trunk-based Git workflow: no feature branches, no pull requests. Every task is captured in one or more small commits pushed straight to `main`. This skill covers the small set of commands needed to do that. For commit message conventions, see the `source_control` knowledge base doc.

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

## 3. Commit — `git commit`

Prefer combining the stage-and-commit step with the `-a` flag when every tracked file you touched belongs in the commit, and always pass the message inline with `-m` rather than opening an editor:

```
git commit -am "<type>(<scope>): <description>"
```

- Use `-a` to automatically stage modifications to already-tracked files (it will not pick up new, untracked files — use `git add` for those first).
- Use `-m` to supply the Conventional Commits message directly on the command line.
- Keep each commit atomic: one logical change per commit.

**Note:** this repository is configured to run pre-commit checks, which can be found in the [.pre-commit-config.yaml](../../.pre-commit-config.yaml) file in the repository root. If any of these checks fail, you **must** resolve the errors as described in the output before you can proceed with the next step of the task. If you attempt to proceed without resolving these errors, then **all** subsequent attempted commits will fail your latest changes will not be synchronised with the Git repository.

## 4. Sync before you push — `git pull --rebase`

Always rebase onto the latest trunk before pushing, so history stays linear and your commits land on top of the current `main`:

```
git pull --rebase origin main
```

The Git pull tool does not support continuing a rebase. If conflicts arise, stop and report the failure rather than attempting to resolve and continue the rebase yourself.

## 5. Push — `git push`

Push your rebased commits directly to the trunk:

```
git push origin main
```

**Never** force-push (`--force` / `--force-with-lease`) to `main`. If the push is rejected because the trunk has moved, repeat step 4 (`git pull --rebase`) and push again.

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
git commit -am "feat: add retry logic to API client"
git pull --rebase origin main
git push origin main
```
