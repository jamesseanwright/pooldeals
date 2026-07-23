from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai_tools import FileReadTool

from pooldeals.tools.analysis_tools import (
    MypyCheckTool,
    RuffCheckTool,
    require_static_analysis_passes,
)
from pooldeals.tools.git_tools import (
    GitAddTool,
    GitCommitTool,
    GitPullRebaseTool,
    GitPushTool,
    GitStatusTool,
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
                RuffCheckTool(),
                MypyCheckTool(),
                GitCommitTool(),
                GitPullRebaseTool(),
                GitPushTool(),
            ],
            llm=builder_llm,
            # max_iter bounds the ReAct tool-calling loop *within* a single task
            # execution, separate from PlanningConfig's max_replans/max_steps below.
            # Kept close to CrewAI's own default (25) rather than raised aggressively:
            # the require_static_analysis_passes guardrail (with guardrail_max_retries,
            # below and in main.py) is the more effective retry mechanism for a small
            # quantised model — each guardrail retry restarts with a short, focused
            # prompt containing the exact Ruff/Mypy errors, whereas a large max_iter
            # just lets a stuck attempt keep piling turns onto an ever-growing context,
            # which is exactly where small models degrade.
            max_iter=30,
            # Currently disabled planning as even with low, it seems to get stuck in a loop on the first step
            # planning=True,
            # planning_config=PlanningConfig(
            #     # When attempting "medium" effort, our resource-constrained LLM hallucinates and re-runs the same step infinitely
            #     reasoning_effort="low",
            #     # Was 1: CrewAI force-finalizes the task once max_replans is hit, even
            #     # mid-fix-loop, which cut off large multi-file tasks (e.g. the auth
            #     # backend) before Ruff/Mypy errors were actually resolved.
            #     max_replans=3,
            #     max_steps=30,
            # ),
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
            Task(
                config=t,
                guardrail=require_static_analysis_passes,
                guardrail_max_retries=10,
            )
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
                    ],
                )
            ],
            skills=["./skills"],
            checkpoint=True,  # TODO: resume from latest checkpoint on flow start (or even just accept checkpoint name as command-line arg)
            verbose=True,
        )
