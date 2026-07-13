from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


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
            verbose=True,
        )
