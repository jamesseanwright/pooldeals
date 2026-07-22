from crewai import Task
from crewai.flow.flow import Flow, listen, router, start
from pydantic import BaseModel, Field

from pooldeals.crew import PooldealsCrew


class PooldealsReviewFlowState(BaseModel):
    task_names: list[str] = Field(default_factory=list)
    task_index: int = 0
    task_name: str = ""
    builder_output: str = ""
    review_feedback: str = ""
    final_output: str = ""
    final_outputs: dict[str, str] = Field(default_factory=dict)


class PooldealsDevFlow(Flow[PooldealsReviewFlowState]):
    """Runs each configured task through the builder agent, has the reviewer
    critique its output, then has the builder apply any resulting feedback,
    before moving on to the next task."""

    def __init__(self) -> None:
        super().__init__()

        # This feels a bit hacky; the CrewBaseMeta class which
        # wraps our crew class via the @CrewBase decorator should
        # correctly bind our crew and agents to the configured
        # knowledge sources, tools etc. (https://github.com/crewAIInc/crewAI/blob/6d496f799b4bda411cab23ef04377c14a90f98f8/lib/crewai/src/crewai/project/crew_base.py#L229),
        # but it would be nice to find a cleaner way to integrate our crew with this flow.
        self._pooldeals_crew = PooldealsCrew()
        self._builder = self._pooldeals_crew.builder()
        self._reviewer = self._pooldeals_crew.reviewer()

    @start("run_next_task")
    def run_builder_task(self) -> str:
        if not self.state.task_names:
            self.state.task_names = list(
                self._pooldeals_crew.tasks_config.keys()  # type: ignore[attr-defined]
            )

        task_name = self.state.task_names[self.state.task_index]
        task_config = self._pooldeals_crew.tasks_config[task_name]  # type: ignore[attr-defined]
        self.state.task_name = task_name

        builder_task = Task(config=task_config)
        output = self._builder.execute_task(builder_task)
        self.state.builder_output = output
        return output

    @listen(run_builder_task)
    def review_builder_output(self, builder_output: str) -> str:
        review_task = Task(
            description=(
                f"Review the code produced by the builder agent for the "
                f"'{self.state.task_name}' task.\n\n"
                "Builder's output:\n"
                f"{builder_output}\n\n"
                "Scrutinise it against PoolDeals' coding, testing and security "
                "standards, and list any required changes as concrete, "
                "actionable feedback. If no changes are required, clearly state "
                "that the output is approved as-is."
            ),
            expected_output=(
                "A list of concrete code review feedback items the builder must "
                "address, or a clear statement of approval if no changes are needed."
            ),
            agent=self._reviewer,
        )
        feedback = self._reviewer.execute_task(review_task, context=builder_output)
        self.state.review_feedback = feedback
        return feedback

    @listen(review_builder_output)
    def apply_review_feedback(self, review_feedback: str) -> str:
        fix_task = Task(
            description=(
                f"Update your previous output for the '{self.state.task_name}' "
                "task to address the following code review feedback:\n\n"
                f"{review_feedback}\n\n"
                "Your original output was:\n"
                f"{self.state.builder_output}\n\n"
                "If the feedback states the output is already approved, leave it "
                "unchanged."
            ),
            expected_output=(
                "The final version of the task's output with all review feedback "
                "addressed, with all changes written to their respective output files."
            ),
            agent=self._builder,
        )
        final_output = self._builder.execute_task(
            fix_task, context=self.state.builder_output
        )
        self.state.final_output = final_output
        self.state.final_outputs[self.state.task_name] = final_output
        return final_output

    @router(apply_review_feedback, emit=["run_next_task", "all_tasks_complete"])
    def route_to_next_task(self) -> str:
        self.state.task_index += 1
        if self.state.task_index < len(self.state.task_names):
            return "run_next_task"
        return "all_tasks_complete"

    @listen("all_tasks_complete")
    def finish(self) -> dict[str, str]:
        return self.state.final_outputs


def run_dev_flow():
    PooldealsDevFlow().kickoff()


if __name__ == "__main__":
    run_dev_flow()
