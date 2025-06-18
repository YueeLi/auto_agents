"""LangChain Web爬虫实现"""

import logging
from typing import Dict, Any, Optional, cast
from urllib.parse import urlparse

from langchain_community.document_loaders import WebBaseLoader
import requests
from requests.exceptions import RequestException

from src.tools.crawler.crawl_result import CrawlResult
from src.tools.crawler.crawl_errors import ContentExtractionError

logger = logging.getLogger(__name__)

from src.tools.crawler.base import BaseCrawler

class WebBaseCrawler(BaseCrawler):
    """基于LangChain的Web爬虫实现"""
    
    def __init__(self):
        """初始化爬虫实例"""
        self.session = requests.Session()
        # 添加更全面的浏览器请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })
       
    def cleanup(self):
        """清理资源"""
        self.session.close()

    def validate_url(self, url: str) -> bool:
        """验证URL是否合法且可爬取"""
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False

    def _get_status_code(self, url: str) -> int:
        """获取URL的HTTP状态码"""
        try:
            response = self.session.head(url, allow_redirects=True)
            return response.status_code
        except RequestException:
            return 500

    def crawl(self, url: str, **kwargs) -> CrawlResult:
        """爬取实现"""
        if not self.validate_url(url):
            return CrawlResult(
                url=url,
                content='',
                status_code=400,
                headers={},
                error="Invalid URL"
            )

        # 对于 CSDN，添加 cookie 和 referer
        if 'csdn.net' in url:
            self.session.headers.update({
                'Referer': 'https://blog.csdn.net/',
                'Cookie': 'uuid_tt_dd=1_0; dc_session_id=1_1',
            })

        try:
            # 直接使用 requests 获取内容
            response = self.session.get(
                url,
                timeout=30,
                verify=not kwargs.get('ignore_ssl', False),
                proxies=kwargs.get('proxy', None),
                allow_redirects=True
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding  # 自动检测编码
            content = response.text

            if not content.strip():
                loader = WebBaseLoader(
                    web_paths=[url],
                    verify_ssl=not kwargs.get('ignore_ssl', False),
                    requests_kwargs={
                        'timeout': 30,
                        'headers': self.session.headers,
                        'proxies': kwargs.get('proxy', None),
                        'allow_redirects': True,
                        'verify': not kwargs.get('ignore_ssl', False)
                    }
                )
                
                docs = loader.load()
                if not docs or not docs[0].page_content.strip():
                    raise ContentExtractionError("No content extracted")
                content = docs[0].page_content
                
            return CrawlResult(
                url=url,
                content=content,
                status_code=response.status_code,
                headers=cast(Dict[str, str], dict(response.headers)),
                metadata={'source': url}
            )

        except Exception as e:
            logger.warning(f"Failed to crawl {url}: {e}")
            return CrawlResult(
                url=url,
                content='',
                status_code=500,
                headers={},
                error=str(e)
            )

    async def acrawl(self, url: str, **kwargs: Any) -> CrawlResult:
        """Asynchronously crawls the specified URL using requests and WebBaseLoader.

        Args:
            url: The URL to crawl.
            **kwargs: Additional arguments for the crawl operation (e.g., 'ignore_ssl', 'proxy').

        Returns:
            CrawlResult: The result of the crawl operation.
        """
        if not self.validate_url(url):
            return CrawlResult(
                url=url,
                content='',
                status_code=400,
                headers={},
                error="Invalid URL"
            )

        # For CSDN, update headers (this part is synchronous, consider if it needs async adaptation)
        if 'csdn.net' in url:
            self.session.headers.update({
                'Referer': 'https://blog.csdn.net/',
                'Cookie': 'uuid_tt_dd=1_0; dc_session_id=1_1',
            })
        
        import asyncio
        loop = asyncio.get_event_loop()

        try:
            # Asynchronously perform the GET request
            # requests.Session.get is synchronous. We need an async HTTP client like aiohttp
            # or run the sync call in a thread pool executor.
            # For simplicity, using run_in_executor here.
            
            session_params = {
                'url': url,
                'timeout': 30,
                'verify': not kwargs.get('ignore_ssl', False),
                'proxies': kwargs.get('proxy', None),
                'allow_redirects': True
            }
            response = await loop.run_in_executor(None, lambda: self.session.get(**session_params))
            
            response.raise_for_status()
            # Encoding detection might also be blocking if response.content is large
            response.encoding = response.apparent_encoding 
            content = response.text

            if not content.strip():
                # WebBaseLoader.load is synchronous.
                loader_kwargs = {
                    'web_paths': [url],
                    'verify_ssl': not kwargs.get('ignore_ssl', False),
                    'requests_kwargs': {
                        'timeout': 30,
                        'headers': self.session.headers,
                        'proxies': kwargs.get('proxy', None),
                        'allow_redirects': True,
                        'verify': not kwargs.get('ignore_ssl', False)
                    }
                }
                loader = WebBaseLoader(**loader_kwargs)
                # Run loader.load() in an executor
                docs = await loop.run_in_executor(None, loader.load)
                if not docs or not docs[0].page_content.strip():
                    raise ContentExtractionError("No content extracted by WebBaseLoader async")
                content = docs[0].page_content
                
            return CrawlResult(
                url=url,
                content=content,
                status_code=response.status_code,
                headers=cast(Dict[str, str], dict(response.headers)),
                metadata={'source': url, 'method': 'async'}
            )

        except Exception as e:
            logger.warning(f"Failed to crawl {url} asynchronously: {e}")
            return CrawlResult(
                url=url,
                content='',
                status_code=500, # Or a more specific error code if available
                headers={},
                error=str(e)
            )

if __name__ == "__main__":
    async def test_async_webbase_crawl():
        print("\n--- WebBaseCrawler Async Test ---")
        crawler_async = WebBaseCrawler()
        # test_url_async = "https://blog.csdn.net/b0Q8cpra539haFS7/article/details/89369381"
        test_url_async = "https://www.example.com"
        result_async = await crawler_async.acrawl(test_url_async)
        print(f"Async Crawl Result for {test_url_async}: Success: {result_async.is_success}, Status: {result_async.status_code}, Content Length: {len(result_async.content)}, Error: {result_async.error}")
        crawler_async.cleanup()

    # 示例用法
    crawler = WebBaseCrawler()
    result = crawler.crawl("https://blog.csdn.net/b0Q8cpra539haFS7/article/details/89369381")
    print(f"URL: {result.url}, Status: {result.status_code}, Content Length: {len(result.content)}")
    crawler.cleanup()

    # Run the async test
    import asyncio
    asyncio.run(test_async_webbase_crawl())