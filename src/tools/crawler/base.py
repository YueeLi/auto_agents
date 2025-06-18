from abc import ABC, abstractmethod
from typing import Any, Coroutine

from src.tools.crawler.crawl_result import CrawlResult

class BaseCrawler(ABC):
    """Abstract base class for web crawlers."""

    @abstractmethod
    def crawl(self, url: str, **kwargs: Any) -> CrawlResult:
        """Synchronously crawls the given URL and returns the content.

        Args:
            url: The URL to crawl.
            **kwargs: Additional keyword arguments for the specific crawler implementation.

        Returns:
            A CrawlResult object containing the outcome of the crawl.
        """
        pass

    @abstractmethod
    async def acrawl(self, url: str, **kwargs: Any) -> CrawlResult:
        """Asynchronously crawls the given URL and returns the content.

        Args:
            url: The URL to crawl.
            **kwargs: Additional keyword arguments for the specific crawler implementation.

        Returns:
            A CrawlResult object containing the outcome of the crawl.
        """
        pass

    def cleanup(self) -> None:
        """Optional method to clean up resources used by the crawler (e.g., close sessions)."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False # Do not suppress exceptions