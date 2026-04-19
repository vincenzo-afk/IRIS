"""
IRIS — Web Tools
=================
Web search and scraping tools to provide real-time knowledge.
"""

import logging

logger = logging.getLogger(__name__)

def web_search(query: str, max_results: int = 5) -> str:
    """Perform a web search using DuckDuckGo."""
    logger.info(f"Searching web for: {query}")
    try:
        from duckduckgo_search import DDGS
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        
        output = []
        for i, res in enumerate(results):
            output.append(f"{i+1}. {res.get('title')}\n   URL: {res.get('href')}\n   Snippet: {res.get('body')}")
        return "\n\n".join(output)
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"Error performing web search: {e}"

def scrape_url(url: str) -> str:
    """Fetch text content from a specific URL."""
    logger.info(f"Scraping URL: {url}")
    try:
        import requests
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        # return first 2000 chars to avoid overwhelming the model
        return text[:2000] + ("..." if len(text) > 2000 else "")
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return f"Failed to retrieve URL content: {e}"
