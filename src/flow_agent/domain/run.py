from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from flow_agent.domain.task import Task
from flow_agent.exceptions import (
    DuplicateTaskError,
    InvalidTaskDependency,
    TaskDependencyCycle,
)


class RunStatus(StrEnum):
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_USER = "WAITING_USER"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Run(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), frozen=True)
    goal_id: str = Field(min_length=1, frozen=True)
    status: RunStatus = Field(default=RunStatus.QUEUED, frozen=True)
    tasks: list[Task] = Field(default_factory=list)

    def add_task(self, task: Task) -> None:
        if self._contains_task(task.id):
            raise DuplicateTaskError(task.id)

        self._validate_task_dependencies(task)
        self.tasks.append(task)

        try:
            self._validate_no_dependency_cycle()
        except TaskDependencyCycle:
            self.tasks.pop()
            raise

    def _contains_task(self, task_id: str) -> bool:
        return any(task.id == task_id for task in self.tasks)

    def _validate_task_dependencies(self, task: Task) -> None:
        for dependency_id in task.dependencies:
            if dependency_id == task.id:
                raise InvalidTaskDependency(
                    task_id=task.id,
                    dependency_id=dependency_id,
                )

            if not self._contains_task(dependency_id):
                raise InvalidTaskDependency(
                    task_id=task.id,
                    dependency_id=dependency_id,
                )

    def _validate_no_dependency_cycle(self) -> None:
        graph = {task.id: task.dependencies for task in self.tasks}

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise TaskDependencyCycle(task_id)
            if task_id in visited:
                return

            visiting.add(task_id)

            for dependency_id in graph.get(task_id, []):
                visit(dependency_id)

            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in graph:
            visit(task_id)
