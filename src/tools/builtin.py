from langchain_community.tools import (
    JinaSearch,
    TavilySearchResults,
    ShellTool,
    VectorStoreQATool,
    VectorStoreQAWithSourcesTool,
    RedditSearchRun,
)

tavily_search = TavilySearchResults(
    search_depth="advanced",
    max_results=3,
    time_range="week",
    include_images=False,
    include_raw_content=True,
    country="united states",
)

jina_search = JinaSearch()

local_shell = ShellTool()




if __name__ == "__main__":
    # result = tavily_search.invoke("伊朗形势")
    # print(result)

    # result = jina_search.invoke("中国阅兵")
    # print(result)

    result = local_shell.invoke("ls -l")
    print(result)