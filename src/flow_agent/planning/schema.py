from typing import Self

from pydantic import BaseModel, Field, model_validator, ConfigDict


class PlanTask(BaseModel):

    model_config = ConfigDict(frozen=True)

    key: str = Field(
        min_length=1,
        description="Stable identifier used inside the plan.",
    )
    title: str = Field(min_length=1, description="Short task title.")
    description: str = Field(
        min_length=1,
        description="What this task must accomplish.",
    )
    dependencies: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Keys of tasks that must finish first.",
    )


class ExecutionPlan(BaseModel):

    model_config = ConfigDict(frozen=True)
  
    goal_id: str = Field(min_length=1)
    summary: str = Field(
        min_length=1,
        description="Short explanation of the execution strategy.",
    )
    tasks: tuple[PlanTask, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        self._validate_unique_keys()
        self._validate_dependencies()
        self._validate_no_dependency_cycle()

        return self

    def _validate_unique_keys(self) -> None:
        seen: set[str] = set()

        for task in self.tasks:
            if task.key in seen:
                raise ValueError(f"Duplicate task key: {task.key}")
            seen.add(task.key)

    def _validate_dependencies(self) -> None:
        task_keys = {task.key for task in self.tasks}

        for task in self.tasks:
            for dependency in task.dependencies:
                if dependency == task.key:
                    raise ValueError(f"Task '{task.key}' cannot depend on itself")

                if dependency not in task_keys:
                    raise ValueError(
                        f"Task '{task.key}' depends on unknown task '{dependency}'"
                    )

    def _validate_no_dependency_cycle(self) -> None:
        graph = {task.key: task.dependencies for task in self.tasks}

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_key: str) -> None:
            if task_key in visiting:
                raise ValueError(f"Task dependency cycle detected at '{task_key}'")

            if task_key in visited:
                return

            visiting.add(task_key)

            for dependency in graph[task_key]:
                visit(dependency)

            visiting.remove(task_key)
            visited.add(task_key)

        for task_key in graph:
            visit(task_key)
