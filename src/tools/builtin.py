from langchain_community.tools import (
    JinaSearch,
    TavilySearchResults,
    ShellTool,
    VectorStoreQATool,
    VectorStoreQAWithSourcesTool,
    RedditSearchRun,
)

def create_tavily_search_tool(**kwargs):
    """Creates a Tavily search tool instance."""
    defaults = {
        "search_depth": "advanced",
        "max_results": 5,
        "time_range": "month",
        "include_images": True,
        "include_image_descriptions": True,
        "include_raw_content": "markdown",
        "country": "united states",
    }
    defaults.update(kwargs)
    return TavilySearchResults(**defaults)

def create_jina_search_tool(**kwargs):
    """Creates a Jina search tool instance."""
    return JinaSearch(**kwargs)

def create_local_shell_tool(**kwargs):
    """Creates a Shell tool instance."""
    return ShellTool(**kwargs)



if __name__ == "__main__":
    tavily_tool = create_tavily_search_tool()
    # result = tavily_tool.invoke("伊朗形势")
    # print(result)

    jina_tool = create_jina_search_tool()
    # result = jina_tool.invoke("中国阅兵")
    # print(result)

    shell_tool = create_local_shell_tool()
    result = shell_tool.invoke("ls -l")
    print(result)