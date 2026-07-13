from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

@CrewBase
class Pooldeals():
    """Pooldeals crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def builder(self) -> Agent:
        return Agent(
            config=self.agents_config['builder'], # type: ignore[index]
            verbose=True
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['reviewer'], # type: ignore[index]
            verbose=True
        )

    def get_tasks(self) -> list[Task]:
        return map(lambda t: Task(t), self.tasks_config.values)

    @crew
    def crew(self) -> Crew:
        """Creates the Pooldeals crew"""
        return Crew(
            agents=self.agents,
            tasks=self.get_tasks(),
            process=Process.sequential,
            knowledge_sources=[TextFileKnowledgeSource(
                "backend_coding_standards.md",
                "frontend_coding_standards.md",
                "general.md",
                "security.md",
                "source_control.md",
                "testing.md",
            )],
            verbose=True,
        )
