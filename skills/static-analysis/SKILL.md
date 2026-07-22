---
name: static-analysis
description: Verify code meets PoolDeals' coding standards with Ruff (formatting/linting) and mypy (type checking) before committing. Use whenever you have written or modified code and are about to commit it.
metadata:
  version: "1.0"
---

Before every commit, you **must** verify your changes with these tools — this is not optional. They report exact `file:line` errors so you can fix real issues instead of guessing, and neither of them commits anything.

## 1. Check for lint/formatting errors — Ruff Check

Run Ruff Check against the exact files you changed:

```
ruff format <file> [<file> ...]
ruff check --fix <file> [<file> ...]
```

Read the output. For each `file:line` error it reports, open that exact file and fix only that issue. Call Ruff Check again. Repeat until it reports no errors.

`files` is required and must never be an empty list. If you are not certain which files changed, call Git Status first (see the `git` skill) and pass the exact paths it reports.

## 2. Check for type errors — Mypy Check

Once Ruff Check is clean, run Mypy Check against the same files. mypy isn't a standalone project dependency — it runs inside pre-commit's isolated hook environment, so it's invoked through `pre-commit run` rather than as a bare binary:

```
pre-commit run mypy --files <file> [<file> ...]
```

Read the output. For each `file:line` error it reports, open that exact file and fix only that issue. Call Mypy Check again. Repeat until it reports no errors.

`files` is required and must never be an empty list, for the same reason as Ruff Check.

## Only then commit

**Do not call Git Commit until both Ruff Check and Mypy Check have reported no errors on your latest changes**. See the `git` skill for the commit/push workflow.

## Allowed argument combinations

| Command      | `files`                |
| ------------ | ---------------------- |
| `ruff_check` | ✅ required, non-empty |
| `mypy_check` | ✅ required, non-empty |

`files` must contain at least one path — never `[]`. If you are unsure what changed, call Git Status first and pass the exact paths it reports.

## Typical sequence

```
ruff format <files>                  # repeat with ruff check --fix until clean
ruff check --fix <files>
pre-commit run mypy --files <files>  # repeat until clean
```
