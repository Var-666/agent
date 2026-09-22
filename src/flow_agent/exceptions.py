class FlowAgentError(Exception):
    """FlowAgent domain base exception."""


class InvalidTaskStateTransition(FlowAgentError):
    """Raised when a task cannot transition to the requested status."""

    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            f"Invalid task state transition: {current_status} -> {target_status}"
        )
