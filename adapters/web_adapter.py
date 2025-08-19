import httpx
from bs4 import BeautifulSoup

def fetch_web(url: str) -> dict:
    with httpx.Client(timeout=20, headers={"User-Agent": "W3bStitch/1.0"}) as c:
        r = c.get(url, follow_redirects=True)
        r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    title = (soup.title.string.strip() if soup.title and soup.title.string else None)
    meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    desc = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else None
    return {
        "platform": "web",
        "url": url,
        "title": title,
        "description": desc
    }
