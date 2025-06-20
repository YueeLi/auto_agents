"""Web Crawling Tools using Tavily and Requests.

This module provides two distinct, synchronous web crawling tools for use in a LangGraph agent:
- `tavily_web_crawl`: Utilizes the Tavily API for advanced, AI-powered content extraction.
- `requests_web_crawl`: A standard web crawler using the `requests` and `langchain_community.document_loaders.WebBaseLoader`.

Both tools are decorated with `@tool` to be directly usable by a LangGraph agent.
They are designed to be simple, stateless, and synchronous, aligning with best practices for tool creation.
"""

import os
import logging
import json
from dataclasses import field
from typing import Dict, Any, List, Optional, cast

from pydantic import BaseModel, Field
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.tools import tool
from langchain_tavily import TavilyExtract
from pydantic import BaseModel, Field

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Custom Exceptions ---
class WebCrawlError(Exception):
    """Base exception for all web crawling related errors."""
    pass

class ConfigurationError(WebCrawlError):
    """Error related to tool configuration, like missing API keys."""
    pass

class NetworkError(WebCrawlError):
    """Error related to network issues during the crawl."""
    pass

class ContentExtractionError(WebCrawlError):
    """Error during the content extraction phase."""
    pass

# --- Data Structures ---
class CrawlResult(BaseModel):
    """Represents the outcome of a crawl operation."""
    url: str
    content: str
    status_code: Optional[int] = None
    images: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Indicates if the crawl was successful."""
        return self.status_code is not None and 200 <= self.status_code < 300 and bool(self.content) and not self.error

# --- Input Schema ---
class WebCrawlInput(BaseModel):
    url: str = Field(description="The URL of the web page to crawl.")

# --- Tavily Web Crawl Tool ---

def _get_tavily_client() -> TavilyExtract:
    """Initializes and returns a TavilyExtract client."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ConfigurationError("TAVILY_API_KEY environment variable is required.")
    
    user_agent = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        return TavilyExtract(
            tavily_api_key=api_key,
            extract_depth="advanced",
            include_images=True,
            format="markdown",
            user_agent=user_agent
        )
    except Exception as e:
        raise NetworkError(f"Failed to initialize Tavily client: {e}")

@tool("tavily_web_crawl", args_schema=WebCrawlInput)
def tavily_web_crawl(url: str) -> str:
    """Performs a web crawl and content extraction for a given URL using the Tavily API.

    This tool is ideal for extracting structured content from web pages when high-quality, AI-driven extraction is needed.
    It requires the TAVILY_API_KEY environment variable to be set.
    """
    logger.info(f"Executing Tavily web crawl for URL: {url}")
    result = CrawlResult(url=url, content="")
    try:
        client = _get_tavily_client()
        raw_results = client.invoke({"urls": [url]})
        
        results = raw_results.get("results", [])
        if not results:
            failed_results = raw_results.get("failed_results", [])
            error_details = failed_results[0].get("error", "Unknown error") if failed_results else "No content extracted"
            raise ContentExtractionError(f"Extraction failed: {error_details}")

        first_result = results[0]
        content = first_result.get("raw_content", "").strip()
        if not content:
            raise ContentExtractionError("Empty content extracted from Tavily.")

        logger.info(f"Successfully crawled {url} with Tavily. Content length: {len(content)}")
        result.content = content
        result.status_code = 200  # Assuming 200 for successful Tavily extraction
        return result.model_dump_json()

    except (ConfigurationError, NetworkError, ContentExtractionError) as e:
        logger.error(f"Tavily crawl failed for {url}: {e}")
        result.error = str(e)
        return result.model_dump_json()
    except Exception as e:
        logger.exception(f"An unexpected error occurred during Tavily crawl for {url}: {e}")
        result.error = f"An unexpected error occurred: {e}"
        return result.model_dump_json()

# --- Requests-based Web Crawl Tool ---

def _create_requests_session() -> requests.Session:
    """Creates a requests session with standard browser headers."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    })
    return session

@tool("requests_web_crawl", args_schema=WebCrawlInput)
def requests_web_crawl(url: str) -> str:
    """Crawls a web page using a standard HTTP GET request and extracts content.

    This tool is suitable for general-purpose crawling. It first tries a direct `requests.get()`
    and falls back to `WebBaseLoader` if the initial content is empty.
    """
    logger.info(f"Executing requests-based web crawl for URL: {url}")
    result = CrawlResult(url=url, content="")

    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme in ('http', 'https'), parsed_url.netloc]):
            raise WebCrawlError(f"Invalid URL provided: {url}")
    except Exception:
        result.error = f"Invalid URL format for {url}."
        return result.model_dump_json()

    with _create_requests_session() as session:
        try:
            response = session.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            content = response.text

            result.status_code = response.status_code


            if not content.strip():
                logger.info(f"Initial request for {url} returned empty content, trying WebBaseLoader.")
                loader = WebBaseLoader(
                    web_paths=[url],
                    requests_kwargs={'headers': session.headers, 'timeout': 30}
                )
                docs = loader.load()
                if not docs or not docs[0].page_content.strip():
                    raise ContentExtractionError("No content extracted by WebBaseLoader.")
                content = docs[0].page_content

            result.content = content
            logger.info(f"Successfully crawled {url} with Requests. Content length: {len(content)}")
            return result.model_dump_json()

        except RequestException as e:
            logger.error(f"Network error crawling {url} with Requests: {e}")
            result.error = f"A network error occurred: {e}"
            if e.response is not None:
                result.status_code = e.response.status_code
            return result.model_dump_json()
        except ContentExtractionError as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            result.error = f"Failed to extract content: {e}"
            return result.model_dump_json()
        except Exception as e:
            logger.exception(f"An unexpected error occurred during Requests crawl for {url}: {e}")
            result.error = f"An unexpected error occurred: {e}"
            return result.model_dump_json()


if __name__ == "__main__":
    url = "https://deepwiki.com/private-repo"
    print("******tavily_web_crawl******")
    print(tavily_web_crawl.invoke({"url": url}))
    print("******requests_web_crawl******")
    print(requests_web_crawl.invoke({"url": url}))
