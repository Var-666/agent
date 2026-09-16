from typing import Any,Dict,List,Literal,Optional
from pydantic import BaseModel,Field

AgentStatus = Literal[
  "idle",
  "running",
  "completed",
  "failed"
]

class AgentState(BaseModel):
  """Agent 当前任务执行状态"""
  
  task:str
  status:AgentStatus = "idle"
  step:int = 0
  
  tools_called:List[str] = Field(default_factory=list)
  tool_results:List[Dict[str,Any]] = Field(default_factory=list)
  tool_call_counts:Dict[str,int] = Field(default_factory=dict)

  error_count:int = 0
  last_error:Optional[str] = None
