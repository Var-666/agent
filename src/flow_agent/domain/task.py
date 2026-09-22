from enum import StrEnum
from typing import ClassVar
from uuid import uuid4

from pydantic import BaseModel, Field

from flow_agent.exceptions import InvalidTaskStateTransition

class TaskStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class Task(BaseModel):
    _ALLOWED_TRANSITIONS: ClassVar[dict[TaskStatus, frozenset[TaskStatus]]] = {
        TaskStatus.PENDING: frozenset(
            {TaskStatus.RUNNING, TaskStatus.SKIPPED, TaskStatus.CANCELLED}
        ),
        TaskStatus.RUNNING: frozenset(
            {
                TaskStatus.WAITING,
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            }
        ),
        TaskStatus.WAITING: frozenset(
            {TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.CANCELLED}
        ),
        TaskStatus.COMPLETED: frozenset(),
        TaskStatus.FAILED: frozenset(),
        TaskStatus.SKIPPED: frozenset(),
        TaskStatus.CANCELLED: frozenset(),
    }

    id: str = Field(default_factory=lambda: str(uuid4()), frozen=True)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: TaskStatus = Field(default=TaskStatus.PENDING, frozen=True)
    dependencies: list[str] = Field(default_factory=list)

    def transition_to(self, new_status: TaskStatus) -> None:
        target_status = TaskStatus(new_status)
        allowed_transitions = self._ALLOWED_TRANSITIONS[self.status]

        if target_status not in allowed_transitions:
            raise InvalidTaskStateTransition(
                current_status=self.status.value,
                target_status=target_status.value,
            )

        object.__setattr__(self, "status", target_status)
