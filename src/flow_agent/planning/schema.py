from pydantic import BaseModel, Field


class PlanTask(BaseModel):
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
    goal_id: str = Field(min_length=1)
    summary: str = Field(
        min_length=1,
        description="Short explanation of the execution strategy.",
    )
    tasks: tuple[PlanTask, ...] = Field(min_length=1)
