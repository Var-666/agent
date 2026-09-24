from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from flow_agent.config import Settings

def create_chat_model(settings: Settings) -> BaseChatModel:
  if not settings.llm_model:
    raise ValueError("FLOW_AGENT_LLM_MODEL is required")
  
  if (settings.llm_api_key is None or not settings.llm_api_key.get_secret_value()):
    raise ValueError("FLOW_AGENT_LLM_API_KEY is required")

  return init_chat_model(
      model=settings.llm_model,
      model_provider="openai",
      api_key=settings.llm_api_key.get_secret_value(),
      base_url=settings.llm_base_url or None,
      temperature=0,
      timeout=settings.llm_timeout_seconds,
      max_retries=settings.llm_max_retries,
  )