import subprocess
from typing import List, Literal, Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, model_validator

# Commands supported by this project's trunk-based Git workflow, as documented
# in skills/git/SKILL.md. Kept intentionally narrow: no branching, no force
# operations, nothing that could rewrite or discard history.
GitCommand = Literal["add", "commit", "pull_rebase", "push"]


class GitToolInput(BaseModel):
    """Input schema for GitTool."""

    command: GitCommand = Field(
        ...,
        description=(
            "Git operation to run: 'add' to stage files, 'commit' to commit staged "
            "(or all tracked, with all_tracked=True) changes, 'pull_rebase' to sync "
            "with origin/main via rebase, or 'push' to push to origin main."
        ),
    )
    files: Optional[List[str]] = Field(
        default=None,
        description="File paths to stage. Required for 'add', ignored otherwise.",
    )
    message: Optional[str] = Field(
        default=None,
        description=(
            "Conventional Commits message, e.g. 'feat(scope): description'. "
            "Required for 'commit', ignored otherwise."
        ),
    )
    all_tracked: bool = Field(
        default=False,
        description=(
            "For 'commit' only: pass -a to automatically stage modifications to "
            "already-tracked files, per SKILL.md guidance. Does not pick up new, "
            "untracked files."
        ),
    )

    @model_validator(mode="after")
    def _validate_command_args(self) -> "GitToolInput":
        if self.command == "add" and not self.files:
            raise ValueError("'files' is required for the 'add' command.")
        if self.command == "commit" and not self.message:
            raise ValueError("'message' is required for the 'commit' command.")
        return self


class GitTool(BaseTool):
    name: str = "Git"
    description: str = (
        "Stage, commit, sync, and push changes using Git, following this project's "
        "trunk-based workflow (no branches, no force-push, no history rewriting). "
        "Supports only: add, commit, pull_rebase (git pull --rebase origin main), "
        "and push (git push origin main)."
    )
    args_schema: Type[BaseModel] = GitToolInput
    working_directory: Optional[str] = None

    def _run(
        self,
        command: GitCommand,
        files: Optional[List[str]] = None,
        message: Optional[str] = None,
        all_tracked: bool = False,
    ) -> str:
        self._validate_argument_combination(command, files, message, all_tracked)
        argv = self._build_argv(command, files, message, all_tracked)
        try:
            result = subprocess.run(
                argv,
                cwd=self.working_directory,
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

    @staticmethod
    def _validate_argument_combination(
        command: GitCommand,
        files: Optional[List[str]],
        message: Optional[str],
        all_tracked: bool,
    ) -> None:
        """Reject any command/argument permutation other than the strictly
        allowed ones: files only with 'add', message/all_tracked only with
        'commit'. Guards against agent mistakes like `push` with a message."""
        if command != "add" and files:
            raise ValueError("'files' is only allowed with the 'add' command.")
        if command != "commit" and (message is not None or all_tracked):
            raise ValueError(
                "'message' and 'all_tracked' are only allowed with the 'commit' command."
            )

    @staticmethod
    def _build_argv(
        command: GitCommand,
        files: Optional[List[str]],
        message: Optional[str],
        all_tracked: bool,
    ) -> List[str]:
        if command == "add":
            return ["git", "add", "--", *(files or [])]
        if command == "commit":
            assert message is not None, "GitToolInput requires 'message' for 'commit'."
            flag = "-am" if all_tracked else "-m"
            return ["git", "commit", flag, message]
        if command == "pull_rebase":
            return ["git", "pull", "--rebase", "origin", "main"]
        if command == "push":
            return ["git", "push", "origin", "main"]
        raise ValueError(f"Unsupported command: {command}")
