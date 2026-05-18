import sys

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

def perform_web_search(query: str, max_results: int = 4) -> list:
    """
    Performs a live web search using DuckDuckGo.
    Returns a list of dictionaries with keys: 'title', 'href', 'body'.
    """
    if DDGS is None:
        print("Warning: Neither 'ddgs' nor 'duckduckgo_search' is installed. Run `pip install -U ddgs`.")
        return []
    
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            if results:
                return [
                    {
                        "title": r.get("title", ""),
                        "href": r.get("href", r.get("link", "")),
                        "body": r.get("body", r.get("snippet", ""))
                    }
                    for r in results
                ]
    except Exception as e:
        print(f"Error during DuckDuckGo search: {e}")
    return []

def format_web_search_context(results: list) -> str:
    """
    Formats the search results into a clean text block to inject as context into the RAG pipeline.
    """
    if not results:
        return "No web search results found."
    
    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(
            f"[{i}] Title: {r['title']}\n"
            f"Source URL: {r['href']}\n"
            f"Excerpt: {r['body']}"
        )
    return "\n\n---\n\n".join(formatted)
