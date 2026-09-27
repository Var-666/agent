class FlowAgentError(Exception):
    """FlowAgent base exception."""

"""==============================Task error=============================="""

class InvalidTaskStateTransition(FlowAgentError):
    """Raised when a task cannot transition to the requested status."""

    def __init__(self, current_status: str, target_status: str):
        super().__init__(f"Invalid task state transition: {current_status} -> {target_status}")


class DuplicateTaskError(FlowAgentError):
    """Raised when a run already contains the task."""

    def __init__(self, task_id: str):
        super().__init__(f"Task already exists in run: {task_id}")


class InvalidTaskDependency(FlowAgentError):
    """Raised when a task dependency is invalid."""

    def __init__(self, task_id: str, dependency_id: str):
        super().__init__(f"Invalid dependency for task {task_id}: {dependency_id}")


class TaskDependencyCycle(FlowAgentError):
    """Raised when task dependencies contain a cycle."""

    def __init__(self, task_id: str):
        super().__init__(f"Task dependency cycle detected involving task: {task_id}")

"""==============================Run error=============================="""

class InvalidRunStateTransition(FlowAgentError):
    """Raised when a run cannot transition to the requested status."""

    def __init__(self, current_status: str, target_status: str):
        super().__init__(f"Invalid run state transition: "f"{current_status} -> {target_status}")


class RunNotCompletable(FlowAgentError):
    """Raised when a run does not satisfy completion requirements."""

    def __init__(self):
        super().__init__("Run cannot be completed while non-skipped tasks are not completed")


class TerminalRunMutationError(FlowAgentError):
    """Raised when attempting to modify a terminal run."""

    def __init__(self, status: str):
        super().__init__(f"Cannot modify run in terminal status: {status}")

"""==============================Artifact error=============================="""

class DuplicateArtifactError(FlowAgentError):
    """Raised when a run already contains an artifact."""

    def __init__(self, artifact_id: str):
        super().__init__(f"Artifact already exists in run: {artifact_id}")


class ArtifactRunMismatch(FlowAgentError):
    """Raised when an artifact belongs to another run."""

    def __init__(self, artifact_run_id: str, run_id: str):
        super().__init__(f"Artifact belongs to run {artifact_run_id}, "f"not run {run_id}")


class ArtifactTaskMismatch(FlowAgentError):
    """Raised when artifact producer task is not in the run."""

    def __init__(self, task_id: str):
        super().__init__(f"Artifact producer task does not belong to run: "f"{task_id}")

"""==============================Planner error=============================="""

class PlannerError(FlowAgentError):
    """Base exception for planner failures."""


class PlannerModelError(PlannerError):
    """Raised when the planner model invocation fails."""

    def __init__(self):
        super().__init__("Planner model invocation failed")


class PlannerOutputError(PlannerError):
    """Raised when planner output cannot be validated."""

    def __init__(self):
        super().__init__("Planner returned invalid structured output")
