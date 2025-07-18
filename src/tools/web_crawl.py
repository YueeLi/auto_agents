"""Web Crawling Tools.

This module provides multiple web crawling tools:
1. Tavily API for advanced, AI-powered content extraction.
2. Playwright for direct browser-based content extraction.
"""

import os
import json
import logging
from pydantic import BaseModel, Field
import trafilatura
from langchain_core.tools import tool
from langchain_tavily import TavilyExtract
from langchain_community.tools.playwright.utils import create_sync_playwright_browser

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

class ContentExtractionError(WebCrawlError):
    """Error during the content extraction phase."""
    pass

# --- Input Schema ---
class WebCrawlInput(BaseModel):
    """Input for both Tavily and Playwright web crawl tools."""
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
        raise WebCrawlError(f"Failed to initialize Tavily client: {e}")

@tool("tavily_web_crawl", args_schema=WebCrawlInput)
def tavily_web_crawl(url: str) -> str:
    """Performs a web crawl and content extraction for a given URL using the Tavily API.

    This tool is ideal for extracting structured content from web pages when high-quality, AI-driven extraction is needed.
    It requires the TAVILY_API_KEY environment variable to be set.
    """
    logger.info(f"Executing Tavily web crawl for URL: {url}")
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
        
        crawl_result = {
            "url": url,
            "content": content,
            "status_code": 200,
            "error": None
        }
        return json.dumps(crawl_result, indent=2)

    except (ConfigurationError, ContentExtractionError, WebCrawlError) as e:
        logger.error(f"Tavily crawl failed for {url}: {e}")
        error_result = {"url": url, "content": "", "status_code": 500, "error": str(e)}
        return json.dumps(error_result, indent=2)
    except Exception as e:
        logger.exception(f"An unexpected error occurred during Tavily crawl for {url}: {e}")
        error_result = {"url": url, "content": "", "status_code": 500, "error": f"An unexpected error occurred: {e}"} 
        return json.dumps(error_result, indent=2)

def _html_to_markdown(html_content: str) -> str:
    """Converts HTML content to Markdown format using trafilatura for a more generic solution.

    Args:
        html_content: The HTML content to convert.

    Returns:
        The converted Markdown content.
    """
    # Use trafilatura to extract the main content and convert it to Markdown
    markdown_content = trafilatura.extract(
        html_content,
        output_format='markdown',
        include_comments=False,  # Don't include comments
        include_tables=True,  # Include tables
        favor_precision=True  # Favor precision over recall
    )

    if not markdown_content:
        return "No main content found."

    return markdown_content

@tool("playwright_web_crawl", args_schema=WebCrawlInput)
def playwright_web_crawl(url: str) -> str:
    """Performs a web crawl and extracts text content from a given URL using Playwright.

    This tool is useful for rendering JavaScript-heavy pages to get the full content.
    It requires the `playwright` and `beautifulsoup4` packages.
    """
    logger.info(f"Executing Playwright web crawl for URL: {url}")
    browser = None
    try:
        browser = create_sync_playwright_browser()
        page = browser.new_page()

        # Add anti-scraping measures
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        })

        response = page.goto(url, timeout=60000, wait_until="networkidle")
        status_code = response.status if response else 0
        html_content = page.content()
        content = _html_to_markdown(html_content)

        if not content:
            raise ContentExtractionError("Empty content extracted from Playwright.")

        logger.info(f"Successfully crawled {url} with Playwright. Content length: {len(content)}")
        crawl_result = {
            "url": url,
            "content": content,
            "status_code": status_code,
            "error": None
        }
        return json.dumps(crawl_result, indent=2)

    except Exception as e:
        logger.error(f"Playwright crawl failed for {url}: {e}")
        error_result = {"url": url, "content": "", "status_code": 500, "error": str(e)}
        return json.dumps(error_result, indent=2)
    finally:
        if browser:
            browser.close()


if __name__ == "__main__":
    # # Example usage for Tavily:
    # print("****** tavily_web_crawl ******")
    # tavily_test_url = "https://changelog.langchain.com/?categories=cat_5UBL6DD8PcXXL"
    # result_json = tavily_web_crawl.invoke({"url": tavily_test_url})
    # print(json.dumps(json.loads(result_json), indent=4, ensure_ascii=False))
    
    # Example usage for Playwright:
    print("\n****** playwright_web_crawl ******")
    playwright_test_url = "https://mp.weixin.qq.com/s/SnvovJF-Hs3L15XeQRSG7A"
    result_json = playwright_web_crawl.invoke({"url": playwright_test_url})
    print(json.dumps(json.loads(result_json), indent=4, ensure_ascii=False))
