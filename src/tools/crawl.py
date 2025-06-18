import os
from typing import Type, Optional, Any
from langchain_core.tools import BaseTool, Tool, ArgsSchema
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from pydantic.v1.types import NoneBytes

from src.tools.crawler import TavilyCrawler, WebBaseCrawler, CrawlResult
from src.tools.crawler.base import BaseCrawler # Assuming a base class for crawlers
from src.config.tools_config import CrawlerEngine, SELECTED_CRAWLER_ENGINE

# --- Crawler Input Schema ---
class CrawlerInput(BaseModel):
    url: str = Field(description="The URL of the web page to crawl.")

# --- Crawler Engine Factory ---
class CrawlerEngineFactory:
    @staticmethod
    def get_crawler(engine_type: CrawlerEngine = CrawlerEngine(SELECTED_CRAWLER_ENGINE)) -> BaseCrawler:
        """Creates and returns a crawler instance based on the specified engine type."""
        if engine_type == CrawlerEngine.TAVILY:
            # Assuming TavilyCrawler might take config or be singleton
            return TavilyCrawler()
        elif engine_type == CrawlerEngine.REQUESTS:
            # Assuming WebBaseCrawler is the one using requests
            return WebBaseCrawler()
        # elif engine_type == CrawlerEngine.CUSTOM:
        #     # Placeholder for a custom crawler implementation
        #     raise NotImplementedError("Custom crawler not yet implemented.")
        else:
            raise ValueError(f"Unsupported crawler engine: {engine_type}")

# --- LangGraph Compatible Crawler Tool ---
class CrawlerTool(BaseTool):
    name: str = "web_crawler"
    description: str = "Crawls a given URL to extract its content. Uses the configured default crawler engine."
    args_schema: ArgsSchema | None = CrawlerInput

    def _run(
        self, url: str, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any
    ) -> str:
        """Use the tool to crawl a webpage."""
        try:
            crawler = CrawlerEngineFactory.get_crawler()
            result: CrawlResult = crawler.crawl(url)

            if result.is_success:
                return f"Successfully crawled {url}. Results:\n {result}."
            else:
                error_message = result.error or f"Failed to crawl {url} with status code {result.status_code}."
                # Log the error if a logger is available
                # logger.error(error_message)
                return f"Error crawling {url}: {error_message}"
        except Exception as e:
            # logger.error(f"Exception in CrawlerTool: {e}", exc_info=True)
            return f"An unexpected error occurred while crawling {url}: {str(e)}"

    async def _arun(
        self, url: str, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any
    ) -> str:
        """Use the tool asynchronously to crawl a webpage."""
        # This is a simplified async version. Proper async crawling would require
        # the underlying crawlers (TavilyCrawler, WebBaseCrawler) to support async operations.
        # For now, we can run the synchronous version in a thread pool executor if needed,
        # or implement true async if the crawlers support it.
        # If Tavily/WebBaseCrawler don't have async methods, this will block.
        try:
            crawler = CrawlerEngineFactory.get_crawler()
            # Assuming crawler.acrawl exists or we adapt _run
            # For simplicity, calling _run here. For true async, crawler.acrawl would be needed.
            # result: CrawlResult = await crawler.acrawl(url) # If acrawl exists
            
            # Simulating async call for now by wrapping sync call
            # In a real scenario, use asyncio.to_thread or ensure crawlers are async
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError: # 'get_running_loop' fails if no loop is running
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            result: CrawlResult = await loop.run_in_executor(None, crawler.crawl, url)

            if result.is_success:
                return f"Successfully crawled {url}. Results:\n {result}."
            else:
                error_message = result.error or f"Failed to crawl {url} with status code {result.status_code}."
                return f"Error crawling {url}: {error_message}"
        except Exception as e:
            return f"An unexpected error occurred while crawling {url}: {str(e)}"

# Example of how to potentially expose it as a Langchain Tool object
# if not directly using the CrawlerTool class in LangGraph
web_crawler_tool = Tool(
    name="web_crawler_tool",
    func=CrawlerTool().run, # Or a wrapper if needed
    description="Crawls a web page and returns its content. Input should be a URL.",
    args_schema=CrawlerInput
)

if __name__ == '__main__':
    # Example Usage (requires TAVILY_API_KEY or appropriate setup for WebBaseCrawler)
    test_url = "https://javaguide.cn/javaguide/intro.html"
    
    # Test with default engine
    tool_instance = CrawlerTool()
    print(f"--- Testing with default crawler ({SELECTED_CRAWLER_ENGINE}) ---")
    output = tool_instance.run(tool_input={"url": test_url})
    print(output)

    # Example of testing with a specific engine if factory/tool supports it
    # print("\n--- Testing with Tavily explicitly ---")
    # tavily_crawler = CrawlerEngineFactory.get_crawler(CrawlerEngine.TAVILY)
    # result_tavily = tavily_crawler.crawl(test_url)
    # print(result_tavily.to_dict() if result_tavily else "Failed")

    # print("\n--- Testing with Requests (WebBaseCrawler) explicitly ---")
    # requests_crawler = CrawlerEngineFactory.get_crawler(CrawlerEngine.REQUESTS)
    # result_requests = requests_crawler.crawl(test_url)
    # print(result_requests.to_dict() if result_requests else "Failed")

    # Async test
    async def main_async():
        print("\n--- Async Test ---")
        output_async = await tool_instance.arun(tool_input={"url": test_url})
        print(output_async)

    import asyncio
    if os.getenv("TAVILY_API_KEY"): # Only run async if Tavily might work
        asyncio.run(main_async())
    else:
        print("\nSkipping async test as TAVILY_API_KEY is not set (Tavily is default crawler).")
   