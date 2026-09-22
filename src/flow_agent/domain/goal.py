from datetime import datetime,timezone
from uuid import uuid4

from pydantic import BaseModel,Field

class Goal(BaseModel):
  id: str = Field(default_factory=lambda:str(uuid4()),frozen=True)
  title: str = Field(min_length=1)
  description: str = Field(min_length=1)
  success_criteria: list[str] = Field(default_factory=list)
  requested_outputs: list[str] = Field(default_factory=list)
  created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc),frozen=True)