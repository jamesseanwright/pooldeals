import subprocess
from typing import List, Optional, Type, Literal

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GitResult(BaseModel):
    status: Literal["succeeded", "failed"]
    contents: str


def _git_status(working_directory: Optional[str]) -> str:
    return _run_git(["git", "status", "--porcelain"], working_directory).contents


def _run_git(argv: List[str], working_directory: Optional[str]) -> GitResult:
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
        return GitResult(
            status="failed", contents=f"Git command timed out: {' '.join(argv)}"
        )

    output = (result.stdout + result.stderr).strip()
    status = "succeeded" if result.returncode == 0 else "failed"

    return GitResult(
        status=status,
        contents=f"`{' '.join(argv)}` {status} (exit {result.returncode}):\n{output}",
    )


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
        return _run_git(argv, self.working_directory).contents


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

    **Note:** this repository is configured to run pre-commit checks, which can be found in the
    .pre-commit-config.yaml file in the repository root. If any of these checks fail, you **must** resolve
    the errors as described in the output before you can proceed with the next step of the task. If you
    attempt to proceed without resolving these errors, then **all** subsequent attempted commits will fail
    your latest changes will not be synchronised with the Git repository.
    """
    args_schema: Type[BaseModel] = GitCommitInput
    working_directory: Optional[str] = None

    def _run(self, message: str, all_tracked: bool = False) -> str:
        if not message:
            raise ValueError("'message' must be a non-empty string.")
        flag = "-am" if all_tracked else "-m"
        argv = ["git", "commit", flag, message]

        res = _run_git(argv, self.working_directory)

        if res.status == "failed":
            return f"""**PRE-COMMIT HOOKS HAVE FAILED!**

            The `git commit` command returned the following error, presumably as a result of the pre-commit
            hook failing:

            {res.contents}

            You **must** fix the reported errors accordingly and then retry the commit. **Do not** attempt to proceed
            without resolving these errors as **all** subsequent attempted commits will fail and your latest changes
            will not be synchronised with the Git repository.

            To understand the tools that are run on pre-commit, consult the .pre-commit-config.yaml file in the repository root.
            """

        return res.contents


class GitPullRebaseInput(BaseModel):
    """Input schema for GitPullRebaseTool. Takes no arguments."""


class GitPullRebaseTool(BaseTool):
    name: str = "Git Pull Rebase"
    description: str = "Sync with origin/main via 'git pull --rebase origin main'."
    args_schema: Type[BaseModel] = GitPullRebaseInput
    working_directory: Optional[str] = None

    def _run(self) -> str:
        argv = ["git", "pull", "--rebase", "origin", "main"]
        return _run_git(argv, self.working_directory).contents


class GitPushInput(BaseModel):
    """Input schema for GitPushTool. Takes no arguments."""


class GitPushTool(BaseTool):
    name: str = "Git Push"
    description: str = "Push local commits using 'git push origin main'."
    args_schema: Type[BaseModel] = GitPushInput
    working_directory: Optional[str] = None

    def _run(self) -> str:
        argv = ["git", "push", "origin", "main"]
        return _run_git(argv, self.working_directory).contents
