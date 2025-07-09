import os
import enum
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 搜索引擎配置
class SearchEngine(enum.Enum):
    """搜索引擎枚举"""
    TAVILY = "tavily"
    DUCKDUCKGO = "duckduckgo"
    BRAVE_SEARCH = "brave_search"
    ARXIV = "arxiv"

class CrawlerEngine(enum.Enum):
    """爬虫类型枚举"""
    TAVILY = "tavily"
    REQUESTS = "requests"
    CUSTOM = "custom"
    


SELECTED_SEARCH_ENGINE=os.getenv("SEARCH_DEFAULT_TYPE", SearchEngine.TAVILY.value)
SELECTED_CRAWLER_ENGINE=os.getenv("CRAWLER_DEFAULT_TYPE", CrawlerEngine.TAVILY.value)


class RAGProvider(enum.Enum):
    RAGFLOW = "ragflow"

SELECTED_RAG_PROVIDER = os.getenv("RAG_PROVIDER", RAGProvider.RAGFLOW.value)
