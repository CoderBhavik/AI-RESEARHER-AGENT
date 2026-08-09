
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.tools import tool
import os
import requests
from rich import print
from tavily import TavilyClient


load_dotenv()

tavily = TavilyClient(os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query : str, max_results : int = 5) -> list:
    """Search the web for recent and reliable information on a topic . Returns Titles , URLs and snippets."""
    result = tavily.search(query=query, max_results=max_results)

    return result["results"]

@tool
def web_scrape(url : str):
    """Scrap and give clean text content for deeper research"""
    try:
        resp = requests.get(url=url, timeout=8, headers={"User-Agent": "Mozilla/5.0" })
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["style","script", "nav","footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Query could not processed, error : {e}"

# print(web_search.invoke("What is stock market?"))