---
name: git
description: Stage, commit, sync, and push changes using Git for this project's trunk-based workflow. Use whenever a task's implementation is ready to be saved to source control.
metadata:
  version: "1.0"
---

This project uses a simple, trunk-based Git workflow: no feature branches, no pull requests. Every task is captured in one or more small commits pushed straight to `main`. This skill covers the small set of commands needed to do that. For commit message conventions, see the `source_control` knowledge base doc.

## 1. Stage your changes — `git add`

Stage only the files relevant to the current, atomic change:

```
git add <file> [<file> ...]
```

Avoid `git add .` or `git add -A` unless you have reviewed `git status` first and are certain every changed file belongs in this commit.

## 2. Commit — `git commit`

Prefer combining the stage-and-commit step with the `-a` flag when every tracked file you touched belongs in the commit, and always pass the message inline with `-m` rather than opening an editor:

```
git commit -am "<type>(<scope>): <description>"
```

- Use `-a` to automatically stage modifications to already-tracked files (it will not pick up new, untracked files — use `git add` for those first).
- Use `-m` to supply the Conventional Commits message directly on the command line.
- Keep each commit atomic: one logical change per commit.

## 3. Sync before you push — `git pull --rebase`

Always rebase onto the latest trunk before pushing, so history stays linear and your commits land on top of the current `main`:

```
git pull --rebase origin main
```

Resolve any conflicts that arise, re-run the test suite and linter, then continue with `git rebase --continue` before proceeding to push.

## 4. Push — `git push`

Push your rebased commits directly to the trunk:

```
git push origin main
```

Never force-push (`--force` / `--force-with-lease`) to `main`. If the push is rejected because the trunk has moved, repeat step 3 (`git pull --rebase`) and push again.

## Typical sequence

```
git add <new-files>          # only if there are new/untracked files
git commit -am "feat: add retry logic to API client"
git pull --rebase origin main
git push origin main
```
