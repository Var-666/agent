from enum import StrEnum
from typing import ClassVar, Self
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from flow_agent.domain.artifact import Artifact
from flow_agent.domain.task import Task, TaskStatus
from flow_agent.exceptions import (
    DuplicateTaskError,
    InvalidRunStateTransition,
    InvalidTaskDependency,
    RunNotCompletable,
    TaskDependencyCycle,
    ArtifactRunMismatch,
    ArtifactTaskMismatch,
    DuplicateArtifactError,
    TerminalRunMutationError,
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
    _ALLOWED_TRANSITIONS: ClassVar[dict[RunStatus, frozenset[RunStatus]]] = {
        RunStatus.QUEUED: frozenset({RunStatus.PLANNING,RunStatus.CANCELLED,}),
        RunStatus.PLANNING: frozenset({RunStatus.RUNNING,RunStatus.WAITING_USER,RunStatus.BLOCKED,RunStatus.FAILED,RunStatus.CANCELLED,}),
        RunStatus.RUNNING: frozenset({RunStatus.WAITING_USER,RunStatus.WAITING_APPROVAL,RunStatus.WAITING_EXTERNAL,RunStatus.BLOCKED,RunStatus.COMPLETED,RunStatus.FAILED,RunStatus.CANCELLED,}),
        RunStatus.WAITING_USER: frozenset({RunStatus.RUNNING,RunStatus.BLOCKED,RunStatus.FAILED,RunStatus.CANCELLED,}),
        RunStatus.WAITING_APPROVAL: frozenset({RunStatus.RUNNING,RunStatus.BLOCKED,RunStatus.FAILED,RunStatus.CANCELLED,}),
        RunStatus.WAITING_EXTERNAL: frozenset({RunStatus.RUNNING,RunStatus.BLOCKED,RunStatus.FAILED,RunStatus.CANCELLED,}),
        RunStatus.BLOCKED: frozenset({RunStatus.RUNNING,RunStatus.FAILED,RunStatus.CANCELLED,}),
        RunStatus.COMPLETED: frozenset(),
        RunStatus.FAILED: frozenset(),
        RunStatus.CANCELLED: frozenset(),
    }

    _TERMINAL_STATUSES: ClassVar[frozenset[RunStatus]] = frozenset(
        {
            RunStatus.COMPLETED,
            RunStatus.FAILED,
            RunStatus.CANCELLED,
        }
    )

    id: str = Field(default_factory=lambda: str(uuid4()), frozen=True)
    goal_id: str = Field(min_length=1, frozen=True)
    status: RunStatus = Field(default=RunStatus.QUEUED, frozen=True)
    tasks: tuple[Task, ...] = Field(default_factory=tuple, frozen=True)
    artifacts: tuple[Artifact, ...] = Field(default_factory=tuple, frozen=True)

    @model_validator(mode="after")
    def validate_domain_invariants(self) -> Self:
        self._validate_task_collection(self.tasks)
        self._validate_artifact_collection(self.artifacts)

        if self.status == RunStatus.COMPLETED:
            self._validate_completion()

        return self

    def add_task(self, task: Task) -> None:
        self._ensure_mutable()
        candidate_tasks = self.tasks + (task,)
        self._validate_task_collection(candidate_tasks)
        object.__setattr__(self, "tasks", candidate_tasks)

    def add_artifact(self, artifact: Artifact) -> None:
        self._ensure_mutable()
        candidate_artifacts = self.artifacts + (artifact,)
        self._validate_artifact_collection(candidate_artifacts)
        object.__setattr__(self, "artifacts", candidate_artifacts)

    def transition_to(self, new_status: RunStatus) -> None:
      target_status = RunStatus(new_status)

      allowed_transitions = self._ALLOWED_TRANSITIONS[self.status]

      if target_status not in allowed_transitions:
          raise InvalidRunStateTransition(current_status=self.status.value,target_status=target_status.value)

      if target_status == RunStatus.COMPLETED:
          self._validate_completion()

      object.__setattr__(self,"status",target_status)

    def _validate_task_collection(self, tasks: tuple[Task, ...]) -> None:
        task_ids: set[str] = set()

        for task in tasks:
            if task.id in task_ids:
                raise DuplicateTaskError(task.id)

            task_ids.add(task.id)

        for task in tasks:
            for dependency_id in task.dependencies:
                if dependency_id == task.id:
                    raise InvalidTaskDependency(
                        task_id=task.id,
                        dependency_id=dependency_id,
                    )

                if dependency_id not in task_ids:
                    raise InvalidTaskDependency(
                        task_id=task.id,
                        dependency_id=dependency_id,
                    )

        self._validate_no_dependency_cycle(tasks)

    def _validate_artifact_collection(
        self,
        artifacts: tuple[Artifact, ...],
    ) -> None:
        artifact_ids: set[str] = set()

        for artifact in artifacts:
            if artifact.id in artifact_ids:
                raise DuplicateArtifactError(artifact.id)

            artifact_ids.add(artifact.id)

            if artifact.run_id != self.id:
                raise ArtifactRunMismatch(
                    artifact_run_id=artifact.run_id,
                    run_id=self.id,
                )

            if (
                artifact.producer_task_id is not None
                and not self._contains_task(artifact.producer_task_id)
            ):
                raise ArtifactTaskMismatch(artifact.producer_task_id)

    def _validate_completion(self) -> None:
      for task in self.tasks:
          if task.status == TaskStatus.SKIPPED:
              continue

          if task.status != TaskStatus.COMPLETED:
              raise RunNotCompletable()

    def _contains_artifact(self, artifact_id: str) ->bool:
      return any(artifact.id == artifact_id for artifact in self.artifacts)

    def _contains_task(self, task_id: str) -> bool:
        return any(task.id == task_id for task in self.tasks)

    def _validate_no_dependency_cycle(self, tasks: tuple[Task, ...]) -> None:
        graph = {task.id: task.dependencies for task in tasks}

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise TaskDependencyCycle(task_id)
            if task_id in visited:
                return

            visiting.add(task_id)

            for dependency_id in graph.get(task_id, ()):
                visit(dependency_id)

            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in graph:
            visit(task_id)

    def _ensure_mutable(self) -> None:
        if self.status in self._TERMINAL_STATUSES:
            raise TerminalRunMutationError(self.status.value)
