import subprocess
from typing import List, Optional, Tuple, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


def _git_status(working_directory: Optional[str]) -> str:
    return _run_git(["git", "status", "--porcelain"], working_directory)[1]


def dirty_files(working_directory: Optional[str]) -> List[str]:
    """Return the paths of every uncommitted (modified, staged, or untracked) file.

    Used by the static-analysis guardrail to work out which files to run Ruff/Mypy
    against when a task claims to be finished but hasn't actually committed everything.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=working_directory,
        capture_output=True,
        text=True,
        timeout=60,
        stdin=subprocess.DEVNULL,
    )
    files = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.append(path)
    return files


def _run_git(argv: List[str], working_directory: Optional[str]) -> Tuple[int, str]:
    """Run a git subprocess, always returning a result rather than raising.

    Earlier this raised `GitCommandError` on non-zero exit or timeout, on the
    assumption that CrewAI's tool executor would catch it and retry the current step.
    In practice, exceptions raised from a tool's `_run` propagate past the step-level
    handling to the agent's own execute_task retry logic, which restarts the whole
    task from scratch — a fresh plan included — rather than just retrying the step.
    Returning a normal pass/fail observation (mirroring analysis_tools._run_check)
    lets the agent react and retry in place instead.
    """
    try:
        result = subprocess.run(
            argv,
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return False, f"`{' '.join(argv)}` timed out after 60s."

    output = (result.stdout + result.stderr).strip()
    success = result.returncode == 0
    status = "succeeded" if success else "failed"
    return (
        result.returncode,
        f"`{' '.join(argv)}` {status} (exit {result.returncode}):\n{output}",
    )


def _commit_output_contains_ignored_git_nonzero_exit_reason(output: str) -> bool:
    return (
        "nothing to commit, working tree clean" in output
    )  # Currently the only ignored exit reason


class GitAddInput(BaseModel):
    """Input schema for GitAddTool."""

    files: List[str] = Field(
        ...,
        min_length=1,
        description=(
            "File paths to stage with 'git add'. Required. Must contain at least "
            "one file path — NEVER pass an empty list. If you are not certain "
            "which files changed, call Git Status first and pass the exact paths "
            "it reports."
        ),
    )


class GitAddTool(BaseTool):
    name: str = "Git Add"
    description: str = "Stage file paths for commit using 'git add -- <files>'."
    args_schema: Type[BaseModel] = GitAddInput
    working_directory: Optional[str] = None

    def _run(self, files: List[str]) -> str:
        if not files:
            status = _git_status(self.working_directory)
            return (
                "Error: 'files' must be a non-empty list. Call Git Status and pass "
                f"the exact paths you want staged. Current repo state:\n{status}"
            )
        argv = ["git", "add", "--", *files]

        exit_code, output = _run_git(argv, self.working_directory)

        if exit_code == 128:
            return (
                "Error: `git add` exited with a 128 exit code; this is most likely caused "
                "by trying to add/stage a file that does not exist. Make sure that each of the "
                "files you've provided actually exist, and correct the paths accordingly. It's "
                "possible that the file you're trying to add exists under a different path or filename.\n\n"
                f"Command output:\n\n{output}"
            )

        return output


class GitStatusInput(BaseModel):
    """Input schema for GitStatusTool. Takes no arguments."""


class GitStatusTool(BaseTool):
    name: str = "Git Status"
    description: str = (
        "Check which files have changed using 'git status --porcelain'. Use this "
        "before Git Add whenever you are not certain which files were modified, "
        "created, or deleted, so you can pass exact paths instead of guessing."
    )
    args_schema: Type[BaseModel] = GitStatusInput
    working_directory: Optional[str] = None

    def _run(self) -> str:
        return _git_status(self.working_directory)


class GitCommitInput(BaseModel):
    """Input schema for GitCommitTool."""

    message: str = Field(
        ...,
        description="Conventional Commits message, e.g. 'feat(scope): description'. Required.",
    )
    all_tracked: bool = Field(
        default=False,
        description=(
            "Pass -a to automatically stage modifications to already-tracked files, "
            "per SKILL.md guidance. Does not pick up new, untracked files."
        ),
    )


class GitCommitTool(BaseTool):
    name: str = "Git Commit"
    description: str = """Commit staged (or all tracked, with all_tracked=True) changes using 'git commit'.

    Follow this exact procedure before calling this tool:
    1. Call `Ruff Check` on the files you changed.
    2. Call `Mypy Check` on the same files.
    3. Read both outputs line by line. For each `file:line` error either reports, open
       that exact file and fix only that issue.
    4. Call `Ruff Check` and `Mypy Check` again. Repeat steps 3-4 until both report no
       errors.
    5. Only then call this tool (`Git Commit`).

    This repository runs pre-commit hooks (ruff-format, ruff-check, mypy — see
    .pre-commit-config.yaml) on every commit. If you call this tool without following the
    procedure above, the commit will fail and your changes will remain unsynchronised
    with the Git repository.
    """
    args_schema: Type[BaseModel] = GitCommitInput
    working_directory: Optional[str] = None

    def _run(self, message: str, all_tracked: bool = False) -> str:
        if not message:
            return "Error: 'message' must be a non-empty string."
        flag = "-am" if all_tracked else "-m"
        argv = ["git", "commit", flag, message]

        exit_code, output = _run_git(argv, self.working_directory)
        if (
            exit_code != 0
            and not _commit_output_contains_ignored_git_nonzero_exit_reason(output)
        ):
            return (
                "Error: the `git commit` command failed! This is most likely "
                f"because a pre-commit hook (mypy/Ruff) rejected the change:\n\n{output}\n\n"
                "Assess the command output. If there is an error to resolve, you must fix the reported "
                "errors and then retry the commit. Do not proceed "
                "to any other step — the commit does not exist and your changes are not "
                "synchronised with the Git repository until this succeeds. Consult "
                ".pre-commit-config.yaml in the repository root for the checks that run."
            )
        return output


class GitPullRebaseInput(BaseModel):
    """Input schema for GitPullRebaseTool. Takes no arguments."""


class GitPullRebaseTool(BaseTool):
    name: str = "Git Pull Rebase"
    description: str = "Sync with origin/main via 'git pull --rebase origin main'."
    args_schema: Type[BaseModel] = GitPullRebaseInput
    working_directory: Optional[str] = None

    def _run(self) -> str:
        argv = ["git", "pull", "--rebase", "origin", "main"]
        return _run_git(argv, self.working_directory)[1]


class GitPushInput(BaseModel):
    """Input schema for GitPushTool. Takes no arguments."""


class GitPushTool(BaseTool):
    name: str = "Git Push"
    description: str = "Push local commits using 'git push origin main'."
    args_schema: Type[BaseModel] = GitPushInput
    working_directory: Optional[str] = None

    def _run(self) -> str:
        argv = ["git", "push", "origin", "main"]
        return _run_git(argv, self.working_directory)[1]
