import unittest

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from tools.tool_async_executor import AsyncToolExecutor
from tools.tool import Tool, ToolCall, ToolRegistry
from tools.tool_chain_manager import ToolChain, ToolChainManager
from tools.tool_list.calculator_tool import CalculatorTool


class EchoArguments(BaseModel):
  model_config = ConfigDict(extra="forbid")

  text:str = Field(description="Text to return")


class EchoTool(Tool[EchoArguments]):

  def __init__(self):
    super().__init__(
      "echo",
      "Return the supplied text",
      EchoArguments
    )

  def run(self,arguments:EchoArguments):
    return arguments.text


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

  def test_tool_rejects_missing_arguments(self):
    with self.assertRaises(ValidationError):
      self.registry.execute_tool("echo",{})

  def test_tool_rejects_invalid_argument_types(self):
    with self.assertRaises(ValidationError):
      self.registry.execute_tool("echo",{"text":{"invalid":"value"}})

  def test_tool_rejects_extra_arguments(self):
    with self.assertRaises(ValidationError):
      self.registry.execute_tool(
        "echo",
        {"text":"hello","unexpected":True}
      )

  def test_openai_schema_comes_from_arguments_model(self):
    parameters = EchoTool().to_openai_schema()["function"]["parameters"]

    self.assertEqual(parameters["properties"]["text"]["type"],"string")
    self.assertEqual(
      parameters["properties"]["text"]["description"],
      "Text to return"
    )
    self.assertEqual(parameters["required"],["text"])
    self.assertFalse(parameters["additionalProperties"])


class CalculatorToolTests(unittest.TestCase):

  def setUp(self):
    self.registry = ToolRegistry()
    self.registry.register_tool(CalculatorTool())

  def test_calculator_accepts_integer_and_float_arguments(self):
    self.assertEqual(
      self.registry.execute_tool("calculator",{"a":25,"b":37}),
      "62"
    )
    self.assertEqual(
      self.registry.execute_tool("calculator",{"a":1.5,"b":2}),
      "3.5"
    )

  def test_calculator_rejects_numeric_strings(self):
    with self.assertRaises(ValidationError):
      self.registry.execute_tool("calculator",{"a":"25","b":37})

  def test_calculator_rejects_missing_and_extra_arguments(self):
    invalid_arguments = (
      {"a":25},
      {"a":25,"b":37,"operation":"multiply"}
    )

    for arguments in invalid_arguments:
      with self.subTest(arguments=arguments):
        with self.assertRaises(ValidationError):
          self.registry.execute_tool("calculator",arguments)


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
