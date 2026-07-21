from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai_tools import FileWriterTool


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
            verbose=True,
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["reviewer"],  # type: ignore[index]
            verbose=True,
        )

    def get_tasks(self) -> list[Task]:
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
