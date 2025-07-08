"""
This module initializes a collection of pre-built tools from LangChain and LangChain Community.

The purpose of this file is to provide a centralized place to configure and instantiate
various tools that can be used by LangGraph agents. Each tool is set up with sensible
defaults and is ready to be imported and used in different parts of the application.

To add a new tool:
1. Import the tool from the appropriate `langchain_community.tools` module.
2. Instantiate it with the desired configuration.
3. Add the new tool instance to the `all_tools` list.
4. (Optional) Add a demonstration of its usage in the `if __name__ == "__main__":` block.

Note on API Keys:
Some tools require API keys to be set as environment variables (e.g., TAVILY_API_KEY).
Make sure these are configured in your environment before using the tools.
"""

import os
import wikipedia as _wikipedia_pkg  # type: ignore
import arxiv as _arxiv_pkg  # type: ignore

from langchain_community.tools import (
    TavilySearchResults,
    ShellTool,
    DuckDuckGoSearchRun,
    ArxivQueryRun,
    WikipediaQueryRun,
)
from langchain_community.utilities import (
    ArxivAPIWrapper, 
    WikipediaAPIWrapper
)

# --- Tool Configuration ---

# 1. Tavily Search Tool
# An advanced search tool that uses the Tavily API for in-depth web searches.
# Requires TAVILY_API_KEY environment variable.
tavily_search = TavilySearchResults(
    name="tavily_search",
    search_depth="advanced",
    max_results=3,
    description="A powerful search engine for finding up-to-date information on the web."
)

# 2. DuckDuckGo Search Tool
# A simple and effective search tool that does not require an API key.
ddgo_search = DuckDuckGoSearchRun(
    name="duckduckgo_search",
    description="A standard search engine for quick web searches."
)

# 3. Local Shell Tool
# A tool that allows executing shell commands. Use with caution.
local_shell = ShellTool(
    name="local_shell",
    description="Executes shell commands on the local machine. Use with caution."
)


# 4. Wikipedia Search Tool
# A tool for querying Wikipedia.
wikipedia_api = WikipediaAPIWrapper(wiki_client=_wikipedia_pkg)
wikipedia = WikipediaQueryRun(
    name="wikipedia_search",
    api_wrapper=wikipedia_api,
    description="A tool to search for information on Wikipedia."
)


# 5. Arxiv Search Tool
# A tool for searching for scientific papers on ArXiv.
arxiv_api = ArxivAPIWrapper(
    arxiv_search=_arxiv_pkg.Search,
    arxiv_exceptions=(
        _arxiv_pkg.ArxivError,
        _arxiv_pkg.UnexpectedEmptyPageError,
        _arxiv_pkg.HTTPError,
    ),
)
arxiv = ArxivQueryRun(
    name="arxiv_search",
    api_wrapper=arxiv_api,
    description="A tool to search for scientific papers on ArXiv."
)


# --- Tool Collection ---

# A list containing all the instantiated tools.
# This list can be imported and used by the agent factory or graph builder.
all_tools = [
    tavily_search,
    ddgo_search,
    local_shell,
    wikipedia,
    arxiv,
]


# --- Tool Demonstrations ---

def demonstrate_tools():
    """Runs a series of demonstrations for the configured tools."""
    print("--- Demonstrating Built-in Tools ---\n")

    # Tavily Search
    print("1. Tavily Search")
    if os.getenv("TAVILY_API_KEY"):
        try:
            result = tavily_search.invoke("What are the latest developments in AI?")
            print(f"   Result: {result[:200]}...\n")
        except Exception as e:
            print(f"   Error invoking Tavily Search: {e}\n")
    else:
        print("   Skipping Tavily Search: TAVILY_API_KEY not set.\n")

    # DuckDuckGo Search
    print("2. DuckDuckGo Search")
    try:
        result = ddgo_search.invoke("Python programming language")
        print(f"   Result: {result}\n")
    except Exception as e:
        print(f"   Error invoking DuckDuckGo Search: {e}\n")

    # Local Shell
    print("3. Local Shell")
    try:
        result = local_shell.invoke("ls -l")
        print(f"   Result:\n{result}\n")
    except Exception as e:
        print(f"   Error invoking Local Shell: {e}\n")

    # Wikipedia Search
    print("4. Wikipedia Search")
    try:
        result = wikipedia.invoke("LangChain")
        print(f"   Result: {result[:200]}...\n")
    except Exception as e:
        print(f"   Error invoking Wikipedia Search: {e}\n")

    # Arxiv Search
    print("5. Arxiv Search")
    try:
        result = arxiv.invoke("attention is all you need")
        print(f"   Result: {result[:200]}...\n")
    except Exception as e:
        print(f"   Error invoking Arxiv Search: {e}\n")


if __name__ == "__main__":
    demonstrate_tools()
