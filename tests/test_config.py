from pathlib import Path

import pytest
from pydantic import ValidationError

from flow_agent.config import Settings


def test_default_settings():
    settings = Settings(
        _env_file=None,
    )

    assert settings.environment == "development"
    assert settings.workspace_root == Path("workspace")
    assert settings.log_level == "INFO"


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv(
        "FLOW_AGENT_ENVIRONMENT",
        "test",
    )
    monkeypatch.setenv(
        "FLOW_AGENT_WORKSPACE_ROOT",
        "test-workspace",
    )
    monkeypatch.setenv(
        "FLOW_AGENT_LOG_LEVEL",
        "DEBUG",
    )

    settings = Settings(
        _env_file=None,
    )

    assert settings.environment == "test"
    assert settings.workspace_root == Path(
        "test-workspace"
    )
    assert settings.log_level == "DEBUG"


def test_reject_invalid_environment(monkeypatch):
    monkeypatch.setenv(
        "FLOW_AGENT_ENVIRONMENT",
        "invalid",
    )

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
        )


def test_reject_invalid_log_level(monkeypatch):
    monkeypatch.setenv(
        "FLOW_AGENT_LOG_LEVEL",
        "LOUD",
    )

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
        )


def test_settings_are_immutable():
    settings = Settings(
        _env_file=None,
    )

    with pytest.raises(ValidationError):
        settings.log_level = "DEBUG"


def test_settings_load_from_env_file(tmp_path):
    env_file = tmp_path / ".env"

    env_file.write_text(
        "\n".join(
            [
                "FLOW_AGENT_ENVIRONMENT=test",
                "FLOW_AGENT_WORKSPACE_ROOT=fixture-workspace",
                "FLOW_AGENT_LOG_LEVEL=WARNING",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(
        _env_file=env_file,
    )

    assert settings.environment == "test"
    assert settings.workspace_root == Path(
        "fixture-workspace"
    )
    assert settings.log_level == "WARNING"

def test_default_llm_runtime_settings():
    settings = Settings(
        _env_file=None,
    )

    assert settings.llm_timeout_seconds == 30.0
    assert settings.llm_max_retries == 2
    
def test_reject_negative_llm_retries():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            llm_max_retries=-1,
        )
