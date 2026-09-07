import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agents.function_calling_agent import FunctionCallingAgent
from core.agent import Agent
from core.config import Config
from core.llm import AgentsLLM
from core.message import Message
from tools.tool import ToolRegistry


class DummyAgent(Agent):

  def run(self,input_text:str,**kwargs) -> str:
    return input_text


class ConfigTests(unittest.TestCase):

  def test_from_env_loads_shared_runtime_settings(self):
    environment = {
      "LLM_MODEL":"test-model",
      "LLM_PROVIDER":"test-provider",
      "TEMPERATURE":"0.25",
      "MAX_TOKENS":"512",
      "MAX_HISTORY_LENGTH":"3",
      "DEBUG":"true",
      "LOG_LEVEL":"DEBUG"
    }

    with patch.dict(os.environ,environment,clear=True):
      config = Config.from_env()

    self.assertEqual(config.default_model,"test-model")
    self.assertEqual(config.default_provider,"test-provider")
    self.assertEqual(config.temperature,0.25)
    self.assertEqual(config.max_tokens,512)
    self.assertEqual(config.max_history_length,3)
    self.assertTrue(config.debug)
    self.assertEqual(config.log_level,"DEBUG")

  def test_agent_inherits_llm_config_and_limits_history(self):
    config = Config(max_history_length=2)
    llm = SimpleNamespace(config=config)
    agent = DummyAgent("test-agent",llm)

    for content in ("one","two","three"):
      agent.add_message(Message(content,"user"))

    self.assertIs(agent.config,config)
    self.assertEqual(
      [message.content for message in agent.get_history()],
      ["two","three"]
    )


class LLMConfigTests(unittest.TestCase):

  @patch("core.llm.OpenAI")
  def test_think_uses_model_temperature_and_max_tokens(self,openai_class):
    chunk = SimpleNamespace(
      choices=[SimpleNamespace(delta=SimpleNamespace(content="done"))]
    )
    client = openai_class.return_value
    client.chat.completions.create.return_value = [chunk]
    config = Config(
      default_model="configured-model",
      temperature=0.35,
      max_tokens=256
    )
    llm = AgentsLLM(
      config=config,
      apiKey="test-key",
      baseUrl="https://example.test/v1",
      timeout=1
    )

    result = llm.think([{"role":"user","content":"hello"}])

    self.assertEqual(result,"done")
    request = client.chat.completions.create.call_args.kwargs
    self.assertEqual(request["model"],"configured-model")
    self.assertEqual(request["temperature"],0.35)
    self.assertEqual(request["max_tokens"],256)
    self.assertTrue(request["stream"])


class FunctionCallingAgentConfigTests(unittest.TestCase):

  def test_agent_forwards_shared_generation_config(self):
    config = Config(temperature=0.4,max_tokens=128)

    class FakeLLM:
      def __init__(self):
        self.config = config
        self.request = None

      def call_with_tools(self,**kwargs):
        self.request = kwargs
        return SimpleNamespace(tool_calls=[],content="finished")

    llm = FakeLLM()
    agent = FunctionCallingAgent(
      name="test-agent",
      llm=llm,
      registry=ToolRegistry()
    )

    result = agent.run("hello")

    self.assertEqual(result,"finished")
    self.assertIs(agent.config,config)
    self.assertEqual(llm.request["temperature"],0.4)
    self.assertEqual(llm.request["max_tokens"],128)


if __name__ == "__main__":
  unittest.main()
