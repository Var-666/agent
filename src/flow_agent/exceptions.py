class FlowAgentError(Exception):
    """FlowAgent domain base exception."""


class InvalidTaskStateTransition(FlowAgentError):
    """Raised when a task cannot transition to the requested status."""

    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            f"Invalid task state transition: {current_status} -> {target_status}"
        )


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
