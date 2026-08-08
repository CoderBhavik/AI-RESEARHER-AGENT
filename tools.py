
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
def web_search(query : str) -> str:
    """Search the web for recent and reliable information on a topic . Returns Titles , URLs and snippets."""
    result = tavily.search(query=query, max_results=5)

    out = []

    for r in result["results"]:
        out.append(
            f"title : {r["title"]}\nurl : {r["url"]}\ncontent : {r["content"][:350]}"
        )
    return "/n----/n".join(out)

@tool
def web_scrap(url : str):
    """Scrap and give clean text content for deeper research"""
    try:
        resp = requests.get(url=url, timeout=8, headers={"User-Agent": "Mozilla/5.0" })
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["style","script", "nav","footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3500]
    except Exception as e:
        return f"Query could not processed, error : {e}"
