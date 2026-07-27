import os
from typing import Type

from crewai.tools import BaseTool
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field


class SafeFileReadInputSchema(BaseModel):
    """Input schema for SafeFileReadTool."""

    file_path: str = Field(
        ...,
        description="The file path relative to the repository root, e.g. 'app/backend/main.py'.",
    )
    start_line: int | None = Field(
        1, description="Line number to start reading from (1-indexed)."
    )
    line_count: int | None = Field(
        None, description="Number of lines to read. If None, reads the entire file."
    )


class SafeFileReadTool(BaseTool):
    name: str = "Read a file's content"
    description: str = (
        "Useful to read the content of a file relative to the repository root. This "
        "custom tool mitigates the broken usage of the base `FileReadTool` by "
        "quantised models, which sometimes hallucinate a leading slash onto an "
        "otherwise-relative path (e.g. '/app/backend' instead of 'app/backend'), "
        "which the base tool then rejects as escaping the allowed directory. This "
        "tool strips such a leading slash so the path is resolved relative to the "
        "repository root instead."
    )
    args_schema: Type[BaseModel] = SafeFileReadInputSchema

    def _run(
        self,
        file_path: str,
        start_line: int | None = 1,
        line_count: int | None = None,
    ) -> str:
        # Strip an accidental leading slash the LLM might pass, so an
        # otherwise-relative path isn't misread as filesystem-absolute.
        if os.path.isabs(file_path):
            file_path = file_path.lstrip(os.sep)

        reader = FileReadTool()
        return reader._run(
            file_path=file_path,
            start_line=start_line,
            line_count=line_count,
        )
