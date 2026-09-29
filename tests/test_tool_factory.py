import json

from flow_agent.tools.factory import (
    create_default_tools,
)
from flow_agent.tools.search import (
    WebSearchResult,
)


def fake_search_backend(
    query: str,
) -> tuple[WebSearchResult, ...]:
    return (
        WebSearchResult(
            title="Example",
            url="https://example.com",
            snippet=f"Result for {query}",
        ),
    )
    
def test_create_default_tools(
    tmp_path,
):
    tools = create_default_tools(
        tmp_path,
        search_backend=(
            fake_search_backend
        ),
    )

    names = tuple(
        tool.name
        for tool in tools
    )

    assert names == (
        "search_web",
        "read_url",
        "read_file",
        "write_file",
    )

    assert len(set(names)) == 4

def test_default_tools_use_injected_search_backend(
    tmp_path,
):
    tools = create_default_tools(
        tmp_path,
        search_backend=(
            fake_search_backend
        ),
    )

    tool_by_name = {
        tool.name: tool
        for tool in tools
    }

    result = tool_by_name[
        "search_web"
    ].invoke(
        {
            "query": "LangChain",
        }
    )

    assert json.loads(result) == [
        {
            "title": "Example",
            "url": "https://example.com",
            "snippet":
                "Result for LangChain",
        }
    ]
    
def test_default_file_tools_share_workspace(
    tmp_path,
):
    tools = create_default_tools(
        tmp_path,
        search_backend=(
            fake_search_backend
        ),
    )

    tool_by_name = {
        tool.name: tool
        for tool in tools
    }

    tool_by_name[
        "write_file"
    ].invoke(
        {
            "path": "output/result.txt",
            "content": "hello FlowAgent",
        }
    )

    result = tool_by_name[
        "read_file"
    ].invoke(
        {
            "path": "output/result.txt",
        }
    )

    assert result == "hello FlowAgent"
    
def test_default_tool_schemas(
    tmp_path,
):
    tools = create_default_tools(
        tmp_path,
        search_backend=(
            fake_search_backend
        ),
    )

    schemas = {
        tool.name: set(
            tool.args_schema
            .model_json_schema()[
                "properties"
            ]
        )
        for tool in tools
    }

    assert schemas == {
        "search_web": {
            "query",
        },
        "read_url": {
            "url",
        },
        "read_file": {
            "path",
        },
        "write_file": {
            "path",
            "content",
        },
    }