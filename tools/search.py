import requests
from urllib.parse import urlencode

def web_search(query: str, top_k: int = 3) -> str:
    """
    Perform a web search via Bing Web Search API and return the top_k snippets.
    Expects SEARCH_API_KEY and SEARCH_ENDPOINT in env_vars.
    """
    from nearai import Environment
    env = Environment.current()
    api_key  = env.env_vars.get("SEARCH_API_KEY")
    endpoint = env.env_vars.get("SEARCH_ENDPOINT")
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params  = {"q": query, "count": top_k}
    resp = requests.get(endpoint, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("webPages", {}).get("value", [])
    # Join snippets into a single answer
    snippets = [f"- {p['name']}: {p['snippet']}" for p in pages]
    return "\n".join(snippets) if snippets else "No results found."
