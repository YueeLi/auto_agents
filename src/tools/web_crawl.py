"""Web Crawling Tool using Tavily.

This module provides a web crawling tool using the Tavily API for advanced, AI-powered content extraction.
The tool is decorated with `@tool` to be directly usable by a LangGraph agent.
It is designed to be simple, stateless, and synchronous.
"""

import os
import logging
import json
from typing import Dict, Any

from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_tavily import TavilyExtract

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
        
        # Return a dictionary as a JSON string for better structure
        crawl_result = {
            "url": url,
            "content": content,
            "status_code": 200,
            "error": None
        }
        return json.dumps(crawl_result, indent=2)

    except (ConfigurationError, ContentExtractionError, WebCrawlError) as e:
        logger.error(f"Tavily crawl failed for {url}: {e}")
        error_result = {"url": url, "content": "", "error": str(e)}
        return json.dumps(error_result, indent=2)
    except Exception as e:
        logger.exception(f"An unexpected error occurred during Tavily crawl for {url}: {e}")
        error_result = {"url": url, "content": "", "error": f"An unexpected error occurred: {e}"} 
        return json.dumps(error_result, indent=2)


if __name__ == "__main__":
    # Example usage:
    # Make sure to set the TAVILY_API_KEY environment variable before running.
    # export TAVILY_API_KEY="your_tavily_api_key"
    
    test_url = "https://www.tavily.com/"
    print("****** tavily_web_crawl ******")
    result_json = tavily_web_crawl.invoke({"url": test_url})
    print(json.dumps(json.loads(result_json), indent=4))
