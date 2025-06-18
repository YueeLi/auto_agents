import os
import sys
from pathlib import Path
import json
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool, ArgsSchema
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from langchain_tavily import TavilySearch
from langchain_community.tools import BraveSearch, DuckDuckGoSearchRun, ArxivQueryRun, Tool
from langchain_community.utilities.arxiv import ArxivAPIWrapper
from src.config.tools_config import SELECTED_SEARCH_ENGINE, SearchEngine

class SearchEngineFactory:
    """搜索引擎工厂类,使用单例模式管理搜索引擎实例"""
    
    _instances: Dict[str, Any] = {}
    
    @classmethod
    def get_search_engine(cls, engine_type: str) -> Any:
        """
        获取指定类型的搜索引擎实例
        
        :param engine_type: 搜索引擎类型
        :return: 搜索引擎实例
        """
        if engine_type not in cls._instances:
            if engine_type == SearchEngine.TAVILY.value:
                api_key = os.getenv("TAVILY_API_KEY")
                if not api_key:
                    raise ValueError("TAVILY_API_KEY is not set in the environment variables.")
                cls._instances[engine_type] = TavilySearch(
                    tavily_api_key=api_key,
                    include_images=False,
                    max_results=3,
                    language="en",
                    region="us"
                )
                
            elif engine_type == SearchEngine.DUCKDUCKGO.value:
                cls._instances[engine_type] = DuckDuckGoSearchRun()
                
            elif engine_type == SearchEngine.BRAVE_SEARCH.value:
                cls._instances[engine_type] = BraveSearch()

            elif engine_type == SearchEngine.ARXIV.value:
                cls._instances[engine_type] = ArxivQueryRun(api_wrapper=ArxivAPIWrapper(
                    arxiv_search=Any,
                    arxiv_exceptions=Any,
                    top_k_results=3,
                    ARXIV_MAX_QUERY_LENGTH=300,
                    continue_on_failure=False,
                    load_max_docs=100,
                    load_all_available_meta=False,
                    doc_content_chars_max=40000
                )) # Using ArxivQueryRun for direct search execution
                
            else:
                raise ValueError(f"Unsupported search engine: {engine_type}")
                
        return cls._instances[engine_type]


# --- Search Input Schema ---
class SearchInput(BaseModel):
    query: str = Field(description="The search query.")
    # engine: Optional[SearchEngine] = Field(default=None, description="Specify the search engine to use.")
    # num_results: Optional[int] = Field(default=3, description="Number of search results to return.")

# --- LangGraph Compatible Search Tool ---
class SearchTool(BaseTool):
    name: str = "web_search_tool"
    description: str = (
        "Performs a web search using the configured default search engine. "
        "Input should be a search query. "
        "Returns a list of search results, typically including snippets, titles, and links."
    )
    args_schema: ArgsSchema | None = SearchInput

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any
    ) -> str: # Langchain tools typically return string or list of Documents/strings
        """Use the tool to perform a web search."""
        try:
            # engine_type_str = kwargs.get("engine", SELECTED_SEARCH_ENGINE)
            # engine_type = SearchEngine(engine_type_str) # Ensure it's an enum member
            search_engine_instance = SearchEngineFactory.get_search_engine(SELECTED_SEARCH_ENGINE)
            
            # Some search tools might take num_results, others have it in constructor
            # For Tavily, max_results is in constructor. For others, it might be an invoke param.
            # Adjust this based on how each search_engine_instance.invoke works.
            # num_results = kwargs.get("num_results", 3) 

            # The .invoke() method for most Langchain search tools returns a string (often JSON string) or List[Document]
            # The output type might need to be standardized or handled based on the engine.
            results = search_engine_instance.invoke(query)
            
            # Ensure results are in a string format for LangGraph if it expects strings.
            if isinstance(results, list): # Tavily returns a list of dicts
                return json.dumps(results, ensure_ascii=False)
            elif isinstance(results, dict):
                 return json.dumps(results, ensure_ascii=False)
            elif isinstance(results, str):
                return results
            else:
                return str(results) # Fallback

        except Exception as e:
            # logger.error(f"Exception in SearchTool: {e}", exc_info=True)
            return f"An unexpected error occurred during the search: {str(e)}"

    async def _arun(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any
    ) -> str:
        """Use the tool asynchronously to perform a web search."""
        try:
            search_engine_instance = SearchEngineFactory.get_search_engine(SELECTED_SEARCH_ENGINE)
            
            # Check if the specific search engine instance has an async method (e.g., ainvoke)
            if hasattr(search_engine_instance, 'ainvoke'):
                results = await search_engine_instance.ainvoke(query)
            else:
                # Fallback to running the synchronous version in a thread pool executor
                import asyncio
                loop = asyncio.get_running_loop()
                results = await loop.run_in_executor(None, search_engine_instance.invoke, query)
            
            if isinstance(results, list):
                return json.dumps(results, ensure_ascii=False)
            elif isinstance(results, dict):
                 return json.dumps(results, ensure_ascii=False)
            elif isinstance(results, str):
                return results
            else:
                return str(results)

        except Exception as e:
            # logger.error(f"Async Exception in SearchTool: {e}", exc_info=True)
            return f"An unexpected error occurred during the async search: {str(e)}"

# Example of how to potentially expose it as a Langchain Tool object
# if not directly using the SearchTool class in LangGraph
web_search_tool = Tool(
    name="web_search_tool",
    func=SearchTool().run, 
    description="Performs a web search and returns results. Input should be a search query.",
    args_schema=SearchInput,
    coroutine=SearchTool().arun # if you want to expose async version directly
)


if __name__ == "__main__":
    # Example Usage
    test_query = "Latest advancements in AI 2024"
    
    # Test with default engine (sync)
    tool_instance = SearchTool()
    print(f"--- Testing SearchTool with default engine ({SELECTED_SEARCH_ENGINE}) --- SYNC ---")
    sync_results = tool_instance.run(tool_input={"query": test_query})
    print("Sync Search Results:")
    try:
        # Try to parse if it's JSON for pretty printing
        parsed_sync = json.loads(sync_results)
        print(json.dumps(parsed_sync, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(sync_results) # Print as is if not JSON

    # Test with default engine (async)
    async def main_async():
        print(f"\n--- Testing SearchTool with default engine ({SELECTED_SEARCH_ENGINE}) --- ASYNC ---")
        async_results = await tool_instance.arun(tool_input={"query": test_query})
        print("Async Search Results:")
        try:
            parsed_async = json.loads(async_results)
            print(json.dumps(parsed_async, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(async_results)

    import asyncio
    # Run async test only if Tavily API key is present, as it's often the default and requires a key
    # Adjust this condition if your default search engine is different or doesn't need a key.
    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value and not os.getenv("TAVILY_API_KEY"):
        print("\nSkipping async search test: TAVILY_API_KEY is not set and Tavily is the selected engine.")
    elif SELECTED_SEARCH_ENGINE == SearchEngine.BRAVE_SEARCH.value and not os.getenv("BRAVE_API_KEY"):
        print("\nSkipping async search test: BRAVE_API_KEY is not set and Brave is the selected engine.")
    else:
        asyncio.run(main_async())

