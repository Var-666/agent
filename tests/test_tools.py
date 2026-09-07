import unittest

from tools.tool_async_executor import AsyncToolExecutor
from tools.tool import Tool, ToolCall, ToolParameters, ToolRegistry
from tools.tool_chain_manager import ToolChain, ToolChainManager


class EchoTool(Tool):

  def __init__(self):
    super().__init__("echo","Return the supplied text")

  def run(self,arguments):
    return arguments["text"]

  def get_parameters(self):
    return [
      ToolParameters(
        name="text",
        type="string",
        description="Text to return"
      )
    ]


class ToolRegistryTests(unittest.TestCase):

  def setUp(self):
    self.registry = ToolRegistry()
    self.registry.register_tool(EchoTool())
    self.registry.register_function(
      "join",
      "Join two strings",
      lambda left,right: f"{left}{right}"
    )

  def test_object_tool_receives_dictionary_arguments(self):
    result = self.registry.execute_tool("echo",{"text":"hello"})
    self.assertEqual(result,"hello")

  def test_registered_function_receives_keyword_arguments(self):
    result = self.registry.execute_tool(
      "join",
      {"left":"hello ","right":"world"}
    )
    self.assertEqual(result,"hello world")

  def test_registry_rejects_non_dictionary_arguments(self):
    with self.assertRaisesRegex(TypeError,"must be a dictionary"):
      self.registry.execute_tool("echo","hello")


class AsyncToolExecutorTests(unittest.IsolatedAsyncioTestCase):

  async def test_parallel_calls_use_the_same_tool_call_format(self):
    registry = ToolRegistry()
    registry.register_function("upper","Uppercase text",lambda text:text.upper())

    async with AsyncToolExecutor(registry,max_workers=2) as executor:
      results = await executor.execute_tools_parallel([
        ToolCall(tool_name="upper",arguments={"text":"one"}),
        ToolCall(tool_name="upper",arguments={"text":"two"})
      ])

    self.assertEqual(results,["ONE","TWO"])


class ToolChainTests(unittest.TestCase):

  def setUp(self):
    self.registry = ToolRegistry()
    self.registry.register_function("upper","Uppercase text",lambda text:text.upper())
    self.registry.register_function(
      "format_result",
      "Format a result",
      lambda prefix,text:f"{prefix}{text}"
    )

  def test_chain_renders_argument_dictionaries(self):
    chain = ToolChain("normalize","Normalize and format text")
    chain.add_step("upper",{"text":"{input}"},"normalized")
    chain.add_step(
      "format_result",
      {"prefix":"Result: ","text":"{normalized}"}
    )

    result = chain.execute(self.registry,"hello")

    self.assertEqual(result,"Result: HELLO")

  def test_nested_templates_are_rendered(self):
    self.registry.register_function(
      "read_payload",
      "Read a nested payload",
      lambda payload:payload["items"][0]
    )
    chain = ToolChain("nested","Render nested parameters")
    chain.add_step(
      "read_payload",
      {"payload":{"items":["{input}"]}}
    )

    self.assertEqual(chain.execute(self.registry,"hello"),"hello")

  def test_empty_chain_is_rejected(self):
    chain = ToolChain("empty","No steps")
    with self.assertRaisesRegex(ValueError,"has no steps"):
      chain.execute(self.registry,"hello")

  def test_manager_rejects_unknown_chain(self):
    manager = ToolChainManager(self.registry)
    with self.assertRaisesRegex(ValueError,"does not exist"):
      manager.execute_chain("missing","hello")


if __name__ == "__main__":
  unittest.main()
