import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .config import Config

class LLMClient:
  """
    An LLM client.
    It is used to call any service compatible with the OpenAI API and
    uses streaming responses by default.
  """

  def __init__(
      self,
      model:Optional[str] = None,
      api_key:Optional[str] = None,
      base_url:Optional[str] = None,
      timeout:Optional[int] = None,
      config:Optional[Config] = None):
    self.config = config or Config.from_env()
    self.model = model or self.config.default_model
    api_key = api_key or os.getenv("LLM_API_KEY")
    base_url = base_url or os.getenv("LLM_BASE_URL")
    timeout = timeout or int(os.getenv("LLM_TIMEOUT",60))

    if not all([self.model,api_key,base_url,timeout]):
      raise ValueError("The model, API key, and service address must be provided or defined in the .env file.")

    self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

  def _build_request_options(
      self,
      messages:List[Dict[str,Any]],
      temperature:Optional[float],
      max_tokens:Optional[int]) -> Dict[str,Any]:
    """Build shared request options from per-call overrides and Config."""
    options:Dict[str,Any] = {
      "model":self.model,
      "messages":messages,
      "temperature":(
        self.config.temperature
        if temperature is None
        else temperature
      )
    }

    effective_max_tokens = (
      self.config.max_tokens
      if max_tokens is None
      else max_tokens
    )
    if effective_max_tokens is not None:
      options["max_tokens"] = effective_max_tokens

    return options

  def think(
      self,
      messages:List[Dict[str,Any]],
      temperature:Optional[float] = None,
      max_tokens:Optional[int] = None) -> Optional[str]:
    """
    Invoke the large language model to perform reasoning and return its response.
    """
    print(f"🧠 Calling {self.model} model...")
    try:
        response = self.client.chat.completions.create(
            **self._build_request_options(
              messages,
              temperature,
              max_tokens
            ),
            stream=True
        )

        # Handling streaming responses
        print("✅ LLM response successful:")
        collected_content = []
        for chunk in response:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content or ""
            collected_content.append(content)
        return "".join(collected_content)

    except Exception as e:
        print(f"❌ An error occurred while calling the LLM API: {e}")
        return None

  def call_with_tools(
      self,
      messages:List[Dict[str,Any]],
      tools:List[Dict[str,Any]],
      temperature:Optional[float] = None,
      max_tokens:Optional[int] = None) -> Optional[Any]:
      print(f"🧠 Calling {self.model} model with tools...")

      try:
         response = self.client.chat.completions.create(
            **self._build_request_options(
              messages,
              temperature,
              max_tokens
            ),
            tools=tools,
            tool_choice="auto",
            stream=False
         )

         return response.choices[0].message

      except Exception as e:
        print(f"❌ LLM API 调用失败: {e}")
        return None
