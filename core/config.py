import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


load_dotenv()

class Config(BaseModel):
  """Agent config class"""

  # LLM config
  default_model:str = "gpt-3.5-turbo"
  default_provider:str = "openai"
  temperature:float = Field(default=0.7,ge=0)
  max_tokens:Optional[int] = Field(default=None,gt=0)

  # system config
  debug:bool = False
  log_level:str = "INFO"

  # other config
  max_history_length:int = Field(default=100,gt=0)

  @classmethod
  def from_env(cls)->"Config":
    """create configuration from environment variables"""
    return cls(
      default_model=os.getenv("LLM_MODEL","gpt-3.5-turbo"),
      default_provider=os.getenv("LLM_PROVIDER","openai"),
      debug=os.getenv("DEBUG","false").lower() == "true",
      log_level=os.getenv("LOG_LEVEL","INFO"),
      temperature=float(os.getenv("TEMPERATURE","0.7")),
      max_tokens=int(os.getenv("MAX_TOKENS")) if os.getenv("MAX_TOKENS") else None,
      max_history_length=int(os.getenv("MAX_HISTORY_LENGTH","100"))
    )

  def to_dict(self)->Dict[str,Any]:
    """convert to a dict"""
    return self.model_dump()
