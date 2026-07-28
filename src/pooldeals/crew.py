from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
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
    temperature=0.2,
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
            max_iter=75,
            verbose=True,
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["reviewer"],  # type: ignore[index]
            llm=reviewer_llm,
            verbose=True,
        )

    # Hand-defining a task for each task in tasks.yaml is a bit
    # smelly, but our previous approach of building them
    # dynamically doesn't respect the `context` list we provide since
    # the method we implemented was called after Crew's internal task
    # binding logic; we thus define them with the `@task` decorator to
    # bake them into the aforementioned binding stage.
    @task
    def fastapi_bootstrap_task(self) -> Task:
        return Task(
            config=self.tasks_config["fastapi_bootstrap_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def docker_compose_bootstrap_task(self) -> Task:
        return Task(
            config=self.tasks_config["docker_compose_bootstrap_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def react_bootstrap_task(self) -> Task:
        return Task(
            config=self.tasks_config["react_bootstrap_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def authentication_task(self) -> Task:
        return Task(
            config=self.tasks_config["authentication_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def cicd_pipeline_task(self) -> Task:
        return Task(
            config=self.tasks_config["cicd_pipeline_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def consumer_registration_task(self) -> Task:
        return Task(
            config=self.tasks_config["consumer_registration_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def merchant_onboarding_task(self) -> Task:
        return Task(
            config=self.tasks_config["merchant_onboarding_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def campaign_management_task(self) -> Task:
        return Task(
            config=self.tasks_config["campaign_management_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def deal_discovery_task(self) -> Task:
        return Task(
            config=self.tasks_config["deal_discovery_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def voucher_claiming_task(self) -> Task:
        return Task(
            config=self.tasks_config["voucher_claiming_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def voucher_redemption_task(self) -> Task:
        return Task(
            config=self.tasks_config["voucher_redemption_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @task
    def merchant_analytics_task(self) -> Task:
        return Task(
            config=self.tasks_config["merchant_analytics_task"],  # type: ignore[index]
            guardrail=require_static_analysis_passes,
            guardrail_max_retries=5,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Pooldeals crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
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
