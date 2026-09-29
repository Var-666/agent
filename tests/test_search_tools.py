import json

import pytest

from flow_agent.tools.search import (
    WebSearchResult,
    create_search_web_tool,
    create_tavily_search_backend,
)

def test_search_web_returns_results():
    def backend(
        query: str,
    ) -> tuple[WebSearchResult, ...]:
        assert query == "LangChain updates"

        return (
            WebSearchResult(
                title="LangChain release",
                url="https://example.com/release",
                snippet="New LangChain release.",
            ),
        )

    search_web = create_search_web_tool(
        backend
    )

    result = search_web.invoke(
        {
            "query": "LangChain updates",
        }
    )

    assert json.loads(result) == [
        {
            "title": "LangChain release",
            "url":
                "https://example.com/release",
            "snippet":
                "New LangChain release.",
        }
    ]
    
def test_search_web_normalizes_query():
    received = []

    def backend(
        query: str,
    ) -> tuple[WebSearchResult, ...]:
        received.append(query)
        return ()

    search_web = create_search_web_tool(
        backend
    )

    search_web.invoke(
        {
            "query":
                "  LangChain updates  ",
        }
    )

    assert received == [
        "LangChain updates"
    ]
    
@pytest.mark.parametrize(
    "query",
    [
        "",
        " ",
        "\n\t",
    ],
)
def test_search_web_rejects_empty_query(
    query,
):
    def backend(
        query: str,
    ) -> tuple[WebSearchResult, ...]:
        raise AssertionError(
            "Backend should not be called"
        )

    search_web = create_search_web_tool(
        backend
    )

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        search_web.invoke(
            {
                "query": query,
            }
        )
        
def test_search_web_propagates_backend_error():
    def backend(
        query: str,
    ) -> tuple[WebSearchResult, ...]:
        raise RuntimeError(
            "search provider unavailable"
        )

    search_web = create_search_web_tool(
        backend
    )

    with pytest.raises(
        RuntimeError,
        match="provider unavailable",
    ):
        search_web.invoke(
            {
                "query": "LangChain",
            }
        )
        
def test_search_web_schema_exposes_only_query():
    def backend(
        query: str,
    ) -> tuple[WebSearchResult, ...]:
        return ()

    search_web = create_search_web_tool(
        backend
    )

    schema = (
        search_web
        .args_schema
        .model_json_schema()
    )

    assert set(
        schema["properties"]
    ) == {
        "query",
    }
    
class FakeSearchTool:
    def __init__(
        self,
        response,
    ):
        self.response = response
        self.calls = []

    def invoke(
        self,
        input,
    ):
        self.calls.append(input)
        return self.response
      
def test_tavily_backend_normalizes_results():
    fake_tool = FakeSearchTool(
        {
            "results": [
                {
                    "title": " Result ",
                    "url":
                        " https://example.com ",
                    "content": " Snippet ",
                    "score": 0.9,
                }
            ]
        }
    )

    factory_kwargs = {}

    def tool_factory(
        **kwargs,
    ):
        factory_kwargs.update(kwargs)
        return fake_tool

    backend = create_tavily_search_backend(
        max_results=3,
        tool_factory=tool_factory,
    )

    results = backend(
        "LangChain updates"
    )

    assert fake_tool.calls == [
        {
            "query":
                "LangChain updates"
        }
    ]

    assert results == (
        WebSearchResult(
            title="Result",
            url="https://example.com",
            snippet="Snippet",
        ),
    )

    assert (
        factory_kwargs["max_results"]
        == 3
    )

    assert (
        factory_kwargs["include_answer"]
        is False
    )

    assert (
        factory_kwargs[
            "include_raw_content"
        ]
        is False
    )

    assert (
        factory_kwargs["include_images"]
        is False
    )
    
@pytest.mark.parametrize(
    "response",
    [
        "invalid",
        {},
        {
            "results": "invalid",
        },
    ],
)
def test_tavily_backend_rejects_invalid_response(
    response,
):
    fake_tool = FakeSearchTool(
        response
    )

    backend = create_tavily_search_backend(
        tool_factory=lambda **kwargs:
            fake_tool
    )

    with pytest.raises(
        ValueError,
        match="invalid",
    ):
        backend(
            "LangChain"
        )
        
def test_tavily_backend_rejects_invalid_result():
    fake_tool = FakeSearchTool(
        {
            "results": [
                "invalid result"
            ]
        }
    )

    backend = create_tavily_search_backend(
        tool_factory=lambda **kwargs:
            fake_tool
    )

    with pytest.raises(
        ValueError,
        match="invalid result",
    ):
        backend(
            "LangChain"
        )
        
from pydantic import ValidationError


def test_tavily_backend_rejects_missing_title():
    fake_tool = FakeSearchTool(
        {
            "results": [
                {
                    "url":
                        "https://example.com",
                    "content": "hello",
                }
            ]
        }
    )

    backend = create_tavily_search_backend(
        tool_factory=lambda **kwargs:
            fake_tool
    )

    with pytest.raises(
        ValidationError
    ):
        backend(
            "LangChain"
        )
        
@pytest.mark.parametrize(
    "max_results",
    [
        0,
        -1,
        11,
    ],
)
def test_tavily_backend_rejects_invalid_max_results(
    max_results,
):
    with pytest.raises(
        ValueError,
        match="between 1 and 10",
    ):
        create_tavily_search_backend(
            max_results=max_results,
            tool_factory=lambda **kwargs:
                FakeSearchTool(
                    {
                        "results": [],
                    }
                ),
        )