import unittest
from unittest.mock import patch

from core.config import Config
from main import create_agent


class MainTests(unittest.TestCase):

  @patch("main.LLMClient")
  def test_create_agent_uses_shared_config_and_registers_calculator(
      self,
      llm_client_class):
    config = Config(default_model="test-model")

    agent = create_agent(config)

    llm_client_class.assert_called_once_with(config=config)
    self.assertIs(agent.config,config)
    self.assertEqual(
      agent.registry.execute_tool("calculator",{"a":25,"b":37}),
      "62"
    )


if __name__ == "__main__":
  unittest.main()
