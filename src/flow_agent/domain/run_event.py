from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

class RunEventKind(StrEnum):
  RUN_STARTED = "RUN_STARTED"
  RUN_COMPLETED = "RUN_COMPLETED"
  RUN_FAILED = "RUN_FAILED"

  TASK_STARTED = "TASK_STARTED"
  TASK_RETRYING = "TASK_RETRYING"
  TASK_COMPLETED = "TASK_COMPLETED"
  TASK_FAILED = "TASK_FAILED"
  
class RunEvent(BaseModel):
  model_config = ConfigDict(frozen=True)
  id: str = Field(default_factory=lambda: str(uuid4()),frozen=True)
  run_id: str = Field(min_length=1,frozen=True)
  task_id: str | None = Field(default=None,frozen=True)
  kind: RunEventKind
  payload: dict[str,Any] = Field(default_factory=dict)
  created_at: AwareDatetime = Field(default_factory=lambda:datetime.now(timezone.utc),frozen=True)
  
  @field_validator("created_at")
  @classmethod
  def normalize_created_at(cls,value: datetime) -> datetime:
    return value.astimezone(timezone.utc)
  
  