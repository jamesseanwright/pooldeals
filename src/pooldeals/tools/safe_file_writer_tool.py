from pydantic import BaseModel, Field
from crewai.tools import tool
from crewai_tools import FileWriterTool
import os


class SafeWriterSchema(BaseModel):
    filename: str = Field(
        ...,
        description="The clean file name ONLY, e.g., 'schemas.py'. DO NOT include directories or slashes.",
    )
    directory: str = Field(
        ...,
        description="The directory path relative to the root, e.g., 'app/backend/auth'.",
    )
    content: str = Field(
        ..., description="The code or text content to write into the file."
    )


@tool("Safe File Writer", args_schema=SafeWriterSchema)
def safe_file_writer(filename: str, directory: str, content: str) -> str:
    """Useful to write or overwrite code files cleanly.

    This custom tool mitigates the broken usage of the base `FileWriterTool` by
    quantised models, which choose to include the full relative path in the filename;
    this is problematic as `FileWriterTool` already concatenates `filename` to `directory`
    anyway, resulting in an attempted write to a non-existent directory. This tool is
    thus more defensive in that it explicitly extracts the basename from the `filename` arg
    regardless of whether it's already a base name or contains the relative path.
    """
    # Strip accidental slashes the LLM might still pass to filename
    clean_filename = os.path.basename(filename)

    # Auto-create the directory path safely in Python first
    os.makedirs(directory, exist_ok=True)

    # Execute the core writer
    writer = FileWriterTool()
    return writer._run(
        filename=clean_filename, content=content, directory=directory, overwrite=True
    )
