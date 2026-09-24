import pytest

from flow_agent.config import Settings
from flow_agent.models import create_chat_model


def test_create_chat_model_requires_model():
    settings = Settings(
        _env_file=None,
        llm_api_key="test-key",
    )

    with pytest.raises(
        ValueError,
        match="FLOW_AGENT_LLM_MODEL",
    ):
        create_chat_model(settings)
        
def test_create_chat_model_requires_api_key():
    settings = Settings(
        _env_file=None,
        llm_model="test-model",
    )

    with pytest.raises(
        ValueError,
        match="FLOW_AGENT_LLM_API_KEY",
    ):
        create_chat_model(settings)