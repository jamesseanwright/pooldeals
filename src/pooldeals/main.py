from crewai import Task
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

from pooldeals.crew import PooldealsCrew


class PooldealsReviewFlowState(BaseModel):
    task_name: str = ""
    builder_output: str = ""
    review_feedback: str = ""
    final_output: str = ""


class PooldealsDevFlow(Flow[PooldealsReviewFlowState]):
    """Runs a builder task, has the reviewer critique its output, then has
    the builder apply any resulting feedback."""

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

    @start()
    def run_builder_task(self) -> str:
        task_name, task_config = next(
            iter(self._pooldeals_crew.tasks_config.items())  # type: ignore[attr-defined]
        )
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
        return final_output


def run_dev_flow():
    PooldealsDevFlow().kickoff()


if __name__ == "main":
    run_dev_flow()
