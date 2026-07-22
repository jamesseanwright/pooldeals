from typing import Any, Tuple

from crewai import Agent, Crew, PlanningConfig, Process, Task, LLM
from crewai.project import CrewBase, agent, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.tasks.task_output import TaskOutput
from crewai_tools import FileReadTool

from pooldeals.tools.git_tools import (
    GitAddTool,
    GitCommitTool,
    GitPullRebaseTool,
    GitPushTool,
    GitStatusTool,
    working_tree_is_clean,
)

from pooldeals.tools.safe_file_writer_tool import SafeFileWriterTool

builder_llm = LLM(
    base_url="http://localhost:8080/v1",
    custom_openai=True,
    model="not-needed",  # model controlled by llama_server (see scripts/run-local-models.sh)
    api_key="not-needed",  # not required as running model locally via llama_server OpenAI-compat API
)

reviewer_llm = LLM(
    base_url="http://localhost:8081/v1",
    custom_openai=True,
    model="not-needed",  # model controlled by llama_server (see scripts/run-local-models.sh)
    api_key="not-needed",  # not required as running model locally via llama_server OpenAI-compat API
)


def _require_clean_working_tree(output: TaskOutput) -> Tuple[bool, Any]:
    """Task guardrail: fail (and force a retry) unless every change has been committed.

    This is a second line of defence alongside GitCommitTool raising GitCommandError on
    pre-commit hook failure. A quantised local model can still decide a task is "done"
    while ignoring a tool error mid-run, so this checks actual repo state at task
    completion rather than trusting the agent's account of what happened — per the
    trunk-based workflow in knowledge/source_control.md, every task must end fully
    committed.
    """
    is_clean, dirty_status = working_tree_is_clean()
    if is_clean:
        return True, output

    return False, (
        "This task is not complete: the working tree still has uncommitted changes, "
        "which violates the source control workflow (every task must end with all "
        "changes committed to main). Stage and commit the remaining changes — resolving "
        "any pre-commit hook (mypy/Ruff) failures first — before finishing this task. "
        f"Uncommitted changes:\n{dirty_status}"
    )


@CrewBase
class PooldealsCrew:  # TODO: => PoolDealsCrew
    """Pooldeals crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def builder(self) -> Agent:
        return Agent(
            config=self.agents_config["builder"],  # type: ignore[index]
            tools=[
                FileReadTool(),
                SafeFileWriterTool(),
                GitStatusTool(),
                GitAddTool(),
                GitCommitTool(),
                GitPullRebaseTool(),
                GitPushTool(),
            ],
            llm=builder_llm,
            planning=True,
            planning_config=PlanningConfig(
                reasoning_effort="low",
                max_attempts=1,
                max_replans=1,
                max_steps=15,
            ),
            verbose=True,
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["reviewer"],  # type: ignore[index]
            llm=reviewer_llm,
            verbose=True,
        )

    def get_tasks(self) -> list[Task]:
        # TODO: type properly
        return [
            Task(config=t, guardrail=_require_clean_working_tree)
            for t in self.tasks_config.values()  # type: ignore
        ]

    @crew
    def crew(self) -> Crew:
        """Creates the Pooldeals crew"""
        return Crew(
            agents=self.agents,
            tasks=self.get_tasks(),
            process=Process.sequential,
            knowledge_sources=[
                TextFileKnowledgeSource(
                    file_paths=[
                        "product.md",
                        "general.md",
                        "backend_coding_standards.md",
                        "frontend_coding_standards.md",
                        "security.md",
                        "source_control.md",
                        "testing.md",
                    ],
                )
            ],
            skills=["./skills"],
            checkpoint=True,  # TODO: resume from latest checkpoint on flow start (or even just accept checkpoint name as command-line arg)
            verbose=True,
        )
