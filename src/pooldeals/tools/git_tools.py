import subprocess
from typing import List, Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GitCommandError(RuntimeError):
    """Raised when a git subprocess exits non-zero or times out.

    Letting this propagate out of a tool's `_run` (rather than returning an error string)
    is deliberate: CrewAI's tool executor catches it, feeds the message back to the agent
    as a distinct tool-error observation, and automatically retries the step — this lands
    with a small quantised model far more reliably than a "success" string containing
    error text ever does.
    """


def _git_status(working_directory: Optional[str]) -> str:
    return _run_git(["git", "status", "--porcelain"], working_directory)


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


def _run_git(argv: List[str], working_directory: Optional[str]) -> str:
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
        raise GitCommandError(f"Git command timed out: {' '.join(argv)}") from None

    output = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        raise GitCommandError(
            f"`{' '.join(argv)}` failed (exit {result.returncode}):\n{output}"
        )

    return f"`{' '.join(argv)}` succeeded (exit 0):\n{output}"


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
            raise ValueError(
                "'files' must be a non-empty list. Call Git Status and pass the "
                f"exact paths you want staged. Current repo state:\n{status}"
            )
        argv = ["git", "add", "--", *files]
        return _run_git(argv, self.working_directory)


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
            raise ValueError("'message' must be a non-empty string.")
        flag = "-am" if all_tracked else "-m"
        argv = ["git", "commit", flag, message]

        try:
            return _run_git(argv, self.working_directory)
        except GitCommandError as exc:
            raise GitCommandError(
                "PRE-COMMIT FAILED! The `git commit` command failed, potentially "
                f"because a pre-commit hook (mypy/Ruff) rejected the change:\n\n{exc}\n\n"
                "Assess the command output. If this is the case, you must fix the reported "
                "errors and then retry the commit. Do not proceed "
                "to any other step — the commit does not exist and your changes are not "
                "synchronised with the Git repository until this succeeds. Consult "
                ".pre-commit-config.yaml in the repository root for the checks that run.\n\n"
                "If the output solely reports that no files are staged for commit then no "
                "remediation is required, and you can proceed with the next step."
            ) from exc


class GitPullRebaseInput(BaseModel):
    """Input schema for GitPullRebaseTool. Takes no arguments."""


class GitPullRebaseTool(BaseTool):
    name: str = "Git Pull Rebase"
    description: str = "Sync with origin/main via 'git pull --rebase origin main'."
    args_schema: Type[BaseModel] = GitPullRebaseInput
    working_directory: Optional[str] = None

    def _run(self) -> str:
        argv = ["git", "pull", "--rebase", "origin", "main"]
        return _run_git(argv, self.working_directory)


class GitPushInput(BaseModel):
    """Input schema for GitPushTool. Takes no arguments."""


class GitPushTool(BaseTool):
    name: str = "Git Push"
    description: str = "Push local commits using 'git push origin main'."
    args_schema: Type[BaseModel] = GitPushInput
    working_directory: Optional[str] = None

    def _run(self) -> str:
        argv = ["git", "push", "origin", "main"]
        return _run_git(argv, self.working_directory)
