from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai_tools import FileWriterTool

builder_llm = LLM(
    model="unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q5_K_S",
    base_url="http://localhost:8080/v1",
    api_key="not-needed",  # not required as running model locally via llama_server OpenAI-compat API
)

reviewer_llm = LLM(
    model="unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q3_K_M",
    base_url="http://localhost:8081/v1",
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
            tools=[FileWriterTool()],
            llm=builder_llm,
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
        return [Task(config=t) for t in self.tasks_config.values()]  # type: ignore

    @crew
    def crew(self) -> Crew:
        """Creates the Pooldeals crew"""
        return Crew(
            agents=self.agents,
            tasks=self.get_tasks(),
            process=Process.sequential,
            knowledge_sources=[
                TextFileKnowledgeSource(
                    "product.md",
                    "general.md",
                    "backend_coding_standards.md",
                    "frontend_coding_standards.md",
                    "security.md",
                    "source_control.md",
                    "testing.md",
                )
            ],
            verbose=True,
        )
