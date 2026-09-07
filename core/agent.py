from abc import ABC,abstractmethod
from typing import Optional
from .message import Message
from .llm import LLMClient
from .config import Config

class Agent(ABC):
  """Agent base class"""

  def __init__(
      self,
      name:str,
      llm:LLMClient,
      system_prompt:Optional[str]=None,
      config:Optional[Config] = None):
    self.name = name
    self.llm = llm
    self.system_prompt = system_prompt
    self.config = config or getattr(llm,"config",None) or Config.from_env()
    self._history : list[Message] = []

  @abstractmethod
  def run(self,input_text:str,**kwargs) -> str:
    """run agent"""
    pass

  def add_message(self,message:Message):
    """add message to history"""
    self._history.append(message)

    overflow = len(self._history) - self.config.max_history_length
    if overflow > 0:
      del self._history[:overflow]

  def clear_history(self):
    """clear history"""
    self._history.clear()

  def get_history(self) -> list[Message]:
    """retrieve history"""
    return self._history.copy()

  def __str__(self):
    return f"Agent(name={self.name})"
