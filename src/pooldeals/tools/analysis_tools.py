import subprocess
from typing import List, Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from pooldeals.tools.git_tools import _git_status


def _run_check(
    argv: List[str], working_directory: Optional[str], timeout: int = 60
) -> str:
    """Run a static-analysis command, returning its output regardless of exit code.

    Unlike the git tools' subprocess helper, this never raises on non-zero exit — these
    are inspection calls the agent makes to see errors before committing, not commit
    attempts, so a "found errors" result must come back as a normal tool observation the
    agent can read and act on, not an exception.
    """
    try:
        result = subprocess.run(
            argv,
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return f"`{' '.join(argv)}` timed out after {timeout}s."

    output = (result.stdout + result.stderr).strip()
    status = "passed — no errors" if result.returncode == 0 else "found errors"
    return f"`{' '.join(argv)}` {status} (exit {result.returncode}):\n{output}"


class RuffCheckInput(BaseModel):
    """Input schema for RuffCheckTool."""

    files: List[str] = Field(
        ...,
        min_length=1,
        description=(
            "File paths to check. Required. Must contain at least one file path — "
            "NEVER pass an empty list. Pass the exact paths you have changed. If you "
            "are not certain which files changed, call Git Status first and pass the "
            "exact paths it reports."
        ),
    )


class RuffCheckTool(BaseTool):
    name: str = "Ruff Check"
    description: str = (
        "Run Ruff's formatter and linter (with autofix) against the given files and "
        "report the exact file:line errors, WITHOUT committing anything. Always call "
        "this before Git Commit, passing the exact files you changed, and call it "
        "again after making fixes — repeat until it reports no errors."
    )
    args_schema: Type[BaseModel] = RuffCheckInput
    working_directory: Optional[str] = None

    def _run(self, files: List[str]) -> str:
        if not files:
            status = _git_status(self.working_directory)
            raise ValueError(
                "'files' must be a non-empty list. Call Git Status and pass the "
                f"exact paths you want checked. Current repo state:\n{status}"
            )
        format_result = _run_check(["ruff", "format", *files], self.working_directory)
        check_result = _run_check(
            ["ruff", "check", "--fix", *files], self.working_directory
        )
        return f"{format_result}\n\n{check_result}"


class MypyCheckInput(BaseModel):
    """Input schema for MypyCheckTool."""

    files: List[str] = Field(
        ...,
        min_length=1,
        description=(
            "File paths to type-check. Required. Must contain at least one file path — "
            "NEVER pass an empty list. Pass the exact paths you have changed. If you "
            "are not certain which files changed, call Git Status first and pass the "
            "exact paths it reports."
        ),
    )


class MypyCheckTool(BaseTool):
    name: str = "Mypy Check"
    description: str = (
        "Run mypy against the given files and report the exact file:line type errors, "
        "WITHOUT committing anything. Always call this before Git Commit, passing the "
        "exact files you changed, and call it again after making fixes — repeat until "
        "it reports no errors."
    )
    args_schema: Type[BaseModel] = MypyCheckInput
    working_directory: Optional[str] = None

    def _run(self, files: List[str]) -> str:
        if not files:
            status = _git_status(self.working_directory)
            raise ValueError(
                "'files' must be a non-empty list. Call Git Status and pass the "
                f"exact paths you want checked. Current repo state:\n{status}"
            )
        # mypy is not a bare project dependency — it only exists inside pre-commit's
        # isolated hook environment (see .pre-commit-config.yaml), so it must be invoked
        # through pre-commit rather than as a standalone binary.
        return _run_check(
            ["pre-commit", "run", "mypy", "--files", *files],
            self.working_directory,
            timeout=120,
        )
