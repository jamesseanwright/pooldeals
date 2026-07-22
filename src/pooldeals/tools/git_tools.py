import subprocess
from typing import List, Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


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
        return f"Git command timed out: {' '.join(argv)}"

    output = (result.stdout + result.stderr).strip()
    status = "succeeded" if result.returncode == 0 else "failed"
    return f"`{' '.join(argv)}` {status} (exit {result.returncode}):\n{output}"


class GitAddInput(BaseModel):
    """Input schema for GitAddTool."""

    files: List[str] = Field(
        ...,
        description="File paths to stage with 'git add'. Required, must be non-empty.",
    )


class GitAddTool(BaseTool):
    name: str = "Git Add"
    description: str = "Stage file paths for commit using 'git add -- <files>'."
    args_schema: Type[BaseModel] = GitAddInput
    working_directory: Optional[str] = None

    def _run(self, files: List[str]) -> str:
        if not files:
            raise ValueError("'files' must be a non-empty list.")
        argv = ["git", "add", "--", *files]
        return _run_git(argv, self.working_directory)


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
    description: str = "Commit staged (or all tracked, with all_tracked=True) changes using 'git commit'."
    args_schema: Type[BaseModel] = GitCommitInput
    working_directory: Optional[str] = None

    def _run(self, message: str, all_tracked: bool = False) -> str:
        if not message:
            raise ValueError("'message' must be a non-empty string.")
        flag = "-am" if all_tracked else "-m"
        argv = ["git", "commit", flag, message]
        return _run_git(argv, self.working_directory)


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
