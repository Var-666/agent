import json
from collections.abc import Callable
from typing import Any

from langchain.tools import tool
from langchain_core.tools import BaseTool
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field

DEFAULT_SEARCH_RESULTS = 5
MAX_SEARCH_RESULTS = 10

class WebSearchResult(BaseModel):
  title: str = Field(min_length=1)
  url: str = Field(min_length=1)
  snippet: str
  
SearchBackend = Callable[[str],tuple[WebSearchResult,...]]

SearchToolFactory = Callable[...,BaseTool]

def create_search_web_tool(backend: SearchBackend) -> BaseTool:
  
  @tool("search_web")
  def search_web(query: str) -> str:
    """Search the public web and return ranked results."""
    
    normalized_query = query.strip()
    
    if not normalized_query:
      raise ValueError("Search query cannot be empty")
    
    results = backend(normalized_query)
    
    return json.dumps([
      result.model_dump()
      for result in results
    ])
    
  return search_web

def create_tavily_search_backend(
  *,
  max_results: int = DEFAULT_SEARCH_RESULTS,
  tool_factory: SearchToolFactory = TavilySearch
) -> SearchBackend:
  
  if not 1 <= max_results <= MAX_SEARCH_RESULTS:
    raise ValueError("max_results must be between 1 and 10")
  
  search_tool = tool_factory(
    max_results=max_results,
    topic="general",
    search_depth="basic",
    include_answer=False,
    include_raw_content=False,
    include_images=False
  )
  
  def search(query: str) -> tuple[WebSearchResult,...]:
    
    response = search_tool.invoke({"query":query})
    
    if not isinstance(response,dict):
      raise ValueError("Search provider returned an invalid response")

    raw_result = response.get("results")
    
    if not isinstance(raw_result,list):
      raise ValueError("Search provider returned invalid results")
    
    results: list[WebSearchResult] = []
    
    for item in raw_result:
      if not isinstance(item,dict):
        raise ValueError("Search provider returned an invalid result")
      
      results.append(
        WebSearchResult(
          title=str(item.get("title","")).strip(),
          url=str(item.get("url","")).strip(),
          snippet=str(item.get("content", "")).strip()
        )
      )
    
    return tuple(results)
  
  return search
  
  
  